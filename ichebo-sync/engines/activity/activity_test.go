package activity_test

import (
	"encoding/json"
	"testing"

	"github.com/ichebo/sync/engines/activity"
)

// E.3f exit criterion: ActivityLog entry written atomically with every status
// transition — activity_type and status vocabularies validated.
func TestValidate_MandatoryFields(t *testing.T) {
	eng := activity.New()

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
				"activity_type": "task",
				"status": "pending",
			},
			wantErr: false,
		},
		{
			name:    "missing id",
			payload: map[string]any{"created_by": "abc", "created_at": "2026-05-13T14:00:00Z", "activity_type": "task", "status": "pending"},
			wantErr: true,
		},
		{
			name:    "non-uuid id",
			payload: map[string]any{"id": "not-a-uuid", "created_by": "abc", "created_at": "2026-05-13T14:00:00Z", "activity_type": "task", "status": "pending"},
			wantErr: true,
		},
		{
			name:    "missing created_by",
			payload: map[string]any{"id": "550e8400-e29b-41d4-a716-446655440000", "created_at": "2026-05-13T14:00:00Z", "activity_type": "task", "status": "pending"},
			wantErr: true,
		},
		{
			name:    "missing created_at",
			payload: map[string]any{"id": "550e8400-e29b-41d4-a716-446655440000", "created_by": "abc", "activity_type": "task", "status": "pending"},
			wantErr: true,
		},
	}

	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			raw, _ := json.Marshal(tc.payload)
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

func TestValidate_AllActivityTypes(t *testing.T) {
	eng := activity.New()
	types := []string{"task", "habit", "goal", "event", "campaign", "project", "programme", "reminder", "skill"}

	for _, at := range types {
		t.Run(at, func(t *testing.T) {
			raw, _ := json.Marshal(map[string]any{
				"id":            "550e8400-e29b-41d4-a716-446655440000",
				"created_by":    "550e8400-e29b-41d4-a716-446655440001",
				"created_at":    "2026-05-13T14:00:00Z",
				"activity_type": at,
				"status":        "pending",
			})
			if err := eng.Validate(raw); err != nil {
				t.Errorf("activity_type %q should be valid: %v", at, err)
			}
		})
	}
}

func TestValidate_InvalidActivityType(t *testing.T) {
	eng := activity.New()
	raw, _ := json.Marshal(map[string]any{
		"id":            "550e8400-e29b-41d4-a716-446655440000",
		"created_by":    "550e8400-e29b-41d4-a716-446655440001",
		"created_at":    "2026-05-13T14:00:00Z",
		"activity_type": "banana",
		"status":        "pending",
	})
	if err := eng.Validate(raw); err == nil {
		t.Error("invalid activity_type should be rejected")
	}
}

func TestValidate_AllStatuses(t *testing.T) {
	eng := activity.New()
	statuses := []string{"pending", "in_progress", "completed", "cancelled", "deferred"}

	for _, s := range statuses {
		t.Run(s, func(t *testing.T) {
			raw, _ := json.Marshal(map[string]any{
				"id":            "550e8400-e29b-41d4-a716-446655440000",
				"created_by":    "550e8400-e29b-41d4-a716-446655440001",
				"created_at":    "2026-05-13T14:00:00Z",
				"activity_type": "task",
				"status":        s,
			})
			if err := eng.Validate(raw); err != nil {
				t.Errorf("status %q should be valid: %v", s, err)
			}
		})
	}
}

func TestValidate_InvalidStatus(t *testing.T) {
	eng := activity.New()
	raw, _ := json.Marshal(map[string]any{
		"id":            "550e8400-e29b-41d4-a716-446655440000",
		"created_by":    "550e8400-e29b-41d4-a716-446655440001",
		"created_at":    "2026-05-13T14:00:00Z",
		"activity_type": "task",
		"status":        "flying",
	})
	if err := eng.Validate(raw); err == nil {
		t.Error("invalid status should be rejected")
	}
}
