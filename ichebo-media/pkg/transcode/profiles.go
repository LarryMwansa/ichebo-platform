package transcode

// QualityProfile defines FFmpeg encoding parameters for one output quality.
type QualityProfile struct {
	Name         string
	Width        int
	Height       int
	VideoBitrate string
	AudioBitrate string
}

// DefaultProfiles are the standard Ichebo Media quality outputs (highest to lowest).
var DefaultProfiles = []QualityProfile{
	{Name: "1080p", Width: 1920, Height: 1080, VideoBitrate: "4M", AudioBitrate: "192k"},
	{Name: "720p", Width: 1280, Height: 720, VideoBitrate: "2M", AudioBitrate: "128k"},
	{Name: "480p", Width: 854, Height: 480, VideoBitrate: "1M", AudioBitrate: "96k"},
	{Name: "360p", Width: 640, Height: 360, VideoBitrate: "600k", AudioBitrate: "64k"},
	{Name: "audio", Width: 0, Height: 0, VideoBitrate: "", AudioBitrate: "128k"},
}

// ProfileByName returns the profile matching the given name, or false if not found.
func ProfileByName(name string) (QualityProfile, bool) {
	for _, p := range DefaultProfiles {
		if p.Name == name {
			return p, true
		}
	}
	return QualityProfile{}, false
}

// FFmpegVideoArgs returns the FFmpeg arguments for this profile's video+audio encoding.
// For the "audio" profile, video stream is disabled.
func (p QualityProfile) FFmpegVideoArgs() []string {
	if p.Name == "audio" {
		return []string{
			"-vn",
			"-c:a", "aac",
			"-b:a", p.AudioBitrate,
		}
	}
	return []string{
		"-vf", "scale=" + itoa(p.Width) + ":" + itoa(p.Height),
		"-c:v", "libx264",
		"-b:v", p.VideoBitrate,
		"-c:a", "aac",
		"-b:a", p.AudioBitrate,
		"-preset", "fast",
	}
}

func itoa(n int) string {
	if n <= 0 {
		return "0"
	}
	s := ""
	for n > 0 {
		s = string(rune('0'+n%10)) + s
		n /= 10
	}
	return s
}
