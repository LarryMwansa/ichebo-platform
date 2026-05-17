// Package pull implements the cloud → local pull cycle (DOC C §3.7).
//
// One job: ask the cloud what has changed since the last sync, receive the
// response, and apply it to the local store through the appropriate domain engine.
package pull

import (
	"context"
	"encoding/json"
	"fmt"

	"github.com/google/uuid"
	"github.com/ichebo/sync/engines/engine"
	"github.com/ichebo/sync/pkg/changelog"
	"github.com/ichebo/sync/pkg/clock"
	"github.com/ichebo/sync/pkg/device"
	"github.com/ichebo/sync/pkg/resolve"
	"github.com/ichebo/sync/pkg/status"
	"github.com/ichebo/sync/pkg/store"
	"github.com/ichebo/sync/pkg/transport"
)

// PullResponse mirrors the cloud GET /api/sync/pull/ response shape.
type PullResponse struct {
	Since       string            `json:"since"`
	RetrievedAt string            `json:"retrieved_at"`
	HasMore     bool              `json:"has_more"`
	Records     []json.RawMessage `json:"records"`
	Activities  []json.RawMessage `json:"activities"`
	Relationships []json.RawMessage `json:"relationships"`
	Notifications []json.RawMessage `json:"notifications"`
}

// Puller executes pull cycles.
type Puller struct {
	log      changelog.Log
	store    store.Store
	transport transport.Client
	engines  *engine.Registry
	resolver resolve.Resolver
	clock    *clock.HybridClock
	device   *device.Identity
	status   *status.Monitor
}

// New creates a Puller.
func New(
	log changelog.Log,
	s store.Store,
	t transport.Client,
	reg *engine.Registry,
	res resolve.Resolver,
	clk *clock.HybridClock,
	dev *device.Identity,
	mon *status.Monitor,
) *Puller {
	return &Puller{
		log:       log,
		store:     s,
		transport: t,
		engines:   reg,
		resolver:  res,
		clock:     clk,
		device:    dev,
		status:    mon,
	}
}

// Run executes one complete pull cycle, following has_more pagination.
func (p *Puller) Run(ctx context.Context) error {
	since, err := p.log.LastSyncedAt(p.device.DeviceID)
	if err != nil {
		return fmt.Errorf("pull.Run: last synced at: %w", err)
	}

	for {
		resp, err := p.fetch(ctx, since)
		if err != nil {
			return fmt.Errorf("pull.Run: fetch: %w", err)
		}

		// Update local HLC with cloud's retrieved_at timestamp
		cloudTS := clock.Parse(resp.RetrievedAt)
		p.clock.Receive(cloudTS)

		// Apply each entity type through the appropriate engine
		entitySets := []struct {
			entityType string
			items      []json.RawMessage
		}{
			{"record", resp.Records},
			{"activity", resp.Activities},
			{"relationship", resp.Relationships},
		}
		for _, set := range entitySets {
			for _, raw := range set.items {
				if err := p.applyOrConflict(ctx, set.entityType, raw); err != nil {
					return fmt.Errorf("pull.Run: apply %s: %w", set.entityType, err)
				}
			}
		}

		if !resp.HasMore {
			break
		}
		ts := clock.Parse(resp.RetrievedAt)
		since = &ts
	}

	return nil
}

// applyOrConflict determines whether to apply a cloud entity directly or
// route it to the conflict resolver.
func (p *Puller) applyOrConflict(ctx context.Context, entityType string, raw json.RawMessage) error {
	entityID := extractID(raw)

	// Check for pending local changes on this entity
	pending, err := p.log.Pending(p.device.DeviceID)
	if err != nil {
		return err
	}
	hasPendingLocal := containsEntity(pending, entityID)

	eng, err := p.engines.For(entityType)
	if err != nil {
		// Unknown entity type from cloud — skip
		return nil
	}

	if !hasPendingLocal {
		// No conflict — apply directly
		return p.store.Tx(func(tx store.TxStore) error {
			return eng.Apply(tx, changelog.OpUpdate, raw)
		})
	}

	// Conflict — extract local version and route to resolver
	localVersion, err := eng.Extract(p.store, entityID)
	if err != nil {
		return fmt.Errorf("pull: extract local %s %s: %w", entityType, entityID, err)
	}

	return p.resolver.Resolve(ctx, resolve.Conflict{
		EntityType:   entityType,
		EntityID:     entityID,
		LocalVersion: localVersion,
		CloudVersion: raw,
		Rule:         resolve.RuleFor(entityType),
	})
}

func (p *Puller) fetch(ctx context.Context, since *clock.Timestamp) (*PullResponse, error) {
	params := map[string]string{
		"device_id": p.device.DeviceID.String(),
		"tenant_id": p.device.TenantID.String(),
	}
	if since != nil {
		params["since"] = since.String()
	}

	data, err := p.transport.Get(ctx, "/api/sync/pull/", params)
	if err != nil {
		return nil, err
	}

	var resp PullResponse
	if err := json.Unmarshal(data, &resp); err != nil {
		return nil, fmt.Errorf("pull: decode response: %w", err)
	}
	return &resp, nil
}

func extractID(raw json.RawMessage) uuid.UUID {
	var obj struct {
		ID string `json:"id"`
	}
	json.Unmarshal(raw, &obj)
	id, _ := uuid.Parse(obj.ID)
	return id
}

func containsEntity(entries []changelog.Entry, id uuid.UUID) bool {
	for _, e := range entries {
		if e.EntityID == id {
			return true
		}
	}
	return false
}
