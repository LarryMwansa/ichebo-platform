package upload

import (
	"fmt"
	"sync"
)

const defaultChunkSize = 5 * 1024 * 1024 // 5 MB

type Session struct {
	ID            string
	RecordID      string
	TenantID      string
	Filename      string
	FileSizeBytes int64
	TotalChunks   int
	ChunkSize     int64
	TempDir       string
	Received      map[int]string // chunk index → sha256 checksum
	mu            sync.Mutex
}

func (s *Session) MarkReceived(n int, checksum string) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.Received[n] = checksum
}

func (s *Session) IsComplete() bool {
	s.mu.Lock()
	defer s.mu.Unlock()
	return len(s.Received) == s.TotalChunks
}

func (s *Session) ChecksumFor(n int) (string, bool) {
	s.mu.Lock()
	defer s.mu.Unlock()
	c, ok := s.Received[n]
	return c, ok
}

// Registry holds active upload sessions in memory.
type Registry struct {
	sessions map[string]*Session
	mu       sync.RWMutex
}

func NewRegistry() *Registry {
	return &Registry{sessions: make(map[string]*Session)}
}

func (r *Registry) Create(id, recordID, tenantID, filename string, fileSize, chunkSize int64) *Session {
	if chunkSize <= 0 {
		chunkSize = defaultChunkSize
	}
	totalChunks := int((fileSize + chunkSize - 1) / chunkSize)

	s := &Session{
		ID:            id,
		RecordID:      recordID,
		TenantID:      tenantID,
		Filename:      filename,
		FileSizeBytes: fileSize,
		TotalChunks:   totalChunks,
		ChunkSize:     chunkSize,
		Received:      make(map[int]string),
	}

	r.mu.Lock()
	r.sessions[id] = s
	r.mu.Unlock()
	return s
}

func (r *Registry) Get(id string) (*Session, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()
	s, ok := r.sessions[id]
	if !ok {
		return nil, fmt.Errorf("upload session %q not found", id)
	}
	return s, nil
}

func (r *Registry) Delete(id string) {
	r.mu.Lock()
	delete(r.sessions, id)
	r.mu.Unlock()
}
