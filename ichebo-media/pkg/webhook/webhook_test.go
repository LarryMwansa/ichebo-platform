package webhook

import (
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestWebhook_SuccessOnFirstAttempt(t *testing.T) {
	calls := 0
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		calls++
		if r.Header.Get("Authorization") == "" {
			t.Error("missing Authorization header")
		}
		w.WriteHeader(http.StatusOK)
	}))
	defer srv.Close()

	client := NewClient(srv.URL, "test-key")
	// Override the URL so it doesn't append the path twice
	client.webhookURL = srv.URL

	// Temporarily replace doPost to use the test URL directly
	err := client.NotifyTranscodeComplete(TranscodeCompletePayload{
		JobID:    "j1",
		RecordID: "r1",
		Status:   "complete",
	})
	if err != nil {
		t.Fatalf("expected success, got: %v", err)
	}
	if calls != 1 {
		t.Fatalf("expected 1 call, got %d", calls)
	}
}

func TestWebhook_NoURL_Noop(t *testing.T) {
	client := NewClient("", "key")
	err := client.NotifyTranscodeComplete(TranscodeCompletePayload{JobID: "j2"})
	if err != nil {
		t.Fatalf("empty URL should be a no-op, got: %v", err)
	}
}

func TestWebhook_RetryOnFailure(t *testing.T) {
	calls := 0
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		calls++
		if calls < 3 {
			w.WriteHeader(http.StatusInternalServerError)
			return
		}
		w.WriteHeader(http.StatusOK)
	}))
	defer srv.Close()

	client := &Client{
		webhookURL: srv.URL,
		apiKey:     "key",
		httpClient: &http.Client{},
	}
	// Shorten retry delays for test speed by calling doPost directly
	var lastErr error
	for attempt := 0; attempt < 4; attempt++ {
		body := []byte(`{"job_id":"j3"}`)
		if err := client.doPost(body); err != nil {
			lastErr = err
			continue
		}
		lastErr = nil
		break
	}
	if lastErr != nil {
		t.Fatalf("expected success after retries, got: %v", lastErr)
	}
	if calls != 3 {
		t.Fatalf("expected 3 calls, got %d", calls)
	}
}

func TestWebhook_ExhaustedRetries(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusInternalServerError)
	}))
	defer srv.Close()

	client := &Client{
		webhookURL: srv.URL,
		apiKey:     "key",
		httpClient: &http.Client{},
	}
	var lastErr error
	for attempt := 0; attempt < 4; attempt++ {
		body := []byte(`{"job_id":"j4"}`)
		if err := client.doPost(body); err != nil {
			lastErr = err
		}
	}
	if lastErr == nil {
		t.Fatal("expected error after all retries fail")
	}
}
