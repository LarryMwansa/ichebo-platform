package transcode

import (
	"strings"
	"testing"
)

func TestQueue_EnqueueAndDequeue(t *testing.T) {
	q := NewQueue(10)
	job := &Job{
		ID:           "job1",
		RecordID:     "rec1",
		RawObjectKey: "uploads/rec1/original.mp4",
		Status:       StatusQueued,
	}
	if err := q.Enqueue(job); err != nil {
		t.Fatal(err)
	}

	got := <-q.Chan()
	if got.ID != "job1" {
		t.Fatalf("expected job1, got %s", got.ID)
	}
}

func TestJob_StatusTransitions(t *testing.T) {
	job := &Job{ID: "j1", Status: StatusQueued}
	job.SetStatus(StatusProcessing)
	if job.Status != StatusProcessing {
		t.Fatalf("expected processing, got %s", job.Status)
	}

	job.SetStatus(StatusComplete)
	if job.Status != StatusComplete {
		t.Fatal("expected complete")
	}
	if job.CompletedAt == nil {
		t.Fatal("CompletedAt should be set on complete")
	}
}

func TestJob_ProgressUpdate(t *testing.T) {
	job := &Job{ID: "j2", Status: StatusProcessing}
	job.SetProgress(42)
	snap := job.Snapshot()
	if snap.ProgressPct != 42 {
		t.Fatalf("expected 42, got %d", snap.ProgressPct)
	}
}

func TestProfile_FFmpegArgs_Video(t *testing.T) {
	p := QualityProfile{
		Name:         "720p",
		Width:        1280,
		Height:       720,
		VideoBitrate: "2M",
		AudioBitrate: "128k",
	}
	args := p.FFmpegVideoArgs()
	argsStr := strings.Join(args, " ")

	if !strings.Contains(argsStr, "1280:720") {
		t.Errorf("expected scale=1280:720 in args: %s", argsStr)
	}
	if !strings.Contains(argsStr, "-b:v 2M") {
		t.Errorf("expected -b:v 2M in args: %s", argsStr)
	}
	if !strings.Contains(argsStr, "-b:a 128k") {
		t.Errorf("expected -b:a 128k in args: %s", argsStr)
	}
}

func TestProfile_FFmpegArgs_Audio(t *testing.T) {
	p := QualityProfile{
		Name:         "audio",
		AudioBitrate: "128k",
	}
	args := p.FFmpegVideoArgs()
	argsStr := strings.Join(args, " ")

	if !strings.Contains(argsStr, "-vn") {
		t.Errorf("expected -vn (no video) in audio profile: %s", argsStr)
	}
	if strings.Contains(argsStr, "scale=") {
		t.Errorf("audio profile should not have scale filter: %s", argsStr)
	}
}

func TestWorker_StubMode(t *testing.T) {
	// Verifies that the stub mode path resolves profiles correctly.
	profiles := resolveProfiles(nil)
	if len(profiles) != len(DefaultProfiles) {
		t.Fatalf("expected %d default profiles, got %d", len(DefaultProfiles), len(profiles))
	}

	profiles = resolveProfiles([]string{"720p", "480p"})
	if len(profiles) != 2 {
		t.Fatalf("expected 2 profiles, got %d", len(profiles))
	}
	if profiles[0].Name != "720p" {
		t.Fatalf("expected 720p first, got %s", profiles[0].Name)
	}
}

func TestQueue_Full(t *testing.T) {
	q := NewQueue(1) // buffer of 1
	job1 := &Job{ID: "j1", Status: StatusQueued}
	job2 := &Job{ID: "j2", Status: StatusQueued}

	if err := q.Enqueue(job1); err != nil {
		t.Fatal("first enqueue should succeed")
	}
	if err := q.Enqueue(job2); err == nil {
		t.Fatal("second enqueue to full queue should fail")
	}
}
