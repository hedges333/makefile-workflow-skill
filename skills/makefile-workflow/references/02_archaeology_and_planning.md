# 02. Archaeology and Planning (`Target 15` & `Target 20`)

This manual covers codebase archaeology, the Belnap truth ledger, non-volatile plan creation, and the Human Plan Approval gate.

## 1. Target 15: Codebase Archaeology

Do not design changes on assumptions. Run archaeology to find ground truth before writing a plan.

### Archaeology Steps

1. **Fork Ephemeral Worker**:
   Fork an `archaeology-worker` subagent to preserve the supervisor context window.
2. **Scan for Subprojects and Languages**:
   Scan project files across the 22-language matrix. Identify each subproject root, runtime, package manager, and active test runner.
3. **Audit Pre-Existing Implementations & Sibling Symmetry**:
   Find similar methods, classes, or endpoints in the repository. New code must match existing naming patterns, error handling conventions, and return types.
4. **Compile the Belnap Truth Ledger**:
   Record each technical fact with its four-valued epistemic status:
   - `ESTABLISHED` ($T$): Confirmed true by reading code or documentation.
   - `CONTRADICTED` ($B$): Proved false by code evidence or tests.
   - `UNKNOWN` ($N$): Assumption not yet verified.
   - `RETRACTED` ($F$): Fact previously accepted, but disproven by new evidence.
5. **Compile Gherkin IR**:
   Translate requirements into Given-When-Then scenarios. These scenarios become the test cases in Target 30.
6. **Check Test Harness**:
   If the target subproject has no test directory or runner, prepare the boilerplate smoke test scaffolding.
7. **Write Receipt**:
   Save findings to `.workflow/state/15_archaeology_receipt.md` and chain to Target 20.

## 2. Target 20: Non-Volatile Plan Creation (`plan.md`)

Write `plan.md` in `.workflow/` (and mirror to `<brain>/plan.md` in Antigravity) with `UserFacing: true, RequestFeedback: true`.

### Mandatory Disclosures in the Plan

The plan must contain:
1. **Target Subprojects & Languages**: List each subproject and language involved in the change.
2. **Files to Create or Modify**: Name every file with exact paths.
3. **Targeted and Full Test Commands**: Specify the exact commands for running targeted tests during development and full regression sweeps before commit.
4. **Test Scaffolding**: If the repository lacks tests, state the exact smoke test files and directories to create.
5. **Modified Existing Tests**: If any existing tests must be changed, state which tests will change and provide technical reasons.
6. **Hermetic Test Isolation**: Certify that tests point to isolated test databases (`*_test`), in-memory databases, or mocks, and will not touch production data.

## 3. The Human Plan Approval Gate

Target 20 is an impassable Human Pause Gate.

1. Render the full Executive Summary in chat with clickable links:
   `👉 [Inspect Full Plan: plan.md](file:///.../plan.md)`
2. Set `99_next_action.md` to `AWAITING_DECLARATION (human-plan-approval)`.
3. Stop execution with empty tool calls (`tool_calls: []`).
4. Wait for explicit human approval before touching any code files.
5. When the user approves the plan, write `.workflow/state/20_plan_approved.md` and chain to Target 30.
