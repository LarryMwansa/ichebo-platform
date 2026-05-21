package transcode

import (
	"encoding/json"
	"net/http"
	"strings"
	"time"

	"github.com/google/uuid"
)

type Handler struct {
	queue *Queue
}

func NewHandler(queue *Queue) *Handler {
	return &Handler{queue: queue}
}

type TranscodeRequest struct {
	UploadID       string   `json:"upload_id"`
	RecordID       string   `json:"record_id"`
	RawObjectKey   string   `json:"raw_object_key"`
	TenantID       string   `json:"tenant_id"`
	QualityProfiles []string `json:"quality_profiles"`
}

type TranscodeResponse struct {
	JobID string `json:"job_id"`
}

func (h *Handler) StartTranscode(w http.ResponseWriter, r *http.Request) {
	var req TranscodeRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "invalid request body", http.StatusBadRequest)
		return
	}
	if req.RecordID == "" || req.RawObjectKey == "" {
		http.Error(w, "record_id and raw_object_key are required", http.StatusBadRequest)
		return
	}

	job := &Job{
		ID:           uuid.New().String(),
		UploadID:     req.UploadID,
		RecordID:     req.RecordID,
		TenantID:     req.TenantID,
		RawObjectKey: req.RawObjectKey,
		Profiles:     req.QualityProfiles,
		Status:       StatusQueued,
		CreatedAt:    time.Now(),
	}

	if err := h.queue.Enqueue(job); err != nil {
		http.Error(w, err.Error(), http.StatusServiceUnavailable)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusAccepted)
	json.NewEncoder(w).Encode(TranscodeResponse{JobID: job.ID})
}

func (h *Handler) JobStatus(w http.ResponseWriter, r *http.Request) {
	// URL: GET /engine/transcode/{job_id}/status
	parts := strings.Split(strings.TrimPrefix(r.URL.Path, "/engine/transcode/"), "/")
	if len(parts) < 2 || parts[1] != "status" {
		http.Error(w, "invalid URL", http.StatusBadRequest)
		return
	}
	jobID := parts[0]

	job, err := h.queue.Get(jobID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(job.Snapshot())
}

type StatusResponse struct {
	QueueDepth    int `json:"queue_depth"`
	ActiveWorkers int `json:"active_workers"`
}

func EngineStatusHandler(queue *Queue, workerCount int) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(StatusResponse{
			QueueDepth:    len(queue.ch),
			ActiveWorkers: workerCount,
		})
	}
}
