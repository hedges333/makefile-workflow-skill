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

When dispatching `adversarial-critic` at Target 40:
1. If `.workflow/config.json` specifies models or "inherit", bypass the model picker prompt.
2. When model selection is unconfigured in interactive IDEs, prompt the user to select a deep-reasoning model. Stop tool calls (`tool_calls: []`) to pause before critic dispatch.

## 3. Subagent Tool Permissions (GH-83)

Antigravity CLI (agy 1.5.2+) provisions subagents with tools declared in `agents/*.md`.
Declare tool permissions deterministically in `agents/*.md` with an `options:` block and `tools:` list:

| Subagent Role | `EnableWriteTools` | `EnableMCPTools` | `EnableSubagentTools` | Reason |
| :--- | :--- | :--- | :--- | :--- |
| `archaeology-worker` | `false` | `true` | `false` | Safe read-only inspection with MCP state tools. |
| `tdd-worker` | `true` | `false` | `false` | Requires `write_file`, `edit_file`, and `run_command` for test loops. |
| `adversarial-critic` | `true` | `false` | `false` | Requires `run_command` for git diff checks. File edits remain prohibited by prompt. |
| `triage-worker` | `true` | `true` | `false` | Requires `run_command` for git checks and `call_mcp_tool` for CI polling. |

To extract the predetermined tool call payload for any worker role, run:

```bash
python3 scripts/workflow_gates.py subagent-def --role <role> --json
```

If you register a subagent dynamically, pass the emitted parameters to `define_subagent`.

## 4. Subagent Lifecycle and Timers

Follow three rules when launching background subagents:

1. When you start a long subagent task such as CI polling, pair `invoke_subagent` with `schedule(DurationSeconds: 60, TimerCondition: "<subagent-id>")`.
2. Stop calling tools (`tool_calls: []`) right after dispatch and wait for the system notification. Never poll in a loop with shell `sleep` commands (`SCAR-PROC-53`).
3. If a timer conflict happens twice in a row, stop and yield to the user (`SCAR-PROC-138`).

## 5. Socratic Subagent Delegation Protocol

Do not prompt subagents with flat imperative commands alone. Frame dispatch prompts using directive-embedded Socratic questions to prune reckless reasoning branches:

1. **`archaeology-worker` (Target 15)**:
   > *"Can you discover all languages, subprojects, manifests, test runners, Tier 1 scars (`skills/makeflow/references/scars/`), and Tier 2 scars (`.workflow/scars/`) across the repository? For every technical claim, what concrete file evidence proves it is ESTABLISHED before we plan changes?"*
2. **`tdd-worker` (Target 30)**:
   > *"Would most comprehensive testing result from writing the smallest code change that makes the failing test pass while honoring `skills/makeflow/references/scars/` and `.workflow/scars/`? Did this test fail before you edited production code? Does this production change introduce any abstraction not required by the failing test, and if so, can you do without it to prevent unintended consequences?"*
3. **`adversarial-critic` (Target 40)**:
   > *"Does this staged Merkle tree diff conform to the Six Pillars in skills/makeflow/references/04_six_pillars_adversarial_review.md and both Tier 1 (`skills/makeflow/references/scars/`) and Tier 2 (`.workflow/scars/`) scars? If this diff causes a production outage, what is the most likely failure point? Did changing an existing test mask a real regression?"* (`SCAR-PROC-105`)
4. **`triage-worker` (Target 70)**:
   > *"Did continuous integration checks pass, and did bots or contributors file comments that need to be triaged? If comments exist, does each finding require an Accept, Defend, Defer, or Acknowledge action without expanding ticket scope?"*
