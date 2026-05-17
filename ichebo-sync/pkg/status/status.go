// Package status is the single source of truth for the current sync state.
// It broadcasts state changes to Flutter via channel subscribers. Never blocks.
package status

import (
	"fmt"
	"sync"
	"time"
)

// State is the current sync engine state.
type State int

const (
	Synced   State = iota // ● Synced - N minutes ago
	Offline               // ○ Offline - N changes pending
	Syncing               // ⟳ Syncing - N of M changes...
	Conflict              // ⚠ N records need attention
	Blocked               // ✕ Sync blocked - contact administrator
)

// StateUpdate is broadcast to all subscribers on every state transition.
type StateUpdate struct {
	State         State
	PendingCount  int
	SyncedCount   int
	TotalCount    int
	LastSyncedAt  *time.Time
	ConflictCount int
	Message       string // pre-formatted display string
}

// Option configures a SetState call.
type Option func(*StateUpdate)

func WithPending(count int) Option   { return func(u *StateUpdate) { u.PendingCount = count } }
func WithProgress(synced, total int) Option {
	return func(u *StateUpdate) { u.SyncedCount = synced; u.TotalCount = total }
}
func WithConflicts(count int) Option  { return func(u *StateUpdate) { u.ConflictCount = count } }
func WithLastSynced(t time.Time) Option { return func(u *StateUpdate) { u.LastSyncedAt = &t } }

// Monitor is the sync state broadcaster.
type Monitor struct {
	mu          sync.RWMutex
	current     State
	last        StateUpdate
	subscribers []chan StateUpdate
}

// New creates a Monitor starting in Offline state.
func New() *Monitor { return &Monitor{current: Offline} }

// Current returns the current state snapshot without blocking.
func (m *Monitor) Current() StateUpdate {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return m.last
}

// Subscribe returns a buffered channel that receives a StateUpdate on every
// state transition. The caller must drain the channel; a full channel is
// dropped (non-blocking broadcast).
func (m *Monitor) Subscribe() <-chan StateUpdate {
	ch := make(chan StateUpdate, 8)
	m.mu.Lock()
	m.subscribers = append(m.subscribers, ch)
	m.mu.Unlock()
	return ch
}

// SetState transitions state and broadcasts to all subscribers.
func (m *Monitor) SetState(s State, opts ...Option) {
	update := StateUpdate{State: s}
	for _, opt := range opts {
		opt(&update)
	}
	update.Message = formatMessage(update)

	m.mu.Lock()
	m.current = s
	m.last = update
	subs := make([]chan StateUpdate, len(m.subscribers))
	copy(subs, m.subscribers)
	m.mu.Unlock()

	for _, ch := range subs {
		select {
		case ch <- update:
		default: // subscriber is slow — drop, never block
		}
	}
}

func formatMessage(u StateUpdate) string {
	switch u.State {
	case Synced:
		if u.LastSyncedAt != nil {
			ago := time.Since(*u.LastSyncedAt).Truncate(time.Minute)
			return fmt.Sprintf("● Synced - %v ago", ago)
		}
		return "● Synced"
	case Offline:
		return fmt.Sprintf("○ Offline - %d changes pending", u.PendingCount)
	case Syncing:
		if u.TotalCount > 0 {
			return fmt.Sprintf("⟳ Syncing - %d of %d changes...", u.SyncedCount, u.TotalCount)
		}
		return "⟳ Syncing..."
	case Conflict:
		return fmt.Sprintf("⚠ %d records need attention", u.ConflictCount)
	case Blocked:
		return "✕ Sync blocked - contact your administrator"
	}
	return ""
}
