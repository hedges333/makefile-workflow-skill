# Polyglot Stack Guide: Elixir

This manual details toolchains, test scaffolding, and database isolation for Elixir.

## 1. Detection Markers
- `mix.exs`, `mix.lock`

## 2. Standard Commands
- **Targeted Test**: `mix test <path_to_test>`
- **Format**: `mix format --check-formatted`
- **Lint**: `mix credo --strict`

## 3. Boilerplate Test Scaffolding
If no test exists, create `test/smoke_test.exs`:
```elixir
defmodule SmokeTest do
  use ExUnit.Case

  test "smoke test harness" do
    assert true
  end
end
```

## 4. Test Database Isolation
1. Always use `Ecto.Adapters.SQL.Sandbox` in tests. The sandbox wraps every test case in an isolated SQL transaction and rolls it back automatically.
2. In `config/test.exs`, ensure `database:` points to a test database (e.g. `<app>_test`).
3. Set `pool: Ecto.Adapters.SQL.Sandbox` to prevent database writes from leaking between test runs.
