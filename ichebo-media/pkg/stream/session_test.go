package stream

import (
	"testing"
)

func TestRegistry_StartAndEnd(t *testing.T) {
	r := NewRegistry()

	s, err := r.Start("key1", "record-abc", "tenant-xyz", "https://cdn.example.com")
	if err != nil {
		t.Fatalf("Start: %v", err)
	}
	if s.StreamKey != "key1" || s.RecordID != "record-abc" {
		t.Errorf("unexpected session: %+v", s)
	}

	active := r.Active()
	if len(active) != 1 {
		t.Fatalf("expected 1 active session, got %d", len(active))
	}

	ended, err := r.End("key1")
	if err != nil {
		t.Fatalf("End: %v", err)
	}
	if ended.RecordID != "record-abc" {
		t.Errorf("ended wrong session: %+v", ended)
	}

	if len(r.Active()) != 0 {
		t.Error("expected no active sessions after End")
	}
}

func TestRegistry_Start_DuplicateKey(t *testing.T) {
	r := NewRegistry()
	if _, err := r.Start("key1", "r1", "t1", "https://cdn.example.com"); err != nil {
		t.Fatalf("first Start: %v", err)
	}
	if _, err := r.Start("key1", "r2", "t1", "https://cdn.example.com"); err == nil {
		t.Error("expected error for duplicate stream key, got nil")
	}
}

func TestRegistry_End_UnknownKey(t *testing.T) {
	r := NewRegistry()
	if _, err := r.End("nonexistent"); err == nil {
		t.Error("expected error for unknown stream key, got nil")
	}
}

func TestRegistry_MultipleActiveSessions(t *testing.T) {
	r := NewRegistry()
	for _, key := range []string{"k1", "k2", "k3"} {
		if _, err := r.Start(key, "rec-"+key, "tenant", "https://cdn.example.com"); err != nil {
			t.Fatalf("Start %s: %v", key, err)
		}
	}
	if len(r.Active()) != 3 {
		t.Errorf("expected 3 active sessions, got %d", len(r.Active()))
	}
	if _, err := r.End("k2"); err != nil {
		t.Fatalf("End k2: %v", err)
	}
	if len(r.Active()) != 2 {
		t.Errorf("expected 2 active sessions after one end, got %d", len(r.Active()))
	}
}
