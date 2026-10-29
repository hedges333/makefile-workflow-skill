# Polyglot Stack Guide: SQL & Database Migrations

This manual details toolchains, schema validation, and strict isolation for SQL and database migration projects.

## 1. Detection Markers
- `flyway.conf`, `liquibase.properties`, `dbt_project.yml`, `migrations/`, `schema.sql`, `*.sql`

## 2. Standard Commands
- **Lint & Syntax**: `sqlfluff lint --dialect <dialect> <path>`
- **Format**: `sqlfluff format --dialect <dialect> <path>`
- **Targeted Test**: `pg_prove -U postgres -d <app>_test tests/*.sql` or `dbt test --select <model>`

## 3. Boilerplate Test Scaffolding
If no schema verification test exists, create `tests/test_schema.sql`:
```sql
-- Schema Smoke Test: Verify that basic metadata tables exist
BEGIN;
SELECT plan(1);

SELECT has_table('schema_migrations');

SELECT * FROM finish();
ROLLBACK;
```

## 4. Strict Isolation Rules
1. Never run migrations (`flyway migrate`, `liquibase update`, `dbt run`) against production database endpoints.
2. Require a dedicated local Docker container or an isolated database named `<app>_test`.
3. Wrap verification scripts in transactions (`BEGIN ... ROLLBACK`) so no test state persists.
