# 13. Configuration & User Preferences

This manual explains how users configure models and workflow rules for their own environments.

## 1. Portability Principle

The plugin repository does not force concrete model names on users.
Different organizations and users have different API keys, access tiers, and cost budgets.
Users can configure their preferred models locally without modifying the shared plugin repository.

## 2. Configuration Resolution Order

When the supervisor agent or MCP server starts, it searches for configuration in this exact order:

1. **Workspace Configuration**: `<workspace>/.workflow/config.json`
2. **Global User Configuration**: `~/.gemini/config/makefile-workflow.json`
3. **Environment Variables**:
   - `MAKEFILE_WORKFLOW_CRITIC_MODEL` (Overrides model for `adversarial-critic`)
   - `MAKEFILE_WORKFLOW_WORKER_MODEL` (Overrides model for `archaeology-worker`)
   - `MAKEFILE_WORKFLOW_TDD_MODEL` (Overrides model for `tdd-worker`)
   - `MAKEFILE_WORKFLOW_TRIAGE_MODEL` (Overrides model for `triage-worker`)
4. **Default Abstract Tiers**:
   - `adversarial-critic`: `pro`
   - `archaeology-worker`: `flash`
   - `tdd-worker`: `inherit`
   - `triage-worker`: `flash`

## 3. Configuration File Schema

To create a configuration file, copy [`.workflow/config.json.example`](../../../.workflow/config.json.example) to `.workflow/config.json` or `~/.gemini/config/makefile-workflow.json`:

```json
{
  "models": {
    "adversarial-critic": "pro",
    "archaeology-worker": "flash",
    "tdd-worker": "inherit",
    "triage-worker": "flash"
  },
  "review": {
    "maxReviewRounds": 3,
    "strictSixPillars": true
  },
  "ci": {
    "pollIntervalSeconds": 30,
    "quiescenceSeconds": 180
  }
}
```

### Supported Values for Models

In Antigravity (`agy`), the subagent dispatcher supports abstract tiers:
- `pro`: Routes to high-capacity reasoning models (such as Gemini 4 Argon or Claude Opus).
- `flash`: Routes to high-speed models (such as Gemini 3.8 Flash).
- `flash_lite`: Routes to lightweight models.
- `inherit`: Inherits the active model from your parent session.

If you specify concrete model IDs in `.workflow/config.json` (such as `gemini-4-argon-high`), the orchestrator maps them during invocation.

## 4. User Customization Shadowing in Antigravity

Antigravity supports hierarchical agent shadowing:
1. Workspace: `<workspace>/.agents/agents/<name>.md`
2. Global: `~/.gemini/config/agents/<name>.md`
3. Plugin: `~/.gemini/config/plugins/<plugin>/agents/<name>.md`

If you want custom instructions for `adversarial-critic`:
1. Create `~/.gemini/config/agents/adversarial-critic.md`.
2. Antigravity will load your file instead of the plugin file.
3. Your local customization survives plugin updates.

## 5. Interactive IDE Reminders (Cursor, Copilot, ChatGPT)

In interactive IDE tools, subagent API calls cannot switch models automatically.
The agent must remind the user in chat:

### Target 40 (Six Pillars Adversarial Review)
- In Cursor: "👉 **Please switch the model dropdown to your deep-reasoning model (such as Claude 3.5 Sonnet or o1)** to run the Six-Pillar review."
- In GitHub Copilot: "👉 **Please select Claude 3.5 Sonnet or GPT-4o in the Copilot Chat model picker**."
- In ChatGPT: "👉 **Please switch to o1 or GPT-4o for this deep review step**."

### Target 45 (Review Approval)
- Once the review passes with 0 blockers, remind the user:
  "👉 Review approved. You may switch back to your faster coding model for remaining steps."
