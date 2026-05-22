// Package calendar implements the Calendar Engine (DOC E §6).
//
// EntityType: "calendar_event"
// The Calendar Engine is an aggregation engine. It does not own a first-class
// entity type in the Django ORM. Instead, CalendarEvents are derived views
// computed by aggregating Activity rows that have a scheduled_at or due_at date.
//
// Key invariants:
//   - No direct writes: CalendarEvents are never pushed to the cloud.
//     They are generated locally from the activities table.
//   - Apply is supported for inbound cloud-sourced calendar_event payloads
//     (e.g. shared community events pushed from a coordinator device).
//   - Aggregate() produces a sorted list of CalendarEvents from stored activities.
package calendar

import (
	"encoding/json"
	"fmt"
	"sort"

	"github.com/google/uuid"
	"github.com/ichebo/sync/pkg/changelog"
	"github.com/ichebo/sync/pkg/store"
)

// CalendarEvent is a derived view of an Activity for calendar display.
type CalendarEvent struct {
	ActivityID   uuid.UUID
	TenantID     uuid.UUID
	Title        string
	ActivityType string
	Status       string
	ScheduledAt  string // ISO 8601 — empty string if no scheduled_at
	DueAt        string // ISO 8601 — empty string if no due_at
	// SortKey is the earliest of scheduled_at and due_at, used for ordering.
	SortKey string
}

// Payload is the canonical representation of a calendar_event entity
// when received from the cloud (community shared events).
type Payload struct {
	ID           string  `json:"id"`
	TenantID     *string `json:"tenant_id"`
	CreatedBy    string  `json:"created_by"`
	CreatedAt    string  `json:"created_at"`
	DeletedAt    *string `json:"deleted_at"`
	Title        string  `json:"title"`
	ActivityType string  `json:"activity_type"`
	ScheduledAt  *string `json:"scheduled_at"`
	DueAt        *string `json:"due_at"`
}

// Engine is the Calendar domain engine.
type Engine struct{}

// New creates a Calendar Engine.
func New() *Engine { return &Engine{} }

func (e *Engine) EntityType() string { return "calendar_event" }

// Validate checks that an inbound calendar_event payload has the minimum required fields.
func (e *Engine) Validate(payload json.RawMessage) error {
	var p Payload
	if err := json.Unmarshal(payload, &p); err != nil {
		return fmt.Errorf("calendar.Validate: malformed JSON: %w", err)
	}
	if p.ID == "" {
		return fmt.Errorf("calendar.Validate: missing mandatory field 'id'")
	}
	if _, err := uuid.Parse(p.ID); err != nil {
		return fmt.Errorf("calendar.Validate: 'id' is not a valid UUID: %w", err)
	}
	if p.CreatedBy == "" {
		return fmt.Errorf("calendar.Validate: missing mandatory field 'created_by'")
	}
	if p.CreatedAt == "" {
		return fmt.Errorf("calendar.Validate: missing mandatory field 'created_at'")
	}
	if p.ScheduledAt == nil && p.DueAt == nil {
		return fmt.Errorf("calendar.Validate: at least one of 'scheduled_at' or 'due_at' must be set for a calendar_event")
	}
	return nil
}

// Apply handles inbound cloud-sourced calendar events (shared community events).
// Local calendar views are generated via Aggregate(), not Apply.
func (e *Engine) Apply(tx store.TxStore, op changelog.Operation, payload json.RawMessage) error {
	if err := e.Validate(payload); err != nil {
		return err
	}
	// Full SQLite write path deferred to E.4d+ when store exposes CalendarStore.
	return nil
}

// Extract returns a stub — local CalendarEvents are derived from activities,
// not pushed to the cloud.
func (e *Engine) Extract(_ store.Store, entityID uuid.UUID) (json.RawMessage, error) {
	return json.Marshal(map[string]string{"id": entityID.String(), "entity_type": "calendar_event"})
}

// Aggregate reads all activities for a tenant from the store and returns
// a sorted list of CalendarEvents (ascending by the earliest date field).
// Activities with neither scheduled_at nor due_at are excluded.
func (e *Engine) Aggregate(s store.Store, tenantID uuid.UUID) ([]CalendarEvent, error) {
	activities, err := s.Activities().List(tenantID)
	if err != nil {
		return nil, fmt.Errorf("calendar.Aggregate: %w", err)
	}

	var events []CalendarEvent
	for _, a := range activities {
		if a.ScheduledAt == nil && a.DueAt == nil {
			continue
		}
		ev := CalendarEvent{
			ActivityID:   a.ID,
			TenantID:     a.TenantID,
			Title:        a.Title,
			ActivityType: a.ActivityType,
			Status:       a.Status,
		}
		if a.ScheduledAt != nil {
			ev.ScheduledAt = *a.ScheduledAt
		}
		if a.DueAt != nil {
			ev.DueAt = *a.DueAt
		}
		// SortKey: prefer scheduled_at, fall back to due_at.
		ev.SortKey = ev.ScheduledAt
		if ev.SortKey == "" {
			ev.SortKey = ev.DueAt
		}
		events = append(events, ev)
	}

	sort.Slice(events, func(i, j int) bool {
		return events[i].SortKey < events[j].SortKey
	})

	return events, nil
}
