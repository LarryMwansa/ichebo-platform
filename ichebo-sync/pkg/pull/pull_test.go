// Tests for the pull package — verifies Run, applyOrConflict, pagination,
// and conflict routing using in-memory fakes.
package pull_test

import (
	"context"
	"encoding/json"
	"fmt"
	"testing"
	"time"

	"github.com/google/uuid"
	"github.com/ichebo/sync/engines/engine"
	"github.com/ichebo/sync/pkg/changelog"
	"github.com/ichebo/sync/pkg/clock"
	"github.com/ichebo/sync/pkg/device"
	"github.com/ichebo/sync/pkg/pull"
	"github.com/ichebo/sync/pkg/resolve"
	"github.com/ichebo/sync/pkg/status"
	"github.com/ichebo/sync/pkg/store"
)

// ── Fakes ─────────────────────────────────────────────────────────────────────

// fakeLog tracks entries and pending/synced state.
type fakeLog struct {
	entries []changelog.Entry
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
	now := clock.New().Now()
	set := make(map[uuid.UUID]struct{}, len(ids))
	for _, id := range ids {
		set[id] = struct{}{}
	}
	for i, e := range f.entries {
		if _, ok := set[e.ID]; ok {
			f.entries[i].SyncedAt = &now
		}
	}
	return nil
}

func (f *fakeLog) LastSyncedAt(deviceID uuid.UUID) (*clock.Timestamp, error) {
	return nil, nil
}

func (f *fakeLog) Count(deviceID uuid.UUID) (int, error) {
	return 0, nil
}

// fakeTransport serves canned GET responses keyed by sequence number.
type fakeTransport struct {
	responses [][]byte
	callCount int
	err       error
}

func (f *fakeTransport) Get(_ context.Context, _ string, _ map[string]string) ([]byte, error) {
	if f.err != nil {
		return nil, f.err
	}
	i := f.callCount
	f.callCount++
	if i < len(f.responses) {
		return f.responses[i], nil
	}
	// Default: empty, no more pages
	return emptyPullResponse(), nil
}

func (f *fakeTransport) Post(_ context.Context, _ string, _ any) ([]byte, error) {
	return nil, nil
}

func (f *fakeTransport) IsOnline(_ context.Context) bool { return true }

func emptyPullResponse() []byte {
	resp := pull.PullResponse{
		RetrievedAt: clock.New().Now().String(),
		HasMore:     false,
	}
	b, _ := json.Marshal(resp)
	return b
}

// fakeStore records Apply calls and supports Tx.
type fakeStore struct {
	applied []appliedRecord
}

type appliedRecord struct {
	entityType string
	op         changelog.Operation
	payload    json.RawMessage
}

func (f *fakeStore) Tx(fn func(tx store.TxStore) error) error {
	return fn(&fakeTxStore{parent: f})
}

func (f *fakeStore) ChangeLog() changelog.Log { return nil }
func (f *fakeStore) Members() store.MemberStore { return nil }
func (f *fakeStore) Records() store.RecordStore { return nil }
func (f *fakeStore) Activities() store.ActivityStore { return nil }
func (f *fakeStore) Close() error { return nil }

type fakeTxStore struct{ parent *fakeStore }

func (t *fakeTxStore) ChangeLog() changelog.Writer { return nil }
func (t *fakeTxStore) Members() store.MemberStore  { return nil }
func (t *fakeTxStore) Records() store.RecordStore  { return nil }
func (t *fakeTxStore) Activities() store.ActivityStore { return nil }
func (t *fakeTxStore) SaveAttendance(_, _ string, _ []string, _ string) error { return nil }

// fakeEngine records Apply calls.
type fakeEngine struct {
	entityType string
	applyCalls []json.RawMessage
	extractFn  func(store.Store, uuid.UUID) (json.RawMessage, error)
}

func (e *fakeEngine) EntityType() string { return e.entityType }

func (e *fakeEngine) Apply(tx store.TxStore, op changelog.Operation, payload json.RawMessage) error {
	e.applyCalls = append(e.applyCalls, payload)
	return nil
}

func (e *fakeEngine) Extract(s store.Store, id uuid.UUID) (json.RawMessage, error) {
	if e.extractFn != nil {
		return e.extractFn(s, id)
	}
	return json.RawMessage(`{"id":"` + id.String() + `"}`), nil
}

func (e *fakeEngine) Validate(_ json.RawMessage) error { return nil }

// fakeResolver records resolved conflicts.
type fakeResolver struct {
	resolved []resolve.Conflict
}

func (r *fakeResolver) Resolve(_ context.Context, c resolve.Conflict) error {
	r.resolved = append(r.resolved, c)
	return nil
}

// ── Helpers ───────────────────────────────────────────────────────────────────

func makePuller(
	t *testing.T,
	log changelog.Log,
	s store.Store,
	tr *fakeTransport,
	reg *engine.Registry,
	res resolve.Resolver,
	deviceID uuid.UUID,
) *pull.Puller {
	t.Helper()
	dev := &device.Identity{DeviceID: deviceID, TenantID: uuid.New()}
	mon := status.New()
	clk := clock.New()
	return pull.New(log, s, tr, reg, res, clk, dev, mon)
}

func recordJSON(id uuid.UUID) json.RawMessage {
	return json.RawMessage(fmt.Sprintf(`{"id":%q,"title":"test"}`, id))
}

func pullRespWithRecords(hasMore bool, records ...json.RawMessage) []byte {
	resp := pull.PullResponse{
		RetrievedAt: clock.New().Now().String(),
		HasMore:     hasMore,
		Records:     records,
	}
	b, _ := json.Marshal(resp)
	return b
}

// ── Tests ─────────────────────────────────────────────────────────────────────

// Empty response — no records — Run returns nil.
func TestRun_EmptyResponse(t *testing.T) {
	log := &fakeLog{}
	s := &fakeStore{}
	tr := &fakeTransport{responses: [][]byte{emptyPullResponse()}}
	reg := engine.NewRegistry()
	res := &fakeResolver{}
	deviceID := uuid.New()

	p := makePuller(t, log, s, tr, reg, res, deviceID)
	if err := p.Run(context.Background()); err != nil {
		t.Fatalf("Run: %v", err)
	}
	if tr.callCount != 1 {
		t.Errorf("GET calls = %d, want 1", tr.callCount)
	}
}

// Single record with no local conflict — Apply is called once.
func TestRun_SingleRecord_NoConflict(t *testing.T) {
	log := &fakeLog{}
	s := &fakeStore{}
	eng := &fakeEngine{entityType: "record"}
	reg := engine.NewRegistry()
	reg.Register(eng)
	res := &fakeResolver{}
	deviceID := uuid.New()

	recordID := uuid.New()
	tr := &fakeTransport{responses: [][]byte{
		pullRespWithRecords(false, recordJSON(recordID)),
	}}

	p := makePuller(t, log, s, tr, reg, res, deviceID)
	if err := p.Run(context.Background()); err != nil {
		t.Fatalf("Run: %v", err)
	}
	if len(eng.applyCalls) != 1 {
		t.Errorf("Apply calls = %d, want 1", len(eng.applyCalls))
	}
	if len(res.resolved) != 0 {
		t.Errorf("conflicts resolved = %d, want 0", len(res.resolved))
	}
}

// Record arrives but local has a pending entry for same entity — routed to resolver.
func TestRun_ConflictDetected_RoutedToResolver(t *testing.T) {
	log := &fakeLog{}
	s := &fakeStore{}
	eng := &fakeEngine{entityType: "record"}
	reg := engine.NewRegistry()
	reg.Register(eng)
	res := &fakeResolver{}
	deviceID := uuid.New()

	// Plant a pending local entry for this entity
	recordID := uuid.New()
	pendingEntry := changelog.Entry{
		ID:         uuid.New(),
		EntityType: "record",
		EntityID:   recordID,
		Operation:  changelog.OpUpdate,
		ChangedAt:  clock.Timestamp{Physical: time.Now().UTC()},
		DeviceID:   deviceID,
	}
	_ = log.Append(pendingEntry)

	tr := &fakeTransport{responses: [][]byte{
		pullRespWithRecords(false, recordJSON(recordID)),
	}}

	p := makePuller(t, log, s, tr, reg, res, deviceID)
	if err := p.Run(context.Background()); err != nil {
		t.Fatalf("Run: %v", err)
	}

	// Apply should NOT have been called — conflict goes to resolver
	if len(eng.applyCalls) != 0 {
		t.Errorf("Apply calls = %d, want 0 (conflict should skip Apply)", len(eng.applyCalls))
	}
	if len(res.resolved) != 1 {
		t.Errorf("resolver.Resolve calls = %d, want 1", len(res.resolved))
	}
	if res.resolved[0].EntityID != recordID {
		t.Errorf("conflict EntityID = %v, want %v", res.resolved[0].EntityID, recordID)
	}
}

// Unknown entity type from cloud is silently skipped — no Apply, no error.
func TestRun_UnknownEntityType_Skipped(t *testing.T) {
	log := &fakeLog{}
	s := &fakeStore{}
	reg := engine.NewRegistry()
	// No engine for "unknown_thing"
	res := &fakeResolver{}
	deviceID := uuid.New()

	unknownID := uuid.New()
	unknownPayload := json.RawMessage(fmt.Sprintf(`{"id":%q}`, unknownID))

	// Put the unknown payload in the response — pull package uses entity sets
	// "record", "activity", "relationship"; we simulate by returning a record
	// JSON but registering no engine. The record key is what matters.
	tr := &fakeTransport{responses: [][]byte{
		pullRespWithRecords(false, unknownPayload),
	}}

	p := makePuller(t, log, s, tr, reg, res, deviceID)
	if err := p.Run(context.Background()); err != nil {
		t.Fatalf("Run with unknown entity type: %v", err)
	}
	if len(res.resolved) != 0 {
		t.Errorf("resolver calls = %d, want 0", len(res.resolved))
	}
}

// Pagination: has_more=true on first page, false on second — two GET calls.
func TestRun_Pagination(t *testing.T) {
	log := &fakeLog{}
	s := &fakeStore{}
	eng := &fakeEngine{entityType: "record"}
	reg := engine.NewRegistry()
	reg.Register(eng)
	res := &fakeResolver{}
	deviceID := uuid.New()

	id1, id2 := uuid.New(), uuid.New()
	tr := &fakeTransport{responses: [][]byte{
		pullRespWithRecords(true, recordJSON(id1)),  // page 1: hasMore=true
		pullRespWithRecords(false, recordJSON(id2)), // page 2: hasMore=false
	}}

	p := makePuller(t, log, s, tr, reg, res, deviceID)
	if err := p.Run(context.Background()); err != nil {
		t.Fatalf("Run: %v", err)
	}
	if tr.callCount != 2 {
		t.Errorf("GET calls = %d, want 2", tr.callCount)
	}
	if len(eng.applyCalls) != 2 {
		t.Errorf("Apply calls = %d, want 2", len(eng.applyCalls))
	}
}

// Transport error surfaces from Run.
func TestRun_TransportError(t *testing.T) {
	log := &fakeLog{}
	s := &fakeStore{}
	reg := engine.NewRegistry()
	res := &fakeResolver{}
	deviceID := uuid.New()

	tr := &fakeTransport{err: fmt.Errorf("network unreachable")}
	p := makePuller(t, log, s, tr, reg, res, deviceID)
	if err := p.Run(context.Background()); err == nil {
		t.Fatal("Run: expected error, got nil")
	}
}
