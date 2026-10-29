# 11. Polyglot Monorepo Orchestration

This manual details how to detect and orchestrate repositories containing multiple programming languages and subprojects.

## 1. Subproject Discovery (Target 15)

In complex repositories (for example, a Rust backend, a TypeScript frontend, and Python maintenance scripts), the Archaeology Worker inspects directory trees for manifest markers:

* **Rust**: `Cargo.toml`
* **TypeScript / JavaScript**: `package.json`, `tsconfig.json`
* **Python**: `pyproject.toml`, `requirements.txt`, `setup.py`
* **Go**: `go.mod`
* **Dart / Flutter**: `pubspec.yaml`
* **PHP**: `composer.json`
* **Java / Kotlin / Scala**: `pom.xml`, `build.gradle`, `build.sbt`
* **C / C++**: `CMakeLists.txt`, `meson.build`, `Makefile`
* **Elixir**: `mix.exs`
* **Perl**: `Makefile.PL`, `cpanfile`
* **C# (.NET)**: `*.csproj`, `*.sln`
* **PowerShell**: `*.psd1`, `*.psm1`
* **Swift**: `Package.swift`
* **Ruby**: `Gemfile`
* **SQL & Migrations**: `flyway.conf`, `dbt_project.yml`, `migrations/`
* **R / Julia / Lua**: `DESCRIPTION`, `Project.toml`, `*.rockspec`

When multiple markers exist in different folders, compile a **Subproject Manifest** in `.workflow/state/15_archaeology_receipt.md`:
- Subproject name and relative path.
- Language and runtime.
- Targeted unit test command.
- Linter and formatter commands.
- Test database isolation requirement.

## 2. Directory Layout Standardization

If a repository has multiple languages scattered in the root directory without clean folder boundaries:
1. Identify the structural confusion during Target 15 Archaeology.
2. In Target 20 (`plan.md`), propose organizing files into standardized subproject directories (e.g. `backend/`, `frontend/`, `scripts/`).
3. **Never move files unilaterally**. Wait for explicit user approval in the plan before moving files.

## 3. Targeted Inner Loops vs Full Outer Sweeps

### The Inner Loop (Target 30: Implementation)
Run tests only in the touched subproject directory:
- If editing `backend/` (Rust), run `cargo test --package backend`.
- If editing `scripts/` (Python), run `pytest scripts/`.
- If editing `frontend/` (TypeScript), run `npm test --prefix frontend`.
This keeps the test-edit feedback cycle fast (under 10 seconds).

### The Outer Loop (Target 50 Commit & Target 75 Landing)
Run the full regression test suite across all detected subprojects before asking the human for commit approval or landing approval. This guarantees that a change in the backend did not break contract assumptions in the frontend or utility scripts.
