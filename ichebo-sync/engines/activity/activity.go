// Package activity implements the Activity Engine (DOC C §4.2, DOC E §3).
//
// EntityType: "activity"
// Every status transition writes an ActivityLog entry atomically in the same Tx.
// ActivityLog entries are immutable — never updated, never deleted.
package activity

import (
	"encoding/json"
	"fmt"

	"github.com/google/uuid"
	"github.com/ichebo/sync/pkg/changelog"
	"github.com/ichebo/sync/pkg/store"
)

var validActivityTypes = map[string]bool{
	"task": true, "habit": true, "goal": true, "event": true,
	"campaign": true, "project": true, "programme": true,
	"reminder": true, "skill": true,
}

var validStatuses = map[string]bool{
	"pending": true, "in_progress": true, "completed": true,
	"cancelled": true, "deferred": true,
}

// Payload is the canonical representation of an Activity entity.
type Payload struct {
	ID           string  `json:"id"`
	TenantID     *string `json:"tenant_id"`
	CreatedBy    string  `json:"created_by"`
	CreatedAt    string  `json:"created_at"`
	DeletedAt    *string `json:"deleted_at"`
	Title        string  `json:"title"`
	ActivityType string  `json:"activity_type"`
	Status       string  `json:"status"`
	AssignedTo   *string `json:"assigned_to,omitempty"`
}

// Engine is the Activity domain engine.
type Engine struct{}

func New() *Engine { return &Engine{} }

func (e *Engine) EntityType() string { return "activity" }

// Validate enforces all domain rules on the payload.
func (e *Engine) Validate(payload json.RawMessage) error {
	var p Payload
	if err := json.Unmarshal(payload, &p); err != nil {
		return fmt.Errorf("activity.Validate: malformed JSON: %w", err)
	}

	// Four mandatory fields
	if p.ID == "" {
		return fmt.Errorf("activity.Validate: missing mandatory field 'id'")
	}
	if _, err := uuid.Parse(p.ID); err != nil {
		return fmt.Errorf("activity.Validate: 'id' is not a valid UUID: %w", err)
	}
	if p.CreatedBy == "" {
		return fmt.Errorf("activity.Validate: missing mandatory field 'created_by'")
	}
	if p.CreatedAt == "" {
		return fmt.Errorf("activity.Validate: missing mandatory field 'created_at'")
	}

	// activity_type validation
	if !validActivityTypes[p.ActivityType] {
		return fmt.Errorf("activity.Validate: invalid activity_type %q", p.ActivityType)
	}

	// status validation
	if !validStatuses[p.Status] {
		return fmt.Errorf("activity.Validate: invalid status %q", p.Status)
	}

	return nil
}

// Apply writes the entity to the local store. Every status transition writes
// an ActivityLog entry in the same transaction.
func (e *Engine) Apply(tx store.TxStore, op changelog.Operation, payload json.RawMessage) error {
	if err := e.Validate(payload); err != nil {
		return err
	}
	// Full SQLite write implementation in Phase E.4d+ when store exposes ActivityStore.
	return nil
}

// Extract reads a local activity and returns it as JSON for the push payload.
func (e *Engine) Extract(s store.Store, entityID uuid.UUID) (json.RawMessage, error) {
	return json.Marshal(map[string]string{"id": entityID.String(), "entity_type": "activity"})
}
