// Package records implements the Records Engine (DOC C §4.1, DOC E §2).
//
// EntityType: "record"
// The Records Engine is the data spine of the Ichebo ecosystem. Every piece
// of institutional content is a Record. The engine enforces the classification
// taxonomy and the permission gate governing access to every piece of content.
package records

import (
	"encoding/json"
	"fmt"

	"github.com/google/uuid"
	"github.com/ichebo/sync/pkg/changelog"
	"github.com/ichebo/sync/pkg/store"
)

// validRecordClasses is the exhaustive set per data contract Part 3.1.
var validRecordClasses = map[string]bool{
	"personal":       true,
	"organizational": true,
	"governance":     true,
}

// validRecordFamilies is the registered set per data contract Part 3.2.
var validRecordFamilies = map[string]bool{
	"journal":    true,
	"governance": true,
	"activity":   true,
	"learning":   true,
	"reference":  true,
	"bible":      true,
	"community":  true,
	"media":      true,
}

// Payload is the canonical representation of a Record entity.
// Used for Validate and Apply — must match the cloud DRF serialiser output.
type Payload struct {
	ID           string          `json:"id"`
	TenantID     *string         `json:"tenant_id"`
	CreatedBy    string          `json:"created_by"`
	CreatedAt    string          `json:"created_at"`
	UpdatedAt    string          `json:"updated_at,omitempty"`
	DeletedAt    *string         `json:"deleted_at"`
	Title        string          `json:"title"`
	RecordClass  string          `json:"record_class"`
	RecordFamily string          `json:"record_family"`
	RecordType   string          `json:"record_type"`
	Status       string          `json:"status"`
	Body         string          `json:"body,omitempty"`
	Metadata     json.RawMessage `json:"metadata,omitempty"`
}

// Engine is the Records domain engine.
type Engine struct{}

// New creates a Records Engine.
func New() *Engine { return &Engine{} }

func (e *Engine) EntityType() string { return "record" }

// Validate checks that a payload conforms to all domain rules.
// Returns a descriptive error for any violation.
func (e *Engine) Validate(payload json.RawMessage) error {
	var p Payload
	if err := json.Unmarshal(payload, &p); err != nil {
		return fmt.Errorf("records.Validate: malformed JSON: %w", err)
	}

	// Four mandatory fields (DOC E §1.3)
	if p.ID == "" {
		return fmt.Errorf("records.Validate: missing mandatory field 'id'")
	}
	if _, err := uuid.Parse(p.ID); err != nil {
		return fmt.Errorf("records.Validate: 'id' is not a valid UUID: %w", err)
	}
	if p.CreatedBy == "" {
		return fmt.Errorf("records.Validate: missing mandatory field 'created_by'")
	}
	if p.CreatedAt == "" {
		return fmt.Errorf("records.Validate: missing mandatory field 'created_at'")
	}

	// Classification taxonomy
	if !validRecordClasses[p.RecordClass] {
		return fmt.Errorf("records.Validate: invalid record_class %q", p.RecordClass)
	}
	if !validRecordFamilies[p.RecordFamily] {
		return fmt.Errorf("records.Validate: invalid record_family %q", p.RecordFamily)
	}
	if p.RecordType == "" {
		return fmt.Errorf("records.Validate: missing 'record_type'")
	}

	return nil
}

// Apply writes the entity to the local store inside a transaction.
// Enforces all domain rules. Governance records can only be applied via
// CloudWins — local governance edits go through The Desk on the web.
func (e *Engine) Apply(tx store.TxStore, op changelog.Operation, payload json.RawMessage) error {
	if err := e.Validate(payload); err != nil {
		return err
	}
	// In the local SQLite store context, Apply writes to the records table via
	// the TxStore. The store package owns the SQL — engines never write raw SQL.
	// This stub satisfies the interface; the full implementation requires
	// store.TxStore to expose a RecordStore write method (Phase E.4d+).
	return nil
}

// Extract reads a local record and returns it as JSON for the push payload.
func (e *Engine) Extract(s store.Store, entityID uuid.UUID) (json.RawMessage, error) {
	// Full implementation requires store.Store to expose a RecordStore read method.
	// Returns a stub payload so the interface is satisfied and tests can run.
	return json.Marshal(map[string]string{"id": entityID.String(), "entity_type": "record"})
}
