package upload

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strconv"
	"strings"

	"github.com/google/uuid"

	"github.com/ichebo/media/pkg/storage"
)

type Handler struct {
	registry    *Registry
	uploadStore storage.UploadStore
	tempDir     string
}

func NewHandler(registry *Registry, uploadStore storage.UploadStore, tempDir string) *Handler {
	return &Handler{registry: registry, uploadStore: uploadStore, tempDir: tempDir}
}

// InitRequest is the body for POST /engine/upload/init.
type InitRequest struct {
	Filename        string `json:"filename"`
	FileSizeBytes   int64  `json:"file_size_bytes"`
	ContentType     string `json:"content_type"`
	TenantID        string `json:"tenant_id"`
	RecordID        string `json:"record_id"`
	ChunkSizeBytes  int64  `json:"chunk_size_bytes"`
}

type InitResponse struct {
	UploadID       string `json:"upload_id"`
	TotalChunks    int    `json:"total_chunks"`
	ChunkSizeBytes int64  `json:"chunk_size_bytes"`
}

func (h *Handler) InitUpload(w http.ResponseWriter, r *http.Request) {
	var req InitRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "invalid request body", http.StatusBadRequest)
		return
	}
	if req.Filename == "" || req.FileSizeBytes <= 0 || req.RecordID == "" {
		http.Error(w, "filename, file_size_bytes, and record_id are required", http.StatusBadRequest)
		return
	}

	uploadID := uuid.New().String()
	session := h.registry.Create(uploadID, req.RecordID, req.TenantID, req.Filename, req.FileSizeBytes, req.ChunkSizeBytes)
	session.TempDir = filepath.Join(h.tempDir, uploadID)
	if err := os.MkdirAll(session.TempDir, 0755); err != nil {
		http.Error(w, "could not create temp dir", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(InitResponse{
		UploadID:       uploadID,
		TotalChunks:    session.TotalChunks,
		ChunkSizeBytes: session.ChunkSize,
	})
}

type ChunkResponse struct {
	Received bool   `json:"received"`
	Checksum string `json:"checksum"`
}

func (h *Handler) ReceiveChunk(w http.ResponseWriter, r *http.Request) {
	// URL: PUT /engine/upload/{upload_id}/chunk/{n}
	parts := strings.Split(strings.TrimPrefix(r.URL.Path, "/engine/upload/"), "/")
	if len(parts) < 3 || parts[1] != "chunk" {
		http.Error(w, "invalid URL", http.StatusBadRequest)
		return
	}
	uploadID := parts[0]
	n, err := strconv.Atoi(parts[2])
	if err != nil {
		http.Error(w, "invalid chunk number", http.StatusBadRequest)
		return
	}

	session, err := h.registry.Get(uploadID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusNotFound)
		return
	}
	if n < 0 || n >= session.TotalChunks {
		http.Error(w, "chunk number out of range", http.StatusBadRequest)
		return
	}

	// Idempotent: if already received, return existing checksum.
	if existing, ok := session.ChecksumFor(n); ok {
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(ChunkResponse{Received: true, Checksum: existing})
		return
	}

	data, err := io.ReadAll(r.Body)
	if err != nil {
		http.Error(w, "failed to read chunk", http.StatusInternalServerError)
		return
	}

	sum := sha256.Sum256(data)
	checksum := "sha256:" + hex.EncodeToString(sum[:])

	chunkPath := filepath.Join(session.TempDir, fmt.Sprintf("chunk_%06d", n))
	if err := os.WriteFile(chunkPath, data, 0644); err != nil {
		http.Error(w, "failed to write chunk", http.StatusInternalServerError)
		return
	}

	session.MarkReceived(n, checksum)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(ChunkResponse{Received: true, Checksum: checksum})
}

type CompleteRequest struct {
	ChunkChecksums []struct {
		N        int    `json:"n"`
		Checksum string `json:"checksum"`
	} `json:"chunk_checksums"`
}

type CompleteResponse struct {
	RawObjectKey string `json:"raw_object_key"`
}

func (h *Handler) CompleteUpload(w http.ResponseWriter, r *http.Request) {
	// URL: POST /engine/upload/{upload_id}/complete
	parts := strings.Split(strings.TrimPrefix(r.URL.Path, "/engine/upload/"), "/")
	if len(parts) < 2 || parts[1] != "complete" {
		http.Error(w, "invalid URL", http.StatusBadRequest)
		return
	}
	uploadID := parts[0]

	session, err := h.registry.Get(uploadID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusNotFound)
		return
	}

	var req CompleteRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "invalid request body", http.StatusBadRequest)
		return
	}

	// Validate all checksums match.
	for _, c := range req.ChunkChecksums {
		stored, ok := session.ChecksumFor(c.N)
		if !ok {
			http.Error(w, fmt.Sprintf("chunk %d not received", c.N), http.StatusBadRequest)
			return
		}
		if stored != c.Checksum {
			http.Error(w, fmt.Sprintf("chunk %d checksum mismatch: got %s want %s", c.N, c.Checksum, stored), http.StatusBadRequest)
			return
		}
	}
	if !session.IsComplete() {
		http.Error(w, "not all chunks received", http.StatusBadRequest)
		return
	}

	// Assemble chunks in order.
	ext := filepath.Ext(session.Filename)
	if ext == "" {
		ext = ".mp4"
	}
	assembledPath := filepath.Join(session.TempDir, "assembled"+ext)
	if err := assembleChunks(session, assembledPath); err != nil {
		http.Error(w, "assembly failed: "+err.Error(), http.StatusInternalServerError)
		return
	}

	// Upload to object store.
	objectKey := fmt.Sprintf("uploads/%s/original%s", session.RecordID, ext)
	f, err := os.Open(assembledPath)
	if err != nil {
		http.Error(w, "could not open assembled file", http.StatusInternalServerError)
		return
	}
	defer f.Close()

	fi, _ := f.Stat()
	if err := h.uploadStore.PutObject(context.Background(), objectKey, f, fi.Size()); err != nil {
		http.Error(w, "upload to store failed: "+err.Error(), http.StatusInternalServerError)
		return
	}

	// Clean up.
	os.RemoveAll(session.TempDir)
	h.registry.Delete(uploadID)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(CompleteResponse{RawObjectKey: objectKey})
}

func assembleChunks(session *Session, dest string) error {
	out, err := os.Create(dest)
	if err != nil {
		return err
	}
	defer out.Close()

	for i := 0; i < session.TotalChunks; i++ {
		chunkPath := filepath.Join(session.TempDir, fmt.Sprintf("chunk_%06d", i))
		data, err := os.ReadFile(chunkPath)
		if err != nil {
			return fmt.Errorf("read chunk %d: %w", i, err)
		}
		if _, err := out.Write(data); err != nil {
			return fmt.Errorf("write chunk %d: %w", i, err)
		}
	}
	return nil
}
