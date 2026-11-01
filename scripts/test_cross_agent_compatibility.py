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
    if "approved_tree.txt" not in content:
      errors.append("CLAUDE.md Target 40 command must reference .workflow/state/approved_tree.txt")
    if "..HEAD" in content:
      errors.append("CLAUDE.md Target 40 command must not diff against ..HEAD (use locked approved_tree)")
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
      assert "models" in cfg_data, f"{cfg_template} must declare 'models' section"
      for role in (
          "adversarial-critic",
          "archaeology-worker",
          "tdd-worker",
          "triage-worker",
      ):
        assert (
            cfg_data["models"].get(role) == "inherit"
        ), f"{cfg_template} role '{role}' must default to 'inherit', got '{cfg_data['models'].get(role)}'"
      with open(cfg_template) as f:
        cfg_raw = f.read()
      if "Antigravity" not in cfg_raw or "inherit" not in cfg_raw:
        errors.append(f"{cfg_template} must document Antigravity specificity and inherit defaults")
      if "flash_lite" not in cfg_raw or "pro" not in cfg_raw:
        errors.append(f"{cfg_template} must document valid Antigravity model tiers (inherit, flash_lite, flash, pro)")
      if "effort" not in cfg_raw.lower():
        errors.append(f"{cfg_template} must document session reasoning effort inheritance")
      print("✔ Workflow configuration template (.workflow/config.json.example) valid.")
    except Exception as e:
      errors.append(f"Invalid {cfg_template}: {e}")

  ref_13 = "skills/makefile-workflow/references/13_configuration_and_user_preferences.md"
  if not os.path.exists(ref_13):
    errors.append(f"Missing {ref_13}")
  else:
    with open(ref_13) as f:
      r13_text = f.read()
    for role in (
        "adversarial-critic",
        "archaeology-worker",
        "tdd-worker",
        "triage-worker",
    ):
      if f"`{role}`: `inherit`" not in r13_text and f'"{role}": "inherit"' not in r13_text:
        errors.append(f"{ref_13} must document 'inherit' default for {role}")
    if "flash_lite" not in r13_text or "flash" not in r13_text or "pro" not in r13_text:
      errors.append(f"{ref_13} must document all four Antigravity tier enums")
    if "reasoning effort" not in r13_text.lower() and "/effort" not in r13_text:
      errors.append(f"{ref_13} must document reasoning effort (/effort) inheritance")
    if not any("references/13_" in e for e in errors):
      print("✔ Configuration reference manual (references/13_configuration_and_user_preferences.md) valid.")

  ref_08 = "skills/makefile-workflow/references/08_subagent_orchestration.md"
  if not os.path.exists(ref_08):
    errors.append(f"Missing {ref_08}")
  else:
    with open(ref_08) as f:
      r08_text = f.read()
    if "Default tier: flash" in r08_text or "Default tier: pro" in r08_text:
      errors.append(f"{ref_08} must default all subagents to inherit")

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
    if "SCAR-TEST-10" not in r09_text:
      errors.append(f"{ref_09} must document SCAR-TEST-10")
    if "SCAR-SYS-05" not in r09_text:
      errors.append(f"{ref_09} must document SCAR-SYS-05")
    if "SCAR-SYS-06" not in r09_text:
      errors.append(f"{ref_09} must document SCAR-SYS-06")
    if "SCAR-TEST-11" not in r09_text:
      errors.append(f"{ref_09} must document SCAR-TEST-11")
    if "Hub-and-Spoke" not in r09_text and "Master Routing" not in r09_text and "Master Index" not in r09_text:
      errors.append(f"{ref_09} must document Hub-and-Spoke architecture and Master Index")
    if "scars/process.md" not in r09_text or "scars/testing.md" not in r09_text:
      errors.append(f"{ref_09} must link to domain spoke category files")

  # 11b. Hub-and-Spoke Category Files (references/scars/)
  scars_dir = "skills/makefile-workflow/references/scars"
  spoke_files = (
      "process.md",
      "testing.md",
      "git_and_shell.md",
      "system_and_os.md",
      "data_and_database.md",
      "security_and_auth.md",
      "tooling_and_hci.md",
  )
  for sf in spoke_files:
    sf_path = os.path.join(scars_dir, sf)
    if not os.path.exists(sf_path):
      errors.append(f"Missing category spoke file {sf_path}")

  testing_spoke = os.path.join(scars_dir, "testing.md")
  if os.path.exists(testing_spoke):
    with open(testing_spoke) as f:
      t_text = f.read()
    if "SCAR-TEST-10" not in t_text:
      errors.append(f"{testing_spoke} must document SCAR-TEST-10")
    if "SCAR-TEST-11" not in t_text:
      errors.append(f"{testing_spoke} must document SCAR-TEST-11")
    if "burden" not in t_text.lower() or "shift-left" not in t_text.lower():
      errors.append(f"{testing_spoke} must document shift-left testing burden balance for SCAR-TEST-11")

  system_spoke = os.path.join(scars_dir, "system_and_os.md")
  if os.path.exists(system_spoke):
    with open(system_spoke) as f:
      sys_text = f.read()
    if "SCAR-SYS-05" not in sys_text:
      errors.append(f"{system_spoke} must document SCAR-SYS-05")
    if "shutil.copyfile" not in sys_text or "copystat" not in sys_text:
      errors.append(f"{system_spoke} must document shutil.copyfile and copystat for SCAR-SYS-05")
    if "SCAR-SYS-06" not in sys_text:
      errors.append(f"{system_spoke} must document SCAR-SYS-06")
    if "TMPDIR" not in sys_text or "validate_runtime_path" not in sys_text:
      errors.append(f"{system_spoke} must document TMPDIR and validate_runtime_path for SCAR-SYS-06")

  # 11c. Full Language Name Polyglot Scars (dart_flutter.md)
  dart_guide = "skills/makefile-workflow/references/polyglot/dart_flutter.md"
  if not os.path.exists(dart_guide):
    errors.append(f"Missing {dart_guide}")
  else:
    with open(dart_guide) as f:
      dg_text = f.read()
    for d_scar in ("SCAR-LANG-DART-01", "SCAR-LANG-DART-02", "SCAR-LANG-DART-03", "SCAR-LANG-DART-04"):
      if d_scar not in dg_text:
        errors.append(f"{dart_guide} must document full language name {d_scar}")

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
    if "SCAR-TEST-10" not in r03_text:
      errors.append(f"{ref_03} must document SCAR-TEST-10")

  ref_04 = "skills/makefile-workflow/references/04_testing_isolation.md"
  if not os.path.exists(ref_04):
    errors.append(f"Missing {ref_04}")
  else:
    with open(ref_04) as f:
      r04_text = f.read()
    if "SCAR-TEST-08" not in r04_text or "two-tier" not in r04_text.lower():
      errors.append(f"{ref_04} must document SCAR-TEST-08 and two-tier test isolation")
    if "ephemeral loopback socket" not in r04_text.lower() and "127.0.0.1:0" not in r04_text:
      errors.append(f"{ref_04} must document self-contained ephemeral loopback sockets (127.0.0.1:0)")

  # Archaeology worker and planning manual shift-left checks (SCAR-TEST-11)
  arch_worker = "agents/archaeology-worker.md"
  if not os.path.exists(arch_worker):
    errors.append(f"Missing {arch_worker}")
  else:
    with open(arch_worker) as f:
      aw_text = f.read()
    if "failure mechanism" not in aw_text.lower() or "burden" not in aw_text.lower():
      errors.append(f"{arch_worker} must instruct worker to classify failure mechanisms and evaluate testing burden balance")

  ref_02 = "skills/makefile-workflow/references/02_archaeology_and_planning.md"
  if not os.path.exists(ref_02):
    errors.append(f"Missing {ref_02}")
  else:
    with open(ref_02) as f:
      r02_text = f.read()
    if "burden" not in r02_text.lower() or "Testing Strategy and Burden-Balance" not in r02_text:
      errors.append(f"{ref_02} must mandate Testing Strategy and Burden-Balance Analysis in Target 20 plan disclosures")

  # Critic agent and Six Pillars review definitions
  critic_agent = "agents/adversarial-critic.md"
  if not os.path.exists(critic_agent):
    errors.append(f"Missing {critic_agent}")
  else:
    with open(critic_agent) as f:
      critic_text = f.read()
    if "approved_tree" not in critic_text:
      errors.append(f"{critic_agent} Rule 2 must reference approved_tree.txt")
    if "git diff $(git merge-base HEAD origin/main) HEAD" in critic_text:
      errors.append(f"{critic_agent} Rule 2 must not diff against HEAD")
    if "comprehensiveness" not in critic_text.lower() and "comprehensive" not in critic_text.lower():
      errors.append(f"{critic_agent} Pillar 2 must assess test comprehensiveness")
    if "burden" not in critic_text.lower() and "balance" not in critic_text.lower():
      errors.append(f"{critic_agent} Pillar 2 must assess test execution burden balance")
    if "ephemeral" not in critic_text.lower():
      errors.append(f"{critic_agent} Pillar 2 must clarify ephemeral loopback socket permissions")
    if "simple english" not in critic_text.lower():
      errors.append(f"{critic_agent} Pillar 5 must enforce Simple English standards")
    if "20 words" not in critic_text:
      errors.append(f"{critic_agent} Pillar 5 must document sentence length caps (20 words)")

  ref_04_review = "skills/makefile-workflow/references/04_six_pillars_adversarial_review.md"
  if not os.path.exists(ref_04_review):
    errors.append(f"Missing {ref_04_review}")
  else:
    with open(ref_04_review) as f:
      r04_rev_text = f.read()
    if "comprehensiveness" not in r04_rev_text.lower() and "comprehensive" not in r04_rev_text.lower():
      errors.append(f"{ref_04_review} Pillar 2 must evaluate test comprehensiveness")
    if "burden" not in r04_rev_text.lower():
      errors.append(f"{ref_04_review} Pillar 2 must evaluate test burden balance")
    if "ephemeral" not in r04_rev_text.lower():
      errors.append(f"{ref_04_review} Pillar 2 must clarify ephemeral loopback socket permissions")
    if "simple english" not in r04_rev_text.lower():
      errors.append(f"{ref_04_review} Pillar 5 must evaluate Simple English compliance")
    if "20 words" not in r04_rev_text:
      errors.append(f"{ref_04_review} Pillar 5 must document sentence length caps (20 words)")

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
    if "SCAR-SYS-05" not in r10_text or "copyfile" not in r10_text.lower():
      errors.append(f"{ref_10} Section 5 must document SCAR-SYS-05 and cross-user file promotion")
    if "SCAR-SYS-06" not in r10_text or "TMPDIR" not in r10_text:
      errors.append(f"{ref_10} Section 6 must document SCAR-SYS-06 and native runtime environment path pre-flight")

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
    if "`agyModelTiers[\"archaeology-worker\"]` (default `inherit`)" not in s_text:
      errors.append(f"{skill_md} Target 15 must document 'archaeology-worker' default inherit")
    if "`agyModelTiers[\"tdd-worker\"]` (default `inherit`)" not in s_text:
      errors.append(f"{skill_md} Target 30 must document 'tdd-worker' default inherit")
    if "`agyModelTiers[\"adversarial-critic\"]` (default `inherit`)" not in s_text:
      errors.append(f"{skill_md} Target 40 must document 'adversarial-critic' default inherit")
    if "`agyModelTiers[\"triage-worker\"]` (default `inherit`)" not in s_text:
      errors.append(f"{skill_md} Target 70 must document 'triage-worker' default inherit")
    if "burden" not in s_text.lower() and "feasibility" not in s_text.lower():
      errors.append(f"{skill_md} must document testing burden balance in Target 15 / Target 20")

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
    if "SCAR-TEST-10" not in a_text or "static analysis" not in a_text.lower():
      errors.append(f"{agents_md} Section 3 must document SCAR-TEST-10 and pre-flight structural static analysis")
    if "SCAR-TEST-08" not in a_text or "two tiers" not in a_text.lower():
      errors.append(f"{agents_md} Section 2 must document SCAR-TEST-08 and two-tier test isolation")
    if "ephemeral loopback socket" not in a_text.lower() and "127.0.0.1:0" not in a_text:
      errors.append(f"{agents_md} Section 2 must clarify ephemeral loopback socket permissions")
    if "SCAR-SYS-05" not in a_text or "shutil.copyfile" not in a_text:
      errors.append(f"{agents_md} Section 2 must document SCAR-SYS-05 cross-user file promotion")
    if "SCAR-SYS-06" not in a_text or "validate_runtime_path" not in a_text and "TMPDIR" not in a_text:
      errors.append(f"{agents_md} Section 2 must document SCAR-SYS-06 native runtime environment path pre-flight")
    if "SCAR-TEST-11" not in a_text or "burden-balance" not in a_text.lower() and "burden balance" not in a_text.lower():
      errors.append(f"{agents_md} Section 1.1 must document SCAR-TEST-11 testing strategy and burden-balance analysis")
    if not any("rules/AGENTS.md" in e for e in errors):
      print(f"✔ Antigravity artifact lifecycle and demotion rules ({agents_md}) valid.")

  # 14. SimpleEnglish Companion Plugin Recommendation & Subagent Roles in README.md
  readme_path = "README.md"
  if not os.path.exists(readme_path):
    errors.append(f"Missing {readme_path}")
  else:
    with open(readme_path) as f:
      rm_text = f.read()
    if "Recommended Companion: SimpleEnglish Plugin" not in rm_text or "https://github.com/AminBlg/SimpleEnglish" not in rm_text:
      errors.append(f"{readme_path} must recommend SimpleEnglish companion plugin under Installation with repository URL")
    else:
      print("✔ SimpleEnglish companion plugin recommended in README.md.")

    for role in (
        "adversarial-critic",
        "archaeology-worker",
        "tdd-worker",
        "triage-worker",
    ):
      if f'"{role}": "inherit"' not in rm_text:
        errors.append(f"{readme_path} config snippet must show '{role}': 'inherit'")
      if role not in rm_text:
        errors.append(f"{readme_path} must document worker role '{role}'")

    if "triage-worker" not in rm_text or "quiescence" not in rm_text.lower() or "triage table" not in rm_text.lower():
      errors.append(f"{readme_path} must explain triage-worker purpose (CI polling, quiescence, triage table)")
    if "archaeology-worker" not in rm_text or "polyglot" not in rm_text.lower():
      errors.append(f"{readme_path} must explain archaeology-worker purpose (discovery, polyglot scan)")
    if "adversarial-critic" not in rm_text or "six pillars" not in rm_text.lower():
      errors.append(f"{readme_path} must explain adversarial-critic purpose (independent review, Six Pillars)")
    if "tdd-worker" not in rm_text or "red-green-refactor" not in rm_text.lower():
      errors.append(f"{readme_path} must explain tdd-worker purpose (TDD, red-green-refactor)")
    if "reasoning effort" not in rm_text.lower() and "/effort" not in rm_text:
      errors.append(f"{readme_path} must document reasoning effort inheritance for 'inherit'")
    if "flash_lite" not in rm_text or "flash" not in rm_text or "pro" not in rm_text:
      errors.append(f"{readme_path} must document Antigravity valid enum tiers (inherit, flash_lite, flash, pro)")

  # 15. Pre-flight Static Check Integration in Makefile and scripts (SCAR-TEST-10)
  makefile_path = "Makefile"
  if not os.path.exists(makefile_path):
    errors.append(f"Missing {makefile_path}")
  else:
    with open(makefile_path) as f:
      mk_text = f.read()
    if "test-static:" not in mk_text:
      errors.append(f"{makefile_path} must define 'test-static:' target")
    if "test: test-static" not in mk_text:
      errors.append(f"{makefile_path} 'test:' target must list 'test-static' as first prerequisite")
    if "test-safe-copy:" not in mk_text:
      errors.append(f"{makefile_path} must define 'test-safe-copy:' target")
    if "test-safe-copy" not in mk_text.split("test:")[1].split("\n")[0]:
      errors.append(f"{makefile_path} 'test:' target must list 'test-safe-copy' prerequisite")
    if "test-env-preflight:" not in mk_text:
      errors.append(f"{makefile_path} must define 'test-env-preflight:' target")
    if "test-env-preflight" not in mk_text.split("test:")[1].split("\n")[0]:
      errors.append(f"{makefile_path} 'test:' target must list 'test-env-preflight' prerequisite")

  static_check_script = "scripts/static_check.py"
  if not os.path.exists(static_check_script):
    errors.append(f"Missing {static_check_script}")
  static_test_script = "scripts/test_static_analysis.py"
  if not os.path.exists(static_test_script):
    errors.append(f"Missing {static_test_script}")
  safe_copy_script = "scripts/safe_copy.py"
  if not os.path.exists(safe_copy_script):
    errors.append(f"Missing {safe_copy_script}")
  safe_copy_test_script = "scripts/test_safe_copy.py"
  if not os.path.exists(safe_copy_test_script):
    errors.append(f"Missing {safe_copy_test_script}")
  env_preflight_script = "scripts/env_preflight.py"
  if not os.path.exists(env_preflight_script):
    errors.append(f"Missing {env_preflight_script}")
  env_preflight_test_script = "scripts/test_env_preflight.py"
  if not os.path.exists(env_preflight_test_script):
    errors.append(f"Missing {env_preflight_test_script}")

  if errors:
    print(f"\n❌ Validation failed with {len(errors)} error(s):")
    for err in errors:
      print(f"  - {err}")
    sys.exit(1)
  else:
    print("\n✔ All cross-agent configuration files validated successfully!")


if __name__ == "__main__":
  validate()
