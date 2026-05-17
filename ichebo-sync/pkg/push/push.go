// Package push implements the local → cloud push cycle (DOC C §3.6).
//
// One job: take pending ChangeLog entries and deliver them to the cloud,
// in order, reliably, idempotently.
package push

import (
	"context"
	"encoding/json"
	"fmt"

	"github.com/google/uuid"
	"github.com/ichebo/sync/engines/engine"
	"github.com/ichebo/sync/pkg/changelog"
	"github.com/ichebo/sync/pkg/device"
	"github.com/ichebo/sync/pkg/status"
	"github.com/ichebo/sync/pkg/store"
	"github.com/ichebo/sync/pkg/transport"
)

const defaultBatchSize = 50

// PushChange is one entry in the push request body.
type PushChange struct {
	EntityType  string          `json:"entity_type"`
	EntityID    string          `json:"entity_id"`
	Operation   string          `json:"operation"`
	ChangedAt   string          `json:"changed_at"`
	PayloadHash string          `json:"payload_hash"`
	Payload     json.RawMessage `json:"payload"`
}

// PushPayload is the full request body for POST /api/sync/push/.
type PushPayload struct {
	DeviceID string       `json:"device_id"`
	Entries  []PushChange `json:"entries"`
}

// PushResult is one entry in the cloud response.
type PushResult struct {
	EntityID string `json:"entity_id"`
	Status   string `json:"status"` // "success" | "conflict" | "rejected"
	Reason   string `json:"reason,omitempty"`
}

// PushResponse is the full cloud response body.
type PushResponse struct {
	Results []PushResult `json:"results"`
}

// Pusher executes push cycles.
type Pusher struct {
	log       changelog.Log
	store     store.Store
	transport transport.Client
	engines   *engine.Registry
	device    *device.Identity
	status    *status.Monitor
	batchSize int
}

// New creates a Pusher.
func New(
	log changelog.Log,
	s store.Store,
	t transport.Client,
	reg *engine.Registry,
	dev *device.Identity,
	mon *status.Monitor,
) *Pusher {
	return &Pusher{
		log:       log,
		store:     s,
		transport: t,
		engines:   reg,
		device:    dev,
		status:    mon,
		batchSize: defaultBatchSize,
	}
}

// Run executes one complete push cycle.
// Returns nil if there are no pending entries.
// Returns transport.NetworkError or transport.AuthError on connectivity problems.
func (p *Pusher) Run(ctx context.Context) error {
	pending, err := p.log.Pending(p.device.DeviceID)
	if err != nil {
		return fmt.Errorf("push.Run: read pending: %w", err)
	}
	if len(pending) == 0 {
		return nil
	}

	for _, batch := range batchEntries(pending, p.batchSize) {
		payload, err := p.buildPayload(batch)
		if err != nil {
			return fmt.Errorf("push.Run: build payload: %w", err)
		}

		p.status.SetState(status.Syncing, status.WithProgress(len(batch), len(pending)))

		respBytes, err := p.transport.Post(ctx, "/api/sync/push/", payload)
		if err != nil {
			// NetworkError → Offline, AuthError → Blocked — caller sets state
			return fmt.Errorf("push.Run: post: %w", err)
		}

		var resp PushResponse
		if err := json.Unmarshal(respBytes, &resp); err != nil {
			return fmt.Errorf("push.Run: decode response: %w", err)
		}

		var synced []uuid.UUID
		for _, result := range resp.Results {
			eid, _ := uuid.Parse(result.EntityID)
			switch result.Status {
			case "success":
				synced = append(synced, eid)
			case "conflict":
				// Conflict handed off to resolve package by caller
			case "rejected":
				// Log and skip — permissions issue, not retryable
			}
		}

		if err := p.log.MarkSynced(synced); err != nil {
			return fmt.Errorf("push.Run: mark synced: %w", err)
		}
	}

	return nil
}

func (p *Pusher) buildPayload(batch []changelog.Entry) (*PushPayload, error) {
	changes := make([]PushChange, 0, len(batch))
	for _, entry := range batch {
		eng, err := p.engines.For(entry.EntityType)
		if err != nil {
			// Unknown entity type — skip this entry
			continue
		}
		raw, err := eng.Extract(p.store, entry.EntityID)
		if err != nil {
			return nil, fmt.Errorf("push: extract %s %s: %w", entry.EntityType, entry.EntityID, err)
		}
		changes = append(changes, PushChange{
			EntityType:  entry.EntityType,
			EntityID:    entry.EntityID.String(),
			Operation:   string(entry.Operation),
			ChangedAt:   entry.ChangedAt.String(),
			PayloadHash: entry.PayloadHash,
			Payload:     raw,
		})
	}
	return &PushPayload{
		DeviceID: p.device.DeviceID.String(),
		Entries:  changes,
	}, nil
}

func batchEntries(entries []changelog.Entry, size int) [][]changelog.Entry {
	var batches [][]changelog.Entry
	for i := 0; i < len(entries); i += size {
		end := i + size
		if end > len(entries) {
			end = len(entries)
		}
		batches = append(batches, entries[i:end])
	}
	return batches
}
