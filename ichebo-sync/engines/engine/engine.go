// Package engine defines the Engine interface and Registry.
// Every domain engine implements Engine. The Sync Engine calls engines
// through the Registry — never directly.
package engine

import (
	"encoding/json"
	"fmt"

	"github.com/google/uuid"
	"github.com/ichebo/sync/pkg/changelog"
	"github.com/ichebo/sync/pkg/store"
)

// Engine is the interface every domain engine implements.
type Engine interface {
	// EntityType returns the entity type string this engine handles.
	// Must match entity_type values in the ChangeLog.
	EntityType() string

	// Apply writes a cloud-sourced entity payload to the local store.
	// Called by the Sync Engine Puller when a cloud entity arrives locally.
	// Must enforce all domain rules from the data contract.
	// Returns error if validation fails — the Sync Engine will queue the conflict.
	Apply(tx store.TxStore, op changelog.Operation, payload json.RawMessage) error

	// Extract reads a local entity and returns it as JSON for the push payload.
	// Called by the Sync Engine Pusher when building a cloud-bound payload.
	Extract(store store.Store, entityID uuid.UUID) (json.RawMessage, error)

	// Validate checks a payload conforms to domain rules before Apply.
	// Returns a descriptive error if any rule is violated.
	Validate(payload json.RawMessage) error
}

// Registry maps entity types to engines. Built once at startup. Immutable after init.
type Registry struct {
	engines map[string]Engine
}

// NewRegistry creates an empty Registry.
func NewRegistry() *Registry {
	return &Registry{engines: make(map[string]Engine)}
}

// Register adds an engine to the registry.
func (r *Registry) Register(e Engine) {
	r.engines[e.EntityType()] = e
}

// For returns the engine for the given entity type.
// Returns an error if not found (use MustFor when caller guarantees registration).
func (r *Registry) For(entityType string) (Engine, error) {
	e, ok := r.engines[entityType]
	if !ok {
		return nil, fmt.Errorf("engine: no engine registered for entity type %q", entityType)
	}
	return e, nil
}

// MustFor returns the engine for the given entity type.
// Panics if not found — use only when the entity type is known at compile time.
func (r *Registry) MustFor(entityType string) Engine {
	e, err := r.For(entityType)
	if err != nil {
		panic(err)
	}
	return e
}
