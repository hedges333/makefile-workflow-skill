# Polyglot Stack Guide: SQL and Database Migrations

This guide covers detection markers, lint and test commands, smoke test templates, and database safety rules for SQL migrations.

## 1. Detection Markers

Look for these files and directories when scanning a SQL project:

- `flyway.conf`, `liquibase.properties`, `dbt_project.yml`, `migrations/`, `schema.sql`, `*.sql`

## 2. Standard Commands

Run these commands against isolated test databases only:

- Lint: `sqlfluff lint --dialect <dialect> <path>`
- Format: `sqlfluff format --dialect <dialect> <path>`
- Targeted Test: `pg_prove -U postgres -d <app>_test tests/*.sql` or `dbt test --select <model>`

## 3. Smoke Test Template

If no schema test exists, create `tests/test_schema.sql`:

```sql
-- Schema Smoke Test
BEGIN;
SELECT plan(1);

SELECT has_table('schema_migrations');

SELECT * FROM finish();
ROLLBACK;
```

## 4. Database Isolation and Query Performance Rules

Follow five mandatory rules in SQL and NoSQL projects:

1. Never run `flyway migrate`, `liquibase update`, or `dbt run` against staging or production database hosts.
2. Point every migration test to a local Docker container, a database named `<app>_test`, or a target listed in `database.testDatabases` inside `.workflow/config.json`.
3. Declare custom live database names and hosts in `.workflow/config.json` or `MAKEFILE_WORKFLOW_PROD_DBS`. If live versus test database names are unclear at Target 15, ask the user.
4. Wrap SQL test scripts in `BEGIN` and `ROLLBACK` statements so zero test rows persist.
5. Use an ORM (a library that maps database rows to objects) for standard single-record access. If large datasets outgrow the ORM, encapsulate parameterized SQL or NoSQL queries behind repository methods.
