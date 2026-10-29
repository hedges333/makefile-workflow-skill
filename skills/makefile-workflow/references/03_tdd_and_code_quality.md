# 03. TDD and Code Quality Protocol (`Target 30`)

This manual details Test-Driven Development (TDD), the review-before-edit principle, and concentric documentation rings.

## 1. Review Before Edit Principle

Before you modify any file:
1. **Read Existing Code**: Inspect the file, its imports, its type signatures, and its comments.
2. **Apply Small Confident Edits**: Make minimal surgical edits. Do not rewrite whole classes when a three-line change solves the problem.
3. **Ignore Out-of-Scope Code Smells**: If you notice unrelated typos or legacy patterns, do not edit them. Note them in ticket remarks for a future task.

## 2. Red-Green-Refactor TDD Protocol

Execute code changes through three strict phases:

### Phase 1: Red (Failing Test First)
1. Write unit tests that specify the new behavior or reproduce the reported bug. Translate the Gherkin scenarios from Target 15 directly into test assertions.
2. If no test files exist, create the boilerplate smoke test scaffold approved in Target 20.
3. Run the targeted test command. Verify that the test compiles, runs, and fails for the expected reason (`red_exit != 0`).
4. Never write code before witnessing a failing test. A test that passes before you write code is tautological (meaningless).

### Phase 2: Green (Minimal Implementation)
1. Write the minimal code needed to make the failing test pass.
2. Run the targeted test command.
3. Verify that all targeted tests pass cleanly (`green_exit == 0`).

### Phase 3: Refactor
1. Clean up logic and eliminate duplication.
2. Ensure clean separation of concerns and modular object interfaces.
3. Run the language formatter and linter on touched files.

## 3. Targeted Test Execution Loops

In repositories with multiple subprojects (e.g. backend, frontend, scripts):
1. Run tests only within the modified subproject folder during Target 30.
2. Do not run the entire monorepo test suite on every minor change. Save the full suite for Target 50 pre-commit.

## 4. Concentric Documentation Rings (`SCAR-DOC-16`)

Synchronize documentation alongside code changes across four rings:

* **Ring 1 (Inline Code)**: Update docstrings, parameter descriptions, and return types in source files.
* **Ring 2 (Subproject README)**: Update module README files if API contracts change.
* **Ring 3 (Guides & Examples)**: Update usage examples if public interfaces change.
* **Ring 4 (Changelogs)**: Add an entry to `CHANGELOG.md` under the unreleased section.

When all targeted tests pass, update `99_next_action.md` and chain to Target 40.
