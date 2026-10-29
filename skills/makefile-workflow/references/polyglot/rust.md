# Polyglot Stack Guide: Rust

This manual details toolchains, test scaffolding, and isolation conventions for Rust.

## 1. Detection Markers
- `Cargo.toml`, `Cargo.lock`

## 2. Standard Commands
- **Targeted Test**: `cargo test -p <package>` or `cargo test --test <name>`
- **Format**: `cargo fmt -- --check`
- **Lint**: `cargo clippy --all-targets -- -D warnings`

## 3. Boilerplate Test Scaffolding
If no integration test exists, create `tests/smoke_test.rs`:
```rust
#[test]
fn test_smoke_harness() {
    assert!(true);
}
```

## 4. Test Isolation
1. For file operations, use the `tempfile` crate so directories are automatically deleted upon teardown.
2. Abstract database operations behind traits and mock them in unit tests.
3. For integration tests requiring real databases, use ephemeral containers via `testcontainers-rs` or SQLite in-memory connections.
