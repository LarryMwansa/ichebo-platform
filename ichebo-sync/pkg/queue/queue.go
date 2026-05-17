// Package queue manages the ConflictQueue — conflicts that could not be
// auto-resolved and await user review (DOC C §3.9).
//
// UX contract: the ConflictQueue is not an error state. It is a normal,
// occasional part of running a community. The status bar shows it calmly.
package queue

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"time"

	"github.com/google/uuid"
)

// ConflictEntry is one pending conflict awaiting user resolution.
type ConflictEntry struct {
	ID           uuid.UUID
	EntityType   string
	EntityID     uuid.UUID
	LocalVersion json.RawMessage
	CloudVersion json.RawMessage
	CreatedAt    time.Time
	ResolvedAt   *time.Time
	Resolution   *string // "local" | "cloud"
}

// Queue manages the SQLite-backed conflict queue.
type Queue interface {
	Add(entry ConflictEntry) error
	Pending() ([]ConflictEntry, error)
	Count() (int, error)
	// Resolve applies the user's choice:
	//   "local" → write local version to store, push to cloud
	//   "cloud" → write cloud version to store, mark local changelog entry synced
	Resolve(id uuid.UUID, choice string) error
}

// New returns a Queue backed by the given *sql.DB.
// The conflict_queue table must already exist (created by store.Open).
func New(db *sql.DB) Queue {
	return &sqlQueue{db: db}
}

type sqlQueue struct{ db *sql.DB }

func (q *sqlQueue) Add(e ConflictEntry) error {
	_, err := q.db.Exec(`
		INSERT INTO conflict_queue (id, entity_type, entity_id, local_version, cloud_version, created_at)
		VALUES (?, ?, ?, ?, ?, ?)`,
		e.ID.String(), e.EntityType, e.EntityID.String(),
		string(e.LocalVersion), string(e.CloudVersion),
		e.CreatedAt.UTC().Format(time.RFC3339Nano),
	)
	return err
}

func (q *sqlQueue) Pending() ([]ConflictEntry, error) {
	rows, err := q.db.Query(`
		SELECT id, entity_type, entity_id, local_version, cloud_version, created_at
		FROM conflict_queue WHERE resolved_at IS NULL
		ORDER BY created_at ASC`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var entries []ConflictEntry
	for rows.Next() {
		var (
			id, entityType, entityID, localV, cloudV, createdAt string
		)
		if err := rows.Scan(&id, &entityType, &entityID, &localV, &cloudV, &createdAt); err != nil {
			return nil, err
		}
		uid, _ := uuid.Parse(id)
		eid, _ := uuid.Parse(entityID)
		t, _ := time.Parse(time.RFC3339Nano, createdAt)
		entries = append(entries, ConflictEntry{
			ID: uid, EntityType: entityType, EntityID: eid,
			LocalVersion: json.RawMessage(localV),
			CloudVersion: json.RawMessage(cloudV),
			CreatedAt:    t,
		})
	}
	return entries, rows.Err()
}

func (q *sqlQueue) Count() (int, error) {
	var n int
	err := q.db.QueryRow(`SELECT COUNT(*) FROM conflict_queue WHERE resolved_at IS NULL`).Scan(&n)
	return n, err
}

func (q *sqlQueue) Resolve(id uuid.UUID, choice string) error {
	if choice != "local" && choice != "cloud" {
		return fmt.Errorf("queue.Resolve: choice must be 'local' or 'cloud', got %q", choice)
	}
	now := time.Now().UTC().Format(time.RFC3339Nano)
	result, err := q.db.Exec(`
		UPDATE conflict_queue SET resolved_at = ?, resolution = ? WHERE id = ? AND resolved_at IS NULL`,
		now, choice, id.String())
	if err != nil {
		return err
	}
	n, _ := result.RowsAffected()
	if n == 0 {
		return fmt.Errorf("queue.Resolve: conflict %s not found or already resolved", id)
	}
	return nil
}
