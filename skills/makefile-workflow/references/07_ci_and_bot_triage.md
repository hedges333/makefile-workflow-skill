# 07. CI Quiescence, Bot Review Triage, and Landing (`Target 70`, `75`, and `80`)

This manual covers remote CI checks, review bot triage, the human landing gate, and branch cleanup.

## 1. Target 70: CI and Review Bot Quiescence

After you open a pull request, do not merge right away. Wait for remote CI runners and review bots to finish.

### Phase 1: Fork the Triage Worker

Fork a `triage-worker` subagent with `Model` set to `agyModelTiers["triage-worker"]` (default `inherit`):

1. Poll `gh pr checks` until every remote CI workflow finishes.
2. Wait through the configured quiescence duration (default 180 seconds with no new bot comments) so Gemini, Copilot, CodeRabbit, and SonarQube finish posting.
3. Group every bot finding or CI failure into one of four actions:
   - `Accept`: Real bug or security defect that needs a code fix.
   - `Defend`: Incorrect bot claim paired with a technical reply.
   - `Defer`: Valid improvement outside ticket scope, logged for a future ticket.
   - `Acknowledge`: Informational note that needs no code change.
4. Write the triage table to `.workflow/state/70_bot_triage.md`.

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
5. Advance to Target 90.

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
4. Advance to Target 90.
