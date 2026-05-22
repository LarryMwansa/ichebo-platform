package relationships_test

import (
	"encoding/json"
	"testing"

	"github.com/ichebo/sync/engines/relationships"
)

func strPtr(s string) *string { return &s }

// E.3g exit criterion: Apply() rejects payloads with both to_record_id
// and bible_verse_id set.
func TestValidate_XORConstraint(t *testing.T) {
	eng := relationships.New()

	base := map[string]any{
		"id":                "550e8400-e29b-41d4-a716-446655440000",
		"created_by":        "550e8400-e29b-41d4-a716-446655440001",
		"created_at":        "2026-05-13T14:00:00Z",
		"from_record_id":    "550e8400-e29b-41d4-a716-446655440002",
		"relationship_type": "references",
		"direction":         "directed",
	}

	cases := []struct {
		name         string
		toRecordID   *string
		bibleVerseID *string
		wantErr      bool
	}{
		{"to_record set, bible_verse nil", strPtr("550e8400-e29b-41d4-a716-446655440003"), nil, false},
		{"bible_verse set, to_record nil", nil, strPtr("550e8400-e29b-41d4-a716-446655440004"), false},
		{"both set → rejected", strPtr("550e8400-e29b-41d4-a716-446655440003"), strPtr("550e8400-e29b-41d4-a716-446655440004"), true},
		{"both nil → rejected", nil, nil, true},
	}

	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			p := copyMap(base)
			p["to_record_id"] = tc.toRecordID
			p["bible_verse_id"] = tc.bibleVerseID
			raw, _ := json.Marshal(p)
			err := eng.Validate(raw)
			if tc.wantErr && err == nil {
				t.Error("expected error, got nil")
			}
			if !tc.wantErr && err != nil {
				t.Errorf("unexpected error: %v", err)
			}
		})
	}
}

func TestValidate_Strength(t *testing.T) {
	eng := relationships.New()
	base := map[string]any{
		"id":                "550e8400-e29b-41d4-a716-446655440000",
		"created_by":        "550e8400-e29b-41d4-a716-446655440001",
		"created_at":        "2026-05-13T14:00:00Z",
		"from_record_id":    "550e8400-e29b-41d4-a716-446655440002",
		"to_record_id":      "550e8400-e29b-41d4-a716-446655440003",
		"relationship_type": "references",
		"direction":         "directed",
	}

	for _, s := range []string{"weak", "medium", "strong"} {
		p := copyMap(base)
		p["strength"] = s
		raw, _ := json.Marshal(p)
		if err := eng.Validate(raw); err != nil {
			t.Errorf("strength %q should be valid: %v", s, err)
		}
	}

	// null strength is valid
	p := copyMap(base)
	p["strength"] = nil
	raw, _ := json.Marshal(p)
	if err := eng.Validate(raw); err != nil {
		t.Errorf("null strength should be valid: %v", err)
	}

	// float is not valid
	p = copyMap(base)
	p["strength"] = "0.8"
	raw, _ = json.Marshal(p)
	if err := eng.Validate(raw); err == nil {
		t.Error("float-like string strength should be rejected")
	}
}

func TestValidate_Direction(t *testing.T) {
	eng := relationships.New()
	base := map[string]any{
		"id": "550e8400-e29b-41d4-a716-446655440000",
		"created_by": "550e8400-e29b-41d4-a716-446655440001",
		"created_at": "2026-05-13T14:00:00Z",
		"from_record_id": "550e8400-e29b-41d4-a716-446655440002",
		"to_record_id": "550e8400-e29b-41d4-a716-446655440003",
		"relationship_type": "references",
	}
	for _, d := range []string{"directed", "bidirectional"} {
		p := copyMap(base)
		p["direction"] = d
		raw, _ := json.Marshal(p)
		if err := eng.Validate(raw); err != nil {
			t.Errorf("direction %q should be valid: %v", d, err)
		}
	}
	p := copyMap(base)
	p["direction"] = "sideways"
	raw, _ := json.Marshal(p)
	if err := eng.Validate(raw); err == nil {
		t.Error("invalid direction should be rejected")
	}
}

func TestValidate_AllRelationshipTypes(t *testing.T) {
	eng := relationships.New()
	base := map[string]any{
		"id":             "550e8400-e29b-41d4-a716-446655440000",
		"created_by":     "550e8400-e29b-41d4-a716-446655440001",
		"created_at":     "2026-05-13T14:00:00Z",
		"from_record_id": "550e8400-e29b-41d4-a716-446655440002",
		"to_record_id":   "550e8400-e29b-41d4-a716-446655440003",
		"direction":      "directed",
	}
	allTypes := []string{
		"relates_to", "derived_from", "references", "answers", "fulfills",
		"requests", "has_symbol", "matches_pattern", "assigned_to", "tracks",
		"completes", "part_of", "aligns_with", "authorised_by", "has_subject",
		"has_entity", "tagged_in", "community_ref",
	}
	for _, rt := range allTypes {
		t.Run(rt, func(t *testing.T) {
			p := copyMap(base)
			p["relationship_type"] = rt
			raw, _ := json.Marshal(p)
			if err := eng.Validate(raw); err != nil {
				t.Errorf("relationship_type %q should be valid: %v", rt, err)
			}
		})
	}
	// Old types that were removed must now be rejected.
	for _, rt := range []string{"related_to", "links_to", "annotates", "supersedes"} {
		t.Run("reject_"+rt, func(t *testing.T) {
			p := copyMap(base)
			p["relationship_type"] = rt
			raw, _ := json.Marshal(p)
			if err := eng.Validate(raw); err == nil {
				t.Errorf("removed relationship_type %q should be rejected", rt)
			}
		})
	}
}

func copyMap(m map[string]any) map[string]any {
	out := make(map[string]any, len(m))
	for k, v := range m {
		out[k] = v
	}
	return out
}
