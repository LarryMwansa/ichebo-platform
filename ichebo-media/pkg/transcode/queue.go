package transcode

import (
	"fmt"
	"sync"
	"time"
)

const (
	StatusQueued     = "queued"
	StatusProcessing = "processing"
	StatusComplete   = "complete"
	StatusFailed     = "failed"
)

// Job represents a single transcode request.
type Job struct {
	ID           string
	UploadID     string
	RecordID     string
	TenantID     string
	RawObjectKey string
	Profiles     []string
	Status       string
	ProgressPct  int
	Error        string
	CreatedAt    time.Time
	CompletedAt  *time.Time

	// Output — set once the job completes. Mirrors what the webhook payload
	// carries, so a status poll can fully reconcile a record even if the
	// webhook delivery itself was lost (e.g. Django was briefly unreachable).
	VideoURL        string
	ThumbnailURL    string
	DurationSeconds int

	mu sync.Mutex
}

func (j *Job) SetStatus(status string) {
	j.mu.Lock()
	defer j.mu.Unlock()
	j.Status = status
	if status == StatusComplete || status == StatusFailed {
		now := time.Now()
		j.CompletedAt = &now
	}
}

func (j *Job) SetProgress(pct int) {
	j.mu.Lock()
	defer j.mu.Unlock()
	j.ProgressPct = pct
}

func (j *Job) SetError(err string) {
	j.mu.Lock()
	defer j.mu.Unlock()
	j.Error = err
}

// SetOutput records the transcode result so a later status poll can recover
// it even if the push webhook to Django never arrived.
func (j *Job) SetOutput(videoURL, thumbnailURL string, durationSeconds int) {
	j.mu.Lock()
	defer j.mu.Unlock()
	j.VideoURL = videoURL
	j.ThumbnailURL = thumbnailURL
	j.DurationSeconds = durationSeconds
}

func (j *Job) Snapshot() JobSnapshot {
	j.mu.Lock()
	defer j.mu.Unlock()
	return JobSnapshot{
		ID:              j.ID,
		Status:          j.Status,
		ProgressPct:     j.ProgressPct,
		Error:           j.Error,
		VideoURL:        j.VideoURL,
		ThumbnailURL:    j.ThumbnailURL,
		DurationSeconds: j.DurationSeconds,
	}
}

type JobSnapshot struct {
	ID              string `json:"job_id"`
	Status          string `json:"status"`
	ProgressPct     int    `json:"progress_pct"`
	Error           string `json:"error,omitempty"`
	VideoURL        string `json:"video_url,omitempty"`
	ThumbnailURL    string `json:"thumbnail_url,omitempty"`
	DurationSeconds int    `json:"duration_seconds,omitempty"`
}

// Queue manages the in-memory job list and dispatch channel.
type Queue struct {
	jobs map[string]*Job
	ch   chan *Job
	mu   sync.RWMutex
}

func NewQueue(bufferSize int) *Queue {
	return &Queue{
		jobs: make(map[string]*Job),
		ch:   make(chan *Job, bufferSize),
	}
}

func (q *Queue) Enqueue(job *Job) error {
	q.mu.Lock()
	q.jobs[job.ID] = job
	q.mu.Unlock()

	select {
	case q.ch <- job:
		return nil
	default:
		return fmt.Errorf("queue full — try again later")
	}
}

func (q *Queue) Get(id string) (*Job, error) {
	q.mu.RLock()
	defer q.mu.RUnlock()
	j, ok := q.jobs[id]
	if !ok {
		return nil, fmt.Errorf("job %q not found", id)
	}
	return j, nil
}

// Chan returns the receive-only channel for workers to pull jobs from.
func (q *Queue) Chan() <-chan *Job {
	return q.ch
}
