// Package store provides the local SQLite abstraction layer.
//
// Store is the only place in the codebase that holds a database connection.
// All packages read and write through Store — never raw SQL elsewhere.
//
// SQLite is configured with (DOC C §3.4):
//   - WAL journal mode (concurrent reads + one writer)
//   - busy_timeout=5000ms
//   - foreign_keys=ON
//   - synchronous=NORMAL (safe + fast in WAL mode)
package store

import (
	"database/sql"
	"fmt"

	_ "github.com/mattn/go-sqlite3"

	"github.com/google/uuid"
	"github.com/ichebo/sync/pkg/changelog"
	"github.com/ichebo/sync/pkg/clock"
)

// Store is the interface every package uses to read and write local data.
// Production: SQLite. Tests: MemoryStore.
type Store interface {
	// ChangeLog returns the full Log interface for reads and mark-synced.
	ChangeLog() changelog.Log

	// Tx begins a transaction. All writes within fn are atomic.
	// CRITICAL: domain engines MUST use Tx for all writes so that
	// entity write + ChangeLog.Append are always committed together.
	Tx(fn func(tx TxStore) error) error

	// Close releases the database connection.
	Close() error
}

// TxStore is the write-only view available inside a transaction.
// Reads are deliberately excluded to prevent read-modify-write phantom reads.
type TxStore interface {
	// ChangeLog returns the append-only writer for this transaction.
	ChangeLog() changelog.Writer
}

// Open opens (or creates) a SQLite database at path with the required pragmas.
func Open(path string) (Store, error) {
	db, err := sql.Open("sqlite3", path)
	if err != nil {
		return nil, fmt.Errorf("store.Open: %w", err)
	}

	pragmas := []string{
		"PRAGMA journal_mode=WAL",
		"PRAGMA busy_timeout=5000",
		"PRAGMA foreign_keys=ON",
		"PRAGMA synchronous=NORMAL",
	}
	for _, p := range pragmas {
		if _, err := db.Exec(p); err != nil {
			db.Close()
			return nil, fmt.Errorf("store.Open pragma %q: %w", p, err)
		}
	}

	s := &sqliteStore{db: db}
	if err := s.migrate(); err != nil {
		db.Close()
		return nil, fmt.Errorf("store.Open migrate: %w", err)
	}
	return s, nil
}

// sqliteStore is the production Store backed by SQLite.
type sqliteStore struct {
	db  *sql.DB
	log *sqliteLog
}

func (s *sqliteStore) ChangeLog() changelog.Log {
	if s.log == nil {
		s.log = &sqliteLog{db: s.db}
	}
	return s.log
}

func (s *sqliteStore) Tx(fn func(tx TxStore) error) error {
	tx, err := s.db.Begin()
	if err != nil {
		return fmt.Errorf("store.Tx: begin: %w", err)
	}
	txStore := &sqliteTxStore{tx: tx}
	if err := fn(txStore); err != nil {
		tx.Rollback()
		return err
	}
	return tx.Commit()
}

func (s *sqliteStore) Close() error { return s.db.Close() }

// migrate creates all required tables if they don't exist.
func (s *sqliteStore) migrate() error {
	_, err := s.db.Exec(`
		CREATE TABLE IF NOT EXISTS changelog (
			id           TEXT PRIMARY KEY,
			entity_type  TEXT NOT NULL,
			entity_id    TEXT NOT NULL,
			operation    TEXT NOT NULL CHECK(operation IN ('CREATE','UPDATE','DELETE')),
			changed_at   TEXT NOT NULL,
			synced_at    TEXT,
			device_id    TEXT NOT NULL,
			payload_hash TEXT NOT NULL
		);
		CREATE INDEX IF NOT EXISTS idx_changelog_synced_at ON changelog(synced_at);
		CREATE INDEX IF NOT EXISTS idx_changelog_entity    ON changelog(entity_id, entity_type);

		CREATE TABLE IF NOT EXISTS conflict_queue (
			id             TEXT PRIMARY KEY,
			entity_type    TEXT NOT NULL,
			entity_id      TEXT NOT NULL,
			local_version  TEXT NOT NULL,
			cloud_version  TEXT NOT NULL,
			created_at     TEXT NOT NULL,
			resolved_at    TEXT,
			resolution     TEXT
		);

		CREATE TABLE IF NOT EXISTS settings (
			key   TEXT PRIMARY KEY,
			value TEXT NOT NULL
		);
	`)
	return err
}

// ── sqliteTxStore ─────────────────────────────────────────────────────────────

type sqliteTxStore struct {
	tx  *sql.Tx
	log *txLog
}

func (t *sqliteTxStore) ChangeLog() changelog.Writer {
	if t.log == nil {
		t.log = &txLog{tx: t.tx}
	}
	return t.log
}

// ── sqliteLog ─────────────────────────────────────────────────────────────────

type sqliteLog struct{ db *sql.DB }

func (l *sqliteLog) Append(e changelog.Entry) error {
	_, err := l.db.Exec(`
		INSERT INTO changelog (id, entity_type, entity_id, operation, changed_at, device_id, payload_hash)
		VALUES (?, ?, ?, ?, ?, ?, ?)`,
		e.ID.String(), e.EntityType, e.EntityID.String(),
		string(e.Operation), e.ChangedAt.String(),
		e.DeviceID.String(), e.PayloadHash,
	)
	return err
}

func (l *sqliteLog) Pending(deviceID uuid.UUID) ([]changelog.Entry, error) {
	rows, err := l.db.Query(`
		SELECT id, entity_type, entity_id, operation, changed_at, device_id, payload_hash
		FROM changelog
		WHERE synced_at IS NULL AND device_id = ?
		ORDER BY changed_at ASC`, deviceID.String())
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	return scanEntries(rows)
}

func (l *sqliteLog) MarkSynced(ids []uuid.UUID) error {
	now := clock.New().Now().String()
	for _, id := range ids {
		if _, err := l.db.Exec(`UPDATE changelog SET synced_at = ? WHERE id = ?`,
			now, id.String()); err != nil {
			return err
		}
	}
	return nil
}

func (l *sqliteLog) LastSyncedAt(deviceID uuid.UUID) (*clock.Timestamp, error) {
	var s sql.NullString
	err := l.db.QueryRow(`
		SELECT synced_at FROM changelog
		WHERE device_id = ? AND synced_at IS NOT NULL
		ORDER BY synced_at DESC LIMIT 1`, deviceID.String()).Scan(&s)
	if err == sql.ErrNoRows {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	if !s.Valid {
		return nil, nil
	}
	ts := clock.Parse(s.String)
	return &ts, nil
}

func (l *sqliteLog) Count(deviceID uuid.UUID) (int, error) {
	var n int
	err := l.db.QueryRow(`
		SELECT COUNT(*) FROM changelog WHERE synced_at IS NULL AND device_id = ?`,
		deviceID.String()).Scan(&n)
	return n, err
}

// ── txLog ─────────────────────────────────────────────────────────────────────

type txLog struct{ tx *sql.Tx }

func (l *txLog) Append(e changelog.Entry) error {
	_, err := l.tx.Exec(`
		INSERT INTO changelog (id, entity_type, entity_id, operation, changed_at, device_id, payload_hash)
		VALUES (?, ?, ?, ?, ?, ?, ?)`,
		e.ID.String(), e.EntityType, e.EntityID.String(),
		string(e.Operation), e.ChangedAt.String(),
		e.DeviceID.String(), e.PayloadHash,
	)
	return err
}

// ── helpers ───────────────────────────────────────────────────────────────────

func scanEntries(rows *sql.Rows) ([]changelog.Entry, error) {
	var entries []changelog.Entry
	for rows.Next() {
		var (
			id, entityType, entityID, operation, changedAt, deviceID, payloadHash string
		)
		if err := rows.Scan(&id, &entityType, &entityID, &operation, &changedAt, &deviceID, &payloadHash); err != nil {
			return nil, err
		}
		entry := changelog.Entry{
			ID:          mustParseUUID(id),
			EntityType:  entityType,
			EntityID:    mustParseUUID(entityID),
			Operation:   changelog.Operation(operation),
			ChangedAt:   clock.Parse(changedAt),
			DeviceID:    mustParseUUID(deviceID),
			PayloadHash: payloadHash,
		}
		entries = append(entries, entry)
	}
	return entries, rows.Err()
}

func mustParseUUID(s string) uuid.UUID {
	id, _ := uuid.Parse(s)
	return id
}
