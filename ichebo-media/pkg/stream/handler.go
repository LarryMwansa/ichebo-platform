package stream

import (
	"encoding/json"
	"net/http"
)

// Handler exposes the stream lifecycle endpoints called by MediaMTX on-publish
// and on-publish-done hooks.
type Handler struct {
	registry *Registry
	archiver *Archiver
}

func NewHandler(registry *Registry, archiver *Archiver) *Handler {
	return &Handler{registry: registry, archiver: archiver}
}

// StartRequest is the body sent by MediaMTX (or Django) when a broadcast begins.
type StartRequest struct {
	StreamKey  string `json:"stream_key"`
	RecordID   string `json:"record_id"`
	TenantID   string `json:"tenant_id"`
	HLSBaseURL string `json:"hls_base_url"` // CDN root where MediaMTX writes segments
}

// EndRequest is sent when MediaMTX detects the RTMP connection has closed.
type EndRequest struct {
	StreamKey string `json:"stream_key"`
}

type sessionResponse struct {
	StreamKey string `json:"stream_key"`
	RecordID  string `json:"record_id"`
	StartedAt string `json:"started_at"`
}

// POST /engine/stream/start
// Called by MediaMTX on-publish hook when broadcaster connects.
func (h *Handler) Start(w http.ResponseWriter, r *http.Request) {
	var req StartRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "invalid request body", http.StatusBadRequest)
		return
	}
	if req.StreamKey == "" || req.RecordID == "" {
		http.Error(w, "stream_key and record_id are required", http.StatusBadRequest)
		return
	}

	session, err := h.registry.Start(req.StreamKey, req.RecordID, req.TenantID, req.HLSBaseURL)
	if err != nil {
		http.Error(w, err.Error(), http.StatusConflict)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(sessionResponse{
		StreamKey: session.StreamKey,
		RecordID:  session.RecordID,
		StartedAt: session.StartedAt.Format("2006-01-02T15:04:05Z"),
	})
}

// POST /engine/stream/end
// Called by MediaMTX on-publish-done hook when the RTMP connection closes.
// Triggers async DVR archive compilation.
func (h *Handler) End(w http.ResponseWriter, r *http.Request) {
	var req EndRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "invalid request body", http.StatusBadRequest)
		return
	}
	if req.StreamKey == "" {
		http.Error(w, "stream_key is required", http.StatusBadRequest)
		return
	}

	session, err := h.registry.End(req.StreamKey)
	if err != nil {
		http.Error(w, err.Error(), http.StatusNotFound)
		return
	}

	// Fire archive compilation in the background — do not block the response.
	go h.archiver.Archive(session)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{
		"status":    "archiving",
		"record_id": session.RecordID,
	})
}

// GET /engine/stream/active
// Returns all currently active broadcast sessions. Useful for the Django
// admin dashboard to show live status.
func (h *Handler) Active(w http.ResponseWriter, r *http.Request) {
	sessions := h.registry.Active()
	type item struct {
		StreamKey string `json:"stream_key"`
		RecordID  string `json:"record_id"`
		TenantID  string `json:"tenant_id"`
		StartedAt string `json:"started_at"`
	}
	out := make([]item, 0, len(sessions))
	for _, s := range sessions {
		out = append(out, item{
			StreamKey: s.StreamKey,
			RecordID:  s.RecordID,
			TenantID:  s.TenantID,
			StartedAt: s.StartedAt.Format("2006-01-02T15:04:05Z"),
		})
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(out)
}
