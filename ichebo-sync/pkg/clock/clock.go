// Package clock implements a Hybrid Logical Clock (HLC) for event ordering
// across devices with potentially drifting wall clocks.
//
// HLC timestamps are serialised as "{unix_nano}_{logical}" so they sort
// correctly as strings and survive round-trips through SQLite TEXT columns.
package clock

import (
	"fmt"
	"strconv"
	"strings"
	"sync"
	"time"
)

// Timestamp is a hybrid logical timestamp.
type Timestamp struct {
	Physical time.Time // wall clock component
	Logical  uint32    // counter for same-millisecond ordering
}

// String serialises the timestamp as "{unix_nano}_{logical}".
func (t Timestamp) String() string {
	return fmt.Sprintf("%d_%d", t.Physical.UnixNano(), t.Logical)
}

// IsZero reports whether the timestamp is the zero value.
func (t Timestamp) IsZero() bool {
	return t.Physical.IsZero() && t.Logical == 0
}

// Parse deserialises a timestamp produced by String().
// Returns zero Timestamp on malformed input.
func Parse(s string) Timestamp {
	parts := strings.SplitN(s, "_", 2)
	if len(parts) != 2 {
		return Timestamp{}
	}
	nanos, err := strconv.ParseInt(parts[0], 10, 64)
	if err != nil {
		return Timestamp{}
	}
	logical, err := strconv.ParseUint(parts[1], 10, 32)
	if err != nil {
		return Timestamp{}
	}
	return Timestamp{
		Physical: time.Unix(0, nanos).UTC(),
		Logical:  uint32(logical),
	}
}

// Compare returns -1, 0, or 1 for a < b, a == b, a > b.
// Used by pkg/resolve for LastWriteWins.
func Compare(a, b Timestamp) int {
	if a.Physical.Before(b.Physical) {
		return -1
	}
	if a.Physical.After(b.Physical) {
		return 1
	}
	// Same physical time — compare logical counters
	if a.Logical < b.Logical {
		return -1
	}
	if a.Logical > b.Logical {
		return 1
	}
	return 0
}

// HybridClock maintains the local HLC state.
type HybridClock struct {
	mu      sync.Mutex
	physNow func() time.Time // injectable for testing
	lastTS  Timestamp
}

// New creates a HybridClock using the real wall clock.
func New() *HybridClock {
	return &HybridClock{physNow: func() time.Time { return time.Now().UTC() }}
}

// NewWithClock creates a HybridClock with an injectable time source for tests.
func NewWithClock(physNow func() time.Time) *HybridClock {
	return &HybridClock{physNow: physNow}
}

// Now returns the current HLC timestamp, advancing logical if physical has not.
func (c *HybridClock) Now() Timestamp {
	c.mu.Lock()
	defer c.mu.Unlock()

	phys := c.physNow().UTC().Truncate(time.Millisecond)
	last := c.lastTS

	var next Timestamp
	if phys.After(last.Physical) {
		next = Timestamp{Physical: phys, Logical: 0}
	} else {
		next = Timestamp{Physical: last.Physical, Logical: last.Logical + 1}
	}
	c.lastTS = next
	return next
}

// Receive updates the local clock when a remote timestamp is observed.
// Ensures the local clock is always at least as advanced as any remote seen.
// Called by the Puller when processing cloud responses.
func (c *HybridClock) Receive(remote Timestamp) Timestamp {
	c.mu.Lock()
	defer c.mu.Unlock()

	phys := c.physNow().UTC().Truncate(time.Millisecond)
	last := c.lastTS

	var next Timestamp
	switch {
	case phys.After(last.Physical) && phys.After(remote.Physical):
		next = Timestamp{Physical: phys, Logical: 0}
	case remote.Physical.Equal(last.Physical):
		l := last.Logical
		if remote.Logical > l {
			l = remote.Logical
		}
		next = Timestamp{Physical: last.Physical, Logical: l + 1}
	case remote.Physical.After(last.Physical):
		next = Timestamp{Physical: remote.Physical, Logical: remote.Logical + 1}
	default:
		next = Timestamp{Physical: last.Physical, Logical: last.Logical + 1}
	}
	c.lastTS = next
	return next
}
