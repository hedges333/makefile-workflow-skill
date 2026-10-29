#!/usr/bin/env python3
"""Cross-Agent Compatibility Validator.

Verifies the configuration files, manifests, and rules for:
1. Anthropic Claude Code (.claude-plugin/plugin.json, CLAUDE.md)
2. OpenAI Codex (.codex-plugin/plugin.json)
3. Cursor IDE (.cursorrules, .cursor/rules/makefile-workflow.mdc)
4. GitHub Copilot (.github/copilot-instructions.md)
5. ChatGPT (adapters/chatgpt/instructions.md)
6. Hooks & MCP Declarations (hooks.json, mcp_config.json)
"""

import json
import os
import sys


def validate():
  errors = []

  # 1. Claude Plugin Manifest
  claude_path = ".claude-plugin/plugin.json"
  if not os.path.exists(claude_path):
    errors.append(f"Missing {claude_path}")
  else:
    try:
      with open(claude_path) as f:
        data = json.load(f)
      assert data.get("name") == "makefile-workflow"
      assert "skills" in data
      print("✔ Claude Code plugin manifest (.claude-plugin/plugin.json) valid.")
    except Exception as e:
      errors.append(f"Invalid {claude_path}: {e}")

  # 2. Codex Plugin Manifest
  codex_path = ".codex-plugin/plugin.json"
  if not os.path.exists(codex_path):
    errors.append(f"Missing {codex_path}")
  else:
    try:
      with open(codex_path) as f:
        data = json.load(f)
      assert data.get("name") == "makefile-workflow"
      print("✔ OpenAI Codex plugin manifest (.codex-plugin/plugin.json) valid.")
    except Exception as e:
      errors.append(f"Invalid {codex_path}: {e}")

  # 3. CLAUDE.md
  claude_md = "CLAUDE.md"
  if not os.path.exists(claude_md):
    errors.append(f"Missing {claude_md}")
  else:
    with open(claude_md) as f:
      content = f.read()
    assert "Makefile Workflow" in content
    assert "Target 20" in content
    assert "Target 50" in content
    print("✔ Claude Code root instructions (CLAUDE.md) valid.")

  # 4. Cursor Rules
  cursorrules = ".cursorrules"
  cursor_mdc = ".cursor/rules/makefile-workflow.mdc"
  if not os.path.exists(cursorrules):
    errors.append(f"Missing {cursorrules}")
  else:
    with open(cursorrules) as f:
      cr_text = f.read()
    assert "Target 40" in cr_text or "deep-reasoning" in cr_text
    print("✔ Cursor rules (.cursorrules) valid with model reminder.")

  if not os.path.exists(cursor_mdc):
    errors.append(f"Missing {cursor_mdc}")
  else:
    with open(cursor_mdc) as f:
      mdc_content = f.read()
    assert mdc_content.startswith("---")
    assert "description:" in mdc_content
    assert "globs:" in mdc_content
    assert "alwaysApply:" in mdc_content
    assert "Model Switch Reminder" in mdc_content
    print("✔ Cursor MDC rule file (.cursor/rules/makefile-workflow.mdc) valid.")

  # 5. GitHub Copilot Instructions
  copilot_path = ".github/copilot-instructions.md"
  if not os.path.exists(copilot_path):
    errors.append(f"Missing {copilot_path}")
  else:
    with open(copilot_path) as f:
      c_content = f.read()
    assert "Makefile Workflow" in c_content
    assert "Six Pillars" in c_content
    assert "Interactive Model Switch Reminder" in c_content
    print("✔ GitHub Copilot instructions (.github/copilot-instructions.md) valid.")

  # 6. ChatGPT System Prompt
  chatgpt_path = "adapters/chatgpt/instructions.md"
  if not os.path.exists(chatgpt_path):
    errors.append(f"Missing {chatgpt_path}")
  else:
    with open(chatgpt_path) as f:
      cg_content = f.read()
    assert "Target 00" in cg_content
    assert "Target 90" in cg_content
    print("✔ ChatGPT system instructions (adapters/chatgpt/instructions.md) valid.")

  # 7. Hooks Configuration
  hooks_path = "hooks.json"
  if not os.path.exists(hooks_path):
    errors.append(f"Missing {hooks_path}")
  else:
    try:
      with open(hooks_path) as f:
        hooks_data = json.load(f)
      guard = hooks_data.get("makefile-workflow-guard", {})
      assert "PreToolUse" in guard
      assert "SessionStart" in guard
      print("✔ Antigravity hooks manifest (hooks.json) valid.")
    except Exception as e:
      errors.append(f"Invalid {hooks_path}: {e}")

  # 8. MCP Server Configuration
  mcp_path = "mcp_config.json"
  if not os.path.exists(mcp_path):
    errors.append(f"Missing {mcp_path}")
  else:
    try:
      with open(mcp_path) as f:
        mcp_data = json.load(f)
      servers = mcp_data.get("mcpServers", {})
      assert "makefile-workflow" in servers
      server_script = servers["makefile-workflow"]["args"][0]
      assert os.path.exists(server_script)
      print("✔ MCP configuration (mcp_config.json) valid.")
    except Exception as e:
      errors.append(f"Invalid {mcp_path}: {e}")

  # 9. Configuration Template & Reference Manual
  cfg_template = ".workflow/config.json.example"
  if not os.path.exists(cfg_template):
    errors.append(f"Missing {cfg_template}")
  else:
    print("✔ Workflow configuration template (.workflow/config.json.example) valid.")

  ref_13 = "skills/makefile-workflow/references/13_configuration_and_user_preferences.md"
  if not os.path.exists(ref_13):
    errors.append(f"Missing {ref_13}")
  else:
    print("✔ Configuration reference manual (references/13_configuration_and_user_preferences.md) valid.")

  if errors:
    print(f"\n❌ Validation failed with {len(errors)} error(s):")
    for err in errors:
      print(f"  - {err}")
    sys.exit(1)
  else:
    print("\n✔ All cross-agent configuration files validated successfully!")


if __name__ == "__main__":
  validate()
