# 07. CI Quiescence, Bot Review Triage, and Landing (`Target 70`, `75`, and `80`)

This manual covers remote CI checks, review bot triage, the human landing gate, and branch cleanup.

## 1. Target 70: CI and Review Bot Quiescence

After you open a pull request, do not merge right away. Wait for remote CI runners and review bots to finish.

### Phase 1: Fast CI and Bot Polling (`workflow_poll_ci`)

Call the `workflow_poll_ci` MCP tool (or run `gh pr view <pr> --json statusCheckRollup,comments,reviews`):

1. It reads `ci.quiescenceSeconds` and `ci.pollIntervalSeconds` from `.workflow/config.json` before falling back to defaults.
2. It polls CI checks in a fast programmatic loop until all workflows complete.
3. It waits until the quiescence duration elapses with no new review bot comments from Gemini, Copilot, CodeRabbit, or SonarQube.
4. If zero bot comments exist and CI succeeds, write `.workflow/state/70_bot_triage.md` and advance directly to Target 75 without launching subagents.
5. If bot comments exist, pass the pre-fetched comments to a `triage-worker` subagent in a single prompt. The worker groups each comment in one model turn into:
   - `Accept`: Real bug or security defect that needs a code fix.
   - `Defend`: Incorrect bot claim paired with a technical reply.
   - `Defer`: Valid improvement outside ticket scope, logged for a future ticket.
   - `Acknowledge`: Informational note that needs no code change.
6. Write the triage table to `.workflow/state/70_bot_triage.md`.

### Phase 2: Fix Accepted Findings

If any accepted finding needs a code edit, return through the review and commit loop:

1. Return to Target 30, write a failing test for the defect, and fix the code.
2. Run Target 40 review and wait for Target 45 review sign-off.
3. Run Target 50 commit and Target 60 push.
4. Re-enter Target 70 and restart the quiescence timer.
5. When CI is green and zero open comments remain, advance to Target 75.

## 2. Target 75: Ready to Land Gate

Target 75 is a mandatory human pause gate.

1. Make sure that `gh pr view` reports `mergeable: "MERGEABLE"` and `mergeStateStatus: "CLEAN"`.
2. Print the CI status summary and resolved bot comment count in chat.
3. Print the 7-criteria review policy table:
   - Security impact.
   - Breaking API changes.
   - Database schema changes.
   - Performance impact.
   - Documentation updates.
   - Dependency changes.
   - Test coverage.
4. Stop tool calls (`tool_calls: []`) and wait for `human-landing-approval`.
5. If branch protection forbids direct push, commit ledger updates on the feature branch before requesting landing approval.

## 3. Target 80: Merge and Branch Cleanup

After the user approves landing, merge the pull request and clean up local Git state:

1. Squash-merge the pull request and delete the remote branch:
   ```bash
   gh pr merge <PR_NUMBER> --squash --delete-branch
   ```
2. Make sure that the linked issue is closed.
3. Switch to the default branch and pull the merged commit:
   ```bash
   git checkout main && git pull --ff-only
   ```
4. Delete the local feature branch:
   ```bash
   git branch -D <branch-name>
   ```
5. Advance to Target 90. At Target 90, update the history ledger and push to `origin main` if direct push is permitted.

## 4. Pure Git Mode (`SCAR-GIT-30`)

If the repository uses Pure Git Mode (`HOSTING_MODE: PURE_GIT`), remote bots and GitHub API actions do not exist:

1. At Target 70, run the full repository test suite locally (`make all`). Write `.workflow/state/70_bot_triage.md` noting pure Git verification and advance to Target 75.
2. At Target 75, present local test results and the 7-criteria policy table, then wait for `human-landing-approval`.
3. At Target 80, squash-merge directly with Git on `main`:
   ```bash
   git checkout main && git pull --ff-only
   git merge --squash <branch-name>
   git commit -F .workflow/state/50_commit_msg.txt
   git push origin main
   git branch -d <branch-name>
   ```
4. Advance to Target 90. Update `.workflow/history.json` and `.workflow/history.md`, commit, and run `git push origin main`.
