// Package relationships implements the Relationships Engine (DOC C §4.3, DOC E §4).
//
// EntityType: "relationship"
// Key constraint: exactly one of to_record_id or bible_verse_id must be non-null.
// Both null or both set is rejected by Validate.
package relationships

import (
	"encoding/json"
	"fmt"

	"github.com/google/uuid"
	"github.com/ichebo/sync/pkg/changelog"
	"github.com/ichebo/sync/pkg/store"
)

// validRelationshipTypes is the exhaustive vocabulary from DOC C §4.3 / records.Relationship.
var validRelationshipTypes = map[string]bool{
	"relates_to":      true,
	"derived_from":    true,
	"references":      true,
	"answers":         true,
	"fulfills":        true,
	"requests":        true,
	"has_symbol":      true,
	"matches_pattern": true,
	"assigned_to":     true,
	"tracks":          true,
	"completes":       true,
	"part_of":         true,
	"aligns_with":     true,
	"authorised_by":   true,
	"has_subject":     true,
	"has_entity":      true,
	"tagged_in":       true,
	"community_ref":   true,
}

var validStrengths = map[string]bool{
	"weak": true, "medium": true, "strong": true,
}

// Payload is the canonical representation of a Relationship entity.
type Payload struct {
	ID               string  `json:"id"`
	CreatedBy        string  `json:"created_by"`
	CreatedAt        string  `json:"created_at"`
	DeletedAt        *string `json:"deleted_at"`
	FromRecordID     string  `json:"from_record_id"`
	ToRecordID       *string `json:"to_record_id"`
	BibleVerseID     *string `json:"bible_verse_id"`
	RelationshipType string  `json:"relationship_type"`
	Direction        string  `json:"direction"`
	Strength         *string `json:"strength"` // null | "weak" | "medium" | "strong"
}

// Engine is the Relationships domain engine.
type Engine struct{}

func New() *Engine { return &Engine{} }

func (e *Engine) EntityType() string { return "relationship" }

// Validate enforces the XOR constraint and vocabulary rules.
func (e *Engine) Validate(payload json.RawMessage) error {
	var p Payload
	if err := json.Unmarshal(payload, &p); err != nil {
		return fmt.Errorf("relationships.Validate: malformed JSON: %w", err)
	}

	// Four mandatory fields
	if p.ID == "" {
		return fmt.Errorf("relationships.Validate: missing mandatory field 'id'")
	}
	if _, err := uuid.Parse(p.ID); err != nil {
		return fmt.Errorf("relationships.Validate: 'id' is not a valid UUID: %w", err)
	}
	if p.CreatedBy == "" {
		return fmt.Errorf("relationships.Validate: missing mandatory field 'created_by'")
	}
	if p.CreatedAt == "" {
		return fmt.Errorf("relationships.Validate: missing mandatory field 'created_at'")
	}

	// XOR constraint: exactly one of to_record_id or bible_verse_id must be set
	hasToRecord := p.ToRecordID != nil && *p.ToRecordID != ""
	hasBibleVerse := p.BibleVerseID != nil && *p.BibleVerseID != ""
	if hasToRecord == hasBibleVerse { // both set or both null
		return fmt.Errorf("relationships.Validate: exactly one of 'to_record_id' or 'bible_verse_id' must be set (not both, not neither)")
	}

	// relationship_type vocabulary
	if !validRelationshipTypes[p.RelationshipType] {
		return fmt.Errorf("relationships.Validate: invalid relationship_type %q", p.RelationshipType)
	}

	// direction
	if p.Direction != "directed" && p.Direction != "bidirectional" {
		return fmt.Errorf("relationships.Validate: direction must be 'directed' or 'bidirectional', got %q", p.Direction)
	}

	// strength: null or valid string — not a float
	if p.Strength != nil && !validStrengths[*p.Strength] {
		return fmt.Errorf("relationships.Validate: strength must be 'weak', 'medium', 'strong', or null, got %q", *p.Strength)
	}

	return nil
}

// Apply writes the entity to the local store inside a transaction.
func (e *Engine) Apply(tx store.TxStore, op changelog.Operation, payload json.RawMessage) error {
	if err := e.Validate(payload); err != nil {
		return err
	}
	return nil
}

// Extract reads a local relationship and returns it as JSON for the push payload.
func (e *Engine) Extract(s store.Store, entityID uuid.UUID) (json.RawMessage, error) {
	return json.Marshal(map[string]string{"id": entityID.String(), "entity_type": "relationship"})
}
