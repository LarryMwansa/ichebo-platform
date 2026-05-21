package storage

import (
	"context"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"time"
)

// UploadStore handles raw upload bucket operations.
type UploadStore interface {
	PutObject(ctx context.Context, key string, body io.Reader, size int64) error
	DeleteObject(ctx context.Context, key string) error
	GetPresignedURL(ctx context.Context, key string, expiry time.Duration) (string, error)
}

// DeliveryStore handles CDN-backed delivery bucket operations.
type DeliveryStore interface {
	PutObject(ctx context.Context, key string, body io.Reader, size int64) error
	GetPublicURL(key string) string
}

// LocalStore writes objects to disk. Used in local dev when no S3 credentials are set.
type LocalStore struct {
	baseDir    string
	cdnBaseURL string
}

func NewLocalStore(baseDir string) (*LocalStore, error) {
	if err := os.MkdirAll(baseDir, 0755); err != nil {
		return nil, fmt.Errorf("storage: create local dir %s: %w", baseDir, err)
	}
	return &LocalStore{baseDir: baseDir, cdnBaseURL: "file://" + baseDir}, nil
}

func (l *LocalStore) PutObject(_ context.Context, key string, body io.Reader, _ int64) error {
	dest := filepath.Join(l.baseDir, key)
	if err := os.MkdirAll(filepath.Dir(dest), 0755); err != nil {
		return err
	}
	f, err := os.Create(dest)
	if err != nil {
		return err
	}
	defer f.Close()
	_, err = io.Copy(f, body)
	return err
}

func (l *LocalStore) DeleteObject(_ context.Context, key string) error {
	return os.Remove(filepath.Join(l.baseDir, key))
}

func (l *LocalStore) GetPresignedURL(_ context.Context, key string, _ time.Duration) (string, error) {
	return "file://" + filepath.Join(l.baseDir, key), nil
}

func (l *LocalStore) GetPublicURL(key string) string {
	return "file://" + filepath.Join(l.baseDir, key)
}

// S3Config holds credentials for production S3/Hetzner storage.
// The actual S3 client is constructed by NewS3Store in s3.go (requires aws-sdk-go-v2).
type S3Config struct {
	Endpoint    string
	Region      string
	AccessKey   string
	SecretKey   string
	Bucket      string
	CDNBaseURL  string
}
