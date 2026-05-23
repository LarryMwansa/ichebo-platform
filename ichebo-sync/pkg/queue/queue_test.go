// Tests for the queue package — verifies Add, Pending, Count, Resolve using
// a real in-memory SQLite database.
package queue_test

import (
	"database/sql"
	"encoding/json"
	"testing"
	"time"

	_ "github.com/mattn/go-sqlite3"

	"github.com/google/uuid"
	"github.com/ichebo/sync/pkg/queue"
)

// ── Setup ─────────────────────────────────────────────────────────────────────

func openDB(t *testing.T) *sql.DB {
	t.Helper()
	db, err := sql.Open("sqlite3", ":memory:")
	if err != nil {
		t.Fatalf("open in-memory db: %v", err)
	}
	t.Cleanup(func() { db.Close() })

	_, err = db.Exec(`
		CREATE TABLE conflict_queue (
			id           TEXT PRIMARY KEY,
			entity_type  TEXT NOT NULL,
			entity_id    TEXT NOT NULL,
			local_version TEXT NOT NULL,
			cloud_version TEXT NOT NULL,
			created_at   TEXT NOT NULL,
			resolved_at  TEXT,
			resolution   TEXT
		)`)
	if err != nil {
		t.Fatalf("create conflict_queue table: %v", err)
	}
	return db
}

func makeConflict(entityType string) queue.ConflictEntry {
	return queue.ConflictEntry{
		ID:           uuid.New(),
		EntityType:   entityType,
		EntityID:     uuid.New(),
		LocalVersion: json.RawMessage(`{"id":"local"}`),
		CloudVersion: json.RawMessage(`{"id":"cloud"}`),
		CreatedAt:    time.Now().UTC(),
	}
}

// ── Tests ─────────────────────────────────────────────────────────────────────

// Add stores an entry; Pending returns it; Count reflects it.
func TestQueue_Add_Pending_Count(t *testing.T) {
	q := queue.New(openDB(t))

	e := makeConflict("record")
	if err := q.Add(e); err != nil {
		t.Fatalf("Add: %v", err)
	}

	pending, err := q.Pending()
	if err != nil {
		t.Fatalf("Pending: %v", err)
	}
	if len(pending) != 1 {
		t.Fatalf("Pending len = %d, want 1", len(pending))
	}
	if pending[0].ID != e.ID {
		t.Errorf("ID mismatch: got %v want %v", pending[0].ID, e.ID)
	}
	if pending[0].EntityType != "record" {
		t.Errorf("EntityType = %q, want record", pending[0].EntityType)
	}

	n, err := q.Count()
	if err != nil {
		t.Fatalf("Count: %v", err)
	}
	if n != 1 {
		t.Errorf("Count = %d, want 1", n)
	}
}

// Pending returns entries ordered oldest-first.
func TestQueue_Pending_OrderedOldestFirst(t *testing.T) {
	q := queue.New(openDB(t))

	early := makeConflict("record")
	early.CreatedAt = time.Now().Add(-2 * time.Minute).UTC()

	late := makeConflict("activity")
	late.CreatedAt = time.Now().UTC()

	_ = q.Add(late)
	_ = q.Add(early)

	pending, _ := q.Pending()
	if len(pending) != 2 {
		t.Fatalf("Pending len = %d, want 2", len(pending))
	}
	if !pending[0].CreatedAt.Before(pending[1].CreatedAt) {
		t.Errorf("expected oldest first: got %v then %v", pending[0].CreatedAt, pending[1].CreatedAt)
	}
}

// Resolve with "local" marks the entry resolved; it disappears from Pending.
func TestQueue_Resolve_Local(t *testing.T) {
	q := queue.New(openDB(t))

	e := makeConflict("record")
	_ = q.Add(e)

	if err := q.Resolve(e.ID, "local"); err != nil {
		t.Fatalf("Resolve(local): %v", err)
	}

	pending, _ := q.Pending()
	if len(pending) != 0 {
		t.Errorf("Pending after resolve = %d, want 0", len(pending))
	}

	n, _ := q.Count()
	if n != 0 {
		t.Errorf("Count after resolve = %d, want 0", n)
	}
}

// Resolve with "cloud" also marks the entry resolved.
func TestQueue_Resolve_Cloud(t *testing.T) {
	q := queue.New(openDB(t))

	e := makeConflict("record")
	_ = q.Add(e)

	if err := q.Resolve(e.ID, "cloud"); err != nil {
		t.Fatalf("Resolve(cloud): %v", err)
	}

	pending, _ := q.Pending()
	if len(pending) != 0 {
		t.Errorf("Pending after cloud resolve = %d, want 0", len(pending))
	}
}

// Resolve with an invalid choice returns an error.
func TestQueue_Resolve_InvalidChoice(t *testing.T) {
	q := queue.New(openDB(t))

	e := makeConflict("record")
	_ = q.Add(e)

	if err := q.Resolve(e.ID, "merge"); err == nil {
		t.Error("Resolve(merge): expected error, got nil")
	}
}

// Resolve on an unknown ID returns an error.
func TestQueue_Resolve_UnknownID(t *testing.T) {
	q := queue.New(openDB(t))

	if err := q.Resolve(uuid.New(), "local"); err == nil {
		t.Error("Resolve unknown ID: expected error, got nil")
	}
}

// Resolve an already-resolved entry returns an error.
func TestQueue_Resolve_AlreadyResolved(t *testing.T) {
	q := queue.New(openDB(t))

	e := makeConflict("record")
	_ = q.Add(e)
	_ = q.Resolve(e.ID, "local")

	if err := q.Resolve(e.ID, "cloud"); err == nil {
		t.Error("double resolve: expected error, got nil")
	}
}

// Multiple conflicts — resolving one leaves the other pending.
func TestQueue_Resolve_LeavesOthersPending(t *testing.T) {
	q := queue.New(openDB(t))

	e1 := makeConflict("record")
	e2 := makeConflict("activity")
	_ = q.Add(e1)
	_ = q.Add(e2)

	_ = q.Resolve(e1.ID, "local")

	pending, _ := q.Pending()
	if len(pending) != 1 {
		t.Fatalf("Pending after partial resolve = %d, want 1", len(pending))
	}
	if pending[0].ID != e2.ID {
		t.Errorf("wrong entry still pending")
	}
}

// Count returns 0 for an empty queue.
func TestQueue_Count_Empty(t *testing.T) {
	q := queue.New(openDB(t))

	n, err := q.Count()
	if err != nil {
		t.Fatalf("Count: %v", err)
	}
	if n != 0 {
		t.Errorf("Count on empty queue = %d, want 0", n)
	}
}

// Pending returns nil (not error) when queue is empty.
func TestQueue_Pending_Empty(t *testing.T) {
	q := queue.New(openDB(t))

	entries, err := q.Pending()
	if err != nil {
		t.Fatalf("Pending on empty queue: %v", err)
	}
	if len(entries) != 0 {
		t.Errorf("Pending len = %d, want 0", len(entries))
	}
}
