# 13. Configuration and User Preferences

This manual explains how users assign custom AI models and review limits in their local environments without editing shared plugin files.

## 1. Portability Design

Different teams use different AI providers, API keys, and cost budgets. For that reason, `./agents/*.md` files omit hardcoded `model:` fields. Each user sets local preferences through JSON configuration files or environment variables.

## 2. Configuration Precedence Order

When a session starts or `workflow_get_config` runs, the plugin resolves configuration in this order (later environment variables override JSON values):

1. Workspace file: `<workspace>/.workflow/config.json` (git-ignored).
2. Global user file: `~/.gemini/config/makefile-workflow.json`.
3. Environment variables:
   - `MAKEFILE_WORKFLOW_CRITIC_MODEL` for `adversarial-critic`.
   - `MAKEFILE_WORKFLOW_WORKER_MODEL` or `MAKEFILE_WORKFLOW_ARCHAEOLOGY_MODEL` for `archaeology-worker`.
   - `MAKEFILE_WORKFLOW_TDD_MODEL` for `tdd-worker`.
   - `MAKEFILE_WORKFLOW_TRIAGE_MODEL` for `triage-worker`.
4. Built-in defaults:
   - `adversarial-critic`: `pro`
   - `archaeology-worker`: `flash`
   - `tdd-worker`: `inherit`
   - `triage-worker`: `flash`

## 3. Configuration File Schema

Copy [`.workflow/config.json.example`](../../../.workflow/config.json.example) to `<workspace>/.workflow/config.json` or `~/.gemini/config/makefile-workflow.json`:

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

### Model Tiers in Antigravity (`agy`)

Antigravity `invoke_subagent` accepts four model tier names:

- `pro`: High-capacity reasoning models such as Gemini 4 Argon or Claude Opus.
- `flash`: Fast workhorse models such as Gemini 3.8 Flash.
- `flash_lite`: Lightweight low-cost models.
- `inherit`: Uses the active model of the parent session.

If you put a concrete model ID such as `gemini-4-argon-high` in `models`, `workflow_get_config` normalizes it under `agyModelTiers`. Each role maps to `pro`, `flash`, `flash_lite`, or `inherit`.

## 4. Agent File Shadowing in Antigravity

Antigravity loads agent definitions in priority order from three paths:

1. Workspace path: `<workspace>/.agents/agents/<name>.md`
2. Global user path: `~/.gemini/config/agents/<name>.md`
3. Plugin path: `~/.gemini/config/plugins/makefile-workflow/agents/<name>.md`

If you want custom prompt rules for `adversarial-critic`, create `~/.gemini/config/agents/adversarial-critic.md`. Antigravity loads your file instead of the plugin copy, and your file survives plugin upgrades.

## 5. Interactive IDE Prompts (Cursor, Copilot, ChatGPT)

Interactive chat IDEs cannot switch models through subagent API calls. The agent prints reminders in chat at review boundaries:

1. At Target 40, prompt the user: "Switch the model picker to a deep-reasoning model for the Six-Pillar review."
2. At Target 45 (Review Sign-Off), prompt the user: "Review passed. You can switch back to your fast coding model for the remaining steps."
