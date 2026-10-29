# Claude Code Guidelines: Makefile Workflow

This project uses the Makefile Workflow. Follow this disciplined lifecycle on every ticket.

## Core Rules

1. **State Persistence**: Read active state cards from `.workflow/state/*.md` in lexical order (`cat .workflow/state/*.md`). Never forget the active target. Each project repository maintains its own isolated `.workflow/state/` directory.
2. **Feature Branching**: Before writing code, verify that `git status --short` is clean on `main`, then create a branch: `git checkout -b ticket/<id>-<slug>`.
3. **Review Before Edit**: Inspect the target files before editing. Apply small, confident edits. Do not refactor unrelated files.
4. **Hermetic Test Isolation**: Never use production databases or production files in tests. Use `*_test` databases, in-memory instances, or mocks.
5. **Red-Green TDD**: Write failing tests before writing implementation code. Run targeted tests in the subproject directory during development.
6. **Mandatory Pause Gates**: You must stop and wait for user approval at:
   - **Target 20**: Plan approval (especially if existing tests change).
   - **Target 42**: Blocker triage (if review catches issues).
   - **Target 45**: Review sign-off.
   - **Target 50**: Commit approval.
   - **Target 60**: Push approval.
   - **Target 75**: PR merge and landing approval.
7. **Monorepo Tests**: Run targeted tests during Target 30. Run the full suite across all subprojects at Target 50 and Target 75.
8. **Simple English**: Write PR descriptions, commit messages, and documentation in plain English with short sentences and active voice.
9. **Workflow Configuration**: Check `.workflow/config.json` or `~/.gemini/config/makefile-workflow.json` if present for user settings and model preferences.
10. **Targeted Model Selection**:
    - For fast worker operations: Use default session model (e.g. `claude-3-5-sonnet-20241022`).
    - For Target 40 (Adversarial Review): Use high-reasoning model (e.g. `claude -p --model claude-3-opus-20240229 "Run Six-Pillar review..."`).

## Target Cheat Sheet

- `T00`: Read state files.
- `T10`: Claim ticket, create branch.
- `T15`: Archaeology, detect languages, build Belnap ledger (`ESTABLISHED`, `CONTRADICTED`, `UNKNOWN`, `RETRACTED`).
- `T20`: Write plan, declare test modifications, wait for plan approval.
- `T30`: TDD Red-Green-Refactor, run targeted tests.
- `T40`: Six Pillars code review (Intent, Verification, Architecture, Blast Radius, Reviewer Defense, Immune Defenses).
- `T42`: Blocker triage gate (if blockers exist).
- `T45`: Review approval gate (0 blockers).
- `T50`: Pre-commit check, full test run, wait for commit approval, commit atomically.
- `T60`: Verify mergeability (`git merge-tree`), push branch, open PR.
- `T70`: Poll CI and bots (180s quiescence), triage feedback.
- `T75`: Policy check, wait for landing approval.
- `T80`: Squash-merge PR, delete branch, pull default branch.
- `T90`: Codify scars, append to `.workflow/history.json` and `.workflow/history.md`, finish.
