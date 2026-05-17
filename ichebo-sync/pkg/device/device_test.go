package device_test

import (
	"database/sql"
	"errors"
	"path/filepath"
	"sync"
	"testing"

	"github.com/google/uuid"
	_ "github.com/mattn/go-sqlite3"

	"github.com/ichebo/sync/pkg/device"
)

func openDB(t *testing.T) *sql.DB {
	t.Helper()
	db, err := sql.Open("sqlite3", filepath.Join(t.TempDir(), "test.sqlite"))
	if err != nil {
		t.Fatalf("sql.Open: %v", err)
	}
	t.Cleanup(func() { db.Close() })

	_, err = db.Exec(`
		CREATE TABLE IF NOT EXISTS settings (
			key   TEXT PRIMARY KEY,
			value TEXT NOT NULL
		)
	`)
	if err != nil {
		t.Fatalf("create settings table: %v", err)
	}
	return db
}

// E.3a exit criterion: device.Init() and device.Load() pass all unit tests
// including concurrency tests.
func TestInit_WritesIdentity(t *testing.T) {
	db := openDB(t)
	tenantID := uuid.New()

	id, err := device.Init(db, tenantID, "key-abc")
	if err != nil {
		t.Fatalf("Init: %v", err)
	}
	if id.DeviceID == uuid.Nil {
		t.Error("DeviceID should not be nil")
	}
	if id.TenantID != tenantID {
		t.Errorf("TenantID = %v, want %v", id.TenantID, tenantID)
	}
	if id.LicenceKey != "key-abc" {
		t.Errorf("LicenceKey = %q, want %q", id.LicenceKey, "key-abc")
	}
}

func TestLoad_ReturnsErrNotInitialised(t *testing.T) {
	db := openDB(t)
	_, err := device.Load(db)
	if !errors.Is(err, device.ErrNotInitialised) {
		t.Errorf("expected ErrNotInitialised, got %v", err)
	}
}

func TestLoad_RoundTrip(t *testing.T) {
	db := openDB(t)
	tenantID := uuid.New()

	want, err := device.Init(db, tenantID, "key-xyz")
	if err != nil {
		t.Fatalf("Init: %v", err)
	}

	got, err := device.Load(db)
	if err != nil {
		t.Fatalf("Load: %v", err)
	}

	if got.DeviceID != want.DeviceID {
		t.Errorf("DeviceID mismatch: got %v, want %v", got.DeviceID, want.DeviceID)
	}
	if got.TenantID != want.TenantID {
		t.Errorf("TenantID mismatch: got %v, want %v", got.TenantID, want.TenantID)
	}
	if got.LicenceKey != want.LicenceKey {
		t.Errorf("LicenceKey mismatch: got %q, want %q", got.LicenceKey, want.LicenceKey)
	}
}

func TestInit_RejectsDoubleInit(t *testing.T) {
	db := openDB(t)
	tenantID := uuid.New()

	if _, err := device.Init(db, tenantID, "key-1"); err != nil {
		t.Fatalf("first Init: %v", err)
	}

	_, err := device.Init(db, tenantID, "key-2")
	if err == nil {
		t.Error("expected error on second Init, got nil")
	}
}

func TestInit_DeviceIDIsUnique(t *testing.T) {
	ids := make([]uuid.UUID, 10)
	for i := range ids {
		db := openDB(t)
		id, err := device.Init(db, uuid.New(), "key")
		if err != nil {
			t.Fatalf("Init[%d]: %v", i, err)
		}
		ids[i] = id.DeviceID
	}
	seen := make(map[uuid.UUID]bool)
	for _, id := range ids {
		if seen[id] {
			t.Errorf("duplicate DeviceID: %v", id)
		}
		seen[id] = true
	}
}

// Concurrency test: concurrent Init calls must not both succeed on the same DB.
func TestInit_ConcurrentSafety(t *testing.T) {
	db := openDB(t)
	tenantID := uuid.New()

	var wg sync.WaitGroup
	successes := 0
	var mu sync.Mutex

	for i := 0; i < 5; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			_, err := device.Init(db, tenantID, "key")
			if err == nil {
				mu.Lock()
				successes++
				mu.Unlock()
			}
		}()
	}
	wg.Wait()

	if successes != 1 {
		t.Errorf("expected exactly 1 successful Init, got %d", successes)
	}
}
