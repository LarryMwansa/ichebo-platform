package main

import (
	"context"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/ichebo/media/pkg/config"
	"github.com/ichebo/media/pkg/health"
	"github.com/ichebo/media/pkg/storage"
	"github.com/ichebo/media/pkg/stream"
	"github.com/ichebo/media/pkg/transcode"
	"github.com/ichebo/media/pkg/upload"
	"github.com/ichebo/media/pkg/webhook"
)

// withCORS wraps a handler with CORS headers scoped to a single allowed
// origin, plus OPTIONS preflight handling. Only applied to the upload
// routes (PUT/POST /engine/upload/...) — those are the only ones called
// directly from a browser (Learn's lesson-authoring page, on
// app.ichebo.org); every other /engine/ route is called server-to-server
// (Django's webhook handlers, MediaMTX's hooks), which never needs CORS
// because the browser is never the caller.
func withCORS(allowedOrigin string, next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", allowedOrigin)
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type, X-Chunk-Checksum")
		if r.Method == http.MethodOptions {
			w.WriteHeader(http.StatusNoContent)
			return
		}
		next(w, r)
	}
}

func main() {
	cfg := config.Load()
	if err := cfg.Validate(); err != nil {
		log.Fatalf("[mediad] config error: %v", err)
	}

	// ── Storage ──────────────────────────────────────────────────────────────
	var uploadStore storage.UploadStore
	var deliveryStore storage.DeliveryStore

	if cfg.LocalMode {
		log.Println("[mediad] local mode — using disk storage at", cfg.TempDir)
		uploadLocal, err := storage.NewLocalStore(cfg.TempDir + "/upload")
		if err != nil {
			log.Fatalf("init upload store: %v", err)
		}
		deliveryLocal, err := storage.NewLocalStore(cfg.TempDir + "/delivery")
		if err != nil {
			log.Fatalf("init delivery store: %v", err)
		}
		uploadStore = uploadLocal
		deliveryStore = deliveryLocal
	} else {
		log.Println("[mediad] production mode — S3 storage at", cfg.S3Endpoint)
		uploadS3, err := storage.NewS3Store(storage.S3Config{
			Endpoint:   cfg.S3Endpoint,
			Region:     cfg.S3Region,
			AccessKey:  cfg.S3AccessKey,
			SecretKey:  cfg.S3SecretKey,
			Bucket:     cfg.UploadBucket,
			CDNBaseURL: "",
		})
		if err != nil {
			log.Fatalf("init upload S3 store: %v", err)
		}
		deliveryS3, err := storage.NewS3Store(storage.S3Config{
			Endpoint:   cfg.S3Endpoint,
			Region:     cfg.S3Region,
			AccessKey:  cfg.S3AccessKey,
			SecretKey:  cfg.S3SecretKey,
			Bucket:     cfg.DeliveryBucket,
			CDNBaseURL: cfg.CDNBaseURL,
		})
		if err != nil {
			log.Fatalf("init delivery S3 store: %v", err)
		}
		uploadStore = uploadS3
		deliveryStore = deliveryS3
	}

	// ── Webhook client ───────────────────────────────────────────────────────
	var webhookClient *webhook.Client
	if cfg.DjangoWebhookURL != "" {
		webhookClient = webhook.NewClient(cfg.DjangoWebhookURL, cfg.DjangoAPIKey)
	}

	// ── Stream session registry + archiver ──────────────────────────────────
	streamRegistry := stream.NewRegistry()
	streamArchiver := stream.NewArchiver(deliveryStore, cfg.FFmpegPath, cfg.TempDir, webhookClient)
	streamHandler := stream.NewHandler(streamRegistry, streamArchiver)

	// ── Upload registry ──────────────────────────────────────────────────────
	registry := upload.NewRegistry()
	uploadHandler := upload.NewHandler(registry, uploadStore, cfg.TempDir)

	// ── Transcode queue + worker pool ────────────────────────────────────────
	queue := transcode.NewQueue(100)
	pool := transcode.NewWorkerPool(
		cfg.WorkerCount,
		queue,
		uploadStore,
		deliveryStore,
		cfg.FFmpegPath,
		cfg.TempDir,
		webhookClient,
	)
	pool.Start()
	log.Printf("[mediad] started %d transcode workers", cfg.WorkerCount)

	transcodeHandler := transcode.NewHandler(queue)

	// ── HTTP routes ──────────────────────────────────────────────────────────
	mux := http.NewServeMux()

	mux.HandleFunc("/health", health.Handler)
	mux.HandleFunc("/engine/status", transcode.EngineStatusHandler(queue, cfg.WorkerCount))

	// Upload routes — wrapped in withCORS since these are called directly
	// from the browser (see withCORS's doc comment for why the other
	// /engine/ routes below are not).
	mux.HandleFunc("/engine/upload/init", withCORS(cfg.CORSAllowedOrigin, func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
			return
		}
		uploadHandler.InitUpload(w, r)
	}))
	mux.HandleFunc("/engine/upload/", withCORS(cfg.CORSAllowedOrigin, func(w http.ResponseWriter, r *http.Request) {
		switch r.Method {
		case http.MethodPut:
			uploadHandler.ReceiveChunk(w, r)
		case http.MethodPost:
			uploadHandler.CompleteUpload(w, r)
		default:
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		}
	}))

	// Stream routes
	mux.HandleFunc("/engine/stream/start", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
			return
		}
		streamHandler.Start(w, r)
	})
	mux.HandleFunc("/engine/stream/end", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
			return
		}
		streamHandler.End(w, r)
	})
	mux.HandleFunc("/engine/stream/active", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodGet {
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
			return
		}
		streamHandler.Active(w, r)
	})

	// Transcode routes
	mux.HandleFunc("/engine/transcode", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
			return
		}
		transcodeHandler.StartTranscode(w, r)
	})
	mux.HandleFunc("/engine/transcode/", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodGet {
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
			return
		}
		transcodeHandler.JobStatus(w, r)
	})

	// ── Server ───────────────────────────────────────────────────────────────
	srv := &http.Server{
		Addr:    ":" + cfg.Port,
		Handler: mux,
	}

	go func() {
		log.Printf("[mediad] listening on :%s", cfg.Port)
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("server error: %v", err)
		}
	}()

	// Graceful shutdown — drain in-flight transcodes up to 10 minutes.
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGTERM, syscall.SIGINT)
	<-quit

	log.Println("[mediad] shutting down — waiting for in-flight transcodes (max 10 min)...")
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Minute)
	defer cancel()
	if err := srv.Shutdown(ctx); err != nil {
		log.Printf("[mediad] shutdown error: %v", err)
	}
	log.Println("[mediad] stopped")
}
