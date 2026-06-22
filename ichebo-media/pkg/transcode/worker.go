package transcode

import (
	"bufio"
	"context"
	"fmt"
	"io"
	"log"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
	"time"

	"github.com/ichebo/media/pkg/hls"
	"github.com/ichebo/media/pkg/storage"
	"github.com/ichebo/media/pkg/webhook"
)

// s3Downloader is satisfied by *storage.S3Store, enabling direct GetObject
// without a round-trip through a presigned URL.
type s3Downloader interface {
	DownloadToWriter(ctx context.Context, key string, w io.Writer) error
}

// WorkerPool runs workerCount goroutines pulling jobs from q.
type WorkerPool struct {
	count         int
	queue         *Queue
	uploadStore   storage.UploadStore
	deliveryStore storage.DeliveryStore
	ffmpegPath    string
	tempDir       string
	webhookCli    *webhook.Client
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
		job.SetOutput(stubURL, "", 0)
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

	// Probe duration so we can report it to Django on completion.
	durationSeconds := wp.probeDuration(inputPath)

	// Transcode each profile — emit per-profile progress using the probed duration.
	for i, profile := range profiles {
		baseProgress := (i * 80) / len(profiles)
		profileProgress := 80 / len(profiles)
		job.SetProgress(baseProgress)

		outDir := filepath.Join(workDir, profile.Name)
		if err := os.MkdirAll(outDir, 0755); err != nil {
			return fmt.Errorf("create output dir for %s: %w", profile.Name, err)
		}
		if err := wp.transcodeProfileWithProgress(inputPath, outDir, profile, durationSeconds, func(pct int) {
			job.SetProgress(baseProgress + (pct*profileProgress)/100)
		}); err != nil {
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
	job.SetOutput(videoURL, thumbURL, durationSeconds)
	wp.notifyDjango(job, videoURL, thumbURL, durationSeconds)

	return nil
}

// transcodeProfileWithProgress runs FFmpeg for one quality profile and calls
// onProgress(0-100) as FFmpeg reports time= on stderr.
// totalSeconds==0 disables percentage reporting (onProgress is still called at 0 and 100).
func (wp *WorkerPool) transcodeProfileWithProgress(
	inputPath, outDir string,
	profile QualityProfile,
	totalSeconds int,
	onProgress func(int),
) error {
	segPattern := filepath.Join(outDir, "segment_%03d.ts")
	manifestPath := filepath.Join(outDir, "index.m3u8")

	args := []string{"-i", inputPath, "-y", "-progress", "pipe:2", "-nostats"}
	args = append(args, profile.FFmpegVideoArgs()...)
	args = append(args,
		"-hls_time", "6",
		"-hls_list_size", "0",
		"-hls_segment_filename", segPattern,
		manifestPath,
	)

	cmd := exec.Command(wp.ffmpegPath, args...)
	stderrPipe, err := cmd.StderrPipe()
	if err != nil {
		return fmt.Errorf("ffmpeg stderr pipe: %w", err)
	}

	if err := cmd.Start(); err != nil {
		return fmt.Errorf("ffmpeg start: %w", err)
	}

	onProgress(0)
	for pct := range parseFFmpegProgress(stderrPipe, totalSeconds) {
		onProgress(pct)
	}

	if err := cmd.Wait(); err != nil {
		return fmt.Errorf("ffmpeg: %w", err)
	}
	onProgress(100)
	return nil
}

// transcodeProfile is the simple non-progress variant kept for callers that
// do not need per-profile progress updates (e.g. tests).
func (wp *WorkerPool) transcodeProfile(inputPath, outDir string, profile QualityProfile) error {
	return wp.transcodeProfileWithProgress(inputPath, outDir, profile, 0, func(int) {})
}

// probeDuration runs ffprobe to get the duration of the input file in seconds.
// Returns 0 on any error — callers treat 0 as "duration unknown".
func (wp *WorkerPool) probeDuration(inputPath string) int {
	out, err := exec.Command(
		"ffprobe",
		"-v", "error",
		"-show_entries", "format=duration",
		"-of", "default=noprint_wrappers=1:nokey=1",
		inputPath,
	).Output()
	if err != nil {
		return 0
	}
	s := strings.TrimSpace(string(out))
	// duration may be "123.456000"
	if dot := strings.IndexByte(s, '.'); dot >= 0 {
		s = s[:dot]
	}
	n, err := strconv.Atoi(s)
	if err != nil {
		return 0
	}
	return n
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
	if err := os.MkdirAll(filepath.Dir(destPath), 0755); err != nil {
		return err
	}

	// S3Store implements s3Downloader — use direct GetObject (no presigned round-trip).
	if dl, ok := wp.uploadStore.(s3Downloader); ok {
		f, err := os.Create(destPath)
		if err != nil {
			return err
		}
		defer f.Close()
		return dl.DownloadToWriter(context.Background(), key, f)
	}

	// LocalStore: GetPresignedURL returns a file:// URI — copy the file directly.
	url, err := wp.uploadStore.GetPresignedURL(context.Background(), key, time.Hour)
	if err != nil {
		return err
	}
	if strings.HasPrefix(url, "file://") {
		return copyFile(strings.TrimPrefix(url, "file://"), destPath)
	}

	// Generic fallback: HTTP download of a presigned URL.
	f, err := os.Create(destPath)
	if err != nil {
		return err
	}
	defer f.Close()
	return storage.HTTPDownload(url, f)
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

// parseFFmpegProgress reads FFmpeg's -progress pipe:2 output and emits
// progress percentages (0-100) based on out_time_ms lines.
// totalSeconds==0 disables percentage calculation — channel stays silent
// until FFmpeg finishes (no values emitted, just closed).
func parseFFmpegProgress(r io.Reader, totalSeconds int) <-chan int {
	ch := make(chan int, 10)
	go func() {
		defer close(ch)
		if totalSeconds <= 0 {
			// Drain the reader so the pipe doesn't block FFmpeg.
			_, _ = io.Copy(io.Discard, r)
			return
		}
		totalMS := int64(totalSeconds) * 1_000_000 // out_time_ms is in microseconds
		scanner := bufio.NewScanner(r)
		for scanner.Scan() {
			line := scanner.Text()
			// -progress pipe:2 emits key=value lines; out_time_ms is microseconds elapsed.
			if !strings.HasPrefix(line, "out_time_ms=") {
				continue
			}
			val := strings.TrimPrefix(line, "out_time_ms=")
			us, err := strconv.ParseInt(strings.TrimSpace(val), 10, 64)
			if err != nil || us <= 0 {
				continue
			}
			pct := int((us * 100) / totalMS)
			if pct > 99 {
				pct = 99 // 100 is emitted by the caller after cmd.Wait()
			}
			ch <- pct
		}
	}()
	return ch
}
