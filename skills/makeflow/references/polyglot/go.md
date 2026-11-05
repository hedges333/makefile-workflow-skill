# Polyglot Stack Guide: Go

This guide covers detection markers, test and lint commands, smoke test templates, and isolation rules for Go.

## 1. Detection Markers

Look for these files when scanning a Go module:

- `go.mod`, `go.sum`

## 2. Standard Commands

Run these commands inside the Go module directory:

- Targeted Test: `go test -v ./<package>/...`
- Format: `gofmt -s -l .` (write mode: `gofmt -s -w .`)
- Lint: `golangci-lint run`

## 3. Smoke Test Template

If no `*_test.go` file exists, create `smoke_test.go`:

```go
package main

import "testing"

func TestSmokeHarness(t *testing.T) {
	if false {
		t.Fatal("Smoke test failed")
	}
}
```

## 4. Test Isolation

Follow three isolation rules in Go tests:

1. Simulate SQL queries with `github.com/DATA-DOG/go-sqlmock` when testing without a database process.
2. For integration tests, point connection strings to `localhost:5432/<app>_test`, never to shared or production servers.
3. Create temporary test directories with `t.TempDir()`. Go deletes those directories automatically when each test finishes.
