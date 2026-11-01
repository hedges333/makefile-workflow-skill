# 08. Subagent Orchestration and Delegation Protocol

This manual explains how the supervisor agent delegates work to child subagents so the main context window stays small.

## 1. Depth-0 Supervisor Role

The main orchestrator agent runs at Depth 0 as a `make` supervisor:

1. Do not run large directory scans, long test suites, or full builds directly in the supervisor context.
2. Delegate heavy commands to child subagents so the supervisor stays below 30,000 tokens and avoids chat compression.
3. Only the supervisor writes `.workflow/state/*.md` cards (`SCAR-TOOL-13`). Subagents return concise markdown summaries in their completion messages.

## 2. Subagent Roles

Four subagent roles handle isolated phases of the workflow:

- `archaeology-worker` (Target 15): Scans languages, subprojects, sibling APIs, and existing tests with read-only tools. Default tier: `inherit`.
- `tdd-worker` (Target 30): Writes failing tests first, writes minimal feature code, and runs subproject test loops. Default tier: `inherit`.
- `adversarial-critic` (Target 40): Audits the Git tree diff in an isolated read-only context without authoring bias. Default tier: `inherit`.
- `triage-worker` (Target 70): Polls remote CI checks and review bot comments through 180 seconds of quiet time. Default tier: `inherit`.

Read [13. Configuration and User Preferences](13_configuration_and_user_preferences.md) to override model tiers per role.

## 3. Subagent Lifecycle and Timers

Follow three rules when launching background subagents:

1. When you start a long subagent task such as CI polling, pair `invoke_subagent` with `schedule(DurationSeconds: 60, TimerCondition: "<subagent-id>")`.
2. Stop calling tools (`tool_calls: []`) right after dispatch and wait for the system notification. Never poll in a loop with shell `sleep` commands (`SCAR-PROC-53`).
3. If a timer conflict happens twice in a row, stop and yield to the user (`SCAR-PROC-138`).
