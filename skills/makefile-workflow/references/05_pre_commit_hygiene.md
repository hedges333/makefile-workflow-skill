# 05. Pre-Commit Hygiene & Git Commit Protocol (`Target 50`)

This manual details the pre-commit checks, full regression sweeps, and atomic git commit execution.

## 1. Pre-Commit Verification Steps

Before presenting a commit proposal to the user, run these verification steps under `set -euo pipefail`:

1. **Format Check**:
   Run the project code formatter to confirm zero unformatted files (e.g. `prettier --check`, `black --check`, `cargo fmt -- --check`, `gofmt -l`).
2. **Static Analysis & Linting**:
   Run workspace static analysis with fatal warnings enabled (e.g. `eslint`, `ruff check`, `cargo clippy`, `golangci-lint`).
3. **Full Monorepo Test Sweep**:
   Run the complete test suite across all detected subprojects in the repository. While Target 30 ran targeted tests in the active folder, Target 50 must confirm zero regressions across the whole repository.
4. **Two-Layer Drift Check**:
   Confirm that the working tree still matches `$APPROVED_TREE`:
   - Layer 1: Verify `git status --porcelain` has zero unstaged changes or untracked files.
   - Layer 2: Verify `test "$(git write-tree)" = "$APPROVED_TREE"`.

## 2. Commit Message Structure

Draft an atomic commit message following Conventional Commits (v1.0.0) with issue autoclose:
```text
<type>(<scope>): <short description> (closes #<ISSUE_ID>)

<longer explanation in Simple English: what changed and why>

Issue: #<ISSUE_ID>
Reviewed-by: adversarial-critic
Co-authored-by: <model_name> <agent@antigravity.google.com>
```

When targeting GitHub or GitLab, `closes #<ISSUE_ID>` or `fixes #<ISSUE_ID>` automatically links and closes the issue when the PR merges.

Save the proposed message to `.workflow/commit_msg.txt`.

## 3. The Human Commit Approval Gate

Target 50 is an impassable Human Pause Gate.

1. Print `git status --short`, diff summary, and the complete proposed commit message directly in chat.
2. Set `99_next_action.md` to `AWAITING_DECLARATION (human-commit-approval)`.
3. **PAUSE** with empty tool calls (`tool_calls: []`).
4. Wait for explicit human approval before running `git commit`.
5. Upon approval, execute:
   ```bash
   git commit -F <scratch>/commit_msg.txt
   ```
6. Verify that the post-commit tree matches:
   ```bash
   test "$(git rev-parse HEAD^{tree})" = "$APPROVED_TREE"
   ```
7. Chain to Target 60.
