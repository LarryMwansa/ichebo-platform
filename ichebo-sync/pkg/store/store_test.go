package store_test

import (
	"errors"
	"os"
	"path/filepath"
	"testing"

	"github.com/google/uuid"
	"github.com/ichebo/sync/pkg/changelog"
	"github.com/ichebo/sync/pkg/clock"
	"github.com/ichebo/sync/pkg/store"
)

func openTemp(t *testing.T) store.Store {
	t.Helper()
	dir := t.TempDir()
	s, err := store.Open(filepath.Join(dir, "test.sqlite"))
	if err != nil {
		t.Fatalf("store.Open: %v", err)
	}
	t.Cleanup(func() { s.Close() })
	return s
}

func sampleEntry(deviceID uuid.UUID) changelog.Entry {
	return changelog.Entry{
		ID:          uuid.New(),
		EntityType:  "record",
		EntityID:    uuid.New(),
		Operation:   changelog.OpCreate,
		ChangedAt:   clock.New().Now(),
		DeviceID:    deviceID,
		PayloadHash: "abc123def456abc123def456abc123def456abc123def456abc123def456abc1",
	}
}

// E.3c exit criterion: Tx() correctly rolls back both writes if either fails.
func TestTx_RollbackOnError(t *testing.T) {
	s := openTemp(t)
	deviceID := uuid.New()
	entry := sampleEntry(deviceID)

	boom := errors.New("deliberate failure")
	err := s.Tx(func(tx store.TxStore) error {
		if err := tx.ChangeLog().Append(entry); err != nil {
			return err
		}
		return boom
	})

	if !errors.Is(err, boom) {
		t.Fatalf("expected boom error, got %v", err)
	}

	pending, err := s.ChangeLog().Pending(deviceID)
	if err != nil {
		t.Fatalf("Pending: %v", err)
	}
	if len(pending) != 0 {
		t.Errorf("rollback failed: found %d entries, want 0", len(pending))
	}
}

func TestTx_CommitPersistsEntry(t *testing.T) {
	s := openTemp(t)
	deviceID := uuid.New()
	entry := sampleEntry(deviceID)

	err := s.Tx(func(tx store.TxStore) error {
		return tx.ChangeLog().Append(entry)
	})
	if err != nil {
		t.Fatalf("Tx commit: %v", err)
	}

	pending, err := s.ChangeLog().Pending(deviceID)
	if err != nil {
		t.Fatalf("Pending: %v", err)
	}
	if len(pending) != 1 {
		t.Fatalf("expected 1 entry, got %d", len(pending))
	}
	if pending[0].ID != entry.ID {
		t.Errorf("entry ID mismatch: got %v, want %v", pending[0].ID, entry.ID)
	}
}

func TestMarkSynced(t *testing.T) {
	s := openTemp(t)
	deviceID := uuid.New()
	entry := sampleEntry(deviceID)

	_ = s.Tx(func(tx store.TxStore) error {
		return tx.ChangeLog().Append(entry)
	})

	if err := s.ChangeLog().MarkSynced([]uuid.UUID{entry.ID}); err != nil {
		t.Fatalf("MarkSynced: %v", err)
	}

	pending, _ := s.ChangeLog().Pending(deviceID)
	if len(pending) != 0 {
		t.Errorf("entry still pending after MarkSynced")
	}
}

func TestCount(t *testing.T) {
	s := openTemp(t)
	deviceID := uuid.New()

	for i := 0; i < 3; i++ {
		_ = s.Tx(func(tx store.TxStore) error {
			return tx.ChangeLog().Append(sampleEntry(deviceID))
		})
	}

	n, err := s.ChangeLog().Count(deviceID)
	if err != nil {
		t.Fatalf("Count: %v", err)
	}
	if n != 3 {
		t.Errorf("Count = %d, want 3", n)
	}
}

func TestLastSyncedAt_NilWhenNonesynced(t *testing.T) {
	s := openTemp(t)
	deviceID := uuid.New()
	_ = s.Tx(func(tx store.TxStore) error {
		return tx.ChangeLog().Append(sampleEntry(deviceID))
	})

	ts, err := s.ChangeLog().LastSyncedAt(deviceID)
	if err != nil {
		t.Fatalf("LastSyncedAt: %v", err)
	}
	if ts != nil {
		t.Errorf("expected nil before any sync, got %v", ts)
	}
}

func TestOpen_CreatesFileIfMissing(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "new.sqlite")

	if _, err := os.Stat(path); !errors.Is(err, os.ErrNotExist) {
		t.Fatal("expected file to not exist yet")
	}

	s, err := store.Open(path)
	if err != nil {
		t.Fatalf("Open: %v", err)
	}
	s.Close()

	if _, err := os.Stat(path); err != nil {
		t.Errorf("expected file to exist after Open: %v", err)
	}
}

func TestPending_IsolatedByDeviceID(t *testing.T) {
	s := openTemp(t)
	d1, d2 := uuid.New(), uuid.New()

	_ = s.Tx(func(tx store.TxStore) error { return tx.ChangeLog().Append(sampleEntry(d1)) })
	_ = s.Tx(func(tx store.TxStore) error { return tx.ChangeLog().Append(sampleEntry(d2)) })

	p1, _ := s.ChangeLog().Pending(d1)
	p2, _ := s.ChangeLog().Pending(d2)

	if len(p1) != 1 || len(p2) != 1 {
		t.Errorf("Pending not isolated by device_id: d1=%d d2=%d", len(p1), len(p2))
	}
	if p1[0].DeviceID != d1 {
		t.Errorf("wrong device_id in d1 result")
	}
}
