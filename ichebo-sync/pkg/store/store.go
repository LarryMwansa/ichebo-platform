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

	// Members returns the member read/write store.
	Members() MemberStore

	// Records returns the record read/write store.
	Records() RecordStore

	// Activities returns the activity read/write store.
	Activities() ActivityStore

	// Tx begins a transaction. All writes within fn are atomic.
	// CRITICAL: domain engines MUST use Tx for all writes so that
	// entity write + ChangeLog.Append are always committed together.
	Tx(fn func(tx TxStore) error) error

	// Close releases the database connection.
	Close() error
}

// ── Domain store interfaces ───────────────────────────────────────────────────

// MemberStore provides read access to the members table.
// Writes always go through Tx so the ChangeLog entry is atomic.
type MemberStore interface {
	// Get returns a member by UUID. Returns sql.ErrNoRows if not found.
	Get(id uuid.UUID) (*Member, error)
	// List returns all non-deleted members for a tenant, ordered by display_name.
	List(tenantID uuid.UUID) ([]*Member, error)
	// Upsert inserts or replaces a member row. Called inside Tx by domain engines.
	Upsert(m *Member) error
}

// RecordStore provides read access to the records table.
type RecordStore interface {
	Get(id uuid.UUID) (*Record, error)
	List(tenantID uuid.UUID) ([]*Record, error)
	Upsert(r *Record) error
}

// ActivityStore provides read access to the activities table.
type ActivityStore interface {
	Get(id uuid.UUID) (*Activity, error)
	List(tenantID uuid.UUID) ([]*Activity, error)
	Upsert(a *Activity) error
}

// ── Domain value types ────────────────────────────────────────────────────────

// Member is the local representation of a community member (UserPermission row).
type Member struct {
	ID               uuid.UUID
	TenantID         uuid.UUID
	Email            string
	DisplayName      string
	FirstName        string
	LastName         string
	Phone            string
	AvatarURL        string
	CompetenceLevel  int
	IsActive         bool
	ShepherdID       *uuid.UUID
	CustomFields     string // JSON
	CreatedBy        uuid.UUID
	CreatedAt        string
	UpdatedAt        string
	DeletedAt        *string
}

// Record is the local representation of a Record row (ADR-003 single table).
type Record struct {
	ID           uuid.UUID
	TenantID     uuid.UUID
	RecordClass  string
	RecordFamily string
	RecordType   string
	Title        string
	Status       string
	CustomFields string // JSON
	Metadata     string // JSON
	Permissions  string // JSON
	CreatedBy    uuid.UUID
	CreatedAt    string
	UpdatedAt    string
	DeletedAt    *string
}

// Activity is the local representation of an Activity row.
type Activity struct {
	ID                uuid.UUID
	TenantID          uuid.UUID
	ActivityType      string
	Title             string
	Description       string
	Status            string
	Progress          int
	AssignedTo        *uuid.UUID
	LinkedRecordID    *uuid.UUID
	ParentActivityID  *uuid.UUID
	DueAt             *string
	ScheduledAt       *string
	CompletedAt       *string
	SourceApp         string
	Metadata          string // JSON
	CreatedBy         uuid.UUID
	CreatedAt         string
	UpdatedAt         string
	DeletedAt         *string
}

// TxStore is the write-only view available inside a transaction.
// Reads are deliberately excluded to prevent read-modify-write phantom reads.
type TxStore interface {
	// ChangeLog returns the append-only writer for this transaction.
	ChangeLog() changelog.Writer
	// Domain write stores — each Upsert also calls ChangeLog().Append atomically.
	Members() MemberStore
	Records() RecordStore
	Activities() ActivityStore
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

func (s *sqliteStore) Members() MemberStore      { return &sqliteMemberStore{q: s.db} }
func (s *sqliteStore) Records() RecordStore      { return &sqliteRecordStore{q: s.db} }
func (s *sqliteStore) Activities() ActivityStore { return &sqliteActivityStore{q: s.db} }

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
// Tables are append-only additions — never destructive alterations.
func (s *sqliteStore) migrate() error {
	_, err := s.db.Exec(`
		-- ── Sync infrastructure ───────────────────────────────────────────────

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

		-- ── Domain tables (Flutter reads these directly via sqflite) ──────────

		CREATE TABLE IF NOT EXISTS members (
			id                TEXT PRIMARY KEY,
			tenant_id         TEXT NOT NULL,
			email             TEXT,
			display_name      TEXT,
			first_name        TEXT,
			last_name         TEXT,
			phone             TEXT,
			avatar_url        TEXT,
			competence_level  INTEGER NOT NULL DEFAULT 0,
			is_active         INTEGER NOT NULL DEFAULT 1,
			shepherd_id       TEXT,
			custom_fields     TEXT NOT NULL DEFAULT '{}',
			created_by        TEXT NOT NULL,
			created_at        TEXT NOT NULL,
			updated_at        TEXT NOT NULL,
			deleted_at        TEXT
		);
		CREATE INDEX IF NOT EXISTS idx_members_tenant_id    ON members(tenant_id);
		CREATE INDEX IF NOT EXISTS idx_members_email        ON members(email);
		CREATE INDEX IF NOT EXISTS idx_members_deleted_at   ON members(deleted_at);

		CREATE TABLE IF NOT EXISTS records (
			id             TEXT PRIMARY KEY,
			tenant_id      TEXT NOT NULL,
			record_class   TEXT NOT NULL CHECK(record_class IN ('personal','organizational','governance')),
			record_family  TEXT NOT NULL,
			record_type    TEXT NOT NULL,
			title          TEXT NOT NULL DEFAULT '',
			status         TEXT NOT NULL DEFAULT 'active',
			custom_fields  TEXT NOT NULL DEFAULT '{}',
			metadata       TEXT NOT NULL DEFAULT '{}',
			permissions    TEXT NOT NULL DEFAULT '{}',
			created_by     TEXT NOT NULL,
			created_at     TEXT NOT NULL,
			updated_at     TEXT NOT NULL,
			deleted_at     TEXT
		);
		CREATE INDEX IF NOT EXISTS idx_records_tenant_id    ON records(tenant_id);
		CREATE INDEX IF NOT EXISTS idx_records_class        ON records(record_class);
		CREATE INDEX IF NOT EXISTS idx_records_family       ON records(record_family);
		CREATE INDEX IF NOT EXISTS idx_records_created_by   ON records(created_by);
		CREATE INDEX IF NOT EXISTS idx_records_deleted_at   ON records(deleted_at);

		CREATE TABLE IF NOT EXISTS activities (
			id                   TEXT PRIMARY KEY,
			tenant_id            TEXT NOT NULL,
			activity_type        TEXT NOT NULL,
			title                TEXT NOT NULL DEFAULT '',
			description          TEXT,
			status               TEXT NOT NULL DEFAULT 'pending',
			progress             INTEGER NOT NULL DEFAULT 0,
			assigned_to          TEXT,
			linked_record_id     TEXT,
			parent_activity_id   TEXT,
			due_at               TEXT,
			scheduled_at         TEXT,
			completed_at         TEXT,
			source_app           TEXT,
			metadata             TEXT NOT NULL DEFAULT '{}',
			created_by           TEXT NOT NULL,
			created_at           TEXT NOT NULL,
			updated_at           TEXT NOT NULL,
			deleted_at           TEXT
		);
		CREATE INDEX IF NOT EXISTS idx_activities_tenant_id   ON activities(tenant_id);
		CREATE INDEX IF NOT EXISTS idx_activities_type        ON activities(activity_type);
		CREATE INDEX IF NOT EXISTS idx_activities_assigned_to ON activities(assigned_to);
		CREATE INDEX IF NOT EXISTS idx_activities_status      ON activities(status);
		CREATE INDEX IF NOT EXISTS idx_activities_deleted_at  ON activities(deleted_at);

		CREATE TABLE IF NOT EXISTS activity_log (
			id           TEXT PRIMARY KEY,
			activity_id  TEXT NOT NULL REFERENCES activities(id),
			from_status  TEXT,
			to_status    TEXT NOT NULL,
			note         TEXT,
			changed_by   TEXT NOT NULL,
			changed_at   TEXT NOT NULL
		);
		CREATE INDEX IF NOT EXISTS idx_activity_log_activity ON activity_log(activity_id);

		CREATE TABLE IF NOT EXISTS relationships (
			id                TEXT PRIMARY KEY,
			tenant_id         TEXT NOT NULL,
			from_record_id    TEXT NOT NULL REFERENCES records(id),
			to_record_id      TEXT,
			bible_verse_id    TEXT,
			relationship_type TEXT NOT NULL,
			direction         TEXT NOT NULL DEFAULT 'directed',
			strength          TEXT,
			note              TEXT,
			metadata          TEXT NOT NULL DEFAULT '{}',
			created_by        TEXT NOT NULL,
			created_at        TEXT NOT NULL,
			updated_at        TEXT NOT NULL,
			deleted_at        TEXT
		);
		CREATE INDEX IF NOT EXISTS idx_relationships_from   ON relationships(from_record_id);
		CREATE INDEX IF NOT EXISTS idx_relationships_to     ON relationships(to_record_id);
		CREATE INDEX IF NOT EXISTS idx_relationships_deleted ON relationships(deleted_at);
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

func (t *sqliteTxStore) Members() MemberStore      { return &sqliteMemberStore{q: t.tx} }
func (t *sqliteTxStore) Records() RecordStore      { return &sqliteRecordStore{q: t.tx} }
func (t *sqliteTxStore) Activities() ActivityStore { return &sqliteActivityStore{q: t.tx} }

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

func nullableUUID(s sql.NullString) *uuid.UUID {
	if !s.Valid || s.String == "" {
		return nil
	}
	id, err := uuid.Parse(s.String)
	if err != nil {
		return nil
	}
	return &id
}

func nullableString(s sql.NullString) *string {
	if !s.Valid {
		return nil
	}
	return &s.String
}

// querier is satisfied by both *sql.DB and *sql.Tx.
type querier interface {
	QueryRow(query string, args ...any) *sql.Row
	Query(query string, args ...any) (*sql.Rows, error)
	Exec(query string, args ...any) (sql.Result, error)
}

// ── sqliteMemberStore ─────────────────────────────────────────────────────────

type sqliteMemberStore struct{ q querier }

func (s *sqliteMemberStore) Get(id uuid.UUID) (*Member, error) {
	row := s.q.QueryRow(`
		SELECT id, tenant_id, email, display_name, first_name, last_name,
		       phone, avatar_url, competence_level, is_active, shepherd_id,
		       custom_fields, created_by, created_at, updated_at, deleted_at
		FROM members WHERE id = ?`, id.String())
	return scanMember(row)
}

func (s *sqliteMemberStore) List(tenantID uuid.UUID) ([]*Member, error) {
	rows, err := s.q.Query(`
		SELECT id, tenant_id, email, display_name, first_name, last_name,
		       phone, avatar_url, competence_level, is_active, shepherd_id,
		       custom_fields, created_by, created_at, updated_at, deleted_at
		FROM members
		WHERE tenant_id = ? AND deleted_at IS NULL
		ORDER BY display_name ASC`, tenantID.String())
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []*Member
	for rows.Next() {
		m, err := scanMember(rows)
		if err != nil {
			return nil, err
		}
		out = append(out, m)
	}
	return out, rows.Err()
}

func (s *sqliteMemberStore) Upsert(m *Member) error {
	shepherdID := ""
	if m.ShepherdID != nil {
		shepherdID = m.ShepherdID.String()
	}
	_, err := s.q.Exec(`
		INSERT INTO members (id, tenant_id, email, display_name, first_name, last_name,
		    phone, avatar_url, competence_level, is_active, shepherd_id,
		    custom_fields, created_by, created_at, updated_at, deleted_at)
		VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
		ON CONFLICT(id) DO UPDATE SET
		    email=excluded.email, display_name=excluded.display_name,
		    first_name=excluded.first_name, last_name=excluded.last_name,
		    phone=excluded.phone, avatar_url=excluded.avatar_url,
		    competence_level=excluded.competence_level, is_active=excluded.is_active,
		    shepherd_id=excluded.shepherd_id, custom_fields=excluded.custom_fields,
		    updated_at=excluded.updated_at, deleted_at=excluded.deleted_at`,
		m.ID.String(), m.TenantID.String(), m.Email, m.DisplayName,
		m.FirstName, m.LastName, m.Phone, m.AvatarURL,
		m.CompetenceLevel, m.IsActive, shepherdID,
		m.CustomFields, m.CreatedBy.String(), m.CreatedAt, m.UpdatedAt, m.DeletedAt,
	)
	return err
}

type memberScanner interface {
	Scan(dest ...any) error
}

func scanMember(row memberScanner) (*Member, error) {
	var (
		m          Member
		id, tid, cb string
		isActive   int
		shepherdID sql.NullString
		deletedAt  sql.NullString
	)
	err := row.Scan(
		&id, &tid, &m.Email, &m.DisplayName, &m.FirstName, &m.LastName,
		&m.Phone, &m.AvatarURL, &m.CompetenceLevel, &isActive, &shepherdID,
		&m.CustomFields, &cb, &m.CreatedAt, &m.UpdatedAt, &deletedAt,
	)
	if err != nil {
		return nil, err
	}
	m.ID = mustParseUUID(id)
	m.TenantID = mustParseUUID(tid)
	m.CreatedBy = mustParseUUID(cb)
	m.IsActive = isActive == 1
	m.ShepherdID = nullableUUID(shepherdID)
	m.DeletedAt = nullableString(deletedAt)
	return &m, nil
}

// ── sqliteRecordStore ─────────────────────────────────────────────────────────

type sqliteRecordStore struct{ q querier }

func (s *sqliteRecordStore) Get(id uuid.UUID) (*Record, error) {
	row := s.q.QueryRow(`
		SELECT id, tenant_id, record_class, record_family, record_type, title,
		       status, custom_fields, metadata, permissions, created_by, created_at,
		       updated_at, deleted_at
		FROM records WHERE id = ?`, id.String())
	return scanRecord(row)
}

func (s *sqliteRecordStore) List(tenantID uuid.UUID) ([]*Record, error) {
	rows, err := s.q.Query(`
		SELECT id, tenant_id, record_class, record_family, record_type, title,
		       status, custom_fields, metadata, permissions, created_by, created_at,
		       updated_at, deleted_at
		FROM records WHERE tenant_id = ? AND deleted_at IS NULL
		ORDER BY created_at DESC`, tenantID.String())
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []*Record
	for rows.Next() {
		r, err := scanRecord(rows)
		if err != nil {
			return nil, err
		}
		out = append(out, r)
	}
	return out, rows.Err()
}

func (s *sqliteRecordStore) Upsert(r *Record) error {
	_, err := s.q.Exec(`
		INSERT INTO records (id, tenant_id, record_class, record_family, record_type,
		    title, status, custom_fields, metadata, permissions,
		    created_by, created_at, updated_at, deleted_at)
		VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
		ON CONFLICT(id) DO UPDATE SET
		    title=excluded.title, status=excluded.status,
		    custom_fields=excluded.custom_fields, metadata=excluded.metadata,
		    permissions=excluded.permissions, updated_at=excluded.updated_at,
		    deleted_at=excluded.deleted_at`,
		r.ID.String(), r.TenantID.String(), r.RecordClass, r.RecordFamily,
		r.RecordType, r.Title, r.Status, r.CustomFields, r.Metadata,
		r.Permissions, r.CreatedBy.String(), r.CreatedAt, r.UpdatedAt, r.DeletedAt,
	)
	return err
}

type recordScanner interface {
	Scan(dest ...any) error
}

func scanRecord(row recordScanner) (*Record, error) {
	var (
		r         Record
		id, tid, cb string
		deletedAt sql.NullString
	)
	err := row.Scan(
		&id, &tid, &r.RecordClass, &r.RecordFamily, &r.RecordType,
		&r.Title, &r.Status, &r.CustomFields, &r.Metadata, &r.Permissions,
		&cb, &r.CreatedAt, &r.UpdatedAt, &deletedAt,
	)
	if err != nil {
		return nil, err
	}
	r.ID = mustParseUUID(id)
	r.TenantID = mustParseUUID(tid)
	r.CreatedBy = mustParseUUID(cb)
	r.DeletedAt = nullableString(deletedAt)
	return &r, nil
}

// ── sqliteActivityStore ───────────────────────────────────────────────────────

type sqliteActivityStore struct{ q querier }

func (s *sqliteActivityStore) Get(id uuid.UUID) (*Activity, error) {
	row := s.q.QueryRow(`
		SELECT id, tenant_id, activity_type, title, description, status, progress,
		       assigned_to, linked_record_id, parent_activity_id, due_at, scheduled_at,
		       completed_at, source_app, metadata, created_by, created_at, updated_at, deleted_at
		FROM activities WHERE id = ?`, id.String())
	return scanActivity(row)
}

func (s *sqliteActivityStore) List(tenantID uuid.UUID) ([]*Activity, error) {
	rows, err := s.q.Query(`
		SELECT id, tenant_id, activity_type, title, description, status, progress,
		       assigned_to, linked_record_id, parent_activity_id, due_at, scheduled_at,
		       completed_at, source_app, metadata, created_by, created_at, updated_at, deleted_at
		FROM activities WHERE tenant_id = ? AND deleted_at IS NULL
		ORDER BY created_at DESC`, tenantID.String())
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []*Activity
	for rows.Next() {
		a, err := scanActivity(rows)
		if err != nil {
			return nil, err
		}
		out = append(out, a)
	}
	return out, rows.Err()
}

func (s *sqliteActivityStore) Upsert(a *Activity) error {  //nolint:unused
	assignedTo := ""
	if a.AssignedTo != nil {
		assignedTo = a.AssignedTo.String()
	}
	linkedRecord := ""
	if a.LinkedRecordID != nil {
		linkedRecord = a.LinkedRecordID.String()
	}
	parentID := ""
	if a.ParentActivityID != nil {
		parentID = a.ParentActivityID.String()
	}
	_, err := s.q.Exec(`
		INSERT INTO activities (id, tenant_id, activity_type, title, description, status,
		    progress, assigned_to, linked_record_id, parent_activity_id,
		    due_at, scheduled_at, completed_at, source_app, metadata,
		    created_by, created_at, updated_at, deleted_at)
		VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
		ON CONFLICT(id) DO UPDATE SET
		    title=excluded.title, description=excluded.description, status=excluded.status,
		    progress=excluded.progress, assigned_to=excluded.assigned_to,
		    linked_record_id=excluded.linked_record_id, due_at=excluded.due_at,
		    scheduled_at=excluded.scheduled_at, completed_at=excluded.completed_at,
		    metadata=excluded.metadata, updated_at=excluded.updated_at,
		    deleted_at=excluded.deleted_at`,
		a.ID.String(), a.TenantID.String(), a.ActivityType, a.Title, a.Description,
		a.Status, a.Progress, assignedTo, linkedRecord, parentID,
		a.DueAt, a.ScheduledAt, a.CompletedAt, a.SourceApp, a.Metadata,
		a.CreatedBy.String(), a.CreatedAt, a.UpdatedAt, a.DeletedAt,
	)
	return err
}

type activityScanner interface {
	Scan(dest ...any) error
}

func scanActivity(row activityScanner) (*Activity, error) {
	var (
		a                                     Activity
		id, tid, cb                           string
		assignedTo, linkedRecord, parentID    sql.NullString
		dueAt, scheduledAt, completedAt       sql.NullString
		deletedAt                             sql.NullString
	)
	err := row.Scan(
		&id, &tid, &a.ActivityType, &a.Title, &a.Description, &a.Status, &a.Progress,
		&assignedTo, &linkedRecord, &parentID, &dueAt, &scheduledAt,
		&completedAt, &a.SourceApp, &a.Metadata, &cb, &a.CreatedAt, &a.UpdatedAt, &deletedAt,
	)
	if err != nil {
		return nil, err
	}
	a.ID = mustParseUUID(id)
	a.TenantID = mustParseUUID(tid)
	a.CreatedBy = mustParseUUID(cb)
	a.AssignedTo = nullableUUID(assignedTo)
	a.LinkedRecordID = nullableUUID(linkedRecord)
	a.ParentActivityID = nullableUUID(parentID)
	a.DueAt = nullableString(dueAt)
	a.ScheduledAt = nullableString(scheduledAt)
	a.CompletedAt = nullableString(completedAt)
	a.DeletedAt = nullableString(deletedAt)
	return &a, nil
}
