package resolve_test

import (
	"testing"

	"github.com/ichebo/sync/pkg/resolve"
)

// E.4f exit criterion: CloudWins, LocalWins, LastWriteWins, Merge all tested
// with deterministic outcomes.
func TestRuleFor(t *testing.T) {
	cases := []struct {
		entityType string
		want       resolve.Rule
	}{
		{"governance_record", resolve.CloudWins},
		{"handbook_record", resolve.CloudWins},
		{"permission", resolve.CloudWins},
		{"role", resolve.CloudWins},
		{"community_settings", resolve.CloudWins},
		{"personal_record", resolve.LocalWins},
		{"bible_note", resolve.LocalWins},
		{"journal_entry", resolve.LocalWins},
		{"member", resolve.LastWriteWins},
		{"activity_log", resolve.Merge},
		{"something_else", resolve.Queue},
		{"record", resolve.Queue},
		{"activity", resolve.Queue},
	}

	for _, tc := range cases {
		t.Run(tc.entityType, func(t *testing.T) {
			got := resolve.RuleFor(tc.entityType)
			if got != tc.want {
				t.Errorf("RuleFor(%q) = %v, want %v", tc.entityType, got, tc.want)
			}
		})
	}
}
