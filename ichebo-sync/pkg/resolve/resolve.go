// Package resolve implements the conflict resolution policy table (DOC C §3.8).
//
// Every conflict resolution decision flows through RuleFor — it is the single
// authoritative location for conflict policy. Changing this function changes
// the policy everywhere. This is intentional: conflict rules are architectural
// decisions (ADR-018), not configuration values.
package resolve

import (
	"context"
	"encoding/json"

	"github.com/google/uuid"
	"github.com/ichebo/sync/pkg/clock"
)

// Rule is the conflict resolution policy for a given entity type.
type Rule int

const (
	CloudWins     Rule = iota // cloud version replaces local — authority flows downward
	LocalWins                 // local version is pushed, cloud updated
	LastWriteWins             // HLC comparison — later timestamp wins
	Merge                     // both versions kept as separate records
	Queue                     // ConflictQueue — user decides
)

// RuleFor returns the conflict resolution rule for the given entity type.
// This is the single authoritative conflict policy table.
func RuleFor(entityType string) Rule {
	switch entityType {
	case "governance_record", "handbook_record":
		return CloudWins
	case "permission", "role", "community_settings":
		return CloudWins
	case "personal_record", "bible_note", "journal_entry":
		return LocalWins
	case "member":
		return LastWriteWins
	case "activity_log":
		return Merge
	default:
		return Queue
	}
}

// Conflict holds the two versions of an entity that need resolution.
type Conflict struct {
	EntityType     string
	EntityID       uuid.UUID
	LocalVersion   json.RawMessage
	CloudVersion   json.RawMessage
	LocalChangedAt clock.Timestamp
	CloudChangedAt clock.Timestamp
	Rule           Rule
}

// Resolver applies the conflict resolution policy to a Conflict.
type Resolver interface {
	Resolve(ctx context.Context, conflict Conflict) error
}
