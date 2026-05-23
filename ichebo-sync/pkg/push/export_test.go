package push

import "github.com/ichebo/sync/pkg/changelog"

// BatchEntries exports the unexported batchEntries function for tests.
var BatchEntries = func(entries []changelog.Entry, size int) [][]changelog.Entry {
	return batchEntries(entries, size)
}
