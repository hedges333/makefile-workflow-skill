# Process and Workflow Scars

This reference manual documents core process and workflow scars (`SCAR-PROC-*`). These rules govern orchestrator discipline, subagent boundaries, artifact lifecycles, and human approval gates.

## Scars in this Category

| ID | Title | Scope |
| :--- | :--- | :--- |
| `SCAR-PROC-53` | Prohibit Shell Sleep Polling | Subagent & Task Notification |
| `SCAR-PROC-95` | Depth-0 Supervisor and Subagent Isolation | Orchestration Architecture |
| `SCAR-PROC-99` | Single-Page SKILL.md Size Ceiling | Context Budget & Skill Files |
| `SCAR-PROC-102` | Human Declaration Authority | Pause Gate Enforcement |
| `SCAR-PROC-103` | Single Plan Artifact Lifecycle and Demotion | Antigravity Artifact Management |
| `SCAR-PROC-104` | Review Before Edit and Targeted Loops | Code Modification Discipline |
| `SCAR-PROC-138` | Yield on Repeated Timer Conflicts | Schedule Conflict Handling |

---

### SCAR-PROC-53: Prohibit Shell Sleep Polling

- **Wound**: Polling background tasks or timers with `sleep` loops hangs shell sessions, blocks context, and exhausts timeout limits.
- **Trap**: Writing shell `sleep` loops instead of yielding control to event-driven reactive wakeups.
- **Permanent Reflex**: Stop calling tools immediately after dispatching tasks and wait for system notifications. Never poll in a loop with shell `sleep` commands.

### SCAR-PROC-95: Depth-0 Supervisor and Subagent Isolation

- **Wound**: A supervisor that runs large file searches and test suites directly hits token limits, compresses history, and drops rules.
- **Trap**: Running heavy shell commands directly inside the main conversation turn for convenience.
- **Permanent Reflex**: Keep the orchestrator as a Depth-0 supervisor and delegate searches, TDD loops, reviews, and CI polling to child subagents.

### SCAR-PROC-99: Single-Page SKILL.md Size Ceiling

- **Wound**: Large skill files above tool byte limits truncate on read and cut off cleanup targets at the bottom of the file.
- **Trap**: Packing every language guide and protocol detail into one giant `SKILL.md` file.
- **Permanent Reflex**: Keep `SKILL.md` at or below 24 KB and store phase details in `references/`.

### SCAR-PROC-102: Human Declaration Authority

- **Wound**: An agent approves its own plan or code review and runs `git commit` without waiting for the user.
- **Trap**: Treating human pause gates as optional status messages instead of hard stops.
- **Permanent Reflex**: Only the human user can declare approval at Targets 20, 42, 45, 50, 60, and 75.

### SCAR-PROC-103: Single Plan Artifact Lifecycle and Built-in Tool Demotion

- **Wound**: Multiple multi-named plan artifacts left with pending feedback requests confuse agent context after compaction and trigger duplicate execution of already-completed plans.
- **Trap**: Creating uniquely named plan files across sessions and attempting to clean them up with shell `rm` commands that break across operating systems or trigger sandbox permission blocks.
- **Permanent Reflex**: Mirror plans only to a single fixed path `<brain>/plan.md` at Target 20, demote it immediately at Target 30 entry using the built-in `write_file` tool with `UserFacing: false, RequestFeedback: false`, and treat `.workflow/state/20_plan_approved.md` as the canonical guard against duplicate execution.

### SCAR-PROC-104: Review Before Edit, Minimal Confident Edits, and Targeted Test Loops

- **Wound**: An agent makes broad, speculative changes across unreviewed files or methods, introduces silent regressions in adjacent code, and gets stuck in cascading test failures.
- **Trap**: Attempting to fix problems across multiple unreviewed sections at once instead of reading target files first, making small confident edits, and iterating on targeted tests.
- **Permanent Reflex**: Always inspect target files and their type contracts before editing. Apply minimal, high-confidence diffs strictly within ticket scope. Run targeted tests in tight loops (`pytest path/to/test.py::test_name -v -x` or script equivalent) until green, leaving unrelated defects for future tickets, and run the full test suite only after the targeted test passes.

### SCAR-PROC-138: Yield on Repeated Timer Conflicts

- **Wound**: Repeated timer conflicts cause infinite rescheduling loops and consume tokens without making forward progress.
- **Trap**: Continuously retrying failed timer schedules without human intervention.
- **Permanent Reflex**: If a timer conflict happens twice in a row, stop calling tools and yield directly to the user.
