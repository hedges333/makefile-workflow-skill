# Tooling, HCI, and Documentation Scars

This reference manual documents developer tooling, interaction patterns, prompt gates, and documentation architecture scars (`SCAR-TOOL-*`, `SCAR-HCI-*`, and `SCAR-DOC-*`).

## Scars in this Category

| ID | Title | Scope |
| :--- | :--- | :--- |
| `SCAR-TOOL-07` | Prefer Dart Over Python for Scratch Scripts | Temporary Scripts & Escaping |
| `SCAR-TOOL-13` | Single State Writer Isolation | Subagent State File Concurrency |
| `SCAR-TOOL-14` | Programmatic Tool Polling vs Subagent Scrape Loops | Remote Polling & Subagent Latency |
| `SCAR-HCI-08` | Multi-Choice Prompt Rule | User Interaction & Choice Gates |
| `SCAR-DOC-16` | Concentric Documentation Rings | Layered Architecture & Readability |

---

### SCAR-TOOL-07: Prefer Installed Dart and Temporary Files for Scratch Scripts

- **Wound**: Inline shell scripts with nested quoting fail or corrupt strings, and Python scratch scripts fail on missing packages or virtual environment restrictions.
- **Trap**: Defaulting blindly to inline multiline Python commands with complex shell escapes instead of checking for installed Dart or using script files.
- **Permanent Reflex**: If Dart is installed and the language is not specified, prefer Dart over Python for scratch scripts. If Dart is not installed, use Python without attempting to install Dart. If shell commands require complex string escaping, write the script to a file in a temporary directory.

### SCAR-TOOL-13: Single State Writer Isolation

- **Wound**: Child subagents modify `.workflow/state/*.md` files concurrently with the orchestrator, corrupting state and causing race conditions.
- **Trap**: Allowing child subagents write access to workflow state directory cards.
- **Permanent Reflex**: Only the Depth-0 supervisor writes `.workflow/state/*.md` cards. Subagents return concise Markdown summaries in their completion messages for the supervisor to record.

### SCAR-HCI-08: Multi-Choice Prompt Rule

- **Wound**: Calling `ask_question` on single-option gates or opening modal prompts without printing the full proposal in chat degrades user experience.
- **Trap**: Using choice widgets for simple single-action approvals.
- **Permanent Reflex**: Call `ask_question` only when two or more choices exist ($N \ge 2$). For single approvals ($N = 1$), print the proposal in chat and stop tool calls.

### SCAR-DOC-16: Concentric Documentation Rings

- **Wound**: Deep implementation mechanics mixed into top-level user guides overwhelm readers and cause prompt token exhaustion.
- **Trap**: Treating all documentation as a single flat manual without audience layering.
- **Permanent Reflex**: Layer documentation into concentric rings: Ring 1 (Surface Rules for agents and quick lookup), Ring 2 (Workflows and Procedures), and Ring 3 (Deep Architecture and Manuals).

### SCAR-TOOL-14: Programmatic Tool Polling vs Subagent Scrape Loops

- **Wound**: Polling pull request status checks and review bot comments by delegating to a read-only subagent triggered 29 sequential HTTP API round-trips via `read_url_content` and 89 seconds of model inference latency.
- **Trap**: Assuming subagents can poll remote endpoints efficiently without recognizing that read-only subagents lack shell tools and must scrape REST APIs across dozens of sequential model turns.
- **Permanent Reflex**: Keep mechanical polling loops inside programmatic native tools or scripts (`workflow_poll_ci`). Invoke subagents only for single-turn cognitive evaluation after pre-fetching data.

