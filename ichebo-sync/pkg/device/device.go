// Package device manages the stable identity of this installation.
// DeviceID is generated once on first run and never changes (DOC C §3.1).
package device

import (
	"context"
	"database/sql"
	"errors"
	"fmt"
	"time"

	"github.com/google/uuid"
	"github.com/ichebo/sync/pkg/transport"
)

// ErrNotInitialised is returned by Load when no device identity exists yet.
var ErrNotInitialised = errors.New("device: not initialised — run Init first")

// Identity is the stable fingerprint of this installation.
type Identity struct {
	DeviceID    uuid.UUID
	TenantID    uuid.UUID
	LicenceKey  string
	CreatedAt   time.Time
	ValidatedAt time.Time
}

// Load retrieves the identity from the SQLite settings table.
// Returns ErrNotInitialised if no identity has been written yet.
func Load(db *sql.DB) (*Identity, error) {
	var (
		deviceID, tenantID, licenceKey, createdAt, validatedAt string
	)
	err := db.QueryRow(`SELECT value FROM settings WHERE key = 'device_id'`).Scan(&deviceID)
	if err == sql.ErrNoRows {
		return nil, ErrNotInitialised
	}
	if err != nil {
		return nil, fmt.Errorf("device.Load device_id: %w", err)
	}

	for _, row := range []struct {
		key  string
		dest *string
	}{
		{"tenant_id", &tenantID},
		{"licence_key", &licenceKey},
		{"created_at", &createdAt},
		{"validated_at", &validatedAt},
	} {
		if err := db.QueryRow(`SELECT value FROM settings WHERE key = ?`, row.key).Scan(row.dest); err != nil {
			return nil, fmt.Errorf("device.Load %s: %w", row.key, err)
		}
	}

	did, err := uuid.Parse(deviceID)
	if err != nil {
		return nil, fmt.Errorf("device.Load: invalid device_id: %w", err)
	}
	tid, err := uuid.Parse(tenantID)
	if err != nil {
		return nil, fmt.Errorf("device.Load: invalid tenant_id: %w", err)
	}
	ca, _ := time.Parse(time.RFC3339Nano, createdAt)
	va, _ := time.Parse(time.RFC3339Nano, validatedAt)

	return &Identity{
		DeviceID:    did,
		TenantID:    tid,
		LicenceKey:  licenceKey,
		CreatedAt:   ca,
		ValidatedAt: va,
	}, nil
}

// Init generates a new DeviceID and writes the identity to the settings table.
// Called exactly once — on first run after licence activation.
// Returns ErrAlreadyInitialised if a device identity already exists.
func Init(db *sql.DB, tenantID uuid.UUID, licenceKey string) (*Identity, error) {
	// Check if already initialised
	if _, err := Load(db); err == nil {
		return nil, fmt.Errorf("device.Init: already initialised")
	}

	id := &Identity{
		DeviceID:   uuid.New(), // cryptographically random — never sequential
		TenantID:   tenantID,
		LicenceKey: licenceKey,
		CreatedAt:  time.Now().UTC(),
	}

	tx, err := db.Begin()
	if err != nil {
		return nil, fmt.Errorf("device.Init: begin tx: %w", err)
	}
	defer tx.Rollback()

	settings := map[string]string{
		"device_id":    id.DeviceID.String(),
		"tenant_id":    id.TenantID.String(),
		"licence_key":  id.LicenceKey,
		"created_at":   id.CreatedAt.Format(time.RFC3339Nano),
		"validated_at": id.CreatedAt.Format(time.RFC3339Nano),
	}
	for k, v := range settings {
		if _, err := tx.Exec(`INSERT INTO settings (key, value) VALUES (?, ?)`, k, v); err != nil {
			return nil, fmt.Errorf("device.Init write %s: %w", k, err)
		}
	}
	return id, tx.Commit()
}

// Validate confirms the licence key is accepted by Ichebo Cloud.
// Called on first run and monthly thereafter.
// On failure, the caller should transition status to Blocked.
func Validate(identity *Identity, client transport.Client) error {
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	body := map[string]string{
		"device_id":   identity.DeviceID.String(),
		"licence_key": identity.LicenceKey,
		"tenant_id":   identity.TenantID.String(),
	}
	_, err := client.Post(ctx, "/api/sync/validate-licence/", body)
	return err
}
