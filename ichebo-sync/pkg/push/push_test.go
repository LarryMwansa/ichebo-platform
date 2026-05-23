// Tests for the push package — verifies Run, buildPayload, batchEntries using
// in-memory fakes for all dependencies.
package push_test

import (
	"context"
	"encoding/json"
	"errors"
	"testing"
	"time"

	"github.com/google/uuid"
	"github.com/ichebo/sync/engines/engine"
	"github.com/ichebo/sync/pkg/changelog"
	"github.com/ichebo/sync/pkg/clock"
	"github.com/ichebo/sync/pkg/device"
	"github.com/ichebo/sync/pkg/push"
	"github.com/ichebo/sync/pkg/status"
	"github.com/ichebo/sync/pkg/store"
)

// ── Fakes ─────────────────────────────────────────────────────────────────────

type fakeLog struct {
	entries  []changelog.Entry
	synced   []uuid.UUID
}

func (f *fakeLog) Append(e changelog.Entry) error {
	f.entries = append(f.entries, e)
	return nil
}

func (f *fakeLog) Pending(deviceID uuid.UUID) ([]changelog.Entry, error) {
	var out []changelog.Entry
	for _, e := range f.entries {
		if e.DeviceID == deviceID && e.SyncedAt == nil {
			out = append(out, e)
		}
	}
	return out, nil
}

func (f *fakeLog) MarkSynced(ids []uuid.UUID) error {
	f.synced = append(f.synced, ids...)
	now := clock.New().Now()
	for i, e := range f.entries {
		for _, id := range ids {
			if e.ID == id {
				f.entries[i].SyncedAt = &now
			}
		}
	}
	return nil
}

func (f *fakeLog) LastSyncedAt(deviceID uuid.UUID) (*clock.Timestamp, error) {
	return nil, nil
}

func (f *fakeLog) Count(deviceID uuid.UUID) (int, error) {
	n := 0
	for _, e := range f.entries {
		if e.DeviceID == deviceID && e.SyncedAt == nil {
			n++
		}
	}
	return n, nil
}

// fakeTransport captures Post calls and returns a canned response.
type fakeTransport struct {
	postBody []byte
	response []byte
	err      error
	called   int
}

func (f *fakeTransport) Post(_ context.Context, _ string, body any) ([]byte, error) {
	f.called++
	b, _ := json.Marshal(body)
	f.postBody = b
	return f.response, f.err
}

func (f *fakeTransport) Get(_ context.Context, _ string, _ map[string]string) ([]byte, error) {
	return nil, nil
}

func (f *fakeTransport) IsOnline(_ context.Context) bool { return true }

// fakeEngine always returns a simple JSON payload on Extract.
type fakeEngine struct{ entityType string }

func (e *fakeEngine) EntityType() string { return e.entityType }

func (e *fakeEngine) Extract(_ store.Store, id uuid.UUID) (json.RawMessage, error) {
	return json.RawMessage(`{"id":"` + id.String() + `"}`), nil
}

func (e *fakeEngine) Apply(_ store.TxStore, _ changelog.Operation, _ json.RawMessage) error {
	return nil
}

func (e *fakeEngine) Validate(_ json.RawMessage) error { return nil }

// ── Helpers ───────────────────────────────────────────────────────────────────

func makePusher(t *testing.T, log changelog.Log, tr *fakeTransport, reg *engine.Registry, deviceID uuid.UUID) *push.Pusher {
	t.Helper()
	dev := &device.Identity{DeviceID: deviceID, TenantID: uuid.New()}
	mon := status.New()
	return push.New(log, nil, tr, reg, dev, mon)
}

func makeEntry(deviceID uuid.UUID, entityType string, op changelog.Operation) changelog.Entry {
	return changelog.Entry{
		ID:          uuid.New(),
		EntityType:  entityType,
		EntityID:    uuid.New(),
		Operation:   op,
		ChangedAt:   clock.Timestamp{Physical: time.Now().UTC(), Logical: 0},
		DeviceID:    deviceID,
		PayloadHash: "testhash",
	}
}

func successResponse(entityIDs ...uuid.UUID) []byte {
	results := make([]push.PushResult, len(entityIDs))
	for i, id := range entityIDs {
		results[i] = push.PushResult{EntityID: id.String(), Status: "success"}
	}
	resp := push.PushResponse{Results: results}
	b, _ := json.Marshal(resp)
	return b
}

// ── Tests ─────────────────────────────────────────────────────────────────────

// Run with no pending entries returns nil and makes no transport call.
func TestRun_NoPending(t *testing.T) {
	log := &fakeLog{}
	tr := &fakeTransport{}
	reg := engine.NewRegistry()
	deviceID := uuid.New()

	p := makePusher(t, log, tr, reg, deviceID)
	if err := p.Run(context.Background()); err != nil {
		t.Fatalf("Run: %v", err)
	}
	if tr.called != 0 {
		t.Errorf("transport.Post called %d times, want 0", tr.called)
	}
}

// Run with one pending entry posts it and marks it synced on success.
func TestRun_SingleEntry_Success(t *testing.T) {
	log := &fakeLog{}
	tr := &fakeTransport{}
	reg := engine.NewRegistry()
	reg.Register(&fakeEngine{entityType: "record"})
	deviceID := uuid.New()

	e := makeEntry(deviceID, "record", changelog.OpCreate)
	_ = log.Append(e)

	tr.response = successResponse(e.EntityID)

	p := makePusher(t, log, tr, reg, deviceID)
	if err := p.Run(context.Background()); err != nil {
		t.Fatalf("Run: %v", err)
	}
	if tr.called != 1 {
		t.Errorf("transport.Post calls = %d, want 1", tr.called)
	}

	pending, _ := log.Pending(deviceID)
	if len(pending) != 0 {
		t.Errorf("pending after success = %d, want 0", len(pending))
	}
}

// Run on transport NetworkError surfaces the error without marking any entries synced.
func TestRun_NetworkError(t *testing.T) {
	log := &fakeLog{}
	netErr := &networkError{cause: errors.New("dial: connect refused")}
	tr := &fakeTransport{err: netErr}
	reg := engine.NewRegistry()
	reg.Register(&fakeEngine{entityType: "record"})
	deviceID := uuid.New()

	_ = log.Append(makeEntry(deviceID, "record", changelog.OpCreate))

	p := makePusher(t, log, tr, reg, deviceID)
	err := p.Run(context.Background())
	if err == nil {
		t.Fatal("Run: expected error, got nil")
	}

	pending, _ := log.Pending(deviceID)
	if len(pending) != 1 {
		t.Errorf("pending after network error = %d, want 1 (not marked synced)", len(pending))
	}
}

// Run with a "conflict" result keeps entry pending (not marked synced).
func TestRun_ConflictResult_NotMarkedSynced(t *testing.T) {
	log := &fakeLog{}
	tr := &fakeTransport{}
	reg := engine.NewRegistry()
	reg.Register(&fakeEngine{entityType: "record"})
	deviceID := uuid.New()

	e := makeEntry(deviceID, "record", changelog.OpCreate)
	_ = log.Append(e)

	conflictResp := push.PushResponse{Results: []push.PushResult{
		{EntityID: e.EntityID.String(), Status: "conflict"},
	}}
	b, _ := json.Marshal(conflictResp)
	tr.response = b

	p := makePusher(t, log, tr, reg, deviceID)
	if err := p.Run(context.Background()); err != nil {
		t.Fatalf("Run: %v", err)
	}

	pending, _ := log.Pending(deviceID)
	if len(pending) != 1 {
		t.Errorf("pending after conflict = %d, want 1", len(pending))
	}
}

// Unknown entity type is skipped — no error, no payload entry for it.
func TestRun_UnknownEntityType_Skipped(t *testing.T) {
	log := &fakeLog{}
	tr := &fakeTransport{}
	reg := engine.NewRegistry()
	// No engine registered for "unknown_type"
	deviceID := uuid.New()

	_ = log.Append(makeEntry(deviceID, "unknown_type", changelog.OpCreate))

	// Respond with empty results — nothing to mark synced
	resp := push.PushResponse{}
	b, _ := json.Marshal(resp)
	tr.response = b

	p := makePusher(t, log, tr, reg, deviceID)
	// Should not error — unknown types are silently skipped
	if err := p.Run(context.Background()); err != nil {
		t.Fatalf("Run with unknown entity type: %v", err)
	}
}

// ── batchEntries ──────────────────────────────────────────────────────────────

func TestBatchEntries_ExactDivision(t *testing.T) {
	deviceID := uuid.New()
	entries := make([]changelog.Entry, 6)
	for i := range entries {
		entries[i] = makeEntry(deviceID, "record", changelog.OpCreate)
	}

	batches := batchEntriesExported(entries, 2)
	if len(batches) != 3 {
		t.Errorf("batches = %d, want 3", len(batches))
	}
	for i, b := range batches {
		if len(b) != 2 {
			t.Errorf("batch[%d] len = %d, want 2", i, len(b))
		}
	}
}

func TestBatchEntries_Remainder(t *testing.T) {
	deviceID := uuid.New()
	entries := make([]changelog.Entry, 5)
	for i := range entries {
		entries[i] = makeEntry(deviceID, "record", changelog.OpCreate)
	}

	batches := batchEntriesExported(entries, 3)
	if len(batches) != 2 {
		t.Errorf("batches = %d, want 2", len(batches))
	}
	if len(batches[0]) != 3 {
		t.Errorf("batch[0] = %d, want 3", len(batches[0]))
	}
	if len(batches[1]) != 2 {
		t.Errorf("batch[1] = %d, want 2", len(batches[1]))
	}
}

func TestBatchEntries_SmallerThanBatch(t *testing.T) {
	deviceID := uuid.New()
	entries := make([]changelog.Entry, 2)
	for i := range entries {
		entries[i] = makeEntry(deviceID, "record", changelog.OpCreate)
	}

	batches := batchEntriesExported(entries, 50)
	if len(batches) != 1 {
		t.Errorf("batches = %d, want 1", len(batches))
	}
}

func TestBatchEntries_Empty(t *testing.T) {
	batches := batchEntriesExported(nil, 50)
	if len(batches) != 0 {
		t.Errorf("batches = %d, want 0", len(batches))
	}
}

// ── helpers ───────────────────────────────────────────────────────────────────

// networkError mirrors transport.NetworkError without importing it — avoids
// a circular dependency in tests. Run propagates it as-is.
type networkError struct{ cause error }

func (e *networkError) Error() string { return "network error: " + e.cause.Error() }
func (e *networkError) Unwrap() error { return e.cause }

// batchEntriesExported calls the package-internal batchEntries by wrapping it
// via the exported test helper pattern.
func batchEntriesExported(entries []changelog.Entry, size int) [][]changelog.Entry {
	return push.BatchEntries(entries, size)
}
