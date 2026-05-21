package hls

import (
	"fmt"
	"strings"
	"testing"
)

func TestManifest_ContainsAllProfiles(t *testing.T) {
	manifest := BuildMasterManifest(StandardProfiles())

	for _, name := range []string{"1080p", "720p", "480p", "360p", "audio"} {
		if !strings.Contains(manifest, name+"/index.m3u8") {
			t.Errorf("manifest missing profile %q", name)
		}
	}
}

func TestManifest_StartsWithHeader(t *testing.T) {
	manifest := BuildMasterManifest(StandardProfiles())
	if !strings.HasPrefix(manifest, "#EXTM3U") {
		t.Error("manifest must start with #EXTM3U")
	}
	if !strings.Contains(manifest, "#EXT-X-VERSION:3") {
		t.Error("manifest must contain #EXT-X-VERSION:3")
	}
}

func TestManifest_BandwidthOrder(t *testing.T) {
	profiles := StandardProfiles()
	manifest := BuildMasterManifest(profiles)
	lines := strings.Split(manifest, "\n")

	var bandwidths []int
	for _, line := range lines {
		if strings.HasPrefix(line, "#EXT-X-STREAM-INF:") {
			var bw int
			fmt.Sscanf(line, "#EXT-X-STREAM-INF:BANDWIDTH=%d", &bw)
			bandwidths = append(bandwidths, bw)
		}
	}

	for i := 1; i < len(bandwidths); i++ {
		if bandwidths[i] > bandwidths[i-1] {
			t.Errorf("bandwidth not in descending order at index %d: %d > %d", i, bandwidths[i], bandwidths[i-1])
		}
	}
}

func TestManifest_AudioProfileNoResolution(t *testing.T) {
	profiles := []Profile{
		{Name: "audio", Width: 0, Height: 0, Bandwidth: 128_000},
	}
	manifest := BuildMasterManifest(profiles)
	if strings.Contains(manifest, "RESOLUTION=") {
		t.Error("audio profile should not include RESOLUTION in manifest")
	}
}

func TestManifest_VideoProfileHasResolution(t *testing.T) {
	profiles := []Profile{
		{Name: "720p", Width: 1280, Height: 720, Bandwidth: 2_000_000},
	}
	manifest := BuildMasterManifest(profiles)
	if !strings.Contains(manifest, "RESOLUTION=1280x720") {
		t.Error("video profile should include RESOLUTION")
	}
}
