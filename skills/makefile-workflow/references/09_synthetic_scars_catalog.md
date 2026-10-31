# 09. Synthetic Scars Reference Catalog

This manual lists core Synthetic Scars (process rules codified from past failures) so agents do not repeat known mistakes.

## 1. Structure of a Synthetic Scar

Every scar records three facts:

1. Wound: The exact bug, data loss, or broken build that happened.
2. Trap: The false assumption or shortcut that caused the failure.
3. Permanent Reflex: The mandatory rule that prevents the failure from happening again.

## 2. Core Process Scars

### SCAR-PROC-95: Depth-0 Supervisor and Subagent Isolation

- Wound: A supervisor that runs large file searches and test suites directly hits token limits, compresses history, and drops rules.
- Trap: Running heavy shell commands directly inside the main conversation turn for convenience.
- Permanent Reflex: Keep the orchestrator as a Depth-0 supervisor and delegate searches, TDD loops, reviews, and CI polling to child subagents.

### SCAR-PROC-99: Single-Page SKILL.md Size Ceiling

- Wound: Large skill files above tool byte limits truncate on read and cut off cleanup targets at the bottom of the file.
- Trap: Packing every language guide and protocol detail into one giant `SKILL.md` file.
- Permanent Reflex: Keep `SKILL.md` at or below 24 KB and store phase details in `references/`.

### SCAR-PROC-102: Human Declaration Authority

- Wound: An agent approves its own plan or code review and runs `git commit` without waiting for the user.
- Trap: Treating human pause gates as optional status messages instead of hard stops.
- Permanent Reflex: Only the human user can declare approval at Targets 20, 42, 45, 50, 60, and 75.

### SCAR-PROC-103: Single Plan Artifact Lifecycle and Built-in Tool Demotion

- Wound: Multiple multi-named plan artifacts left with pending feedback requests confuse agent context after compaction and trigger duplicate execution of already-completed plans.
- Trap: Creating uniquely named plan files across sessions and attempting to clean them up with shell `rm` commands that break across operating systems or trigger sandbox permission blocks.
- Permanent Reflex: Mirror plans only to a single fixed path `<brain>/plan.md` at Target 20, demote it immediately at Target 30 entry using the built-in `write_file` tool with `UserFacing: false, RequestFeedback: false`, and treat `.workflow/state/20_plan_approved.md` as the canonical guard against duplicate execution.

### SCAR-PROC-104: Review Before Edit, Minimal Confident Edits, and Targeted Test Loops

- Wound: An agent makes broad, speculative changes across unreviewed files or methods, introduces silent regressions in adjacent code, and gets stuck in cascading test failures.
- Trap: Attempting to fix problems across multiple unreviewed sections at once instead of reading target files first, making small confident edits, and iterating on targeted tests.
- Permanent Reflex: Always inspect target files and their type contracts before editing. Apply minimal, high-confidence diffs strictly within ticket scope. Run targeted tests in tight loops (`pytest path/to/test.py::test_name -v -x` or script equivalent) until green, leaving unrelated defects for future tickets, and run the full test suite only after the targeted test passes.

### SCAR-GIT-20: Pre-Push Merge Check

- Wound: An agent pushes a branch that conflicts with `main`, breaks CI, and needs history rewrites.
- Trap: Assuming that passing local unit tests means a clean merge with `origin/main`.
- Permanent Reflex: Run `git fetch origin main` and `git merge-tree $(git merge-base HEAD origin/main) HEAD origin/main` before every push.

### SCAR-GIT-25: Destructive Working-Tree and History Guards

- Wound: An agent runs `git reset --hard`, `git clean -fd`, or `git checkout --` after a test failure and destroys uncommitted work.
- Trap: Blocking only `git push --force` to `main` while trusting prompt rules to stop other destructive Git commands.
- Permanent Reflex: Block work-discarding and force-push Git commands in hooks and MCP. Require human approval before `git rebase` and `git branch -D`.

### SCAR-GIT-30: Pure Git Mode and Hosting Tool Discovery

- Wound: An agent attempts to run `gh pr create` or `gh pr checks` in an SSH-only or non-GitHub repository and stalls at Target 60 or Target 70 even though Git push succeeded.
- Trap: Assuming every repository uses authenticated GitHub CLI tooling instead of checking whether `gh` is authenticated.
- Permanent Reflex: Check `gh auth status` at Target 15. If `gh` is unavailable or unauthenticated, use Pure Git Mode: skip remote PR creation at Target 60, run full local repository tests at Target 70, present local landing readiness at Target 75, and squash-merge on `main` at Target 80 using standard Git commands.

### SCAR-HCI-08: Multi-Choice Prompt Rule

- Wound: Calling `ask_question` on single-option gates or opening modal prompts without printing the full proposal in chat.
- Trap: Using choice widgets for simple single-action approvals.
- Permanent Reflex: Call `ask_question` only when two or more choices exist ($N \ge 2$). For single approvals ($N = 1$), print the proposal in chat and stop tool calls.

### SCAR-TEST-05: Isolated Test Environments

- Wound: Automated tests connect to a shared or production database and alter live rows.
- Trap: Running test suites with default environment variables instead of dedicated test database credentials.
- Permanent Reflex: Point all tests to `*_test` databases, in-memory stores, or mock fixtures.

### SCAR-TEST-08: Two-Tier Test Isolation (Hermetic Unit vs Integration Fixtures)

- Wound: An unprivileged test runner or CI container fails session-level database DDL or network initialization in a root fixture, causing the entire test suite to crash before running any pure unit tests.
- Trap: Attaching database connections, socket initialization, or schema migrations to global `autouse=True` session fixtures instead of isolating them behind explicit markers.
- Permanent Reflex: Partition test suites into two tiers: Tier 1 hermetic unit tests with zero external daemon or socket dependencies, and Tier 2 marked integration tests that verify external dependencies during pre-flight. Never attach live database connections or network sockets to un-isolated session fixtures.

### SCAR-TEST-09: Fail-Fast Targeted TDD Loop (pytest -x -v)

- Wound: Running a large test suite during active debugging generates hundreds of cascading tracebacks, exhausting context limits and obscuring the initial defect.
- Trap: Running broad test suites without fail-fast flags while attempting to iterate on a single failing test.
- Permanent Reflex: Use fail-fast flags (`pytest -x -v` or language equivalent) during active Red-Green TDD cycles. Iterate exclusively on the targeted failing test until green before running the full regression suite.

### SCAR-TOOL-07: Prefer Installed Dart and Temporary Files for Scratch Scripts

- Wound: Inline shell scripts with nested quoting fail or corrupt strings, and Python scratch scripts fail on missing packages or virtual environment restrictions.
- Trap: Defaulting blindly to inline multiline Python commands with complex shell escapes instead of checking for installed Dart or using script files.
- Permanent Reflex: If Dart is installed and the language is not specified, prefer Dart over Python for scratch scripts. If Dart is not installed, use Python without attempting to install Dart. If shell commands require complex string escaping, write the script to a file in a temporary directory.

## 3. Recording New Scars at Target 90

During Target 90 cleanup, capture lessons from the active ticket:

1. Check the session for any user corrections, rejected reviews, or CI surprises.
2. Write each lesson using the Wound, Trap, and Permanent Reflex fields.
3. Record the scar ID in `.workflow/history.json` and append the rule to the matching reference manual.
