# Polyglot Stack Guide: Rust

This guide covers detection markers, test and lint commands, smoke test templates, and isolation rules for Rust.

## 1. Detection Markers

Look for these files when scanning a Rust crate or workspace:

- `Cargo.toml`, `Cargo.lock`

## 2. Standard Commands

Run these commands inside the crate or workspace root:

- Targeted Test: `cargo test -p <package>` or `cargo test --test <name>`
- Format: `cargo fmt -- --check`
- Lint: `cargo clippy --all-targets -- -D warnings`

## 3. Smoke Test Template

If no integration test exists, create `tests/smoke_test.rs`:

```rust
#[test]
fn test_smoke_harness() {
    assert!(true);
}
```

## 4. Test Isolation

Follow three isolation rules in Rust tests:

1. Create temporary directories with the `tempfile` crate so Rust deletes them automatically on drop.
2. Place database access behind traits and pass mock implementations in unit tests.
3. For database integration tests, use SQLite in-memory connections or local containers through `testcontainers-rs`.
