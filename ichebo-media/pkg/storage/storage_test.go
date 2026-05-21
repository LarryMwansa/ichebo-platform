package storage

import (
	"bytes"
	"context"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

func TestLocalStore_PutGetDelete(t *testing.T) {
	dir := t.TempDir()
	store, err := NewLocalStore(dir)
	if err != nil {
		t.Fatal(err)
	}

	key := "uploads/test-record/original.mp4"
	data := []byte("fake video data")

	if err := store.PutObject(context.Background(), key, bytes.NewReader(data), int64(len(data))); err != nil {
		t.Fatalf("PutObject: %v", err)
	}

	dest := filepath.Join(dir, key)
	got, err := os.ReadFile(dest)
	if err != nil {
		t.Fatalf("read file: %v", err)
	}
	if string(got) != string(data) {
		t.Fatalf("data mismatch: got %q want %q", got, data)
	}

	if err := store.DeleteObject(context.Background(), key); err != nil {
		t.Fatalf("DeleteObject: %v", err)
	}
	if _, err := os.Stat(dest); !os.IsNotExist(err) {
		t.Fatal("file should have been deleted")
	}
}

func TestLocalStore_PresignedURL(t *testing.T) {
	store, _ := NewLocalStore(t.TempDir())
	url, err := store.GetPresignedURL(context.Background(), "some/key.mp4", time.Hour)
	if err != nil {
		t.Fatal(err)
	}
	if !strings.HasPrefix(url, "file://") {
		t.Fatalf("expected file:// URL, got %q", url)
	}
}

func TestLocalStore_PublicURL(t *testing.T) {
	store, _ := NewLocalStore("/tmp/test-store")
	url := store.GetPublicURL("videos/abc/index.m3u8")
	if !strings.Contains(url, "videos/abc/index.m3u8") {
		t.Fatalf("unexpected URL: %q", url)
	}
}
