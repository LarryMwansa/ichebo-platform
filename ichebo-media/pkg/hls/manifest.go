package hls

import (
	"fmt"
	"strings"
)

// Profile describes one quality variant for the master manifest.
type Profile struct {
	Name      string
	Width     int
	Height    int
	Bandwidth int // bits per second
}

// StandardProfiles returns the default Ichebo Media quality profiles ordered highest to lowest.
func StandardProfiles() []Profile {
	return []Profile{
		{Name: "1080p", Width: 1920, Height: 1080, Bandwidth: 4_000_000},
		{Name: "720p", Width: 1280, Height: 720, Bandwidth: 2_000_000},
		{Name: "480p", Width: 854, Height: 480, Bandwidth: 1_000_000},
		{Name: "360p", Width: 640, Height: 360, Bandwidth: 600_000},
		{Name: "audio", Width: 0, Height: 0, Bandwidth: 128_000},
	}
}

// BuildMasterManifest constructs an HLS master playlist (.m3u8) from the given profiles.
// Profiles must be ordered highest to lowest bandwidth.
func BuildMasterManifest(profiles []Profile) string {
	var sb strings.Builder
	sb.WriteString("#EXTM3U\n")
	sb.WriteString("#EXT-X-VERSION:3\n\n")
	for _, p := range profiles {
		if p.Name == "audio" {
			sb.WriteString(fmt.Sprintf("#EXT-X-STREAM-INF:BANDWIDTH=%d\n", p.Bandwidth))
		} else {
			sb.WriteString(fmt.Sprintf(
				"#EXT-X-STREAM-INF:BANDWIDTH=%d,RESOLUTION=%dx%d\n",
				p.Bandwidth, p.Width, p.Height,
			))
		}
		sb.WriteString(p.Name + "/index.m3u8\n\n")
	}
	return sb.String()
}
