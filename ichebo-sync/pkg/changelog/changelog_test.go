// Tests for the changelog package — verifies Entry construction, Operation
// constants, and the in-memory Log implementation used throughout tests.
package changelog_test

import (
	"testing"
	"time"

	"github.com/google/uuid"
	"github.com/ichebo/sync/pkg/changelog"
	"github.com/ichebo/sync/pkg/clock"
)

// memLog is a minimal in-memory Log used across changelog tests.
// Production code uses the SQLite-backed implementation in pkg/store.
type memLog struct {
	entries []changelog.Entry
}

func (m *memLog) Append(e changelog.Entry) error {
	m.entries = append(m.entries, e)
	return nil
}

func (m *memLog) Pending(deviceID uuid.UUID) ([]changelog.Entry, error) {
	var out []changelog.Entry
	for _, e := range m.entries {
		if e.DeviceID == deviceID && e.SyncedAt == nil {
			out = append(out, e)
		}
	}
	return out, nil
}

func (m *memLog) MarkSynced(ids []uuid.UUID) error {
	set := make(map[uuid.UUID]struct{}, len(ids))
	for _, id := range ids {
		set[id] = struct{}{}
	}
	now := clock.New().Now()
	for i, e := range m.entries {
		if _, ok := set[e.ID]; ok {
			m.entries[i].SyncedAt = &now
		}
	}
	return nil
}

func (m *memLog) LastSyncedAt(deviceID uuid.UUID) (*clock.Timestamp, error) {
	var latest *clock.Timestamp
	for _, e := range m.entries {
		if e.DeviceID == deviceID && e.SyncedAt != nil {
			if latest == nil || e.SyncedAt.Physical.After(latest.Physical) {
				ts := *e.SyncedAt
				latest = &ts
			}
		}
	}
	return latest, nil
}

func (m *memLog) Count(deviceID uuid.UUID) (int, error) {
	n := 0
	for _, e := range m.entries {
		if e.DeviceID == deviceID && e.SyncedAt == nil {
			n++
		}
	}
	return n, nil
}

// ── Operation constants ───────────────────────────────────────────────────────

func TestOperationConstants(t *testing.T) {
	if changelog.OpCreate != "CREATE" {
		t.Errorf("OpCreate = %q, want CREATE", changelog.OpCreate)
	}
	if changelog.OpUpdate != "UPDATE" {
		t.Errorf("OpUpdate = %q, want UPDATE", changelog.OpUpdate)
	}
	if changelog.OpDelete != "DELETE" {
		t.Errorf("OpDelete = %q, want DELETE", changelog.OpDelete)
	}
}

// ── Entry construction ────────────────────────────────────────────────────────

func TestEntry_Fields(t *testing.T) {
	deviceID := uuid.New()
	entityID := uuid.New()
	ts := clock.New().Now()

	e := changelog.Entry{
		ID:          uuid.New(),
		EntityType:  "record",
		EntityID:    entityID,
		Operation:   changelog.OpCreate,
		ChangedAt:   ts,
		DeviceID:    deviceID,
		PayloadHash: "deadbeef",
	}

	if e.EntityType != "record" {
		t.Errorf("EntityType = %q, want record", e.EntityType)
	}
	if e.Operation != changelog.OpCreate {
		t.Errorf("Operation = %q, want CREATE", e.Operation)
	}
	if e.SyncedAt != nil {
		t.Errorf("SyncedAt should be nil on a fresh entry")
	}
}

// ── In-memory Log: Append + Pending ──────────────────────────────────────────

func TestMemLog_AppendAndPending(t *testing.T) {
	log := &memLog{}
	deviceID := uuid.New()

	e := makeEntry(deviceID, "record", changelog.OpCreate)
	if err := log.Append(e); err != nil {
		t.Fatalf("Append: %v", err)
	}

	pending, err := log.Pending(deviceID)
	if err != nil {
		t.Fatalf("Pending: %v", err)
	}
	if len(pending) != 1 {
		t.Fatalf("Pending len = %d, want 1", len(pending))
	}
	if pending[0].ID != e.ID {
		t.Errorf("ID mismatch")
	}
}

// ── Pending is isolated by device ID ─────────────────────────────────────────

func TestMemLog_Pending_IsolatedByDevice(t *testing.T) {
	log := &memLog{}
	d1, d2 := uuid.New(), uuid.New()

	_ = log.Append(makeEntry(d1, "record", changelog.OpCreate))
	_ = log.Append(makeEntry(d2, "activity", changelog.OpUpdate))

	p1, _ := log.Pending(d1)
	p2, _ := log.Pending(d2)

	if len(p1) != 1 {
		t.Errorf("d1 pending = %d, want 1", len(p1))
	}
	if len(p2) != 1 {
		t.Errorf("d2 pending = %d, want 1", len(p2))
	}
	if p1[0].DeviceID != d1 {
		t.Errorf("wrong DeviceID in d1 result")
	}
}

// ── MarkSynced removes entries from Pending ───────────────────────────────────

func TestMemLog_MarkSynced(t *testing.T) {
	log := &memLog{}
	deviceID := uuid.New()

	e1 := makeEntry(deviceID, "record", changelog.OpCreate)
	e2 := makeEntry(deviceID, "activity", changelog.OpUpdate)
	_ = log.Append(e1)
	_ = log.Append(e2)

	if err := log.MarkSynced([]uuid.UUID{e1.ID}); err != nil {
		t.Fatalf("MarkSynced: %v", err)
	}

	pending, _ := log.Pending(deviceID)
	if len(pending) != 1 {
		t.Fatalf("after MarkSynced(e1): pending = %d, want 1", len(pending))
	}
	if pending[0].ID != e2.ID {
		t.Errorf("wrong entry still pending")
	}
}

// ── MarkSynced of all entries leaves Pending empty ───────────────────────────

func TestMemLog_MarkSynced_All(t *testing.T) {
	log := &memLog{}
	deviceID := uuid.New()
	var ids []uuid.UUID
	for i := 0; i < 5; i++ {
		e := makeEntry(deviceID, "record", changelog.OpCreate)
		_ = log.Append(e)
		ids = append(ids, e.ID)
	}

	_ = log.MarkSynced(ids)

	pending, _ := log.Pending(deviceID)
	if len(pending) != 0 {
		t.Errorf("Pending after MarkSynced all = %d, want 0", len(pending))
	}
}

// ── Count returns pending entry count ────────────────────────────────────────

func TestMemLog_Count(t *testing.T) {
	log := &memLog{}
	deviceID := uuid.New()

	for i := 0; i < 4; i++ {
		_ = log.Append(makeEntry(deviceID, "record", changelog.OpCreate))
	}

	n, err := log.Count(deviceID)
	if err != nil {
		t.Fatalf("Count: %v", err)
	}
	if n != 4 {
		t.Errorf("Count = %d, want 4", n)
	}
}

// ── LastSyncedAt is nil when nothing synced ───────────────────────────────────

func TestMemLog_LastSyncedAt_NilWhenNoneSynced(t *testing.T) {
	log := &memLog{}
	deviceID := uuid.New()
	_ = log.Append(makeEntry(deviceID, "record", changelog.OpCreate))

	ts, err := log.LastSyncedAt(deviceID)
	if err != nil {
		t.Fatalf("LastSyncedAt: %v", err)
	}
	if ts != nil {
		t.Errorf("LastSyncedAt = %v, want nil before any sync", ts)
	}
}

// ── LastSyncedAt returns most recent SyncedAt ─────────────────────────────────

func TestMemLog_LastSyncedAt_AfterSync(t *testing.T) {
	log := &memLog{}
	deviceID := uuid.New()
	e := makeEntry(deviceID, "record", changelog.OpCreate)
	_ = log.Append(e)
	_ = log.MarkSynced([]uuid.UUID{e.ID})

	ts, err := log.LastSyncedAt(deviceID)
	if err != nil {
		t.Fatalf("LastSyncedAt: %v", err)
	}
	if ts == nil {
		t.Errorf("LastSyncedAt = nil after MarkSynced, want non-nil")
	}
	if ts.Physical.IsZero() {
		t.Errorf("LastSyncedAt.Physical is zero")
	}
}

// ── AppendOnly: entries are never modified on re-Append ──────────────────────

func TestMemLog_AppendOnly(t *testing.T) {
	log := &memLog{}
	deviceID := uuid.New()
	e := makeEntry(deviceID, "record", changelog.OpCreate)
	_ = log.Append(e)

	// Append a second entry — first entry must be unchanged
	_ = log.Append(makeEntry(deviceID, "record", changelog.OpUpdate))

	pending, _ := log.Pending(deviceID)
	if len(pending) != 2 {
		t.Fatalf("expected 2 entries, got %d", len(pending))
	}
	if pending[0].ID != e.ID {
		t.Errorf("first entry changed — append-only invariant violated")
	}
}

// ── helpers ──────────────────────────────────────────────────────────────────

func makeEntry(deviceID uuid.UUID, entityType string, op changelog.Operation) changelog.Entry {
	return changelog.Entry{
		ID:          uuid.New(),
		EntityType:  entityType,
		EntityID:    uuid.New(),
		Operation:   op,
		ChangedAt:   clock.Timestamp{Physical: time.Now().UTC()},
		DeviceID:    deviceID,
		PayloadHash: "testhash",
	}
}
