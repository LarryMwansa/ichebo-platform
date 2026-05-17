package clock_test

import (
	"testing"
	"time"

	"github.com/ichebo/sync/pkg/clock"
)

func TestCompare(t *testing.T) {
	base := time.Date(2026, 5, 13, 14, 0, 0, 0, time.UTC)
	later := base.Add(time.Second)

	a := clock.Timestamp{Physical: base, Logical: 0}
	b := clock.Timestamp{Physical: base, Logical: 1}
	c := clock.Timestamp{Physical: later, Logical: 0}

	if clock.Compare(a, b) != -1 {
		t.Error("same physical, lower logical should be less")
	}
	if clock.Compare(b, a) != 1 {
		t.Error("same physical, higher logical should be greater")
	}
	if clock.Compare(a, a) != 0 {
		t.Error("identical timestamps should be equal")
	}
	if clock.Compare(a, c) != -1 {
		t.Error("earlier physical should be less regardless of logical")
	}
}

// E.3b exit criterion: Compare() correctly orders events from two devices
// with identical wall clock times.
func TestCompareIdenticalWallClock(t *testing.T) {
	wall := time.Date(2026, 5, 13, 14, 0, 0, 0, time.UTC)

	deviceA := clock.Timestamp{Physical: wall, Logical: 0}
	deviceB := clock.Timestamp{Physical: wall, Logical: 1}

	if clock.Compare(deviceA, deviceB) != -1 {
		t.Error("device A (logical=0) must be before device B (logical=1) at same wall time")
	}
	if clock.Compare(deviceB, deviceA) != 1 {
		t.Error("device B (logical=1) must be after device A (logical=0) at same wall time")
	}
}

func TestNowMonotonic(t *testing.T) {
	c := clock.New()
	prev := c.Now()
	for i := 0; i < 100; i++ {
		next := c.Now()
		if clock.Compare(next, prev) <= 0 {
			t.Errorf("Now() must be strictly monotonic: %v not > %v", next, prev)
		}
		prev = next
	}
}

func TestReceiveAdvancesLocal(t *testing.T) {
	base := time.Date(2026, 5, 13, 14, 0, 0, 0, time.UTC)
	c := clock.NewWithClock(func() time.Time { return base })

	future := clock.Timestamp{Physical: base.Add(time.Hour), Logical: 5}
	result := c.Receive(future)

	if clock.Compare(result, future) <= 0 {
		t.Error("after Receive, local clock must be strictly after the remote timestamp")
	}
}

func TestParseSerialisationRoundtrip(t *testing.T) {
	original := clock.Timestamp{
		Physical: time.Date(2026, 5, 13, 14, 0, 0, 123000000, time.UTC),
		Logical:  42,
	}
	s := original.String()
	parsed := clock.Parse(s)

	if clock.Compare(original, parsed) != 0 {
		t.Errorf("round-trip failed: %v → %q → %v", original, s, parsed)
	}
}

func TestParseMalformed(t *testing.T) {
	cases := []string{"", "abc", "123", "123_abc", "_42"}
	for _, s := range cases {
		ts := clock.Parse(s)
		if !ts.IsZero() {
			t.Errorf("Parse(%q) should return zero Timestamp, got %v", s, ts)
		}
	}
}
