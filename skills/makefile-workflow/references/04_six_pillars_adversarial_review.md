# 04. Six Pillars Adversarial Review (`Target 40`, `42`, and `45`)

This manual covers the Six Pillars code audit, the Git Merkle tree lock, and human review gates.

## 1. Target 40: Adversarial Review Protocol

An agent that wrote a diff has authoring bias when reviewing its own work. Delegate the audit to an independent read-only critic.

### Phase 1: Lock the Merkle Tree

Stage all workspace changes and record the Git Merkle tree hash (a cryptographic snapshot of staged files):

```bash
git add -A && git write-tree > .workflow/state/approved_tree.txt
```

Because `.workflow/state/` is listed in `.git/info/exclude`, Git ignores state files while hashing your code changes.

### Phase 2: Fork the Critic Subagent

In Antigravity, fork `adversarial-critic` with `Model` set to `agyModelTiers["adversarial-critic"]` (default `inherit`). Have the critic inspect the exact tree diff:

```bash
APPROVED_TREE=$(cat .workflow/state/approved_tree.txt)
git diff $(git merge-base HEAD origin/main) "$APPROVED_TREE"
```

### Phase 3: Audit Against the Six Pillars

Evaluate the diff across six engineering pillars:

1. Pillar 1 (Intent and Scope): Does the diff solve the ticket without scope creep or unrelated edits?
2. Pillar 2 (Verification and Test Comprehensiveness): Did failing tests run first, and does every new branch have a passing test? Are tests as comprehensive as possible across boundary limits, error paths, and invalid inputs within a reasonable balance of execution time and dependency burden? For network protocols or daemons, do tests use self-contained ephemeral loopback sockets (such as 127.0.0.1:0 or temporary Unix domain sockets) instead of unmanaged external host daemons?
3. Pillar 3 (Architecture and Symmetry): Does the diff match existing contracts and apply Gang of Four or game patterns ([`14_design_patterns_and_architecture.md`](./14_design_patterns_and_architecture.md))? Does it encapsulate ORM or parameterized large-dataset queries behind clean boundaries?
4. Pillar 4 (Blast Radius): Can this change break sibling modules, public APIs, or downstream subprojects?
5. Pillar 5 (Readability and Simple English): Is the diff clear, documented, and free of debug statements or dead code? Do modified documentation, plans, comments, and commit messages follow Simple English standards? Are procedural sentences 20 words or fewer and descriptive sentences 25 words or fewer? Does the condition come before the command with a comma? Are technical terms defined simply, with contractions, semicolons, em-dashes, and filler words deleted?
6. Pillar 6 (Error Handling): Does the code handle null pointers, empty inputs, timeouts, and resource cleanup?

Write the full report to `.workflow/state/40_critic_review.md` and end with one exact verdict line:

- `VERDICT: APPROVED (0 BLOCKERS)`
- `VERDICT: REJECTED (<N> BLOCKERS)`

## 2. Target 42: Blocker Triage Gate (`BLOCKERS > 0`)

If `40_critic_review.md` reports one or more blockers, run Target 42:

1. Print every blocker ID, file path, root cause, and proposed fix directly in chat.
2. Stop tool calls (`tool_calls: []`) and wait for `human-blocker-triage-approval`.
3. After user approval, return to Target 30 to fix the blockers, then run a fresh Target 40 review.

## 3. Target 45: Review Sign-Off Gate (`0 BLOCKERS`)

If `40_critic_review.md` reports zero blockers, run Target 45:

1. Make sure that the staged tree still matches `.workflow/state/approved_tree.txt`:
   ```bash
   test "$(git write-tree)" = "$(cat .workflow/state/approved_tree.txt)"
   ```
2. Print the Six Pillars table and non-blocking notes in chat with a `file://` link to `.workflow/state/40_critic_review.md`.
3. Stop tool calls (`tool_calls: []`) and wait for `human-review-approval`.
4. After user approval, write `.workflow/state/45_review_approved.md` and advance to Target 50.
