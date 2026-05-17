// Package transport provides the HTTP client for the Ichebo Cloud DRF API.
// Handles authentication, retries, timeouts, and connectivity detection.
package transport

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"time"
)

// Client is the interface for communicating with the Ichebo Cloud API.
type Client interface {
	// Post sends a JSON payload with auth, timeout (30s), retry (3x exponential backoff).
	Post(ctx context.Context, path string, body any) ([]byte, error)

	// Get sends a GET request with query parameters.
	Get(ctx context.Context, path string, params map[string]string) ([]byte, error)

	// IsOnline checks connectivity via HEAD /api/health/. Cached 10 seconds.
	IsOnline(ctx context.Context) bool
}

// Config holds the transport configuration.
type Config struct {
	BaseURL    string        // e.g. "https://app.ichebo.org"
	AuthToken  string        // DRF token for this device's user account
	DeviceID   string        // sent as X-Device-ID header on every request
	Timeout    time.Duration // default 30s
	MaxRetries int           // default 3
}

// AuthError is returned on 401 or 403 — triggers Blocked state.
type AuthError struct {
	StatusCode int
	Message    string
}

func (e *AuthError) Error() string {
	return fmt.Sprintf("auth error %d: %s", e.StatusCode, e.Message)
}

// NetworkError is returned when the server is unreachable — triggers Offline state.
type NetworkError struct{ Cause error }

func (e *NetworkError) Error() string { return fmt.Sprintf("network error: %v", e.Cause) }
func (e *NetworkError) Unwrap() error { return e.Cause }

// ServerError is returned on 5xx responses — triggers retry with backoff.
type ServerError struct {
	StatusCode int
	Message    string
}

func (e *ServerError) Error() string {
	return fmt.Sprintf("server error %d: %s", e.StatusCode, e.Message)
}

// New creates a Client with the given config.
func New(cfg Config) Client {
	if cfg.Timeout == 0 {
		cfg.Timeout = 30 * time.Second
	}
	if cfg.MaxRetries == 0 {
		cfg.MaxRetries = 3
	}
	return &httpClient{
		cfg:    cfg,
		http:   &http.Client{Timeout: cfg.Timeout},
		onlineCache: onlineCache{ttl: 10 * time.Second},
	}
}

type httpClient struct {
	cfg         Config
	http        *http.Client
	onlineCache onlineCache
}

type onlineCache struct {
	ttl     time.Duration
	last    bool
	checkedAt time.Time
}

func (c *httpClient) Post(ctx context.Context, path string, body any) ([]byte, error) {
	data, err := json.Marshal(body)
	if err != nil {
		return nil, fmt.Errorf("transport.Post marshal: %w", err)
	}
	return c.doWithRetry(ctx, http.MethodPost, path, data)
}

func (c *httpClient) Get(ctx context.Context, path string, params map[string]string) ([]byte, error) {
	u, err := url.Parse(c.cfg.BaseURL + path)
	if err != nil {
		return nil, &NetworkError{Cause: err}
	}
	q := u.Query()
	for k, v := range params {
		q.Set(k, v)
	}
	u.RawQuery = q.Encode()
	return c.doWithRetry(ctx, http.MethodGet, u.String(), nil)
}

func (c *httpClient) IsOnline(ctx context.Context) bool {
	if time.Since(c.onlineCache.checkedAt) < c.onlineCache.ttl {
		return c.onlineCache.last
	}
	req, err := http.NewRequestWithContext(ctx, http.MethodHead, c.cfg.BaseURL+"/api/health/", nil)
	if err != nil {
		c.onlineCache.last = false
		c.onlineCache.checkedAt = time.Now()
		return false
	}
	resp, err := c.http.Do(req)
	online := err == nil && resp.StatusCode < 500
	if resp != nil {
		resp.Body.Close()
	}
	c.onlineCache.last = online
	c.onlineCache.checkedAt = time.Now()
	return online
}

func (c *httpClient) doWithRetry(ctx context.Context, method, path string, body []byte) ([]byte, error) {
	target := path
	if len(path) > 0 && path[0] == '/' {
		target = c.cfg.BaseURL + path
	}

	var lastErr error
	for attempt := 0; attempt <= c.cfg.MaxRetries; attempt++ {
		if attempt > 0 {
			wait := time.Duration(1<<uint(attempt-1)) * time.Second
			select {
			case <-time.After(wait):
			case <-ctx.Done():
				return nil, &NetworkError{Cause: ctx.Err()}
			}
		}

		var bodyReader io.Reader
		if body != nil {
			bodyReader = bytes.NewReader(body)
		}
		req, err := http.NewRequestWithContext(ctx, method, target, bodyReader)
		if err != nil {
			return nil, &NetworkError{Cause: err}
		}
		req.Header.Set("Authorization", "Token "+c.cfg.AuthToken)
		req.Header.Set("X-Device-ID", c.cfg.DeviceID)
		if body != nil {
			req.Header.Set("Content-Type", "application/json")
		}

		resp, err := c.http.Do(req)
		if err != nil {
			lastErr = &NetworkError{Cause: err}
			continue // retry
		}
		defer resp.Body.Close()

		respBody, _ := io.ReadAll(resp.Body)
		switch {
		case resp.StatusCode == 401 || resp.StatusCode == 403:
			return nil, &AuthError{StatusCode: resp.StatusCode, Message: string(respBody)}
		case resp.StatusCode >= 500:
			lastErr = &ServerError{StatusCode: resp.StatusCode, Message: string(respBody)}
			continue // retry
		case resp.StatusCode >= 400:
			return nil, fmt.Errorf("transport: HTTP %d: %s", resp.StatusCode, respBody)
		}
		return respBody, nil
	}
	return nil, lastErr
}
