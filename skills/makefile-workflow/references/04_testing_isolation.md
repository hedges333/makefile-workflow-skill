# 04. Testing Isolation and Safe Environments

This manual defines the rules for hermetic tests (isolated tests with zero live dependencies) and production data safety.

## 1. Zero Production Data Rules

Automated tests must never connect to live systems:

1. Never point automated tests to live production databases or read production credentials.
2. Connect database tests to dedicated `*_test` databases, local Docker test containers, or in-memory engines such as SQLite `:memory:` and H2.
3. Wrap database test cases in transactions that roll back on exit when the framework supports it, for example Elixir `Ecto.Adapters.SQL.Sandbox`, `pytest`, or `rspec`.
4. Write test files inside temporary directories (for example `tempfile`, `t.TempDir()`, or mocked file systems), never in shared host paths.
5. Mock or stub all external HTTP APIs, payment gateways, authentication providers, and email services.

## 2. Pre-Test Environment Checks

Run four safety steps before you execute any test suite:

1. Make sure that the test environment variable is active, such as `NODE_ENV=test`, `RAILS_ENV=test`, or `APP_ENV=testing`.
2. Read `.workflow/config.json` (`database` section) or `MAKEFILE_WORKFLOW_*` environment variables for declared `prodDatabases`, `testDatabases`, and `prodHosts`.
3. Inspect the database connection string. If it names a cloud host, staging server, `prod` database, or configured `prodDatabases` entry, stop at once.
4. If live versus test database names remain unclear, ask the user before running tests. Never fall back to a shared or production database.
