# 06. Clean Commit & Pull Request Creation (`Target 60`)

This manual details the landability check, push gate, and pull request creation.

## 1. Pre-Push Landability Barrier (`SCAR-GIT-20`)

Never push a branch that cannot cleanly merge with the remote default branch.

1. Fetch latest changes from remote:
   ```bash
   git fetch origin main
   ```
2. Verify clean mergeability using `git merge-tree`:
   ```bash
   git merge-tree $(git merge-base HEAD origin/main) HEAD origin/main
   ```
3. If merge conflicts exist, halt immediately. Do not push. Rebase on `origin/main`, rerun tests, and request fresh review.

## 2. The Human Push Approval Gate

Target 60 is an impassable Human Pause Gate.

1. Present the branch name, remote target, and commit hash in chat.
2. Set `99_next_action.md` to `AWAITING_DECLARATION (human-push-approval)`.
3. **PAUSE** with empty tool calls (`tool_calls: []`).
4. Wait for explicit human approval before running `git push`.

## 3. Pushing and Opening the Pull Request

Upon approval:
1. Push the feature branch to the remote repository:
   ```bash
   git push -u origin <branch-name>
   ```
2. Create the pull request using `gh pr create`.
3. The PR body must include the complete Six Pillars review summary:
   - Intent and scope summary.
   - Verification evidence (tests added and passed).
   - Architectural considerations.
   - Blast radius assessment.
   - Reviewer defense notes.
   - Immune defenses and edge cases handled.
4. Record the PR URL and number in `.workflow/state/99_next_action.md`.
5. Chain to Target 70.
