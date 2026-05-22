package storage

import (
	"context"
	"fmt"
	"io"
	"net/http"
	"time"

	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/credentials"
	"github.com/aws/aws-sdk-go-v2/service/s3"
	"github.com/aws/aws-sdk-go-v2/service/s3/types"
)

// S3Store implements both UploadStore and DeliveryStore against an S3-compatible
// endpoint (Hetzner Object Storage in production). A single S3Store instance can
// be used for both buckets — use separate instances with different bucket names
// for the upload bucket and the delivery bucket.
type S3Store struct {
	client     *s3.Client
	bucket     string
	cdnBaseURL string // empty → use standard S3 public URL pattern
}

// NewS3Store constructs an S3Store from an S3Config.
// The upload and delivery stores are created as separate instances pointing to
// their respective buckets, but both share the same credentials and endpoint.
//
// Hetzner Object Storage is S3-compatible with endpoint:
//
//	https://{region}.your-objectstorage.com
//
// Set UsePathStyle=true — Hetzner Object Storage requires path-style addressing.
func NewS3Store(cfg S3Config) (*S3Store, error) {
	if cfg.Endpoint == "" {
		return nil, fmt.Errorf("storage.NewS3Store: endpoint is required")
	}
	if cfg.AccessKey == "" || cfg.SecretKey == "" {
		return nil, fmt.Errorf("storage.NewS3Store: access key and secret key are required")
	}

	creds := credentials.NewStaticCredentialsProvider(cfg.AccessKey, cfg.SecretKey, "")

	client := s3.New(s3.Options{
		BaseEndpoint:       aws.String(cfg.Endpoint),
		Region:             cfg.Region,
		Credentials:        creds,
		UsePathStyle:       true, // required for Hetzner Object Storage
		EndpointResolverV2: nil,  // use BaseEndpoint
	})

	return &S3Store{
		client:     client,
		bucket:     cfg.Bucket,
		cdnBaseURL: cfg.CDNBaseURL,
	}, nil
}

// PutObject uploads body to the bucket at key.
// size is used for the Content-Length header — pass -1 if unknown (chunked encoding).
// cacheControl sets the Cache-Control header on the object (e.g. "public, max-age=3600").
// Pass an empty string to omit it.
func (s *S3Store) PutObject(ctx context.Context, key string, body io.Reader, size int64, cacheControl ...string) error {
	input := &s3.PutObjectInput{
		Bucket: aws.String(s.bucket),
		Key:    aws.String(key),
		Body:   body,
	}
	if size >= 0 {
		input.ContentLength = aws.Int64(size)
	}
	if len(cacheControl) > 0 && cacheControl[0] != "" {
		input.CacheControl = aws.String(cacheControl[0])
	}

	// Set ACL to public-read for delivery bucket objects so HLS segments
	// are accessible without authentication. For the upload bucket (raw files),
	// this is a no-op — the bucket policy restricts access anyway.
	input.ACL = types.ObjectCannedACLPublicRead

	_, err := s.client.PutObject(ctx, input)
	if err != nil {
		return fmt.Errorf("s3.PutObject %s/%s: %w", s.bucket, key, err)
	}
	return nil
}

// DeleteObject removes an object from the bucket.
func (s *S3Store) DeleteObject(ctx context.Context, key string) error {
	_, err := s.client.DeleteObject(ctx, &s3.DeleteObjectInput{
		Bucket: aws.String(s.bucket),
		Key:    aws.String(key),
	})
	if err != nil {
		return fmt.Errorf("s3.DeleteObject %s/%s: %w", s.bucket, key, err)
	}
	return nil
}

// GetPresignedURL generates a time-limited pre-signed GET URL for a private object.
// Used by the transcode worker to download raw uploads from the upload bucket.
func (s *S3Store) GetPresignedURL(ctx context.Context, key string, expiry time.Duration) (string, error) {
	presigner := s3.NewPresignClient(s.client)
	req, err := presigner.PresignGetObject(ctx, &s3.GetObjectInput{
		Bucket: aws.String(s.bucket),
		Key:    aws.String(key),
	}, s3.WithPresignExpires(expiry))
	if err != nil {
		return "", fmt.Errorf("s3.PresignGetObject %s/%s: %w", s.bucket, key, err)
	}
	return req.URL, nil
}

// GetPublicURL returns the public URL for a delivered object.
// If a CDN base URL is configured, uses that. Otherwise constructs the
// standard Hetzner Object Storage public URL.
func (s *S3Store) GetPublicURL(key string) string {
	if s.cdnBaseURL != "" {
		return s.cdnBaseURL + "/" + key
	}
	// Standard Hetzner Object Storage public URL pattern:
	// https://{bucket}.{region}.your-objectstorage.com/{key}
	return fmt.Sprintf("https://%s/%s", s.bucket, key)
}

// DownloadToWriter fetches an object from S3 and streams it into w.
// Used by the transcode worker when downloading raw uploads in S3 mode.
func (s *S3Store) DownloadToWriter(ctx context.Context, key string, w io.Writer) error {
	out, err := s.client.GetObject(ctx, &s3.GetObjectInput{
		Bucket: aws.String(s.bucket),
		Key:    aws.String(key),
	})
	if err != nil {
		return fmt.Errorf("s3.GetObject %s/%s: %w", s.bucket, key, err)
	}
	defer out.Body.Close()
	if _, err := io.Copy(w, out.Body); err != nil {
		return fmt.Errorf("s3.GetObject read body %s/%s: %w", s.bucket, key, err)
	}
	return nil
}

// HTTPDownload fetches a URL (presigned or public) and streams it into w.
// Used by the worker's downloadFromStore for the HTTP-presigned-URL path.
func HTTPDownload(url string, w io.Writer) error {
	resp, err := http.Get(url) //nolint:noctx
	if err != nil {
		return fmt.Errorf("http.Get %s: %w", url, err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("http.Get %s: status %d", url, resp.StatusCode)
	}
	_, err = io.Copy(w, resp.Body)
	return err
}
