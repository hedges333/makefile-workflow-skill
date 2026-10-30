# 11. Polyglot Monorepo Orchestration

This manual explains how to scan and test repositories that contain multiple programming languages and subprojects.

## 1. Subproject Discovery (Target 15)

In multi-language repositories (for example a Rust backend, a TypeScript web client, and Python scripts), `archaeology-worker` searches for manifest files:

- Rust: `Cargo.toml`
- TypeScript and JavaScript: `package.json`, `tsconfig.json`
- Python: `pyproject.toml`, `requirements.txt`, `setup.py`
- Go: `go.mod`
- Dart and Flutter: `pubspec.yaml`
- PHP: `composer.json`
- Java, Kotlin, and Scala: `pom.xml`, `build.gradle`, `build.gradle.kts`, `build.sbt`
- C and C++: `CMakeLists.txt`, `meson.build`, `Makefile`
- Elixir: `mix.exs`
- Perl: `Makefile.PL`, `cpanfile`
- C# (.NET): `*.csproj`, `*.sln`
- PowerShell: `*.psd1`, `*.psm1`
- Swift: `Package.swift`
- Ruby: `Gemfile`
- SQL and Migrations: `flyway.conf`, `dbt_project.yml`, `migrations/`
- R, Julia, and Lua: `DESCRIPTION`, `Project.toml`, `*.rockspec`

When manifests appear in multiple directories, record a subproject table in `.workflow/state/15_archaeology_receipt.md` with five fields:

1. Subproject name and relative directory path.
2. Language and runtime version.
3. Targeted unit test command.
4. Formatter and linter commands.
5. Test database isolation method.

## 2. Directory Layout Rules

If a repository mixes multiple languages in the root directory without clear boundaries, handle layout changes with user approval:

1. Note the mixed layout in `.workflow/state/15_archaeology_receipt.md` during Target 15.
2. If moving files helps the ticket, propose clear subproject directories (for example `backend/`, `frontend/`, `scripts/`) in `.workflow/state/20_plan.md`.
3. Never move directories without explicit user approval at Target 20.

## 3. Inner Test Loops vs Full Test Sweeps

### Inner Loop (Target 30 Implementation)

Run unit tests only inside the subproject directory that you edited:

- Rust in `backend/`: `cargo test --package backend`
- Python in `scripts/`: `pytest scripts/`
- TypeScript in `frontend/`: `npm test --prefix frontend`

Targeted runs keep each Red-Green-Refactor cycle under ten seconds.

### Outer Sweep (Target 50 Commit and Target 75 Landing)

Run the full test suite across every subproject in the repository before asking for commit or landing approval. Full sweeps make sure that backend changes do not break frontend contracts or shared scripts.
