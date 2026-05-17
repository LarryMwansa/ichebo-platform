package records_test

import (
	"encoding/json"
	"testing"

	"github.com/ichebo/sync/engines/records"
)

func TestValidate_MandatoryFields(t *testing.T) {
	eng := records.New()

	// E.3e exit criterion: Apply() rejects payloads missing mandatory fields.
	cases := []struct {
		name    string
		payload map[string]any
		wantErr bool
	}{
		{
			name: "valid payload",
			payload: map[string]any{
				"id": "550e8400-e29b-41d4-a716-446655440000",
				"created_by": "550e8400-e29b-41d4-a716-446655440001",
				"created_at": "2026-05-13T14:00:00Z",
				"record_class": "personal",
				"record_family": "journal",
				"record_type": "note",
				"status": "active",
			},
			wantErr: false,
		},
		{
			name: "missing id",
			payload: map[string]any{
				"created_by": "550e8400-e29b-41d4-a716-446655440001",
				"created_at": "2026-05-13T14:00:00Z",
				"record_class": "personal", "record_family": "journal", "record_type": "note",
			},
			wantErr: true,
		},
		{
			name: "missing created_by",
			payload: map[string]any{
				"id": "550e8400-e29b-41d4-a716-446655440000",
				"created_at": "2026-05-13T14:00:00Z",
				"record_class": "personal", "record_family": "journal", "record_type": "note",
			},
			wantErr: true,
		},
		{
			name: "missing created_at",
			payload: map[string]any{
				"id": "550e8400-e29b-41d4-a716-446655440000",
				"created_by": "550e8400-e29b-41d4-a716-446655440001",
				"record_class": "personal", "record_family": "journal", "record_type": "note",
			},
			wantErr: true,
		},
		{
			name: "invalid record_class",
			payload: map[string]any{
				"id": "550e8400-e29b-41d4-a716-446655440000",
				"created_by": "550e8400-e29b-41d4-a716-446655440001",
				"created_at": "2026-05-13T14:00:00Z",
				"record_class": "banana", "record_family": "journal", "record_type": "note",
			},
			wantErr: true,
		},
		{
			name: "invalid record_family",
			payload: map[string]any{
				"id": "550e8400-e29b-41d4-a716-446655440000",
				"created_by": "550e8400-e29b-41d4-a716-446655440001",
				"created_at": "2026-05-13T14:00:00Z",
				"record_class": "personal", "record_family": "not_a_family", "record_type": "note",
			},
			wantErr: true,
		},
		{
			name: "non-uuid id",
			payload: map[string]any{
				"id": "not-a-uuid",
				"created_by": "550e8400-e29b-41d4-a716-446655440001",
				"created_at": "2026-05-13T14:00:00Z",
				"record_class": "personal", "record_family": "journal", "record_type": "note",
			},
			wantErr: true,
		},
	}

	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			raw, _ := json.Marshal(tc.payload)
			err := eng.Validate(raw)
			if tc.wantErr && err == nil {
				t.Error("expected validation error, got nil")
			}
			if !tc.wantErr && err != nil {
				t.Errorf("unexpected error: %v", err)
			}
		})
	}
}

func TestValidate_AllRecordClasses(t *testing.T) {
	eng := records.New()
	for _, class := range []string{"personal", "organizational", "governance"} {
		payload, _ := json.Marshal(map[string]any{
			"id": "550e8400-e29b-41d4-a716-446655440000",
			"created_by": "550e8400-e29b-41d4-a716-446655440001",
			"created_at": "2026-05-13T14:00:00Z",
			"record_class": class, "record_family": "journal", "record_type": "note",
		})
		if err := eng.Validate(payload); err != nil {
			t.Errorf("record_class %q should be valid: %v", class, err)
		}
	}
}
