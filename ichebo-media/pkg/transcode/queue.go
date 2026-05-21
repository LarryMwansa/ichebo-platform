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

func (j *Job) Snapshot() JobSnapshot {
	j.mu.Lock()
	defer j.mu.Unlock()
	return JobSnapshot{
		ID:          j.ID,
		Status:      j.Status,
		ProgressPct: j.ProgressPct,
		Error:       j.Error,
	}
}

type JobSnapshot struct {
	ID          string `json:"job_id"`
	Status      string `json:"status"`
	ProgressPct int    `json:"progress_pct"`
	Error       string `json:"error,omitempty"`
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
