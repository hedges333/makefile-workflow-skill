# 05. Pre-Commit Hygiene and Git Commit Protocol (`Target 50`)

This manual covers pre-commit formatting, full test sweeps, tree drift checks, and atomic Git commits.

## 1. Pre-Commit Verification Steps

Run these four checks under `set -euo pipefail` before you propose a commit:

1. Format check: Run the project formatter in check mode, for example `prettier --check .`, `ruff format --check .`, `cargo fmt -- --check`, or `gofmt -l .`.
2. Static analysis: Run the project linter with warnings treated as errors, for example `eslint .`, `ruff check .`, `cargo clippy -- -D warnings`, or `golangci-lint run`.
3. Full repository test sweep: Run the test suite across every subproject in the repository so that changes in one module do not break another.
4. Two-layer tree drift check: Make sure that no unreviewed edits entered the workspace after Target 40:
   ```bash
   git diff --quiet
   test -z "$(git ls-files --others --exclude-standard)"
   test "$(git write-tree)" = "$(cat .workflow/state/approved_tree.txt)"
   ```

## 2. Commit Message Format

Write an atomic commit message to `.workflow/state/50_commit_msg.txt` using Conventional Commits (v1.0.0):

```text
<type>(<scope>): <short summary> (closes #<ISSUE_ID>)

<plain English explanation of what changed and why>

Issue: #<ISSUE_ID>
Reviewed-by: adversarial-critic
```

On GitHub and GitLab, `closes #<ISSUE_ID>` links the pull request and closes the issue automatically upon merge.

## 3. Human Commit Approval Gate

Target 50 is a mandatory human pause gate.

1. Print `git status --short`, the diff stat, and the full text of `.workflow/state/50_commit_msg.txt` in chat.
2. Set `.workflow/state/99_next_action.md` to `AWAITING_DECLARATION (human-commit-approval)`.
3. Stop tool calls (`tool_calls: []`) and wait for explicit user approval in chat.
4. After user approval, commit the staged tree from the saved message file:
   ```bash
   git commit -F .workflow/state/50_commit_msg.txt
   ```
5. Make sure that the committed Git tree hash matches the approved snapshot:
   ```bash
   test "$(git rev-parse HEAD^{tree})" = "$(cat .workflow/state/approved_tree.txt)"
   ```
6. Advance to Target 60.
