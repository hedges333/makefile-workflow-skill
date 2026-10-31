# Makefile Workflow Plugin Rules

These rules apply when the `makefile-workflow` plugin is active.

## 1. Chat Presentation, Input, and Artifact Rules

The chat stream is the main presentation surface. The `ask_question` tool is an input prompt, not a display surface.

### 1.1 Target 20 Plan Artifact Lifecycle in Antigravity

Antigravity renders an interactive review panel for artifacts. Follow these rules for implementation plans:

1. Write the implementation plan to `.workflow/state/20_plan.md`.
2. Mirror the plan to `<brain>/plan.md` with the built-in `write_file` tool.
3. Set `Overwrite: true` and `ArtifactMetadata: { UserFacing: true, RequestFeedback: true }`.
4. Always use the single fixed filename `<brain>/plan.md`. Do not create multiple plan files with different names.
5. Print a concise summary in chat with a `file://` link to `.workflow/state/20_plan.md`, then stop tool calls.
6. Accept either `/artifact` approval or verbal chat approval at Target 20.
7. If the user approves the plan, demote the artifact immediately at Target 30 entry.
8. Use the built-in `write_file` tool to overwrite `<brain>/plan.md`.
9. Set `Overwrite: true` and `ArtifactMetadata: { UserFacing: false, RequestFeedback: false }`.
10. Write an approved tombstone body inside `<brain>/plan.md`.
11. Do not use shell `rm` commands to delete artifacts. Overwriting with the built-in tool updates markdown content and companion JSON attributes safely.
12. If `.workflow/state/20_plan_approved.md` exists, never re-execute Target 30 from old artifact notifications. Always verify progress from `.workflow/state/`.

### 1.2 Pause Gates and Question Prompts

1. If the user must choose between two or more alternatives ($N \ge 2$), call `ask_question`.
2. If a gate has one approval action ($N = 1$), do not call `ask_question`. Print the full proposal in chat with `file://` links and stop tool calls. This rule covers Review Approval (Target 45), Commit Approval (Target 50), Push Approval (Target 60), and Landing Approval (Target 75).
3. Before you ask for a decision, print the full facts in the chat message.
4. Add a `file://` markdown link for every file, diff, plan, or review card that you name.

## 2. Production Data Protection Rules

Never connect tests or agent commands to live systems.

1. Do not connect to live production databases, cloud storage, or mutable production files.
2. Point tests to isolated test databases (for example `*_test` or configured `database.testDatabases`), in-memory databases, or mock fixtures. If live versus test database names are unclear, ask the user before running tests.
3. Run file operations during tests inside temporary directories or mocked file systems.
4. Partition tests into two tiers (`SCAR-TEST-08`): Run pure unit tests in memory with zero external socket or daemon dependencies. Isolate integration tests behind explicit markers, and never connect live sockets or database DDL inside global autouse session fixtures. Tests may use self-contained ephemeral loopback sockets (`127.0.0.1:0` or temporary Unix domain sockets) for protocol or daemon verification.

## 3. Code Edit and Architecture Rules (`SCAR-PROC-104`)

Keep each code change small and within ticket scope.

1. Review before edit (`SCAR-PROC-104`): Read target files and their type contracts before you edit them.
2. Apply minimal edits that solve the active ticket. Favor object composition over deep class inheritance.
3. Run pre-flight structural static analysis (`SCAR-TEST-10`): If you modify code, run fast structural checks before functional test suites. Check syntax errors and undefined symbols with `ruff`, `flake8`, or standard library AST parsers.
4. Run fail-fast targeted test loops (`SCAR-PROC-104`, `SCAR-TEST-09`): Execute targeted subproject test commands in tight loops with fail-fast flags (`pytest path/to/test.py::test_name -v -x` or script equivalent) until green before running full regression suites.
5. Use an ORM (a library that maps database rows to objects) by default. If large datasets slow down the ORM, encapsulate parameterized SQL or NoSQL queries behind repository methods.
6. If you find unrelated defects during a ticket, do not edit them. Record them in ticket notes for a separate task.

### 3.1 Temporary Script and Automation Rules

Apply these rules for scratch scripts and automation utilities:

1. For one-off scripts and automation tasks where the language is not specified, prefer Dart over Python if Dart is installed.
2. If Dart is not installed, use Python.
3. Never attempt to install Dart.
4. If shell commands require complex string escaping, write the script to a file in a temporary directory.

## 4. Simple English Documentation Rules

Apply the rules of the `simple-english` plugin to documentation, plans, changelogs, and pull request descriptions:

1. Keep procedural sentences at 20 words or fewer, with one instruction per sentence.
2. Keep descriptive sentences at 25 words or fewer, in simple tenses and active voice.
3. Put the condition before the command with a comma: "If the build fails, read the log."
4. Define each technical concept term in under ten words at first use.
5. Delete filler words, contractions, semicolons, and em-dashes.
