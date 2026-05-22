// Package stream manages live broadcast sessions.
// It validates stream keys issued by Django, tracks active sessions,
// and triggers DVR archive compilation when a broadcast ends.
package stream

import (
	"fmt"
	"sync"
	"time"
)

// Session holds state for a single active broadcast.
type Session struct {
	StreamKey  string
	RecordID   string // Gathering record ID on Django
	TenantID   string
	StartedAt  time.Time
	HLSBaseURL string // CDN path where MediaMTX is writing HLS segments
}

// Registry is an in-memory store of active broadcast sessions keyed by stream key.
// Sessions are created when MediaMTX signals stream start and removed on stream end.
type Registry struct {
	mu       sync.RWMutex
	sessions map[string]*Session
}

func NewRegistry() *Registry {
	return &Registry{sessions: make(map[string]*Session)}
}

// Start registers a new session. Returns an error if the key is already active.
func (r *Registry) Start(key, recordID, tenantID, hlsBaseURL string) (*Session, error) {
	r.mu.Lock()
	defer r.mu.Unlock()

	if _, exists := r.sessions[key]; exists {
		return nil, fmt.Errorf("stream: key %q already active", key)
	}
	s := &Session{
		StreamKey:  key,
		RecordID:   recordID,
		TenantID:   tenantID,
		StartedAt:  time.Now().UTC(),
		HLSBaseURL: hlsBaseURL,
	}
	r.sessions[key] = s
	return s, nil
}

// End removes the session and returns it for archive processing.
// Returns an error if the key is not active.
func (r *Registry) End(key string) (*Session, error) {
	r.mu.Lock()
	defer r.mu.Unlock()

	s, exists := r.sessions[key]
	if !exists {
		return nil, fmt.Errorf("stream: key %q not found", key)
	}
	delete(r.sessions, key)
	return s, nil
}

// Active returns a snapshot of all active sessions.
func (r *Registry) Active() []*Session {
	r.mu.RLock()
	defer r.mu.RUnlock()

	out := make([]*Session, 0, len(r.sessions))
	for _, s := range r.sessions {
		out = append(out, s)
	}
	return out
}
