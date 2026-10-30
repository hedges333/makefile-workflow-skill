# 02. Archaeology and Planning (`Target 15` and `Target 20`)

This manual covers codebase archaeology, the Belnap fact table, plan file creation, and the human plan gate.

## 1. Target 15: Codebase Archaeology

Do not plan code edits from guesswork. Inspect the repository first to gather facts.

1. Fork an `archaeology-worker` subagent so the supervisor context stays small.
2. Scan the repository across all 27 supported languages to find every subproject root, manifest, runtime, and test runner.
3. Read sibling modules so that new code matches existing names, error handling, and return types.
4. Inspect `.workflow/config.json`, environment variables, and database manifests to identify live and test database names.
5. Tag each technical claim with one Belnap truth state (a four-state fact label):
   - `ESTABLISHED`: Proved true by reading source files or test output.
   - `CONTRADICTED`: Proved false by source files or test output.
   - `UNKNOWN`: Not yet checked against source files.
   - `RETRACTED`: Accepted earlier, then disproved by new facts.
6. If a project uses databases and live versus test database names remain `UNKNOWN`, ask the user and offer to save them in `.workflow/config.json`.
7. Convert user requirements into Given-When-Then scenarios that become unit tests in Target 30.
8. If the target subproject has no test runner or test directory, prepare a smoke test template.
9. Write `.workflow/state/15_archaeology_receipt.md` and advance to Target 20.

## 2. Target 20: Plan File Creation (`20_plan.md`)

Write the implementation plan to `.workflow/state/20_plan.md`. In Antigravity sessions, mirror it to `<brain>/plan.md` with `UserFacing: true, RequestFeedback: true`.

Include these six items in every plan:

1. Target subprojects and programming languages involved in the task.
2. Exact file paths to create or edit.
3. Targeted subproject test commands for Target 30 and full repository test commands for Target 50.
4. Smoke test files and directories to create if the subproject lacks tests.
5. Any existing tests that must change, paired with the technical reason for each change.
6. Database and file isolation rules proving that tests use `*_test` databases, in-memory stores, or mocks, never production data.

## 3. Human Plan Approval Gate

Target 20 is a mandatory human pause gate.

1. Print the plan summary in chat with a `file://` link to `.workflow/state/20_plan.md` (or `<brain>/plan.md`).
2. Set `.workflow/state/99_next_action.md` to `AWAITING_DECLARATION (human-plan-approval)`.
3. Stop execution with empty tool calls (`tool_calls: []`).
4. Wait for explicit human approval in chat before editing any source files.
5. After the user approves the plan, write `.workflow/state/20_plan_approved.md` and advance to Target 30.
