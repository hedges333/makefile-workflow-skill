# 06. Clean Commit and Pull Request Creation (`Target 60`)

This manual covers the pre-push merge check, the human push gate, and pull request creation.

## 1. Pre-Push Merge Check (`SCAR-GIT-20`)

Never push a branch that conflicts with the remote default branch.

1. Fetch the latest default branch from `origin`:
   ```bash
   git fetch origin main
   ```
2. Test a clean merge in memory with `git merge-tree`:
   ```bash
   git merge-tree $(git merge-base HEAD origin/main) HEAD origin/main
   ```
3. If `git merge-tree` reports conflict markers, stop at once. Rebase onto `origin/main`, re-run tests, and repeat Target 40 review before pushing.

## 2. Human Push Approval Gate

Target 60 is a mandatory human pause gate.

1. Print the branch name, remote repository name, and local `HEAD` commit hash in chat.
2. Set `.workflow/state/99_next_action.md` to `AWAITING_DECLARATION (human-push-approval)`.
3. Stop tool calls (`tool_calls: []`) and wait for explicit user approval before running `git push`.

## 3. Push Branch and Open Pull Request

After the user approves the push, run these steps:

1. Push the feature branch to `origin`:
   ```bash
   git push -u origin <branch-name>
   ```
2. If `gh auth status` succeeds, open a pull request with `gh pr create` and include the Six Pillars summary in the description:
   - Intent and scope summary.
   - Verification commands and passing test counts.
   - Architecture and API symmetry notes.
   - Blast radius review.
   - Readability notes.
   - Error handling and edge cases covered.
3. If `gh` is unavailable or unauthenticated, use Pure Git Mode (`SCAR-GIT-30`). Record `HOSTING_MODE: PURE_GIT` in `.workflow/state/99_next_action.md` and skip `gh pr create`.
4. Advance to Target 70.
