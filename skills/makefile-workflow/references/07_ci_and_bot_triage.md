# 07. CI Quiescence, Bot Review Triage & Landing (`Target 70`, `75` & `80`)

This manual details remote CI polling, review bot triage, human landing approval, and branch mop-up.

## 1. Target 70: CI & Review Bot Quiescence

After pushing a pull request, do not attempt to merge immediately. External CI suites and automated review bots take time to run.

### Phase 1: Fork the Triage Worker
Spawn a `triage-worker` subagent to monitor CI status:
1. Poll `gh pr checks` until all remote CI workflows finish.
2. Maintain a 180-second quiescence timer after the latest push to allow automated bots (Gemini, Copilot, CodeRabbit, SonarQube) to post comments.
3. If any CI run fails or bots leave comments, compile a 4-part triage matrix:
   - **Accept**: Valid defect or security vulnerability.
   - **Defend**: Counterfeit bot comment; draft a technical defense.
   - **Defer**: Valid idea outside current scope; record as a follow-up ticket.
   - **Acknowledge**: Informational note requiring no code edits.
4. Save the triage matrix to `.workflow/state/70_bot_triage.md`.

### Phase 2: Remediation Sub-DAG
If any accepted bot comment requires code changes:
1. Return to Target 30: write a test for the bot finding and fix the code.
2. Advance through Target 40 (Critic review) and Target 45 (Review approval).
3. Advance through Target 50 (Commit) and Target 60 (Push).
4. Re-enter Target 70 and restart the quiescence timer.
5. When CI is 100% green and zero open comments remain, chain to Target 75.

## 2. Target 75: Ready to Land Gate

Target 75 is an impassable Human Pause Gate.

1. Verify that `gh pr view` reports `mergeable: "MERGEABLE"` and `mergeStateStatus: "CLEAN"`.
2. Present the mechanical assertions table (CI status, bot threads resolved, zero regressions).
3. Present the 7-Criteria Human Review Policy Table:
   - Security impact.
   - Breaking API changes.
   - Database schema changes.
   - Performance implications.
   - Documentation synchronization.
   - Dependency updates.
   - Test coverage adequacy.
4. **PAUSE** for `human-landing-approval`.

## 3. Target 80: Merge & Branch Cleanup

Upon human landing approval:
1. Squash-merge the pull request:
   ```bash
   gh pr merge <PR_NUMBER> --squash --delete-branch
   ```
2. Verify that the associated issue is closed.
3. Switch back to the default branch and pull latest changes:
   ```bash
   git checkout main && git pull --ff-only
   ```
4. Delete the local feature branch:
   ```bash
   git branch -D ticket/<id>-<slug>
   ```
5. Chain to Target 90.
