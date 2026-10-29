# Polyglot Stack Guide: Go

This manual details toolchains, test scaffolding, and isolation conventions for Go.

## 1. Detection Markers
- `go.mod`, `go.sum`

## 2. Standard Commands
- **Targeted Test**: `go test -v ./<package>/...`
- **Format**: `gofmt -s -l .` (write: `gofmt -s -w .`)
- **Lint**: `golangci-lint run`

## 3. Boilerplate Test Scaffolding
If no test exists, create `smoke_test.go`:
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
1. Use `github.com/DATA-DOG/go-sqlmock` to simulate database connections without live databases.
2. For integration tests, read database credentials from environment variables defaulting to `localhost:5432/<app>_test`.
3. Use `t.TempDir()` for all file operations in tests; Go automatically deletes temporary directories when tests finish.
