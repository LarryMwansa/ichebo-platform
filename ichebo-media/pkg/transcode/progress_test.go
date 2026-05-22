package transcode

import (
	"strings"
	"testing"
)

func TestParseFFmpegProgress_EmitsPercentages(t *testing.T) {
	// Simulate ffmpeg -progress pipe:2 output for a 100-second video.
	// out_time_ms is in microseconds.
	input := strings.NewReader(
		"out_time_ms=10000000\n" + // 10s → 10%
			"frame=250\n" + // ignored
			"out_time_ms=50000000\n" + // 50s → 50%
			"out_time_ms=90000000\n" + // 90s → 90%
			"progress=end\n",
	)

	var got []int
	for pct := range parseFFmpegProgress(input, 100) {
		got = append(got, pct)
	}

	if len(got) != 3 {
		t.Fatalf("expected 3 progress values, got %d: %v", len(got), got)
	}
	if got[0] != 10 {
		t.Errorf("first value: want 10, got %d", got[0])
	}
	if got[1] != 50 {
		t.Errorf("second value: want 50, got %d", got[1])
	}
	if got[2] != 90 {
		t.Errorf("third value: want 90, got %d", got[2])
	}
}

func TestParseFFmpegProgress_NeverEmits100(t *testing.T) {
	// At exactly total duration the value should be clamped to 99 —
	// the caller emits 100 after cmd.Wait() returns.
	input := strings.NewReader("out_time_ms=100000000\n") // exactly 100s
	var got []int
	for pct := range parseFFmpegProgress(input, 100) {
		got = append(got, pct)
	}
	for _, v := range got {
		if v >= 100 {
			t.Errorf("progress emitted %d — must never reach 100 from the parser", v)
		}
	}
}

func TestParseFFmpegProgress_ZeroDuration_Silent(t *testing.T) {
	// When totalSeconds == 0, channel closes without emitting anything.
	input := strings.NewReader("out_time_ms=50000000\n")
	var got []int
	for pct := range parseFFmpegProgress(input, 0) {
		got = append(got, pct)
	}
	if len(got) != 0 {
		t.Errorf("expected no values when totalSeconds==0, got %v", got)
	}
}

func TestParseFFmpegProgress_IgnoresNonTimeLines(t *testing.T) {
	input := strings.NewReader(
		"frame=100\n" +
			"fps=25.0\n" +
			"bitrate=2000kbits/s\n" +
			"out_time_ms=25000000\n" + // 25s of 100 → 25%
			"speed=1.0x\n",
	)
	var got []int
	for pct := range parseFFmpegProgress(input, 100) {
		got = append(got, pct)
	}
	if len(got) != 1 || got[0] != 25 {
		t.Errorf("expected [25], got %v", got)
	}
}
