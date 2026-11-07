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
| `SCAR-PROC-105` | Explicit Critic Six Pillars Manual Path | Critic Subagent Dispatch |
| `SCAR-PROC-106` | Predetermined Subagent Tool Mounting via options and tools Blocks | Subagent Tool Mounting |
| `SCAR-PROC-138` | Yield on Repeated Timer Conflicts | Schedule Conflict Handling |

---

### SCAR-PROC-53: Prohibit Shell Sleep Polling

- **Wound**: Polling background tasks or timers with `sleep` loops hangs shell sessions, blocks context, and exhausts timeout limits.
- **Trap**: Writing shell `sleep` loops instead of yielding control to event-driven reactive wakeups.
- **Permanent Reflex**: Stop calling tools immediately after dispatching tasks and wait for system notifications. Never poll in a loop with shell `sleep` commands.
- **Socratic Probe**: If you pause execution by calling shell `sleep` in a loop, will you block the conversation context and miss reactive system wakeups? Would it be safer to stop calling tools and wait for event notifications, or if you need to monitor a log file, can you write a temporary script and run it as a task that exits to notify you of a match?

### SCAR-PROC-95: Depth-0 Supervisor and Subagent Isolation

- **Wound**: A supervisor that runs large file searches and test suites directly hits token limits, compresses history, and drops rules.
- **Trap**: Running heavy shell commands directly inside the main conversation turn for convenience.
- **Permanent Reflex**: Keep the orchestrator as a Depth-0 supervisor and delegate searches, TDD loops, reviews, and CI polling to child subagents.
- **Socratic Probe**: If the supervisor runs broad searches or test suites directly, will context compression lose earlier rules and other information? Should you delegate this exploratory workload to an isolated subagent instead?

### SCAR-PROC-99: Single-Page SKILL.md Size Ceiling

- **Wound**: Large skill files above tool byte limits truncate on read and cut off cleanup targets at the bottom of the file.
- **Trap**: Packing every language guide and protocol detail into one giant `SKILL.md` file.
- **Permanent Reflex**: Keep `SKILL.md` at or below 24 KB and store phase details in `references/`.
- **Socratic Probe**: Does adding instructions directly to `SKILL.md` risk truncating critical targets at the end of the file? Would placing detailed procedures into modular reference files keep the core guide concise?

### SCAR-PROC-102: Human Declaration Authority

- **Wound**: An agent approves its own plan or code review and runs `git commit` without waiting for the user.
- **Trap**: Treating human pause gates as optional status messages instead of hard stops.
- **Permanent Reflex**: Only the human user can declare approval at Targets 20, 42, 45, 50, 60, and 75.
- **Socratic Probe**: If you stop tool execution and wait for human declaration at defined pause gates, will that prevent erroneous edits and unauthorized commits or pushes?

### SCAR-PROC-103: Single Plan Artifact Lifecycle and Built-in Tool Demotion

- **Wound**: Multiple multi-named plan artifacts left with pending feedback requests confuse agent context after compaction and trigger duplicate execution of already-completed plans.
- **Trap**: Creating uniquely named plan files across sessions and attempting to clean them up with shell `rm` commands that break across operating systems or trigger sandbox permission blocks.
- **Permanent Reflex**: Mirror plans only to a single fixed path `<brain>/plan.md` at Target 20, demote it immediately at Target 30 entry using the built-in `write_file` tool with `UserFacing: false, RequestFeedback: false`, and treat `.workflow/state/20_plan_approved.md` as the canonical guard against duplicate execution.
- **Socratic Probe**: If older plan files remain active in context, could the agent accidentally re-execute finished work after compaction? Will overwriting `<brain>/plan.md` using the built-in tool prevent duplicate prompts and OS-specific deletion failures?

### SCAR-PROC-104: Review Before Edit, Minimal Confident Edits, and Targeted Test Loops

- **Wound**: An agent makes broad, speculative changes across unreviewed files or methods, introduces silent regressions in adjacent code, and gets stuck in cascading test failures.
- **Trap**: Attempting to fix problems across multiple unreviewed sections at once instead of reading target files first, making small confident edits, and iterating on targeted tests.
- **Permanent Reflex**: Always inspect target files and their type contracts before editing. Apply minimal, high-confidence diffs strictly within ticket scope. Run targeted tests in tight loops (`pytest path/to/test.py::test_name -v -x` or script equivalent) until green, leaving unrelated defects for future tickets, and run the full test suite only after the targeted test passes.
- **Socratic Probe**: If you review files before editing, apply smaller, higher-confidence edits, stay narrowly focused on the current request, ignore unrelated problems, and iterate with targeted tests, will regressions be less likely?

### SCAR-PROC-105: Explicit Six Pillars Review Manual Path in Adversarial Critic Dispatch

- **Wound**: When launching `adversarial-critic` at Target 40, supervisors that omit the explicit path to `skills/makeflow/references/04_six_pillars_adversarial_review.md` generate shallow, un-anchored review prompts, causing the critic to miss domain invariants, relax scrutiny across canonical headings, or skip mandatory blast radius and crash antibody evaluations.
- **Trap**: Assuming the critic subagent will instinctively remember or infer the detailed Six Pillars criteria and invariants without an explicit file path in the dispatch prompt, or providing a brief informal prompt summary that leaves out key evaluation guidelines.
- **Permanent Reflex**: When launching the `adversarial-critic` subagent at Target 40, the supervisor must explicitly include the full relative workspace path `skills/makeflow/references/04_six_pillars_adversarial_review.md` in the dispatch prompt, instructing the critic to audit the diff against that manual and structure its report with the canonical six headings and binary verdict header.
- **Socratic Probe**: Does the adversarial-critic dispatch prompt explicitly supply the path `skills/makeflow/references/04_six_pillars_adversarial_review.md`? If you omit this explicit manual path, will the critic rely on shallow heuristics and overlook crucial verification, blast radius, or crash antibody invariants?

### SCAR-PROC-106: Predetermined Subagent Tool Mounting via options and tools Blocks

- **Wound**: In Antigravity CLI 1.5.2, plugin subagents loaded via `agents/*.md` receive read-only tools by default. Declaring snake_case frontmatter keys (`enable_write_tools`) fails silently because the runtime ignores them, causing spawned `tdd-worker` and `adversarial-critic` subagents to lack file-write and shell tools.
- **Trap**: Relying on unverified YAML frontmatter keys or assuming dynamic `define_subagent` calls can override existing registered subagent names without naming collisions.
- **Permanent Reflex**: Structure subagent markdown files in `agents/*.md` with an `options:` block using unmutated PascalCase keys (`EnableWriteTools`, `EnableMCPTools`, `EnableSubagentTools`) alongside native `tools:` lists. Provide a deterministic `subagent-def` CLI gate in `scripts/workflow_gates.py` to extract and emit validated JSON argument dictionaries.
- **Socratic Probe**: Before dispatching a subagent that requires shell commands or file edits, what concrete runtime mechanism guarantees that mutating tools are mounted in its child session?

### SCAR-PROC-138: Yield on Repeated Timer Conflicts

- **Wound**: Repeated timer conflicts cause infinite rescheduling loops and consume tokens without making forward progress.
- **Trap**: Continuously retrying failed timer schedules without human intervention.
- **Permanent Reflex**: If a timer conflict happens twice in a row, stop calling tools and yield directly to the user.
- **Socratic Probe**: If a scheduled timer fails twice consecutively, will repeated retries consume context without making progress? Should you stop tool calls immediately and yield the conflict to the user?
