package config

import (
	"fmt"
	"os"
	"runtime"
	"strconv"
	"strings"
)

type Config struct {
	Port             string
	UploadBucket     string
	DeliveryBucket   string
	S3Endpoint       string
	S3Region         string
	S3AccessKey      string
	S3SecretKey      string
	CDNBaseURL       string
	FFmpegPath       string
	WorkerCount      int
	DjangoWebhookURL string
	DjangoAPIKey     string
	TempDir          string
	LocalMode        bool // true when S3Endpoint is empty
	// Live streaming
	MediaMTXHLSBase string // CDN root where MediaMTX writes live HLS segments
	// CORS — chunk uploads (PUT /engine/upload/{id}/chunk/{n}) are called
	// directly from the browser on app.ichebo.org, cross-origin from this
	// server (video.ichebo.org). Added 2026-06-24 when wiring Learn's
	// lesson video upload into the web UI — confirmed by direct browser
	// test that uploads were blocked with zero CORS headers present.
	CORSAllowedOrigin string
}

func Load() *Config {
	workerCount := runtime.NumCPU() - 1
	if workerCount < 1 {
		workerCount = 1
	}
	if workerCount > 4 {
		workerCount = 4
	}
	if v := os.Getenv("MEDIA_WORKER_COUNT"); v != "" {
		if n, err := strconv.Atoi(v); err == nil && n > 0 {
			workerCount = n
		}
	}

	port := os.Getenv("MEDIA_PORT")
	if port == "" {
		port = "8090"
	}

	ffmpegPath := os.Getenv("MEDIA_FFMPEG_PATH")
	if ffmpegPath == "" {
		ffmpegPath = "ffmpeg"
	}

	tempDir := os.Getenv("MEDIA_TEMP_DIR")
	if tempDir == "" {
		tempDir = "/tmp/ichebo-media"
	}

	s3Endpoint := os.Getenv("MEDIA_S3_ENDPOINT")

	corsAllowedOrigin := os.Getenv("MEDIA_CORS_ALLOWED_ORIGIN")
	if corsAllowedOrigin == "" {
		corsAllowedOrigin = "https://app.ichebo.org"
	}

	return &Config{
		Port:              port,
		UploadBucket:      os.Getenv("MEDIA_UPLOAD_BUCKET"),
		DeliveryBucket:    os.Getenv("MEDIA_DELIVERY_BUCKET"),
		S3Endpoint:        s3Endpoint,
		S3Region:          os.Getenv("MEDIA_S3_REGION"),
		S3AccessKey:       os.Getenv("MEDIA_S3_ACCESS_KEY"),
		S3SecretKey:       os.Getenv("MEDIA_S3_SECRET_KEY"),
		CDNBaseURL:        os.Getenv("MEDIA_CDN_BASE_URL"),
		FFmpegPath:        ffmpegPath,
		WorkerCount:       workerCount,
		DjangoWebhookURL:  os.Getenv("MEDIA_DJANGO_WEBHOOK_URL"),
		DjangoAPIKey:      os.Getenv("MEDIA_DJANGO_API_KEY"),
		TempDir:           tempDir,
		LocalMode:         s3Endpoint == "",
		MediaMTXHLSBase:   os.Getenv("MEDIA_MEDIAMTX_HLS_BASE"),
		CORSAllowedOrigin: corsAllowedOrigin,
	}
}

// Validate fails fast on missing required configuration instead of letting
// the service start and silently degrade (e.g. transcodes completing with
// Django never notified, or S3 fields partially blank behind a non-empty
// endpoint). LocalMode (S3Endpoint == "") is treated as an intentional dev
// fallback and is exempt from the S3 checks below.
func (c *Config) Validate() error {
	var missing []string

	if !c.LocalMode {
		if c.S3Region == "" {
			missing = append(missing, "MEDIA_S3_REGION")
		}
		if c.S3AccessKey == "" {
			missing = append(missing, "MEDIA_S3_ACCESS_KEY")
		}
		if c.S3SecretKey == "" {
			missing = append(missing, "MEDIA_S3_SECRET_KEY")
		}
		if c.UploadBucket == "" {
			missing = append(missing, "MEDIA_UPLOAD_BUCKET")
		}
		if c.DeliveryBucket == "" {
			missing = append(missing, "MEDIA_DELIVERY_BUCKET")
		}
		if c.CDNBaseURL == "" {
			missing = append(missing, "MEDIA_CDN_BASE_URL")
		}
	}

	if c.DjangoWebhookURL == "" {
		missing = append(missing, "MEDIA_DJANGO_WEBHOOK_URL")
	}
	if c.DjangoAPIKey == "" {
		missing = append(missing, "MEDIA_DJANGO_API_KEY")
	}

	if len(missing) > 0 {
		return fmt.Errorf(
			"missing required environment variable(s): %s — see .env.example",
			strings.Join(missing, ", "),
		)
	}
	return nil
}
