//go:build cgo

package main

// main is required by -buildmode=c-shared. The entry point is unused;
// the exported C functions in bridge.go are the public API.
func main() {}
