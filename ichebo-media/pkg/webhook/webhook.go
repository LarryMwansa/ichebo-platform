package webhook

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"time"
)

// TranscodeCompletePayload is sent to Django when a transcode job finishes.
type TranscodeCompletePayload struct {
	JobID           string          `json:"job_id"`
	RecordID        string          `json:"record_id"`
	Status          string          `json:"status"`
	VideoURL        string          `json:"video_url"`
	ThumbnailURL    string          `json:"thumbnail_url"`
	DurationSeconds int             `json:"duration_seconds"`
	QualityVariants []QualityVariant `json:"quality_variants"`
	FileSizeBytes   int64           `json:"file_size_bytes"`
}

// QualityVariant describes one quality level in the transcode result.
type QualityVariant struct {
	Name string `json:"name"`
	URL  string `json:"url"`
}

// Client sends webhook notifications to the Django backend.
type Client struct {
	webhookURL string
	apiKey     string
	httpClient *http.Client
}

func NewClient(webhookURL, apiKey string) *Client {
	return &Client{
		webhookURL: webhookURL,
		apiKey:     apiKey,
		httpClient: &http.Client{Timeout: 15 * time.Second},
	}
}

// NotifyTranscodeComplete POSTs the transcode result to Django with retry/backoff.
func (c *Client) NotifyTranscodeComplete(payload TranscodeCompletePayload) error {
	if c.webhookURL == "" {
		return nil // local dev — no Django to notify
	}

	body, err := json.Marshal(payload)
	if err != nil {
		return fmt.Errorf("webhook: marshal payload: %w", err)
	}

	delays := []time.Duration{2 * time.Second, 4 * time.Second, 8 * time.Second}
	var lastErr error
	for attempt := 0; attempt <= len(delays); attempt++ {
		if attempt > 0 {
			time.Sleep(delays[attempt-1])
		}
		if err := c.doPost(body); err != nil {
			lastErr = err
			continue
		}
		return nil
	}
	return fmt.Errorf("webhook: all retries exhausted: %w", lastErr)
}

func (c *Client) doPost(body []byte) error {
	req, err := http.NewRequest(http.MethodPost, c.webhookURL+"/api/media/transcode-complete/", bytes.NewReader(body))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+c.apiKey)

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode >= 300 {
		return fmt.Errorf("webhook: unexpected status %d", resp.StatusCode)
	}
	return nil
}
