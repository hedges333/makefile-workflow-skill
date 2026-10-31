# 03. TDD and Code Quality Protocol (`Target 30`)

This manual covers test-driven development (TDD, writing tests before production code), small edits, and documentation updates.

## 1. Review Before Edit (`SCAR-PROC-104`)

Follow three rules before you modify any source file:

1. Read the file, its imports, its type signatures, and its comments first (`SCAR-PROC-104`).
2. Make minimal, confident edits that solve the ticket. Do not rewrite an entire module when a three-line fix works.
3. Leave unrelated defects or style issues untouched, and note them for a separate ticket.

## 2. Red-Green-Refactor TDD Loop

Execute every code change in three ordered phases.

### Phase 1: Red (Failing Test First)

1. Write unit tests from the Given-When-Then scenarios created in Target 15.
2. If the subproject has no test files, create the smoke test approved in Target 20 first.
3. Run the targeted subproject test command and make sure that the new test fails (`red_exit != 0`).
4. Never write feature code before watching the test fail. A test that passes before code changes proves nothing.

### Phase 2: Green (Minimal Production Code)

1. Write the smallest production code change that makes the failing test pass.
2. Follow [`14_design_patterns_and_architecture.md`](./14_design_patterns_and_architecture.md): favor object composition over deep inheritance, and apply Game Programming Patterns in game subprojects.
3. Balance encapsulation with speed: use an ORM (a library that maps database rows to objects) by default, and place parameterized SQL or NoSQL queries inside repositories for large datasets.
4. Run the targeted subproject test command and make sure that all targeted tests pass (`green_exit == 0`).

### Phase 3: Refactor

1. Remove duplicate logic and keep function interfaces clear.
2. Run the code formatter and linter on the modified files.
3. Re-run the targeted test command to make sure that tests stay green.

## 3. Targeted Subproject Test Loops (`SCAR-PROC-104`, `SCAR-TEST-09`)

In repositories with multiple subprojects (for example `backend/`, `frontend/`, and `scripts/`), keep inner loops fast:

1. Run tests only inside the modified subproject directory during Target 30 (`SCAR-PROC-104`).
2. Run targeted tests in tight loops with fail-fast flags (`pytest path/to/test.py::test_name -v -x` or script equivalent) until green (`SCAR-TEST-09`).
3. Save the full repository test sweep for Target 50 before commit.

## 4. Concentric Documentation Rings (`SCAR-DOC-16`)

Update documentation alongside code across four rings:

- Ring 1 (Inline Code): Update docstrings, parameter descriptions, and return types in modified files.
- Ring 2 (Subproject README): Update module README files when public contracts change.
- Ring 3 (Guides and Examples): Update usage examples when flags or APIs change.
- Ring 4 (Changelogs): Add an entry under the unreleased section of `CHANGELOG.md` when the project maintains one.

When targeted tests and docs are complete, update `.workflow/state/99_next_action.md` and advance to Target 40.
