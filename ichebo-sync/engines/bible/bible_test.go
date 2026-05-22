package bible_test

import (
	"encoding/json"
	"errors"
	"testing"

	"github.com/google/uuid"
	"github.com/ichebo/sync/engines/bible"
	"github.com/ichebo/sync/pkg/changelog"
)

func TestValidate_ValidPayload(t *testing.T) {
	eng := bible.New()
	raw, _ := json.Marshal(map[string]any{
		"id":               "550e8400-e29b-41d4-a716-446655440000",
		"translation_code": "KJV",
		"book_code":        "GEN",
		"book_name":        "Genesis",
		"chapter":          1,
		"verse":            1,
		"text":             "In the beginning God created the heaven and the earth.",
	})
	if err := eng.Validate(raw); err != nil {
		t.Errorf("valid payload should pass: %v", err)
	}
}

func TestValidate_MissingFields(t *testing.T) {
	eng := bible.New()
	cases := []struct {
		name    string
		payload map[string]any
	}{
		{"missing id", map[string]any{"translation_code": "KJV", "book_code": "GEN", "chapter": 1, "verse": 1}},
		{"non-uuid id", map[string]any{"id": "bad", "translation_code": "KJV", "book_code": "GEN", "chapter": 1, "verse": 1}},
		{"missing translation_code", map[string]any{"id": "550e8400-e29b-41d4-a716-446655440000", "book_code": "GEN", "chapter": 1, "verse": 1}},
		{"missing book_code", map[string]any{"id": "550e8400-e29b-41d4-a716-446655440000", "translation_code": "KJV", "chapter": 1, "verse": 1}},
		{"zero chapter", map[string]any{"id": "550e8400-e29b-41d4-a716-446655440000", "translation_code": "KJV", "book_code": "GEN", "chapter": 0, "verse": 1}},
		{"zero verse", map[string]any{"id": "550e8400-e29b-41d4-a716-446655440000", "translation_code": "KJV", "book_code": "GEN", "chapter": 1, "verse": 0}},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			raw, _ := json.Marshal(tc.payload)
			if err := eng.Validate(raw); err == nil {
				t.Error("expected validation error, got nil")
			}
		})
	}
}

// E.3 exit criterion: Apply always returns ErrReadOnly — bible_verse entities
// can never be written by any client device.
func TestApply_AlwaysReadOnly(t *testing.T) {
	eng := bible.New()
	raw, _ := json.Marshal(map[string]any{
		"id":               "550e8400-e29b-41d4-a716-446655440000",
		"translation_code": "KJV",
		"book_code":        "GEN",
		"chapter":          1,
		"verse":            1,
	})
	for _, op := range []changelog.Operation{changelog.OpCreate, changelog.OpUpdate, changelog.OpDelete} {
		err := eng.Apply(nil, op, raw)
		if !errors.Is(err, bible.ErrReadOnly) {
			t.Errorf("op %s: expected ErrReadOnly, got %v", op, err)
		}
	}
}

func TestExtract_ReturnsStub(t *testing.T) {
	eng := bible.New()
	id := uuid.MustParse("550e8400-e29b-41d4-a716-446655440000")
	raw, err := eng.Extract(nil, id)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	var m map[string]string
	if err := json.Unmarshal(raw, &m); err != nil {
		t.Fatalf("invalid JSON: %v", err)
	}
	if m["entity_type"] != "bible_verse" {
		t.Errorf("expected entity_type 'bible_verse', got %q", m["entity_type"])
	}
}

func TestEntityType(t *testing.T) {
	if bible.New().EntityType() != "bible_verse" {
		t.Error("expected EntityType() to return 'bible_verse'")
	}
}
