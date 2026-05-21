//go:build cgo

// Package ffi provides the six exported C functions callable from dart:ffi.
// This file is only compiled when CGO is enabled (i.e. when building the
// shared library — not during regular go test).
//
// Flutter calls these six functions to control the sync engine.
// All data for the UI is read directly from SQLite by Flutter via sqflite.
// No entity data crosses the FFI boundary — only control signals and status.
//
// Build shared library:
//
//	go build -buildmode=c-shared -o libichebo_sync.so ./ffi/
package main

/*
#include <stdlib.h>
*/
import "C"
import (
	"context"
	"encoding/json"
	"sync"
	"unsafe"

	"github.com/ichebo/sync/pkg/clock"
	"github.com/ichebo/sync/pkg/status"
	"github.com/ichebo/sync/pkg/store"
)

// daemon holds the running sync engine state across FFI calls.
var daemon struct {
	mu      sync.Mutex
	started bool
	cancel  context.CancelFunc
	monitor *status.Monitor
	clock   *clock.HybridClock
	db      store.Store
}

// SyncConfig is the JSON-decoded form of the configJSON parameter to SyncStart.
type SyncConfig struct {
	BaseURL    string `json:"base_url"`
	AuthToken  string `json:"auth_token"`
	DeviceID   string `json:"device_id"`
	TenantID   string `json:"tenant_id"`
	DBPath     string `json:"db_path"`
}

// SyncStart starts the sync engine daemon.
// configJSON: JSON string containing SyncConfig.
// Returns 0 on success, non-zero on error.
//
//export SyncStart
func SyncStart(configJSON *C.char) C.int {
	daemon.mu.Lock()
	defer daemon.mu.Unlock()

	if daemon.started {
		return 0 // idempotent
	}

	cfgStr := C.GoString(configJSON)
	var cfg SyncConfig
	if err := json.Unmarshal([]byte(cfgStr), &cfg); err != nil {
		return -1
	}

	db, err := store.Open(cfg.DBPath)
	if err != nil {
		return -2
	}

	daemon.db = db
	daemon.monitor = status.New()
	daemon.clock = clock.New()

	ctx, cancel := context.WithCancel(context.Background())
	daemon.cancel = cancel
	daemon.started = true

	// Background daemon: transitions to Offline on start.
	// Full push/pull wiring added in D.5.
	go func() {
		daemon.monitor.SetState(status.Offline)
		<-ctx.Done()
		db.Close()
	}()

	return 0
}

// SyncStop gracefully shuts down the sync engine.
// Flushes pending operations, closes SQLite connections, stops goroutines.
//
//export SyncStop
func SyncStop() {
	daemon.mu.Lock()
	defer daemon.mu.Unlock()

	if !daemon.started {
		return
	}
	daemon.cancel()
	daemon.started = false
	daemon.db = nil
}

// SyncNow triggers an immediate sync cycle (push + pull).
// Returns immediately — the cycle runs in the background.
//
//export SyncNow
func SyncNow() {
	daemon.mu.Lock()
	mon := daemon.monitor
	daemon.mu.Unlock()

	if mon == nil {
		return
	}
	// Full implementation triggers push.Pusher.Run + pull.Puller.Run.
	mon.SetState(status.Syncing)
}

// SyncStatus returns the current status as a JSON string.
// The caller is responsible for freeing the returned *C.char via C.free.
//
//export SyncStatus
func SyncStatus() *C.char {
	daemon.mu.Lock()
	mon := daemon.monitor
	daemon.mu.Unlock()

	if mon == nil {
		data, _ := json.Marshal(map[string]any{
			"state":          "offline",
			"pending":        0,
			"conflict_count": 0,
		})
		return C.CString(string(data))
	}

	u := mon.Current()
	stateStr := [...]string{"synced", "offline", "syncing", "conflict", "blocked"}[u.State]
	data, _ := json.Marshal(map[string]any{
		"state":          stateStr,
		"pending":        u.PendingCount,
		"conflict_count": u.ConflictCount,
		"message":        u.Message,
	})
	return C.CString(string(data))
}

// SyncConflictCount returns the number of pending conflicts.
//
//export SyncConflictCount
func SyncConflictCount() C.int {
	daemon.mu.Lock()
	mon := daemon.monitor
	daemon.mu.Unlock()

	if mon == nil {
		return 0
	}
	return C.int(mon.Current().ConflictCount)
}

// SyncResolveConflict applies the user's resolution to a specific conflict.
// conflictID: UUID string of the ConflictEntry.
// choice: 0 = keep local version, 1 = keep cloud version.
// Returns 0 on success.
//
//export SyncResolveConflict
func SyncResolveConflict(conflictID *C.char, choice C.int) C.int {
	_ = C.GoString(conflictID)
	_ = unsafe.Pointer(nil) // keep unsafe import used
	// Full implementation calls queue.Queue.Resolve(id, choiceStr).
	return 0
}
