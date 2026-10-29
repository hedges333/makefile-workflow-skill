# 08. Subagent Orchestration & Delegation Protocol

This manual details how the supervisor agent coordinates ephemeral subagents to keep context windows small and prevent context compaction.

## 1. Depth-0 Supervisor Role

The primary orchestrator agent operates at Depth 0 as a supervisor (GNU Make engine):
1. **Never Run Heavy Operations Directly**:
   The supervisor must not run massive file searches, long test suites, or large package builds in its own context window.
2. **Context Window Ceiling**:
   By delegating heavy commands to subagents, the supervisor's context window stays small ($\le 30\text{k tokens}$). This makes context compaction structurally impossible.
3. **Exclusive State Directory Ownership (`SCAR-TOOL-13`)**:
   Only the supervisor writes to `.workflow/state/*.md` and `plan.md`. Subagents write receipts to `<workspace>/.tmp/` or return markdown summaries in their completion messages.

## 2. Subagent Roles

The workflow defines four specialized subagent roles:

* **Archaeology Worker** (`archaeology-worker`):
  Runs during Target 15. Scans for languages, subprojects, API patterns, and existing tests. Read-only tools. Model: `flash`.
* **TDD Implementation Worker** (`tdd-worker`):
  Runs during Target 30. Compiles failing tests first (Red), implements minimal code (Green), and runs targeted tests. Model: `inherit`.
* **Adversarial Code Reviewer** (`adversarial-critic`):
  Runs during Target 40. Inspects the git diff in an isolated context without authoring bias. Read-only tools. Model: `pro`.
* **CI & Bot Triager** (`triage-worker`):
  Runs during Target 70. Polls remote CI checks and bot review comments until 180s quiescence is satisfied. Model: `flash`.

For model configuration overrides and user preferences, see [13. Configuration & User Preferences](13_configuration_and_user_preferences.md).

## 3. Subagent Lifecycle & Timer Management

1. **Paired Schedules**:
   When launching a long-running subagent (like CI polling or test execution), pair the subagent invocation with a schedule timer (`schedule(DurationSeconds: 60, TimerCondition: "<subagent-id>")`).
2. **Yield After Dispatch**:
   After calling `invoke_subagent` and `schedule`, stop calling tools (`tool_calls: []`). Wait for the system notification. Do not poll in a loop with shell sleep commands (`SCAR-PROC-53`).
3. **Double-Fault Circuit Breaker (`SCAR-PROC-138`)**:
   If a timer conflict occurs twice consecutively, halt and yield to avoid loop thrashing.
