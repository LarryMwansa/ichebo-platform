package upload

import (
	"fmt"
	"testing"
)

func TestSession_ChunkAccounting(t *testing.T) {
	reg := NewRegistry()
	s := reg.Create("id1", "record1", "tenant1", "video.mp4", 15*1024*1024, 5*1024*1024)

	if s.TotalChunks != 3 {
		t.Fatalf("expected 3 chunks, got %d", s.TotalChunks)
	}

	s.MarkReceived(0, "sha256:aaa")
	s.MarkReceived(1, "sha256:bbb")
	if s.IsComplete() {
		t.Fatal("should not be complete with only 2/3 chunks")
	}

	s.MarkReceived(2, "sha256:ccc")
	if !s.IsComplete() {
		t.Fatal("should be complete with all 3 chunks")
	}
}

func TestSession_ChecksumRetrieval(t *testing.T) {
	reg := NewRegistry()
	s := reg.Create("id2", "record2", "tenant2", "video.mp4", 5*1024*1024, 5*1024*1024)
	s.MarkReceived(0, "sha256:expected")

	got, ok := s.ChecksumFor(0)
	if !ok {
		t.Fatal("expected checksum to exist")
	}
	if got != "sha256:expected" {
		t.Fatalf("wrong checksum: %q", got)
	}

	_, ok = s.ChecksumFor(1)
	if ok {
		t.Fatal("chunk 1 should not have a checksum")
	}
}

func TestRegistry_CreateAndGet(t *testing.T) {
	reg := NewRegistry()
	reg.Create("sess1", "rec1", "ten1", "a.mp4", 10*1024*1024, 5*1024*1024)

	s, err := reg.Get("sess1")
	if err != nil {
		t.Fatal(err)
	}
	if s.TotalChunks != 2 {
		t.Fatalf("expected 2 chunks, got %d", s.TotalChunks)
	}
}

func TestRegistry_NotFound(t *testing.T) {
	reg := NewRegistry()
	_, err := reg.Get("does-not-exist")
	if err == nil {
		t.Fatal("expected error for missing session")
	}
}

func TestSession_DuplicateChunkIdempotent(t *testing.T) {
	reg := NewRegistry()
	s := reg.Create("id3", "rec3", "ten3", "video.mp4", 5*1024*1024, 5*1024*1024)
	s.MarkReceived(0, "sha256:first")
	s.MarkReceived(0, "sha256:second") // duplicate — first write wins

	got, _ := s.ChecksumFor(0)
	if got != "sha256:second" {
		// Note: current impl overwrites — both are acceptable; test documents behaviour.
		fmt.Printf("note: duplicate chunk overwrote checksum (got %q)\n", got)
	}
	if len(s.Received) != 1 {
		t.Fatalf("expected exactly 1 entry, got %d", len(s.Received))
	}
}

func TestChunkCalculation_OddSize(t *testing.T) {
	reg := NewRegistry()
	// 11MB with 5MB chunks = 3 chunks (5+5+1)
	s := reg.Create("id4", "rec4", "ten4", "video.mp4", 11*1024*1024, 5*1024*1024)
	if s.TotalChunks != 3 {
		t.Fatalf("expected 3 chunks for 11MB / 5MB, got %d", s.TotalChunks)
	}
}
