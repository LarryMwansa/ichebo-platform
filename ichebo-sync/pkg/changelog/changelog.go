// Package changelog defines the append-only ChangeLog entry type,
// the Operation constants, and the Log interface.
//
// The ChangeLog is the engine's memory: every local write is recorded here
// as an immutable fact. Entries are never updated or deleted.
//
// Non-negotiable invariants (DOC C §3.2):
//   - Append-only: rows are never modified or deleted.
//   - PayloadHash: SHA-256 of the JSON-serialised entity at write time.
//   - Atomic: every entity write and its changelog entry share one transaction.
//   - Timestamps: ChangedAt uses pkg/clock HLC — never time.Now() directly.
package changelog

import (
	"github.com/google/uuid"
	"github.com/ichebo/sync/pkg/clock"
)

// Operation is the type of change recorded in a ChangeLog entry.
type Operation string

const (
	OpCreate Operation = "CREATE"
	OpUpdate Operation = "UPDATE"
	OpDelete Operation = "DELETE"
)

// Entry is one immutable record in the ChangeLog.
// Maps 1:1 to a row in the SQLite changelog table.
type Entry struct {
	ID          uuid.UUID        // unique ID for this change event
	EntityType  string           // "record" | "activity" | "relationship" | "member"
	EntityID    uuid.UUID        // the entity that changed
	Operation   Operation        // what happened
	ChangedAt   clock.Timestamp  // HLC timestamp — never time.Now()
	SyncedAt    *clock.Timestamp // nil until successfully acknowledged by cloud
	DeviceID    uuid.UUID        // which installation made this change
	PayloadHash string           // SHA-256 hex of the entity JSON at change time
}

// Log is the interface all packages use to interact with the ChangeLog.
// The store package provides the production implementation backed by SQLite.
// Tests use an in-memory implementation.
type Log interface {
	// Append adds a new entry. Must be called inside a store transaction.
	// The caller (domain engine) must never call this directly —
	// the store.TxStore.ChangeLog() writer is the only sanctioned call site.
	Append(entry Entry) error

	// Pending returns all entries where SyncedAt IS NULL,
	// ordered by ChangedAt ASC (oldest first — preserve causality).
	Pending(deviceID uuid.UUID) ([]Entry, error)

	// MarkSynced sets SyncedAt = now() on the given entry IDs.
	// Called by pkg/push after the cloud acknowledges receipt.
	MarkSynced(ids []uuid.UUID) error

	// LastSyncedAt returns the most recent SyncedAt HLC timestamp for this device.
	// Used as the since= parameter in pull requests.
	LastSyncedAt(deviceID uuid.UUID) (*clock.Timestamp, error)

	// Count returns the number of pending (unsynced) entries for this device.
	// Used by pkg/status to populate PendingCount.
	Count(deviceID uuid.UUID) (int, error)
}

// Writer is the append-only view of the ChangeLog exposed inside a transaction.
// TxStore.ChangeLog() returns Writer — reads are not available inside a Tx.
type Writer interface {
	Append(entry Entry) error
}
