# 04. Six Pillars Adversarial Review (`Target 40`, `42` & `45`)

This manual details the Six Pillars review protocol, the Merkle tree lock, and the human review approval gates.

## 1. Target 40: Adversarial Review Protocol

The agent that authored the code cannot review its own diff without bias. Review is executed by an orthogonal critic subagent.

### Phase 1: Lock the Merkle Tree
Before invoking the critic, lock the exact working tree:
```bash
git add -A && APPROVED_TREE=$(git write-tree)
```
Save `$APPROVED_TREE` to `<scratch>/approved_tree.txt`. The critic will evaluate this exact tree.

### Phase 2: Fork the Critic Subagent
Spawn an `adversarial-critic` subagent (`Model: "pro"`, read-only tools). Pass the base commit and tree hash:
```bash
git diff $(git merge-base HEAD origin/main) "$APPROVED_TREE"
```

### Phase 3: The Six Pillars Audit
The critic evaluates the diff across six dimensions:

1. **Pillar 1: Intent & Scope**:
   Does the change accomplish what the ticket requested? Does it introduce scope creep or unrelated edits?
2. **Pillar 2: Verification & Test Bijection**:
   Did the tests run and pass? Does each feature branch or bug fix have a corresponding test case?
3. **Pillar 3: Architecture & API Symmetry**:
   Does the code respect existing repository patterns, type contracts, and folder conventions?
4. **Pillar 4: Blast Radius & Regressions**:
   What other modules or subprojects could break?
5. **Pillar 5: Reviewer Defense**:
   Is the diff clean, readable, well-commented, and free of leftover debug prints?
6. **Pillar 6: Immune Defenses & Crash Antibodies**:
   Does the code guard against null/nil pointers, empty collections, timeouts, resource leaks, and unhandled errors?

The critic writes `.workflow/state/40_critic_review.md` ending with an explicit verdict:
- `VERDICT: APPROVED (0 BLOCKERS)`
- `VERDICT: REJECTED (<N> BLOCKERS)`

## 2. Target 42: Triaged Blockers Gate (`BLOCKERS > 0`)

If the critic reports one or more blockers:
1. Target 42 becomes active.
2. Present the complete blocker digest directly in chat:
   - Blocker ID and file location.
   - Root cause explanation.
   - Proposed remediation plan.
3. **PAUSE** for `human-blocker-triage-approval`.
4. If the user confirms the fix, loop back to Target 30 to make code edits, then run a fresh Target 40 critic review.

## 3. Target 45: Approved Review Gate (`0 BLOCKERS`)

If the critic reports zero blockers:
1. Verify that the working tree matches `$APPROVED_TREE`:
   ```bash
   test "$(git write-tree)" = "$APPROVED_TREE"
   ```
2. Present the full Six Pillars summary and the Non-Blocking Observations (NBO) table in chat.
3. Link the full review card:
   `👉 [Inspect Review: 40_critic_review.md](file:///.../40_critic_review.md)`
4. **PAUSE** for `human-review-approval`.
5. Upon approval, write `.workflow/state/45_review_approved.md` and chain to Target 50.
