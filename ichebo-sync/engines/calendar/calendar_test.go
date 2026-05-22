package calendar_test

import (
	"encoding/json"
	"path/filepath"
	"testing"

	"github.com/google/uuid"
	"github.com/ichebo/sync/engines/calendar"
	"github.com/ichebo/sync/pkg/store"
)

func openTemp(t *testing.T) store.Store {
	t.Helper()
	s, err := store.Open(filepath.Join(t.TempDir(), "cal_test.sqlite"))
	if err != nil {
		t.Fatalf("store.Open: %v", err)
	}
	t.Cleanup(func() { s.Close() })
	return s
}

func strPtr(s string) *string { return &s }

func TestEntityType(t *testing.T) {
	if calendar.New().EntityType() != "calendar_event" {
		t.Error("expected EntityType() to return 'calendar_event'")
	}
}

func TestValidate_ValidPayload(t *testing.T) {
	eng := calendar.New()
	raw, _ := json.Marshal(map[string]any{
		"id":           "550e8400-e29b-41d4-a716-446655440000",
		"created_by":   "550e8400-e29b-41d4-a716-446655440001",
		"created_at":   "2026-05-13T14:00:00Z",
		"scheduled_at": "2026-06-01T09:00:00Z",
	})
	if err := eng.Validate(raw); err != nil {
		t.Errorf("valid payload should pass: %v", err)
	}
}

func TestValidate_NeitherDateSet(t *testing.T) {
	eng := calendar.New()
	raw, _ := json.Marshal(map[string]any{
		"id":         "550e8400-e29b-41d4-a716-446655440000",
		"created_by": "550e8400-e29b-41d4-a716-446655440001",
		"created_at": "2026-05-13T14:00:00Z",
	})
	if err := eng.Validate(raw); err == nil {
		t.Error("payload with neither scheduled_at nor due_at should be rejected")
	}
}

func TestValidate_MissingMandatoryFields(t *testing.T) {
	eng := calendar.New()
	cases := []struct {
		name    string
		payload map[string]any
	}{
		{"missing id", map[string]any{"created_by": "abc", "created_at": "2026-05-13T14:00:00Z", "scheduled_at": "2026-06-01T09:00:00Z"}},
		{"non-uuid id", map[string]any{"id": "bad", "created_by": "abc", "created_at": "2026-05-13T14:00:00Z", "scheduled_at": "2026-06-01T09:00:00Z"}},
		{"missing created_by", map[string]any{"id": "550e8400-e29b-41d4-a716-446655440000", "created_at": "2026-05-13T14:00:00Z", "scheduled_at": "2026-06-01T09:00:00Z"}},
		{"missing created_at", map[string]any{"id": "550e8400-e29b-41d4-a716-446655440000", "created_by": "abc", "scheduled_at": "2026-06-01T09:00:00Z"}},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			raw, _ := json.Marshal(tc.payload)
			if err := eng.Validate(raw); err == nil {
				t.Error("expected error, got nil")
			}
		})
	}
}

// E.3 exit criterion: Aggregate() returns activities with dates in ascending order,
// excluding activities that have neither scheduled_at nor due_at.
func TestAggregate_SortedAndFiltered(t *testing.T) {
	s := openTemp(t)
	tenantID := uuid.New()

	activities := []store.Activity{
		{
			ID: uuid.New(), TenantID: tenantID, ActivityType: "event",
			Title: "Later Event", Status: "pending",
			ScheduledAt: strPtr("2026-07-15T10:00:00Z"),
			CreatedBy: uuid.New(), CreatedAt: "2026-05-01T00:00:00Z",
			UpdatedAt: "2026-05-01T00:00:00Z", Metadata: "{}",
		},
		{
			ID: uuid.New(), TenantID: tenantID, ActivityType: "event",
			Title: "Earlier Event", Status: "pending",
			ScheduledAt: strPtr("2026-06-01T09:00:00Z"),
			CreatedBy: uuid.New(), CreatedAt: "2026-05-01T00:00:00Z",
			UpdatedAt: "2026-05-01T00:00:00Z", Metadata: "{}",
		},
		{
			ID: uuid.New(), TenantID: tenantID, ActivityType: "task",
			Title: "No Date Task", Status: "pending",
			// Neither scheduled_at nor due_at — must be excluded.
			CreatedBy: uuid.New(), CreatedAt: "2026-05-01T00:00:00Z",
			UpdatedAt: "2026-05-01T00:00:00Z", Metadata: "{}",
		},
		{
			ID: uuid.New(), TenantID: tenantID, ActivityType: "task",
			Title: "Task with due_at", Status: "pending",
			DueAt: strPtr("2026-06-20T00:00:00Z"),
			CreatedBy: uuid.New(), CreatedAt: "2026-05-01T00:00:00Z",
			UpdatedAt: "2026-05-01T00:00:00Z", Metadata: "{}",
		},
	}

	err := s.Tx(func(tx store.TxStore) error {
		for i := range activities {
			if err := tx.Activities().Upsert(&activities[i]); err != nil {
				return err
			}
		}
		return nil
	})
	if err != nil {
		t.Fatalf("inserting activities: %v", err)
	}

	eng := calendar.New()
	events, err := eng.Aggregate(s, tenantID)
	if err != nil {
		t.Fatalf("Aggregate: %v", err)
	}

	// 3 activities have a date; 1 is excluded.
	if len(events) != 3 {
		t.Fatalf("expected 3 events, got %d", len(events))
	}

	// Must be in ascending sort order.
	if events[0].Title != "Earlier Event" {
		t.Errorf("first event should be 'Earlier Event', got %q", events[0].Title)
	}
	if events[1].Title != "Task with due_at" {
		t.Errorf("second event should be 'Task with due_at', got %q", events[1].Title)
	}
	if events[2].Title != "Later Event" {
		t.Errorf("third event should be 'Later Event', got %q", events[2].Title)
	}
}

func TestAggregate_EmptyTenant(t *testing.T) {
	s := openTemp(t)
	eng := calendar.New()
	events, err := eng.Aggregate(s, uuid.New())
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(events) != 0 {
		t.Errorf("expected 0 events for empty tenant, got %d", len(events))
	}
}
