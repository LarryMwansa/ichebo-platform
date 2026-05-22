package storage_test

import (
	"io"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"github.com/ichebo/media/pkg/storage"
)

// TestNewS3Store_MissingCredentials verifies constructor rejects empty credentials.
func TestNewS3Store_MissingCredentials(t *testing.T) {
	cases := []struct {
		name string
		cfg  storage.S3Config
	}{
		{"empty endpoint", storage.S3Config{AccessKey: "k", SecretKey: "s", Bucket: "b"}},
		{"empty access key", storage.S3Config{Endpoint: "https://s3.example.com", SecretKey: "s", Bucket: "b"}},
		{"empty secret key", storage.S3Config{Endpoint: "https://s3.example.com", AccessKey: "k", Bucket: "b"}},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			_, err := storage.NewS3Store(tc.cfg)
			if err == nil {
				t.Error("expected error for missing credentials, got nil")
			}
		})
	}
}

// TestS3Store_GetPublicURL_WithCDN verifies CDN base URL is prepended correctly.
func TestS3Store_GetPublicURL_WithCDN(t *testing.T) {
	store, err := storage.NewS3Store(storage.S3Config{
		Endpoint:   "https://s3.example.com",
		AccessKey:  "key",
		SecretKey:  "secret",
		Bucket:     "delivery",
		CDNBaseURL: "https://cdn.example.com",
	})
	if err != nil {
		t.Fatalf("NewS3Store: %v", err)
	}
	url := store.GetPublicURL("videos/abc/index.m3u8")
	want := "https://cdn.example.com/videos/abc/index.m3u8"
	if url != want {
		t.Errorf("got %q, want %q", url, want)
	}
}

// TestS3Store_GetPublicURL_NoCDN verifies fallback URL when no CDN is set.
func TestS3Store_GetPublicURL_NoCDN(t *testing.T) {
	store, err := storage.NewS3Store(storage.S3Config{
		Endpoint:  "https://s3.example.com",
		AccessKey: "key",
		SecretKey: "secret",
		Bucket:    "my-delivery-bucket",
	})
	if err != nil {
		t.Fatalf("NewS3Store: %v", err)
	}
	url := store.GetPublicURL("videos/abc/index.m3u8")
	if !strings.Contains(url, "videos/abc/index.m3u8") {
		t.Errorf("public URL should contain key path, got %q", url)
	}
}

// TestHTTPDownload uses a local test server — no real S3 required.
func TestHTTPDownload(t *testing.T) {
	body := "hello hetzner"
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		_, _ = io.WriteString(w, body)
	}))
	defer srv.Close()

	var buf strings.Builder
	if err := storage.HTTPDownload(srv.URL+"/test-object", &buf); err != nil {
		t.Fatalf("HTTPDownload: %v", err)
	}
	if buf.String() != body {
		t.Errorf("got %q, want %q", buf.String(), body)
	}
}

// TestHTTPDownload_NonOK verifies non-200 responses are returned as errors.
func TestHTTPDownload_NonOK(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusNotFound)
	}))
	defer srv.Close()

	if err := storage.HTTPDownload(srv.URL+"/missing", io.Discard); err == nil {
		t.Error("expected error for 404 response, got nil")
	}
}
