package status_test

import (
	"testing"
	"time"

	"github.com/ichebo/sync/pkg/status"
)

// E.4h exit criterion: all four state transitions broadcast to subscribers
// within 100ms.
func TestStateTransitionsBroadcast(t *testing.T) {
	mon := status.New()
	ch := mon.Subscribe()

	states := []status.State{status.Syncing, status.Offline, status.Conflict, status.Blocked}

	for _, s := range states {
		mon.SetState(s)
		select {
		case update := <-ch:
			if update.State != s {
				t.Errorf("expected state %v, got %v", s, update.State)
			}
		case <-time.After(100 * time.Millisecond):
			t.Errorf("state transition to %v not broadcast within 100ms", s)
		}
	}
}

func TestSyncedMessage(t *testing.T) {
	mon := status.New()
	now := time.Now()
	mon.SetState(status.Synced, status.WithLastSynced(now))
	u := mon.Current()
	if u.Message == "" {
		t.Error("Synced message should not be empty")
	}
}

func TestOfflineMessageIncludesPendingCount(t *testing.T) {
	mon := status.New()
	mon.SetState(status.Offline, status.WithPending(47))
	u := mon.Current()
	if u.PendingCount != 47 {
		t.Errorf("pending count should be 47, got %d", u.PendingCount)
	}
}

func TestSyncingMessageIncludesProgress(t *testing.T) {
	mon := status.New()
	mon.SetState(status.Syncing, status.WithProgress(23, 47))
	u := mon.Current()
	if u.SyncedCount != 23 || u.TotalCount != 47 {
		t.Errorf("progress should be 23/47, got %d/%d", u.SyncedCount, u.TotalCount)
	}
}

func TestConflictMessageIncludesCount(t *testing.T) {
	mon := status.New()
	mon.SetState(status.Conflict, status.WithConflicts(3))
	u := mon.Current()
	if u.ConflictCount != 3 {
		t.Errorf("conflict count should be 3, got %d", u.ConflictCount)
	}
}

func TestMultipleSubscribers(t *testing.T) {
	mon := status.New()
	ch1 := mon.Subscribe()
	ch2 := mon.Subscribe()

	mon.SetState(status.Syncing)

	for _, ch := range []<-chan status.StateUpdate{ch1, ch2} {
		select {
		case <-ch:
		case <-time.After(100 * time.Millisecond):
			t.Error("subscriber did not receive update within 100ms")
		}
	}
}
