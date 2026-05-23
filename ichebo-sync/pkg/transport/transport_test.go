// Tests for the transport package — verifies Post, Get, IsOnline, error types,
// and retry logic using httptest.NewServer.
package transport_test

import (
	"context"
	"errors"
	"net/http"
	"net/http/httptest"
	"sync/atomic"
	"testing"
	"time"

	"github.com/ichebo/sync/pkg/transport"
)

// ── Helpers ───────────────────────────────────────────────────────────────────

func newClient(baseURL string) transport.Client {
	return transport.New(transport.Config{
		BaseURL:    baseURL,
		AuthToken:  "test-token",
		DeviceID:   "test-device",
		Timeout:    5 * time.Second,
		MaxRetries: 0, // no retries by default — keeps tests fast
	})
}

func newClientWithRetries(baseURL string, retries int) transport.Client {
	return transport.New(transport.Config{
		BaseURL:    baseURL,
		AuthToken:  "test-token",
		DeviceID:   "test-device",
		Timeout:    5 * time.Second,
		MaxRetries: retries,
	})
}

// ── Post ──────────────────────────────────────────────────────────────────────

func TestPost_Success(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			t.Errorf("Method = %q, want POST", r.Method)
		}
		if r.Header.Get("Authorization") != "Token test-token" {
			t.Errorf("Authorization header missing or wrong")
		}
		if r.Header.Get("X-Device-ID") != "test-device" {
			t.Errorf("X-Device-ID header missing")
		}
		w.WriteHeader(http.StatusOK)
		w.Write([]byte(`{"ok":true}`))
	}))
	defer srv.Close()

	c := newClient(srv.URL)
	body, err := c.Post(context.Background(), "/api/sync/push/", map[string]string{"key": "value"})
	if err != nil {
		t.Fatalf("Post: %v", err)
	}
	if string(body) != `{"ok":true}` {
		t.Errorf("body = %q, want {\"ok\":true}", body)
	}
}

func TestPost_AuthError_401(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusUnauthorized)
		w.Write([]byte("Unauthorized"))
	}))
	defer srv.Close()

	c := newClient(srv.URL)
	_, err := c.Post(context.Background(), "/api/sync/push/", nil)
	if err == nil {
		t.Fatal("Post 401: expected error, got nil")
	}
	var authErr *transport.AuthError
	if !errors.As(err, &authErr) {
		t.Errorf("error type = %T, want *transport.AuthError", err)
	}
	if authErr.StatusCode != 401 {
		t.Errorf("StatusCode = %d, want 401", authErr.StatusCode)
	}
}

func TestPost_AuthError_403(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusForbidden)
		w.Write([]byte("Forbidden"))
	}))
	defer srv.Close()

	c := newClient(srv.URL)
	_, err := c.Post(context.Background(), "/api/sync/push/", nil)
	var authErr *transport.AuthError
	if !errors.As(err, &authErr) {
		t.Fatalf("error type = %T, want *transport.AuthError", err)
	}
	if authErr.StatusCode != 403 {
		t.Errorf("StatusCode = %d, want 403", authErr.StatusCode)
	}
}

func TestPost_ServerError_500(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusInternalServerError)
		w.Write([]byte("Internal Server Error"))
	}))
	defer srv.Close()

	// MaxRetries=0 so we get the error immediately without waiting on backoff
	c := newClient(srv.URL)
	_, err := c.Post(context.Background(), "/api/sync/push/", nil)
	if err == nil {
		t.Fatal("Post 500: expected error, got nil")
	}
	var srvErr *transport.ServerError
	if !errors.As(err, &srvErr) {
		t.Errorf("error type = %T, want *transport.ServerError", err)
	}
	if srvErr.StatusCode != 500 {
		t.Errorf("StatusCode = %d, want 500", srvErr.StatusCode)
	}
}

func TestPost_ClientError_400(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusBadRequest)
		w.Write([]byte("Bad Request"))
	}))
	defer srv.Close()

	c := newClient(srv.URL)
	_, err := c.Post(context.Background(), "/api/sync/push/", nil)
	if err == nil {
		t.Fatal("Post 400: expected error, got nil")
	}
	// Should not be AuthError or ServerError — just a plain error
	var authErr *transport.AuthError
	var srvErr *transport.ServerError
	if errors.As(err, &authErr) || errors.As(err, &srvErr) {
		t.Errorf("4xx (non-401/403) should not be AuthError or ServerError")
	}
}

func TestPost_NetworkError_UnreachableHost(t *testing.T) {
	// Use a port that nothing listens on
	c := transport.New(transport.Config{
		BaseURL:    "http://127.0.0.1:1",
		AuthToken:  "test-token",
		DeviceID:   "test-device",
		Timeout:    500 * time.Millisecond,
		MaxRetries: 0,
	})
	_, err := c.Post(context.Background(), "/api/sync/push/", nil)
	if err == nil {
		t.Fatal("Post to unreachable host: expected error, got nil")
	}
	var netErr *transport.NetworkError
	if !errors.As(err, &netErr) {
		t.Errorf("error type = %T, want *transport.NetworkError", err)
	}
}

// ── Get ───────────────────────────────────────────────────────────────────────

func TestGet_Success(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodGet {
			t.Errorf("Method = %q, want GET", r.Method)
		}
		if r.URL.Query().Get("since") != "12345_0" {
			t.Errorf("since param = %q, want 12345_0", r.URL.Query().Get("since"))
		}
		w.WriteHeader(http.StatusOK)
		w.Write([]byte(`{"records":[]}`))
	}))
	defer srv.Close()

	c := newClient(srv.URL)
	body, err := c.Get(context.Background(), "/api/sync/pull/", map[string]string{
		"since": "12345_0",
	})
	if err != nil {
		t.Fatalf("Get: %v", err)
	}
	if string(body) != `{"records":[]}` {
		t.Errorf("body = %q", body)
	}
}

func TestGet_QueryParamsEncoded(t *testing.T) {
	var gotQuery string
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		gotQuery = r.URL.RawQuery
		w.WriteHeader(http.StatusOK)
		w.Write([]byte(`{}`))
	}))
	defer srv.Close()

	c := newClient(srv.URL)
	_, err := c.Get(context.Background(), "/api/sync/pull/", map[string]string{
		"device_id": "abc-123",
		"tenant_id": "def-456",
	})
	if err != nil {
		t.Fatalf("Get: %v", err)
	}
	if gotQuery == "" {
		t.Error("expected query params in URL, got empty")
	}
}

// ── IsOnline ──────────────────────────────────────────────────────────────────

func TestIsOnline_True(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodHead {
			t.Errorf("IsOnline method = %q, want HEAD", r.Method)
		}
		w.WriteHeader(http.StatusOK)
	}))
	defer srv.Close()

	c := newClient(srv.URL)
	if !c.IsOnline(context.Background()) {
		t.Error("IsOnline = false, want true")
	}
}

func TestIsOnline_False_ServerDown(t *testing.T) {
	c := transport.New(transport.Config{
		BaseURL:    "http://127.0.0.1:1",
		AuthToken:  "token",
		DeviceID:   "dev",
		Timeout:    500 * time.Millisecond,
		MaxRetries: 0,
	})
	if c.IsOnline(context.Background()) {
		t.Error("IsOnline = true for unreachable server, want false")
	}
}

func TestIsOnline_False_500(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusInternalServerError)
	}))
	defer srv.Close()

	c := newClient(srv.URL)
	if c.IsOnline(context.Background()) {
		t.Error("IsOnline = true for 500 response, want false")
	}
}

// IsOnline result is cached — second call within TTL doesn't hit the server.
func TestIsOnline_Cached(t *testing.T) {
	var hitCount int32
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		atomic.AddInt32(&hitCount, 1)
		w.WriteHeader(http.StatusOK)
	}))
	defer srv.Close()

	c := newClient(srv.URL)
	c.IsOnline(context.Background())
	c.IsOnline(context.Background())

	if atomic.LoadInt32(&hitCount) != 1 {
		t.Errorf("server hit count = %d, want 1 (cached)", hitCount)
	}
}

// ── Retry logic ───────────────────────────────────────────────────────────────

// 5xx triggers retry; if server eventually returns 200, Post succeeds.
func TestPost_Retries_EventualSuccess(t *testing.T) {
	var attempts int32
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		n := atomic.AddInt32(&attempts, 1)
		if n < 3 {
			w.WriteHeader(http.StatusServiceUnavailable) // 503 → retry
			return
		}
		w.WriteHeader(http.StatusOK)
		w.Write([]byte(`{"ok":true}`))
	}))
	defer srv.Close()

	c := newClientWithRetries(srv.URL, 3)
	body, err := c.Post(context.Background(), "/api/sync/push/", nil)
	if err != nil {
		t.Fatalf("Post with retries: %v", err)
	}
	if string(body) != `{"ok":true}` {
		t.Errorf("body = %q, want ok", body)
	}
	if atomic.LoadInt32(&attempts) != 3 {
		t.Errorf("attempts = %d, want 3", attempts)
	}
}

// Context cancellation during retry surfaces as NetworkError.
func TestPost_ContextCancelled(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusServiceUnavailable)
	}))
	defer srv.Close()

	ctx, cancel := context.WithCancel(context.Background())
	cancel() // pre-cancel

	c := newClientWithRetries(srv.URL, 3)
	_, err := c.Post(ctx, "/api/sync/push/", nil)
	if err == nil {
		t.Fatal("expected error on cancelled context, got nil")
	}
}

// ── Error type assertions ─────────────────────────────────────────────────────

func TestAuthError_ErrorString(t *testing.T) {
	err := &transport.AuthError{StatusCode: 401, Message: "bad token"}
	if err.Error() == "" {
		t.Error("AuthError.Error() is empty")
	}
}

func TestNetworkError_ErrorString_And_Unwrap(t *testing.T) {
	inner := errors.New("connection refused")
	err := &transport.NetworkError{Cause: inner}
	if err.Error() == "" {
		t.Error("NetworkError.Error() is empty")
	}
	if errors.Unwrap(err) != inner {
		t.Error("NetworkError.Unwrap() did not return inner error")
	}
}

func TestServerError_ErrorString(t *testing.T) {
	err := &transport.ServerError{StatusCode: 503, Message: "service unavailable"}
	if err.Error() == "" {
		t.Error("ServerError.Error() is empty")
	}
}
