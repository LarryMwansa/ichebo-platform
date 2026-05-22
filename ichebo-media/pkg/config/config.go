package config

import (
	"os"
	"runtime"
	"strconv"
)

type Config struct {
	Port              string
	UploadBucket      string
	DeliveryBucket    string
	S3Endpoint        string
	S3Region          string
	S3AccessKey       string
	S3SecretKey       string
	CDNBaseURL        string
	FFmpegPath        string
	WorkerCount       int
	DjangoWebhookURL  string
	DjangoAPIKey      string
	TempDir           string
	LocalMode         bool // true when S3Endpoint is empty
	// Live streaming
	MediaMTXHLSBase   string // CDN root where MediaMTX writes live HLS segments
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

	return &Config{
		Port:             port,
		UploadBucket:     os.Getenv("MEDIA_UPLOAD_BUCKET"),
		DeliveryBucket:   os.Getenv("MEDIA_DELIVERY_BUCKET"),
		S3Endpoint:       s3Endpoint,
		S3Region:         os.Getenv("MEDIA_S3_REGION"),
		S3AccessKey:      os.Getenv("MEDIA_S3_ACCESS_KEY"),
		S3SecretKey:      os.Getenv("MEDIA_S3_SECRET_KEY"),
		CDNBaseURL:       os.Getenv("MEDIA_CDN_BASE_URL"),
		FFmpegPath:       ffmpegPath,
		WorkerCount:      workerCount,
		DjangoWebhookURL: os.Getenv("MEDIA_DJANGO_WEBHOOK_URL"),
		DjangoAPIKey:     os.Getenv("MEDIA_DJANGO_API_KEY"),
		TempDir:          tempDir,
		LocalMode:        s3Endpoint == "",
		MediaMTXHLSBase:  os.Getenv("MEDIA_MEDIAMTX_HLS_BASE"),
	}
}
