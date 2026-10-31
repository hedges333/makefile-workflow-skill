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
    try:
      with open(cfg_template) as f:
        cfg_data = json.load(f)
      assert "database" in cfg_data
      assert "prodDatabases" in cfg_data["database"]
      assert "testDatabases" in cfg_data["database"]
      assert "prodHosts" in cfg_data["database"]
      print("✔ Workflow configuration template (.workflow/config.json.example) valid.")
    except Exception as e:
      errors.append(f"Invalid {cfg_template}: {e}")

  ref_13 = "skills/makefile-workflow/references/13_configuration_and_user_preferences.md"
  if not os.path.exists(ref_13):
    errors.append(f"Missing {ref_13}")
  else:
    print("✔ Configuration reference manual (references/13_configuration_and_user_preferences.md) valid.")

  # 10. Design Patterns Reference Manual
  ref_14 = "skills/makefile-workflow/references/14_design_patterns_and_architecture.md"
  if not os.path.exists(ref_14):
    errors.append(f"Missing {ref_14}")
  else:
    with open(ref_14) as f:
      r14_text = f.read()
    if "Factory Method" not in r14_text or "Game Loop" not in r14_text or "ORM" not in r14_text:
      errors.append(f"Incomplete pattern coverage in {ref_14}")
    else:
      print("✔ Design patterns reference manual (references/14_design_patterns_and_architecture.md) valid.")

  # 11. Polyglot 27-Language Guides and Manifests
  for guide_name in (
      "gdscript_godot.md",
      "nim.md",
      "haxe.md",
      "odin.md",
      "dlang.md",
  ):
    guide_path = os.path.join(
        "skills", "makefile-workflow", "references", "polyglot", guide_name
    )
    if not os.path.exists(guide_path):
      errors.append(f"Missing polyglot guide {guide_path}")
  if not any("polyglot guide" in e for e in errors):
    with open("skills/makefile-workflow/references/polyglot/dlang.md") as f:
      dlang_text = f.read()
    if "dfmt --check" in dlang_text:
      errors.append("dlang.md must not use nonexistent 'dfmt --check' flag")
    else:
      print("✔ All 5 new polyglot guides (GDScript, Nim, Haxe, Odin, D) present.")

  for manifest_path in (
      "plugin.json",
      ".claude-plugin/plugin.json",
      ".codex-plugin/plugin.json",
  ):
    if os.path.exists(manifest_path):
      with open(manifest_path) as f:
        m_data = json.load(f)
      if m_data.get("version") != "1.4.1" or "27-language" not in m_data.get(
          "description", ""
      ):
        errors.append(
            f"Manifest {manifest_path} must declare version 1.4.1 and 27-language support"
        )

  ref_09 = "skills/makefile-workflow/references/09_synthetic_scars_catalog.md"
  if not os.path.exists(ref_09):
    errors.append(f"Missing {ref_09}")
  else:
    with open(ref_09) as f:
      r09_text = f.read()
    if "SCAR-GIT-25" not in r09_text:
      errors.append(f"{ref_09} must document SCAR-GIT-25")
    if "SCAR-PROC-103" not in r09_text:
      errors.append(f"{ref_09} must document SCAR-PROC-103")
    if "SCAR-PROC-104" not in r09_text:
      errors.append(f"{ref_09} must document SCAR-PROC-104")
    if "SCAR-GIT-30" not in r09_text:
      errors.append(f"{ref_09} must document SCAR-GIT-30")
    if "SCAR-TEST-08" not in r09_text:
      errors.append(f"{ref_09} must document SCAR-TEST-08")
    if "SCAR-TEST-09" not in r09_text:
      errors.append(f"{ref_09} must document SCAR-TEST-09")
    if "SCAR-TOOL-07" not in r09_text:
      errors.append(f"{ref_09} must document SCAR-TOOL-07")

  ref_03 = "skills/makefile-workflow/references/03_tdd_and_code_quality.md"
  if not os.path.exists(ref_03):
    errors.append(f"Missing {ref_03}")
  else:
    with open(ref_03) as f:
      r03_text = f.read()
    if "SCAR-PROC-104" not in r03_text:
      errors.append(f"{ref_03} must document SCAR-PROC-104")
    if "SCAR-TEST-09" not in r03_text:
      errors.append(f"{ref_03} must document SCAR-TEST-09")

  ref_04 = "skills/makefile-workflow/references/04_testing_isolation.md"
  if not os.path.exists(ref_04):
    errors.append(f"Missing {ref_04}")
  else:
    with open(ref_04) as f:
      r04_text = f.read()
    if "SCAR-TEST-08" not in r04_text or "two-tier" not in r04_text.lower():
      errors.append(f"{ref_04} must document SCAR-TEST-08 and two-tier test isolation")

  ref_10 = "skills/makefile-workflow/references/10_security_and_data_isolation.md"
  if not os.path.exists(ref_10):
    errors.append(f"Missing {ref_10}")
  else:
    with open(ref_10) as f:
      r10_text = f.read()
    if "git reset --hard" not in r10_text or "git rebase" not in r10_text:
      errors.append(f"{ref_10} must document destructive Git command protections")
    if "SCAR-TOOL-07" not in r10_text or "prefer dart" not in r10_text.lower():
      errors.append(f"{ref_10} must document Dart scratch script and temporary directory rules")

  # 12. SKILL.md Single-Page Size Ceiling (SCAR-PROC-99)
  skill_md = "skills/makefile-workflow/SKILL.md"
  if not os.path.exists(skill_md):
    errors.append(f"Missing {skill_md}")
  else:
    skill_bytes = os.path.getsize(skill_md)
    if skill_bytes > 24576:
      errors.append(
          f"{skill_md} is {skill_bytes} bytes, exceeding SCAR-PROC-99 24576-byte limit"
      )
    else:
      print(f"✔ {skill_md} size ({skill_bytes} bytes) is within 24 KB limit.")
    with open(skill_md) as f:
      s_text = f.read()
    if "<brain>" in s_text or "<brain/" in s_text:
      errors.append(
          f"{skill_md} must remain platform-neutral and not reference '<brain>'"
      )
    else:
      print(f"✔ {skill_md} is platform-neutral (no <brain> references).")

  # 13. Antigravity Plan Artifact Lifecycle & Demotion Rules (rules/AGENTS.md)
  agents_md = "rules/AGENTS.md"
  if not os.path.exists(agents_md):
    errors.append(f"Missing {agents_md}")
  else:
    with open(agents_md) as f:
      a_text = f.read()
    if "<brain>/plan.md" not in a_text:
      errors.append(f"{agents_md} must reference single artifact '<brain>/plan.md'")
    if "UserFacing: false" not in a_text or "RequestFeedback: false" not in a_text:
      errors.append(f"{agents_md} must specify demotion with UserFacing: false and RequestFeedback: false")
    if "20_plan_approved.md" not in a_text:
      errors.append(f"{agents_md} must guard against duplicate execution using 20_plan_approved.md")
    if "built-in" not in a_text or "shell `rm`" not in a_text and "shell rm" not in a_text:
      errors.append(f"{agents_md} must specify built-in tool demotion without shell rm")
    if "prefer Dart over Python" not in a_text:
      errors.append(f"{agents_md} must specify preference for Dart over Python for scratch scripts")
    if "never attempt to install dart" not in a_text.lower():
      errors.append(f"{agents_md} must forbid attempting to install Dart")
    if "temporary directory" not in a_text:
      errors.append(f"{agents_md} must specify writing temporary scripts to temporary directories")
    if "SCAR-PROC-104" not in a_text or "targeted test loops" not in a_text.lower():
      errors.append(f"{agents_md} Section 3 must document SCAR-PROC-104 and targeted test loops")
    if "SCAR-TEST-09" not in a_text or "fail-fast" not in a_text.lower():
      errors.append(f"{agents_md} Section 3 must document SCAR-TEST-09 and fail-fast targeted test loops")
    if "SCAR-TEST-08" not in a_text or "two tiers" not in a_text.lower():
      errors.append(f"{agents_md} Section 2 must document SCAR-TEST-08 and two-tier test isolation")
    if not any("rules/AGENTS.md" in e for e in errors):
      print(f"✔ Antigravity artifact lifecycle and demotion rules ({agents_md}) valid.")

  if errors:
    print(f"\n❌ Validation failed with {len(errors)} error(s):")
    for err in errors:
      print(f"  - {err}")
    sys.exit(1)
  else:
    print("\n✔ All cross-agent configuration files validated successfully!")


if __name__ == "__main__":
  validate()
