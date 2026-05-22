// Package bible implements the Bible Engine (DOC E §5).
//
// EntityType: "bible_verse"
// The Bible Engine is READ-ONLY. Bible data is pre-loaded seed data bundled
// with the desktop/mobile client. No device ever originates a bible_verse
// entity — the engine rejects all CREATE/UPDATE operations.
//
// Invariant: Apply always returns ErrReadOnly. The Sync Engine must never
// enqueue bible_verse writes to the push queue. The engine enforces this
// at the Apply boundary as a defence-in-depth guard.
package bible

import (
	"encoding/json"
	"errors"
	"fmt"

	"github.com/google/uuid"
	"github.com/ichebo/sync/pkg/changelog"
	"github.com/ichebo/sync/pkg/store"
)

// ErrReadOnly is returned by Apply for any operation on a bible_verse entity.
// Bible data is seed data — no client may create, update, or delete it.
var ErrReadOnly = errors.New("bible: bible_verse entities are read-only; writes are not permitted")

// Payload is the canonical representation of a BibleVerse entity.
// Matches the cloud DRF serialiser output for /api/bible/verses/.
type Payload struct {
	ID               string `json:"id"`
	TranslationCode  string `json:"translation_code"`
	BookCode         string `json:"book_code"`
	BookName         string `json:"book_name"`
	Chapter          int    `json:"chapter"`
	Verse            int    `json:"verse"`
	Text             string `json:"text"`
}

// Engine is the Bible domain engine.
type Engine struct{}

// New creates a Bible Engine.
func New() *Engine { return &Engine{} }

func (e *Engine) EntityType() string { return "bible_verse" }

// Validate checks that a payload has the minimum required fields.
func (e *Engine) Validate(payload json.RawMessage) error {
	var p Payload
	if err := json.Unmarshal(payload, &p); err != nil {
		return fmt.Errorf("bible.Validate: malformed JSON: %w", err)
	}
	if p.ID == "" {
		return fmt.Errorf("bible.Validate: missing mandatory field 'id'")
	}
	if _, err := uuid.Parse(p.ID); err != nil {
		return fmt.Errorf("bible.Validate: 'id' is not a valid UUID: %w", err)
	}
	if p.TranslationCode == "" {
		return fmt.Errorf("bible.Validate: missing mandatory field 'translation_code'")
	}
	if p.BookCode == "" {
		return fmt.Errorf("bible.Validate: missing mandatory field 'book_code'")
	}
	if p.Chapter <= 0 {
		return fmt.Errorf("bible.Validate: 'chapter' must be a positive integer")
	}
	if p.Verse <= 0 {
		return fmt.Errorf("bible.Validate: 'verse' must be a positive integer")
	}
	return nil
}

// Apply always returns ErrReadOnly. Bible data is seed data — no client write path exists.
func (e *Engine) Apply(_ store.TxStore, _ changelog.Operation, _ json.RawMessage) error {
	return ErrReadOnly
}

// Extract returns a stub — Bible verses are read from the bundled SQLite database
// directly by the Flutter layer, never pushed to the cloud.
func (e *Engine) Extract(_ store.Store, entityID uuid.UUID) (json.RawMessage, error) {
	return json.Marshal(map[string]string{"id": entityID.String(), "entity_type": "bible_verse"})
}
