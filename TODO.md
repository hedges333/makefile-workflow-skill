# Synthetic Scars Backlog (TODO)

This document tracks general coding guidelines and synthetic scars derived from operational post-mortems and pair-programming experience, to be codified into `skills/makefile-workflow/references/09_synthetic_scars_catalog.md` and related reference manuals.

Plan comprehensive tests with reasonable balance for performance and dependency burden.

---

## Batch 1: Process & Test Discipline Scars

- [x] **SCAR-PROC-104: Review Before Edit, Minimal Confident Edits, and Targeted Test Loops**
  - **Wound**: An agent makes broad, speculative edits across unreviewed files or methods, introduces silent regressions in adjacent code, and gets stuck in sprawling test failure cascades.
  - **Trap**: Attempting to fix problems across multiple sections at once instead of reading target files first, making small confident edits, and iterating on targeted tests.
  - **Permanent Reflex**: Read target files and their type contracts before editing. Apply minimal, high-confidence diffs strictly within ticket scope. Run targeted tests in tight loops (`pytest path/to/test.py::test_name -v -x`) until green, leaving unrelated defects for future tickets, and run the full test suite only after the targeted test passes.

- [x] **SCAR-TEST-08: Two-Tier Test Isolation (Hermetic Unit vs Integration Fixtures)**
  - **Wound**: An unprivileged test runner or CI container fails session-level database DDL or network initialization in a root fixture, causing the entire test suite to crash before running any pure unit tests.
  - **Trap**: Attaching database connections, socket initialization, or schema migrations to global `autouse=True` session fixtures instead of isolating them behind explicit markers.
  - **Permanent Reflex**: Partition test suites into two tiers: Tier 1 hermetic unit tests with zero external daemon/socket dependencies (mocked, fast, least-privilege), and Tier 2 marked integration tests (`@pytest.mark.integration`) that verify external dependencies during pre-flight.

- [x] **SCAR-TEST-09: Fail-Fast Targeted TDD Loop (`pytest -x -v`)**
  - **Wound**: Running a large test suite during active debugging generates hundreds of cascading tracebacks, exhausting context limits and obscuring the initial defect.
  - **Trap**: Running broad test suites without fail-fast flags while attempting to iterate on a single failing test.
  - **Permanent Reflex**: Use fail-fast flags (`pytest -x -v`) during active Red-Green TDD cycles. Iterate exclusively on the targeted failing test until green before running the full regression suite.

- [x] **SCAR-TEST-10: Pre-Flight Structural Static Analysis Gate**
  - **Wound**: Code changes with syntax errors, undefined variables, or invalid imports fail deep inside execution or integration tests after consuming time and tokens.
  - **Trap**: Relying exclusively on runtime test execution to detect static syntax or import defects in un-executed code branches.
  - **Permanent Reflex**: Run structural static analysis (e.g. `flake8 --select=E9,F63,F7,F82` or compiler checks) as an immediate pre-flight step before running functional test suites.

---

## Batch 2: Operating System, Filesystem & Process Scars

- [x] **SCAR-SYS-05: Cross-User File Promotion (`shutil.copyfile` over `copy2` / `copystat`)**
  - **Wound**: Promoting or syncing files across service accounts or system users crashes with `[Errno 1] EPERM`.
  - **Trap**: Assuming standard library helpers like `shutil.copy2` or `shutil.copytree` are safe across user boundaries; they invoke `copystat` (`chmod`/`utime`), which requires ownership privileges.
  - **Permanent Reflex**: When copying across system users or daemons, copy file contents only (`shutil.copyfile`) or create destination directories with caller permissions rather than copying permission bits and ownership.

- [x] **SCAR-SYS-06: Native Runtime Environment Path Pre-Flight (`TMPDIR`)**
  - **Wound**: Compiled C/C++ libraries, GPU runtimes, or native database drivers crash with a silent segmentation fault during startup without a Python stack trace.
  - **Trap**: Assuming native compiled extensions validate paths in environment variables like `TMPDIR` or `CACHE_DIR` and raise clean exceptions.
  - **Permanent Reflex**: Verify that target cache and temporary directories exist and are writable before launching processes that initialize native compiled runtimes.

- [ ] **SCAR-SYS-07: POSIX Signal Trapping for Long-Running Workers (`SIGTERM` / `SIGINT`)**
  - **Wound**: Stopping a service or background job leaves orphaned lock files, partially written data, or dangling database transactions.
  - **Trap**: Relying on default operating system process killing without handling POSIX termination signals.
  - **Permanent Reflex**: Register explicit handlers for `SIGTERM` and `SIGINT` in long-running batch workers or daemons to complete the active atomic unit of work, flush buffers, and clean up lock files before exiting.

---

## Batch 3: Database & Ledger Scars

- [ ] **SCAR-DATA-10: Immutable Audit Ledger Preservation (`ON DELETE SET NULL` over `CASCADE`)**
  - **Wound**: Purging an entity from a parent lookup table cascades and silently deletes historical transaction ledgers, audit logs, or financial events.
  - **Trap**: Applying `ON DELETE CASCADE` uniformly across all relational foreign keys without distinguishing mutable state from immutable event logs.
  - **Permanent Reflex**: For historical event ledgers or audit tables, use `ON DELETE SET NULL` (or disallow foreign key deletion entirely) and store a denormalized natural key/identifier so historical records survive entity purges.

- [ ] **SCAR-DATA-11: Numeric Type Coercion on Database Aggregates and Decimals**
  - **Wound**: Mathematical calculations fail at runtime with `TypeError: unsupported operand type(s)` when mixing database aggregate or decimal return values with native floats.
  - **Trap**: Assuming database client libraries return native float or int primitives from `SUM()`, `AVG()`, or `DECIMAL` column queries.
  - **Permanent Reflex**: Explicitly cast database aggregate and decimal return values to standard numeric primitives (`float()` or `int()`) before performing arithmetic with native types.

- [ ] **SCAR-DATA-12: Nullability over Sentinel Dummy Values ("Organic Bootstrapping")**
  - **Wound**: Downstream calculations or analytics treat placeholder numbers (like `0.0`, `-1`, or `0.5`) as true measurements, corrupting model training or business metrics.
  - **Trap**: Storing arbitrary placeholder numbers in numeric columns to satisfy schema constraints for uncalculated or immature records.
  - **Permanent Reflex**: Store uncalculated or pending states strictly as `NULL` or `None`. Let downstream consumers handle null values explicitly.

- [ ] **SCAR-DATA-13: Application High-Watermarks vs Database Filter Thrashing**
  - **Wound**: A batch pipeline spends hours computing duplicate data, only for database `INSERT IGNORE` or unique indexes to drop 99% of the output.
  - **Trap**: Relying on database unique constraints as the main filter for whether work needs to be performed.
  - **Permanent Reflex**: Maintain high-watermark cursors or dirty queues in the application layer so batch pipelines only process genuinely new or modified entities.

---

## Batch 4: Architecture & Defensive Execution Scars

- [ ] **SCAR-ARCH-05: Testable Object-Oriented Script Template (BaseScript Pattern)**
  - **Wound**: Procedural CLI scripts with large `if __name__ == '__main__':` blocks cannot be unit-tested in memory without spawning subprocesses or modifying global state.
  - **Trap**: Writing procedural script files that pass long argument lists through helper functions.
  - **Permanent Reflex**: Encapsulate script logic in testable class objects that manage locks, database sessions, and fatal exception trapping. Keep executable CLI scripts to thin two-line wrappers (`ScriptClass().execute()`).

- [ ] **SCAR-ARCH-06: Defensive Range Clamping and Sanity Envelopes Before External Calls**
  - **Wound**: A calculation defect passes a 10x or negative value to an external API or storage subsystem, causing severe side effects.
  - **Trap**: Passing calculated outputs directly to external APIs without asserting plausible bounds.
  - **Permanent Reflex**: Apply explicit range checks and sanity bounds to calculated numbers before sending requests to external or irreversible APIs.

---

## Batch 5: Comprehensive Tests for Previously Implemented Scars

- [ ] **TEST-SCAR-PROC-95: Comprehensive Test for Depth-0 Supervisor & Subagent Isolation**
  - Verify that `test_cross_agent_compatibility.py` validates that orchestrator rules mandate Depth-0 delegation for searches, TDD, and CI polling, keeping the orchestrator context compact.

- [ ] **TEST-SCAR-PROC-102: Comprehensive Test for Human Declaration Authority & Gate Invariants**
  - Assert that all six human pause gates (Targets 20, 42, 45, 50, 60, 75) are present in `rules/AGENTS.md`, `SKILL.md`, `09_synthetic_scars_catalog.md`, and all adapters, and that agent self-declaration is strictly prohibited.

- [ ] **TEST-SCAR-PROC-103: Comprehensive Test for Plan Artifact Demotion & Lifecycle Invariants**
  - Verify that `test_cross_agent_compatibility.py` validates single-file `<brain>/plan.md` mirroring, built-in tool demotion (`UserFacing: false`), prohibition of shell `rm` commands, and reliance on `.workflow/state/20_plan_approved.md`.

- [ ] **TEST-SCAR-GIT-20: Comprehensive Test for Pre-Push Merge-Tree Verification**
  - Assert that Target 60 documentation and pre-push hooks mandate `git fetch origin main` and `git merge-tree $(git merge-base HEAD origin/main) HEAD origin/main` to detect merge conflicts prior to push.

- [ ] **TEST-SCAR-GIT-30: Comprehensive Behavioral Test for Pure Git Mode Fallback**
  - Implement a mock test verifying that when `gh` is unauthenticated or missing, Target 15 selects Pure Git Mode, Target 60 skips PR creation, Target 70 runs local tests, Target 75 presents local landing readiness, and Target 80 executes local squash merge.

- [ ] **TEST-SCAR-HCI-08: Comprehensive Test for Multi-Choice Prompt Rules ($N \ge 2$ vs $N = 1$)**
  - Assert that rule manuals and adapters instruct calling `ask_question` only when $N \ge 2$, and require chat proposals with `file://` links and tool halts when $N = 1$.

- [ ] **TEST-SCAR-TEST-05: Comprehensive Test for Database Isolation & SQLite In-Memory Mock Fallback**
  - Expand test coverage beyond command string blocks: verify that `SCAR-TEST-05` is documented across all rule files, and implement a lightweight SQLite in-memory test harness demonstrating isolated test database fallback (skipping gracefully if `sqlite3` is unavailable).

- [ ] **TEST-SCAR-TOOL-07: Comprehensive Behavioral Test for Dart Scratch Script Priority Rules**
  - Expand `test_cross_agent_compatibility.py` to verify that `rules/AGENTS.md`, `references/10_security_and_data_isolation.md`, and adapters consistently mandate preferring installed Dart over Python, never attempting to install Dart, and writing complex shell scripts to temporary files.

---

## Further research

- [ ] **Polyglot Expansion:** 
  - Analyze whether polyglot files for the following legacy languages, application scripting languages, and data languages would be useful to add to the project:
    - Bash
    - COBOL
    - Fortran
    - PL/SQL
    - Specialized SQL dialects like Snowflake, Cortex AISQL, Databricks, Spark
    - Visual Basic/VB6/VBA
    - Pascal/Delphi
    - Ada
    - Lisp/Scheme
    - Objective-C
    - REXX
    - RPG
    - MATLAB/Simulink
    - VHDL/Verilog
    - Other circuit hardware design languages?
    - Google Apps Script
    - LibreOffice Basic
    - Haskell (Generic)
    - Haskell/EDSL Copilot/Ogma (NASA-specific)
    - GraphQL
    - Legacy Hadoop/Pig/Hive/MapR
    - MQL/MongoDB 
    - MarkLogic/CTS/Xquery/Optic
    - Neo4j/Cypher
    - Gremlin (Amazon Neptune / Apache TinkerPop)
    - CQL (Apache Cassandra/ScyllaDB)
    - InfluxDB
    - KQL (Kusto)
    - SPL (Splunk)
    - LogQL/PromQL (Grafana/Prometheus)
    - Query DSL (ElasticSearch/Opensearch)
    - Google Malloy

- [ ] **Language-specific scars:**
  - For each of the languages in `./skills/makefile-workflow/references/polyglot`, research common pitfalls and traps in that language, and pre-emptively add language-specific scars to the polyglot language MD file.  These could be under a format like 'LANG-SCAR-{language name}-{number}'.

- [ ] **Documentation framework:**
  - Are there code documentation standards that could be applied as part of Pillar 6 to direct the agent to document code in a standardized way, which can then be assembled in a code documentation tree by some documentation utility for the project being worked on?
