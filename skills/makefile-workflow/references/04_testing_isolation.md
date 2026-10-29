# 04. Testing Isolation & Safe Environments

This manual details the rules for hermetic test execution and environment safety.

## 1. Zero Production Data Invariant

Test execution must never touch live systems.

1. **Production Databases Prohibited**:
   Never configure automated test runs to connect to production databases or read live production credentials.
2. **Dedicated Test Databases**:
   Tests that require database access must connect to dedicated test databases (such as `<app>_test`), ephemeral Docker test containers, or in-memory databases (e.g. SQLite `:memory:`, H2).
3. **Rollback Transactions**:
   Where supported (such as Elixir's `Ecto.Adapters.SQL.Sandbox` or database transaction rollbacks in pytest/rspec), wrap test cases in database transactions that roll back automatically upon test completion.
4. **Isolated File Paths**:
   File input/output operations in tests must use temporary scratch directories (such as `tmpdir`, `<brain>/scratch/`, or mocked file systems). Never write test output to the root repository or shared system paths.
5. **Mock External Networks**:
   All external HTTP endpoints, payment gateways, third-party authentication services, and email providers must be stubbed or mocked in tests.

## 2. Preventing Accidental Production Pollution

Before running any test command:
1. Verify that the active environment file is `.env.test` or that `NODE_ENV=test` / `RAILS_ENV=test` / `ENVIRONMENT=testing` is set.
2. Inspect the database connection string. If it points to an external host, cloud database, or production port, abort immediately.
3. If an integration test fails because a local test container is unavailable, report the requirement to the user. Never fall back to a shared or production database.
