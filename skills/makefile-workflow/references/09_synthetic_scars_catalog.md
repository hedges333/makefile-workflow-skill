# 09. Synthetic Scars Master Catalog and Routing Index

This manual serves as the Master Routing Index for all Synthetic Scars (engineering rules codified from past operational failures).

## 1. Hub-and-Spoke Architecture

To scale the synthetic scar catalog to hundreds of community contributions without hitting context limits (`SCAR-PROC-99`) or causing Git merge conflicts, scars are organized into a **Hub-and-Spoke** architecture:

```
references/
├── 09_synthetic_scars_catalog.md    <-- Master Routing Index Table (Hub)
├── scars/                           <-- Category Spokes (Universal Rules)
│   ├── process.md                   <-- SCAR-PROC-*
│   ├── testing.md                   <-- SCAR-TEST-*
│   ├── git_and_shell.md             <-- SCAR-GIT-*, SCAR-SH-*
│   ├── system_and_os.md             <-- SCAR-SYS-*, SCAR-ENV-*
│   ├── data_and_database.md         <-- SCAR-DATA-*, SCAR-DB-*
│   ├── security_and_auth.md         <-- SCAR-SEC-*, SCAR-AUTH-*
│   └── tooling_and_hci.md           <-- SCAR-TOOL-*, SCAR-HCI-*, SCAR-DOC-*
└── polyglot/                        <-- Language Spokes (Domain-Specific)
    ├── dart_flutter.md              <-- SCAR-LANG-DART-*
    ├── python.md                    <-- SCAR-LANG-PYTHON-*
    ├── typescript_node.md           <-- SCAR-LANG-TYPESCRIPT-*
    └── ... (27 languages)
```

### Numbering Rules
1. **Category-Scoped Sequencing**: Scars are ordered monotonically within each category spoke file.
2. **End-of-Sequence Appending**: When adding a new scar, assign the next sequential integer and append it to the end of the appropriate category file.
3. **Full Language Names**: Language-specific failure vaccines use full uppercase language names: `SCAR-LANG-<FULL_LANGUAGE>-<NN>`.
4. **Three-Part Anatomy**: Every scar in a spoke file must record:
   - **Wound**: The exact bug, data loss, or broken build that happened.
   - **Trap**: The false assumption or shortcut that caused the failure.
   - **Permanent Reflex**: The mandatory rule that prevents recurrence.

---

## 2. Master Routing Table

| Scar ID | Title | Category | Spoke File |
| :--- | :--- | :--- | :--- |
| `SCAR-PROC-53` | Prohibit Shell Sleep Polling | Process | [`scars/process.md`](./scars/process.md) |
| `SCAR-PROC-95` | Depth-0 Supervisor and Subagent Isolation | Process | [`scars/process.md`](./scars/process.md) |
| `SCAR-PROC-99` | Single-Page SKILL.md Size Ceiling | Process | [`scars/process.md`](./scars/process.md) |
| `SCAR-PROC-102` | Human Declaration Authority | Process | [`scars/process.md`](./scars/process.md) |
| `SCAR-PROC-103` | Single Plan Artifact Lifecycle and Demotion | Process | [`scars/process.md`](./scars/process.md) |
| `SCAR-PROC-104` | Review Before Edit and Targeted Loops | Process | [`scars/process.md`](./scars/process.md) |
| `SCAR-PROC-138` | Yield on Repeated Timer Conflicts | Process | [`scars/process.md`](./scars/process.md) |
| `SCAR-TEST-05` | Isolated Test Environments | Testing | [`scars/testing.md`](./scars/testing.md) |
| `SCAR-TEST-08` | Two-Tier Test Isolation | Testing | [`scars/testing.md`](./scars/testing.md) |
| `SCAR-TEST-09` | Fail-Fast Targeted TDD Loop | Testing | [`scars/testing.md`](./scars/testing.md) |
| `SCAR-TEST-10` | Pre-Flight Structural Static Analysis Gate | Testing | [`scars/testing.md`](./scars/testing.md) |
| `SCAR-SH-03` | Shell Redirection and Comment Stripping | Git & Shell | [`scars/git_and_shell.md`](./scars/git_and_shell.md) |
| `SCAR-GIT-20` | Pre-Push Merge Check | Git & Shell | [`scars/git_and_shell.md`](./scars/git_and_shell.md) |
| `SCAR-GIT-25` | Destructive Working-Tree and History Guards | Git & Shell | [`scars/git_and_shell.md`](./scars/git_and_shell.md) |
| `SCAR-GIT-30` | Pure Git Mode and Tool Discovery | Git & Shell | [`scars/git_and_shell.md`](./scars/git_and_shell.md) |
| `SCAR-ENV-04` | Shared Workspace Umask Permissions | System & OS | [`scars/system_and_os.md`](./scars/system_and_os.md) |
| `SCAR-DB-09` | Pipeline Splitting and URI Userinfo Stripping | Data & Database | [`scars/data_and_database.md`](./scars/data_and_database.md) |
| `SCAR-SEC-01` | Untrusted External Text Airlock | Security & Auth | [`scars/security_and_auth.md`](./scars/security_and_auth.md) |
| `SCAR-AUTH-02` | Preserve Authorization on Same-Origin Redirects | Security & Auth | [`scars/security_and_auth.md`](./scars/security_and_auth.md) |
| `SCAR-TOOL-07` | Prefer Dart Over Python for Scratch Scripts | Tooling & HCI | [`scars/tooling_and_hci.md`](./scars/tooling_and_hci.md) |
| `SCAR-TOOL-13` | Single State Writer Isolation | Tooling & HCI | [`scars/tooling_and_hci.md`](./scars/tooling_and_hci.md) |
| `SCAR-HCI-08` | Multi-Choice Prompt Rule | Tooling & HCI | [`scars/tooling_and_hci.md`](./scars/tooling_and_hci.md) |
| `SCAR-DOC-16` | Concentric Documentation Rings | Tooling & HCI | [`scars/tooling_and_hci.md`](./scars/tooling_and_hci.md) |

### Language-Specific Failure Vaccines

| Scar ID | Title | Language | Spoke File |
| :--- | :--- | :--- | :--- |
| `SCAR-LANG-DART-01` | Async Timers (fakeAsync & Frame Pumping) | Dart & Flutter | [`polyglot/dart_flutter.md`](./polyglot/dart_flutter.md) |
| `SCAR-LANG-DART-02` | Completer Guard (!isCompleted) | Dart & Flutter | [`polyglot/dart_flutter.md`](./polyglot/dart_flutter.md) |
| `SCAR-LANG-DART-03` | Cascade AST Node Member Offset Inspection | Dart & Flutter | [`polyglot/dart_flutter.md`](./polyglot/dart_flutter.md) |
| `SCAR-LANG-DART-04` | Widget Lifecycle & Controller Disposal | Dart & Flutter | [`polyglot/dart_flutter.md`](./polyglot/dart_flutter.md) |

---

## 3. Recording New Scars at Target 90

During Target 90 cleanup, record lessons from the active ticket:

1. Check the session for user corrections, rejected reviews, or CI surprises.
2. Open the matching domain spoke in `skills/makefile-workflow/references/scars/` or language guide in `skills/makefile-workflow/references/polyglot/`.
3. Append the new scar at the end of the file with the next sequential integer using the Wound, Trap, and Permanent Reflex fields.
4. Add the new entry to the Master Routing Table in this index.
5. Record the scar ID in `.workflow/history.json` and `.workflow/history.md`.
