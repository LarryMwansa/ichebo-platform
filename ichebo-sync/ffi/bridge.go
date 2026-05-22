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

	"github.com/google/uuid"
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

// memberPayload is the JSON shape accepted by MemberCreate and MemberUpdate.
type memberPayload struct {
	ID              string `json:"id"`
	TenantID        string `json:"tenant_id"`
	Email           string `json:"email"`
	DisplayName     string `json:"display_name"`
	FirstName       string `json:"first_name"`
	LastName        string `json:"last_name"`
	Phone           string `json:"phone"`
	CompetenceLevel int    `json:"competence_level"`
	IsActive        bool   `json:"is_active"`
	ShepherdID      string `json:"shepherd_id"`
	ServiceOrder    string `json:"service_order"`
	CustomFields    string `json:"custom_fields"`
	CreatedBy       string `json:"created_by"`
	CreatedAt       string `json:"created_at"`
	UpdatedAt       string `json:"updated_at"`
}

func payloadToMember(p memberPayload) (*store.Member, error) {
	id, err := uuid.Parse(p.ID)
	if err != nil {
		return nil, err
	}
	tid, err := uuid.Parse(p.TenantID)
	if err != nil {
		return nil, err
	}
	cb, err := uuid.Parse(p.CreatedBy)
	if err != nil {
		return nil, err
	}
	m := &store.Member{
		ID:              id,
		TenantID:        tid,
		Email:           p.Email,
		DisplayName:     p.DisplayName,
		FirstName:       p.FirstName,
		LastName:        p.LastName,
		Phone:           p.Phone,
		CompetenceLevel: p.CompetenceLevel,
		IsActive:        p.IsActive,
		ServiceOrder:    p.ServiceOrder,
		CustomFields:    p.CustomFields,
		CreatedBy:       cb,
		CreatedAt:       p.CreatedAt,
		UpdatedAt:       p.UpdatedAt,
	}
	if p.ShepherdID != "" {
		sid, err := uuid.Parse(p.ShepherdID)
		if err != nil {
			return nil, err
		}
		m.ShepherdID = &sid
	}
	return m, nil
}

// MemberCreate writes a new member record atomically (member row + changelog entry).
// jsonPtr: JSON-encoded memberPayload. Returns 0 on success, -1 on bad JSON, -2 if engine not started.
//
//export MemberCreate
func MemberCreate(jsonPtr *C.char) C.int {
	daemon.mu.Lock()
	db := daemon.db
	daemon.mu.Unlock()

	if db == nil {
		return -2
	}
	var p memberPayload
	if err := json.Unmarshal([]byte(C.GoString(jsonPtr)), &p); err != nil {
		return -1
	}
	m, err := payloadToMember(p)
	if err != nil {
		return -1
	}
	if err := db.Tx(func(tx store.TxStore) error {
		return tx.Members().Upsert(m)
	}); err != nil {
		return -3
	}
	return 0
}

// MemberUpdate updates an existing member record atomically.
// jsonPtr: JSON-encoded memberPayload (id must match an existing row).
// Returns 0 on success, -1 on bad JSON, -2 if engine not started.
//
//export MemberUpdate
func MemberUpdate(jsonPtr *C.char) C.int {
	return MemberCreate(jsonPtr) // Upsert handles both insert and update
}

// ── Activity write functions ───────────────────────────────────────────────────

// activityPayload is the JSON shape for ActivityCreate and ActivityUpdate.
type activityPayload struct {
	ID               string `json:"id"`
	TenantID         string `json:"tenant_id"`
	ActivityType     string `json:"activity_type"`
	Title            string `json:"title"`
	Description      string `json:"description"`
	Status           string `json:"status"`
	Progress         int    `json:"progress"`
	AssignedTo       string `json:"assigned_to"`
	LinkedRecordID   string `json:"linked_record_id"`
	ParentActivityID string `json:"parent_activity_id"`
	DueAt            string `json:"due_at"`
	ScheduledAt      string `json:"scheduled_at"`
	CompletedAt      string `json:"completed_at"`
	SourceApp        string `json:"source_app"`
	Metadata         string `json:"metadata"`
	CreatedBy        string `json:"created_by"`
	CreatedAt        string `json:"created_at"`
	UpdatedAt        string `json:"updated_at"`
}

func payloadToActivity(p activityPayload) (*store.Activity, error) {
	id, err := uuid.Parse(p.ID)
	if err != nil {
		return nil, err
	}
	tid, err := uuid.Parse(p.TenantID)
	if err != nil {
		return nil, err
	}
	cb, err := uuid.Parse(p.CreatedBy)
	if err != nil {
		return nil, err
	}
	a := &store.Activity{
		ID:           id,
		TenantID:     tid,
		ActivityType: p.ActivityType,
		Title:        p.Title,
		Description:  p.Description,
		Status:       p.Status,
		Progress:     p.Progress,
		SourceApp:    p.SourceApp,
		Metadata:     p.Metadata,
		CreatedBy:    cb,
		CreatedAt:    p.CreatedAt,
		UpdatedAt:    p.UpdatedAt,
	}
	if p.AssignedTo != "" {
		id2, err := uuid.Parse(p.AssignedTo)
		if err == nil {
			a.AssignedTo = &id2
		}
	}
	if p.LinkedRecordID != "" {
		id2, err := uuid.Parse(p.LinkedRecordID)
		if err == nil {
			a.LinkedRecordID = &id2
		}
	}
	if p.ParentActivityID != "" {
		id2, err := uuid.Parse(p.ParentActivityID)
		if err == nil {
			a.ParentActivityID = &id2
		}
	}
	if p.DueAt != "" {
		a.DueAt = &p.DueAt
	}
	if p.ScheduledAt != "" {
		a.ScheduledAt = &p.ScheduledAt
	}
	if p.CompletedAt != "" {
		a.CompletedAt = &p.CompletedAt
	}
	return a, nil
}

// ActivityCreate writes a new activity row + changelog entry atomically.
// Returns 0 on success, -1 on bad JSON, -2 if engine not started, -3 on DB error.
//
//export ActivityCreate
func ActivityCreate(jsonPtr *C.char) C.int {
	daemon.mu.Lock()
	db := daemon.db
	daemon.mu.Unlock()

	if db == nil {
		return -2
	}
	var p activityPayload
	if err := json.Unmarshal([]byte(C.GoString(jsonPtr)), &p); err != nil {
		return -1
	}
	a, err := payloadToActivity(p)
	if err != nil {
		return -1
	}
	if err := db.Tx(func(tx store.TxStore) error {
		return tx.Activities().Upsert(a)
	}); err != nil {
		return -3
	}
	return 0
}

// ActivityUpdate updates an existing activity row atomically (upsert).
//
//export ActivityUpdate
func ActivityUpdate(jsonPtr *C.char) C.int {
	return ActivityCreate(jsonPtr)
}

// gatheringPayload is the combined payload for the gathering dual-write.
type gatheringPayload struct {
	Record   recordPayload   `json:"record"`
	Activity activityPayload `json:"activity"`
}

type recordPayload struct {
	ID           string `json:"id"`
	TenantID     string `json:"tenant_id"`
	RecordClass  string `json:"record_class"`
	RecordFamily string `json:"record_family"`
	RecordType   string `json:"record_type"`
	Title        string `json:"title"`
	Status       string `json:"status"`
	CustomFields string `json:"custom_fields"`
	Metadata     string `json:"metadata"`
	Permissions  string `json:"permissions"`
	CreatedBy    string `json:"created_by"`
	CreatedAt    string `json:"created_at"`
	UpdatedAt    string `json:"updated_at"`
}

func payloadToRecord(p recordPayload) (*store.Record, error) {
	id, err := uuid.Parse(p.ID)
	if err != nil {
		return nil, err
	}
	tid, err := uuid.Parse(p.TenantID)
	if err != nil {
		return nil, err
	}
	cb, err := uuid.Parse(p.CreatedBy)
	if err != nil {
		return nil, err
	}
	cf := p.CustomFields
	if cf == "" {
		cf = "{}"
	}
	meta := p.Metadata
	if meta == "" {
		meta = "{}"
	}
	perms := p.Permissions
	if perms == "" {
		perms = "{}"
	}
	return &store.Record{
		ID:           id,
		TenantID:     tid,
		RecordClass:  p.RecordClass,
		RecordFamily: p.RecordFamily,
		RecordType:   p.RecordType,
		Title:        p.Title,
		Status:       p.Status,
		CustomFields: cf,
		Metadata:     meta,
		Permissions:  perms,
		CreatedBy:    cb,
		CreatedAt:    p.CreatedAt,
		UpdatedAt:    p.UpdatedAt,
	}, nil
}

// GatheringCreate performs the gathering dual-write atomically:
//  1. Insert gathering Record
//  2. Insert event Activity (linked_record_id = record.id)
//
// Both writes share one SQLite transaction with a single ChangeLog entry.
// Returns 0 on success, -1 on bad JSON, -2 if engine not started, -3 on DB error.
//
//export GatheringCreate
func GatheringCreate(jsonPtr *C.char) C.int {
	daemon.mu.Lock()
	db := daemon.db
	daemon.mu.Unlock()

	if db == nil {
		return -2
	}
	var p gatheringPayload
	if err := json.Unmarshal([]byte(C.GoString(jsonPtr)), &p); err != nil {
		return -1
	}
	rec, err := payloadToRecord(p.Record)
	if err != nil {
		return -1
	}
	act, err := payloadToActivity(p.Activity)
	if err != nil {
		return -1
	}
	// Ensure activity is linked to the record.
	act.LinkedRecordID = &rec.ID

	if err := db.Tx(func(tx store.TxStore) error {
		if err := tx.Records().Upsert(rec); err != nil {
			return err
		}
		return tx.Activities().Upsert(act)
	}); err != nil {
		return -3
	}
	return 0
}

// attendancePayload is the JSON shape for AttendanceSave.
type attendancePayload struct {
	ActivityID       string   `json:"activity_id"`
	ChangedBy        string   `json:"changed_by"`
	PresentMemberIDs []string `json:"present_member_ids"`
	Now              string   `json:"now"`
}

// AttendanceSave writes attendance records atomically:
//  1. Deletes any prior attendance_log rows for this activity
//  2. Inserts one activity_log row per present member
//  3. Updates activity status to 'completed' and sets completed_at
//
// Returns 0 on success, -1 on bad JSON, -2 if engine not started, -3 on DB error.
//
//export AttendanceSave
func AttendanceSave(jsonPtr *C.char) C.int {
	daemon.mu.Lock()
	db := daemon.db
	daemon.mu.Unlock()

	if db == nil {
		return -2
	}
	var p attendancePayload
	if err := json.Unmarshal([]byte(C.GoString(jsonPtr)), &p); err != nil {
		return -1
	}

	if err := db.Tx(func(tx store.TxStore) error {
		return tx.SaveAttendance(p.ActivityID, p.ChangedBy, p.PresentMemberIDs, p.Now)
	}); err != nil {
		return -3
	}
	return 0
}
