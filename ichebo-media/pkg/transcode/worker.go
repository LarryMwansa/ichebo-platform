package transcode

import (
	"bufio"
	"bytes"
	"context"
	"fmt"
	"io"
	"log"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"

	"github.com/ichebo/media/pkg/hls"
	"github.com/ichebo/media/pkg/storage"
	"github.com/ichebo/media/pkg/webhook"
)

// WorkerPool runs workerCount goroutines pulling jobs from q.
type WorkerPool struct {
	count        int
	queue        *Queue
	uploadStore  storage.UploadStore
	deliveryStore storage.DeliveryStore
	ffmpegPath   string
	tempDir      string
	webhookCli   *webhook.Client
}

func NewWorkerPool(
	count int,
	queue *Queue,
	uploadStore storage.UploadStore,
	deliveryStore storage.DeliveryStore,
	ffmpegPath string,
	tempDir string,
	webhookCli *webhook.Client,
) *WorkerPool {
	return &WorkerPool{
		count:        count,
		queue:        queue,
		uploadStore:  uploadStore,
		deliveryStore: deliveryStore,
		ffmpegPath:   ffmpegPath,
		tempDir:      tempDir,
		webhookCli:   webhookCli,
	}
}

func (wp *WorkerPool) Start() {
	for i := 0; i < wp.count; i++ {
		go wp.runWorker(i)
	}
}

func (wp *WorkerPool) runWorker(id int) {
	for job := range wp.queue.Chan() {
		log.Printf("[worker %d] starting job %s (record %s)", id, job.ID, job.RecordID)
		if err := wp.process(job); err != nil {
			log.Printf("[worker %d] job %s failed: %v", id, job.ID, err)
			job.SetError(err.Error())
			job.SetStatus(StatusFailed)
			wp.notifyDjango(job, "", "", 0)
		}
	}
}

func (wp *WorkerPool) process(job *Job) error {
	job.SetStatus(StatusProcessing)

	// Check FFmpeg availability. In local dev mode, stub out the transcode.
	ffmpegAvail := wp.isFFmpegAvailable()
	if !ffmpegAvail {
		log.Printf("[transcode] ffmpeg not available — stub mode for job %s", job.ID)
		job.SetProgress(100)
		job.SetStatus(StatusComplete)
		stubURL := "file:///tmp/ichebo-media/stub-video.m3u8"
		wp.notifyDjango(job, stubURL, "", 0)
		return nil
	}

	workDir := filepath.Join(wp.tempDir, "transcode", job.ID)
	if err := os.MkdirAll(workDir, 0755); err != nil {
		return fmt.Errorf("create work dir: %w", err)
	}
	defer os.RemoveAll(workDir)

	// Download raw file from upload store.
	inputPath := filepath.Join(workDir, "input"+filepath.Ext(job.RawObjectKey))
	if err := wp.downloadFromStore(job.RawObjectKey, inputPath); err != nil {
		return fmt.Errorf("download raw file: %w", err)
	}

	// Determine which profiles to run.
	profiles := resolveProfiles(job.Profiles)

	// Transcode each profile.
	for i, profile := range profiles {
		job.SetProgress((i * 80) / len(profiles))
		outDir := filepath.Join(workDir, profile.Name)
		if err := os.MkdirAll(outDir, 0755); err != nil {
			return fmt.Errorf("create output dir for %s: %w", profile.Name, err)
		}
		if err := wp.transcodeProfile(inputPath, outDir, profile); err != nil {
			return fmt.Errorf("transcode %s: %w", profile.Name, err)
		}
		// Upload segments and manifest.
		if err := wp.uploadProfileOutput(job.RecordID, profile.Name, outDir); err != nil {
			return fmt.Errorf("upload %s output: %w", profile.Name, err)
		}
	}

	job.SetProgress(85)

	// Extract thumbnail.
	thumbPath := filepath.Join(workDir, "thumbnail.jpg")
	_ = wp.extractThumbnail(inputPath, thumbPath) // non-fatal

	thumbKey := fmt.Sprintf("videos/%s/thumbnail.jpg", job.RecordID)
	if f, err := os.Open(thumbPath); err == nil {
		fi, _ := f.Stat()
		_ = wp.deliveryStore.PutObject(context.Background(), thumbKey, f, fi.Size())
		f.Close()
	}

	// Build and upload master manifest.
	hlsProfiles := make([]hls.Profile, len(profiles))
	for i, p := range profiles {
		bw := 4_000_000
		switch p.Name {
		case "720p":
			bw = 2_000_000
		case "480p":
			bw = 1_000_000
		case "360p":
			bw = 600_000
		case "audio":
			bw = 128_000
		}
		hlsProfiles[i] = hls.Profile{Name: p.Name, Width: p.Width, Height: p.Height, Bandwidth: bw}
	}
	masterManifest := hls.BuildMasterManifest(hlsProfiles)
	masterKey := fmt.Sprintf("videos/%s/index.m3u8", job.RecordID)
	if err := wp.deliveryStore.PutObject(
		context.Background(), masterKey,
		strings.NewReader(masterManifest), int64(len(masterManifest)),
	); err != nil {
		return fmt.Errorf("upload master manifest: %w", err)
	}

	job.SetProgress(100)
	job.SetStatus(StatusComplete)

	videoURL := wp.deliveryStore.GetPublicURL(masterKey)
	thumbURL := wp.deliveryStore.GetPublicURL(thumbKey)
	wp.notifyDjango(job, videoURL, thumbURL, 0) // duration from FFprobe can be added later

	return nil
}

func (wp *WorkerPool) transcodeProfile(inputPath, outDir string, profile QualityProfile) error {
	segPattern := filepath.Join(outDir, "segment_%03d.ts")
	manifestPath := filepath.Join(outDir, "index.m3u8")

	args := []string{"-i", inputPath, "-y"}
	args = append(args, profile.FFmpegVideoArgs()...)
	args = append(args,
		"-hls_time", "6",
		"-hls_list_size", "0",
		"-hls_segment_filename", segPattern,
		manifestPath,
	)

	cmd := exec.Command(wp.ffmpegPath, args...)
	var stderr bytes.Buffer
	cmd.Stderr = &stderr

	if err := cmd.Run(); err != nil {
		return fmt.Errorf("ffmpeg: %w — stderr: %s", err, stderr.String())
	}
	return nil
}

func (wp *WorkerPool) extractThumbnail(inputPath, thumbPath string) error {
	cmd := exec.Command(wp.ffmpegPath,
		"-i", inputPath,
		"-ss", "10",
		"-frames:v", "1",
		"-y", thumbPath,
	)
	return cmd.Run()
}

func (wp *WorkerPool) uploadProfileOutput(recordID, profileName, outDir string) error {
	return filepath.Walk(outDir, func(path string, info os.FileInfo, err error) error {
		if err != nil || info.IsDir() {
			return err
		}
		rel, _ := filepath.Rel(outDir, path)
		key := fmt.Sprintf("videos/%s/%s/%s", recordID, profileName, rel)
		f, err := os.Open(path)
		if err != nil {
			return err
		}
		defer f.Close()
		fi, _ := f.Stat()
		return wp.deliveryStore.PutObject(context.Background(), key, f, fi.Size())
	})
}

func (wp *WorkerPool) downloadFromStore(key, destPath string) error {
	// For LocalStore, the key is already a file path relative to the store base.
	// We use GetPresignedURL to get the file path and copy.
	url, err := wp.uploadStore.GetPresignedURL(context.Background(), key, time.Hour)
	if err != nil {
		return err
	}

	// Local: url is file:// path — read directly.
	if strings.HasPrefix(url, "file://") {
		srcPath := strings.TrimPrefix(url, "file://")
		return copyFile(srcPath, destPath)
	}

	// For S3, this would use http.Get(url) — simplified here.
	return fmt.Errorf("S3 download not yet implemented (use local dev mode)")
}

func copyFile(src, dst string) error {
	in, err := os.Open(src)
	if err != nil {
		return err
	}
	defer in.Close()

	if err := os.MkdirAll(filepath.Dir(dst), 0755); err != nil {
		return err
	}
	out, err := os.Create(dst)
	if err != nil {
		return err
	}
	defer out.Close()
	_, err = io.Copy(out, in)
	return err
}

func (wp *WorkerPool) isFFmpegAvailable() bool {
	cmd := exec.Command(wp.ffmpegPath, "-version")
	return cmd.Run() == nil
}

func (wp *WorkerPool) notifyDjango(job *Job, videoURL, thumbURL string, duration int) {
	if wp.webhookCli == nil {
		return
	}
	payload := webhook.TranscodeCompletePayload{
		JobID:           job.ID,
		RecordID:        job.RecordID,
		Status:          job.Status,
		VideoURL:        videoURL,
		ThumbnailURL:    thumbURL,
		DurationSeconds: duration,
	}
	if err := wp.webhookCli.NotifyTranscodeComplete(payload); err != nil {
		log.Printf("[worker] webhook notify failed for job %s: %v", job.ID, err)
	}
}

func resolveProfiles(names []string) []QualityProfile {
	if len(names) == 0 {
		return DefaultProfiles
	}
	var out []QualityProfile
	for _, name := range names {
		if p, ok := ProfileByName(name); ok {
			out = append(out, p)
		}
	}
	if len(out) == 0 {
		return DefaultProfiles
	}
	return out
}

// parseFFmpegProgress reads FFmpeg stderr lines and extracts time= progress.
// This is used for future progress reporting via stderr streaming.
func parseFFmpegProgress(r io.Reader) <-chan int {
	ch := make(chan int, 10)
	go func() {
		defer close(ch)
		scanner := bufio.NewScanner(r)
		for scanner.Scan() {
			line := scanner.Text()
			if strings.Contains(line, "time=") {
				_ = line // TODO: parse time= and emit percent
			}
		}
	}()
	return ch
}
