package stream

import (
	"context"
	"fmt"
	"log"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"

	"github.com/ichebo/media/pkg/storage"
	"github.com/ichebo/media/pkg/webhook"
)

// Archiver compiles a completed DVR recording into a VOD and publishes it to
// the delivery bucket. It is called asynchronously after a stream ends.
type Archiver struct {
	deliveryStore storage.DeliveryStore
	ffmpegPath    string
	tempDir       string
	webhookCli    *webhook.Client
}

func NewArchiver(
	deliveryStore storage.DeliveryStore,
	ffmpegPath string,
	tempDir string,
	webhookCli *webhook.Client,
) *Archiver {
	return &Archiver{
		deliveryStore: deliveryStore,
		ffmpegPath:    ffmpegPath,
		tempDir:       tempDir,
		webhookCli:    webhookCli,
	}
}

// Archive runs in a goroutine after the stream ends.
// It downloads the DVR HLS recording from MediaMTX's output path,
// packages it as an MP4 via FFmpeg, uploads it to the delivery bucket,
// and notifies Django with the VOD URL.
func (a *Archiver) Archive(session *Session) {
	log.Printf("[archiver] starting archive for record %s (stream key %s)", session.RecordID, session.StreamKey)

	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Hour)
	defer cancel()

	workDir := filepath.Join(a.tempDir, "archive", session.RecordID)
	if err := os.MkdirAll(workDir, 0755); err != nil {
		log.Printf("[archiver] failed to create work dir: %v", err)
		return
	}
	defer os.RemoveAll(workDir)

	// The DVR playlist written by MediaMTX to Object Storage.
	// Convention: MediaMTX is configured to write to dvr/{stream_key}/index.m3u8
	// under the delivery bucket — we construct the CDN URL here.
	dvrPlaylist := strings.TrimRight(session.HLSBaseURL, "/") +
		"/dvr/" + session.StreamKey + "/index.m3u8"

	outputPath := filepath.Join(workDir, "archive.mp4")

	// Remux HLS → MP4 — copy streams, no re-encode.
	args := []string{
		"-i", dvrPlaylist,
		"-c", "copy",
		"-movflags", "+faststart",
		"-y", outputPath,
	}
	cmd := exec.CommandContext(ctx, a.ffmpegPath, args...)
	if out, err := cmd.CombinedOutput(); err != nil {
		log.Printf("[archiver] ffmpeg remux failed: %v\n%s", err, out)
		return
	}

	// Upload archive MP4 to delivery bucket.
	archiveKey := fmt.Sprintf("videos/%s/archive.mp4", session.RecordID)
	f, err := os.Open(outputPath)
	if err != nil {
		log.Printf("[archiver] open output: %v", err)
		return
	}
	fi, _ := f.Stat()
	if err := a.deliveryStore.PutObject(ctx, archiveKey, f, fi.Size()); err != nil {
		f.Close()
		log.Printf("[archiver] upload archive: %v", err)
		return
	}
	f.Close()

	archiveURL := a.deliveryStore.GetPublicURL(archiveKey)
	log.Printf("[archiver] archive published: %s", archiveURL)

	// Notify Django so it can update the Gathering record with the VOD URL.
	a.notifyArchiveComplete(session, archiveURL)
}

func (a *Archiver) notifyArchiveComplete(session *Session, archiveURL string) {
	if a.webhookCli == nil {
		return
	}
	payload := webhook.TranscodeCompletePayload{
		JobID:    "archive-" + session.RecordID,
		RecordID: session.RecordID,
		Status:   "complete",
		VideoURL: archiveURL,
	}
	if err := a.webhookCli.NotifyTranscodeComplete(payload); err != nil {
		log.Printf("[archiver] webhook notify failed for record %s: %v", session.RecordID, err)
	}
}
