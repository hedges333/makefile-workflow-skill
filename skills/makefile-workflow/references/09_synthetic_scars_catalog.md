# 09. Synthetic Scars Reference Catalog

This manual catalogs the core process failure vaccines. Each Synthetic Scar records a hard-learned failure mode so the agent never repeats it.

## 1. Anatomy of a Synthetic Scar

Every scar follows a three-part structure:
1. **The Wound**: The exact operational failure, bug, or broken build that occurred.
2. **The Trap**: The mistaken assumption or shortcut that caused the failure.
3. **The Permanent Reflex**: The non-negotiable rule or invariant that prevents the failure from recurring.

## 2. Core Process Scars

### SCAR-PROC-95: Depth-0 Supervisor & Make-Fork Isolation
* **The Wound**: An orchestrator running heavy file edits and test suites in its own context hits the 200k-token limit, triggers context compaction, and forgets rules.
* **The Trap**: The convenience of running commands directly in the supervisor context.
* **The Permanent Reflex**: The orchestrator operates strictly as a Depth-0 supervisor, delegating all code edits, heavy searches, and test suites to ephemeral subagents.

### SCAR-PROC-99: Single-Page SKILL.md Hardware Ceiling
* **The Wound**: Monolithic skill files exceeding 46,080 bytes truncate during tool reading, severing cleanup and landing targets from context.
* **The Permanent Reflex**: Root `SKILL.md` is strictly bounded to $\le 42\text{ KB}$ and $\le 750\text{ lines}$. Detailed reference material lives in modular files under `references/`.

### SCAR-PROC-102: Customer Declaration Authority
* **The Wound**: An agent self-approves its own plan or code review and commits without waiting for human sign-off.
* **The Trap**: Treating human pause gates as informative suggestions rather than impassable barriers.
* **The Permanent Reflex**: Declaration authority belongs strictly to the human operator. Self-declaration by an agent is void.

### SCAR-GIT-20: Pre-Push Landability Barrier
* **The Wound**: An agent pushes a branch that has merge conflicts with `main`, breaking CI and requiring messy force-pushes.
* **The Trap**: Assuming that because local tests pass, the branch will merge cleanly.
* **The Permanent Reflex**: Run `git fetch origin main && git merge-tree $(git merge-base HEAD origin/main) HEAD origin/main` before every push.

### SCAR-HCI-08: The N-ary Choice Constraint
* **The Wound**: Calling interactive modals (`ask_question`) on single-option approval gates, or emitting modals without showing the underlying decision substance in chat.
* **The Trap**: Overusing interactive prompt widgets for simple yes/no checks.
* **The Permanent Reflex**: Only use `ask_question` when selecting between two or more described alternatives ($N \ge 2$). For unary approvals ($N = 1$), print full proposals in chat markdown and pause with empty tool calls.

### SCAR-TEST-05: Hermetic Test Environment Isolation
* **The Wound**: Test execution connects to a development or production database, corrupting live data rows or altering configuration state.
* **The Trap**: Relying on default connection strings instead of dedicated test environment configurations.
* **The Permanent Reflex**: Tests must point strictly to isolated test databases (`*_test`), in-memory databases, or mock fixtures.

## 3. Codifying New Scars at Target 90

During Target 90 post-mortems:
1. Audit the session for any human corrections or nudges ($N_{\text{nudge}} > 0$).
2. Formulate the lesson into The Wound, The Trap, and The Permanent Reflex.
3. Append the new scar to the relevant reference manual.
