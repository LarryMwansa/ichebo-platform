// Command syncd is the standalone sync daemon for development and testing.
// It accepts keyboard commands (s=sync now, q=quit) and outputs sync status.
//
// Usage:
//
//	syncd -db /path/to/local.sqlite -config /path/to/config.json
package main

import (
	"bufio"
	"flag"
	"fmt"
	"os"

	"github.com/ichebo/sync/pkg/status"
)

func main() {
	dbPath := flag.String("db", "ichebo.sqlite", "path to local SQLite database")
	flag.Parse()

	fmt.Printf("ichebo-sync daemon — db: %s\n", *dbPath)
	fmt.Println("Commands: s=sync now  q=quit")

	mon := status.New()
	mon.SetState(status.Offline)

	updates := mon.Subscribe()
	go func() {
		for u := range updates {
			fmt.Println(u.Message)
		}
	}()

	scanner := bufio.NewScanner(os.Stdin)
	for scanner.Scan() {
		switch scanner.Text() {
		case "s":
			fmt.Println("Sync requested...")
			mon.SetState(status.Syncing)
		case "q":
			fmt.Println("Shutting down.")
			return
		}
	}
}
