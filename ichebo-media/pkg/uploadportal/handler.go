package uploadportal

import (
	"bytes"
	"crypto/hmac"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"net/http"
	"strconv"
	"strings"
	"time"
)

// Config holds settings for the upload portal handler.
type Config struct {
	APIKey         string
	DjangoCallback string
}

// Handler serves GET /upload (the portal page).
type Handler struct {
	cfg Config
	hc  *http.Client
}

func NewHandler(cfg Config) *Handler {
	return &Handler{cfg: cfg, hc: &http.Client{Timeout: 20 * time.Second}}
}

// VerifyToken validates a token issued by Django UploadPortalTokenView.
func (h *Handler) VerifyToken(token string) (tenantID, userID string, err error) {
	parts := strings.SplitN(token, ":", 4)
	if len(parts) != 4 {
		return "", "", fmt.Errorf("malformed token")
	}
	tenantID, userID, expiresStr, sig := parts[0], parts[1], parts[2], parts[3]
	expires, err := strconv.ParseInt(expiresStr, 10, 64)
	if err != nil || time.Now().Unix() > expires {
		return "", "", fmt.Errorf("token expired")
	}
	payload := fmt.Sprintf("%s:%s:%s", tenantID, userID, expiresStr)
	mac := hmac.New(sha256.New, []byte(h.cfg.APIKey))
	mac.Write([]byte(payload))
	expected := hex.EncodeToString(mac.Sum(nil))
	if !hmac.Equal([]byte(sig), []byte(expected)) {
		return "", "", fmt.Errorf("invalid signature")
	}
	return tenantID, userID, nil
}

// ServeUploadPage handles GET /upload
func (h *Handler) ServeUploadPage(w http.ResponseWriter, r *http.Request) {
	token := r.URL.Query().Get("token")
	tenantID := r.URL.Query().Get("tenant_id")
	callback := r.URL.Query().Get("callback")

	if token == "" || tenantID == "" {
		http.Error(w, "token and tenant_id are required", http.StatusBadRequest)
		return
	}
	if _, _, err := h.VerifyToken(token); err != nil {
		http.Error(w, "Invalid or expired upload link. Return to the app and request a new one.", http.StatusForbidden)
		return
	}
	if callback == "" {
		callback = strings.TrimRight(h.cfg.DjangoCallback, "/") + "/api/media/upload-complete-webhook/"
	}
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	fmt.Fprint(w, buildPage(token, tenantID, callback))
}

// NotifyDjango fires the upload-complete-webhook to Django.
func (h *Handler) NotifyDjango(payload map[string]interface{}) error {
	if h.cfg.DjangoCallback == "" {
		return nil
	}
	body, _ := json.Marshal(payload)
	url := strings.TrimRight(h.cfg.DjangoCallback, "/") + "/api/media/upload-complete-webhook/"
	req, err := http.NewRequest(http.MethodPost, url, bytes.NewReader(body))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+h.cfg.APIKey)
	resp, err := h.hc.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 300 {
		return fmt.Errorf("django webhook returned %d", resp.StatusCode)
	}
	return nil
}
