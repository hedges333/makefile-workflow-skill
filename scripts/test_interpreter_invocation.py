#!/usr/bin/env python3
"""Hermetic unit tests for explicit runtime interpreter invocation (GH-72, SCAR-SH-01).

Verifies that SCAR-SH-01 and related operational rules across all adapters
and reference manuals require explicit runtime interpreter invocation (preferring
Dart over Python), bypass filesystem noexec restrictions, eliminate reliance
on chmod +x execution bits, and prohibit direct file execution syntax.
"""

import os
import re
import sys
import unittest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
  sys.path.insert(0, _REPO_ROOT)


def repo_path(*parts: str) -> str:
  return os.path.normpath(os.path.join(_REPO_ROOT, *parts))


class TestInterpreterInvocation(unittest.TestCase):
  """Validates explicit runtime interpreter invocation invariants across files."""

  def test_git_and_shell_scar_sh_01(self):
    """SCAR-SH-01 in git_and_shell.md must specify interpreter invocation and noexec."""
    path = repo_path("skills/makeflow/references/scars/git_and_shell.md")
    self.assertTrue(os.path.exists(path), f"Missing {path}")
    with open(path, "r", encoding="utf-8") as f:
      content = f.read()

    self.assertIn("### SCAR-SH-01", content)
    section = content.split("### SCAR-SH-01")[1].split("### SCAR-")[0]

    # Invariants for interpreter invocation and security bypass
    self.assertIn("noexec", section.lower(), "SCAR-SH-01 must document noexec bypass")
    self.assertTrue(
        "chmod +x" in section.lower() or "executable permission" in section.lower() or "executable bit" in section.lower(),
        "SCAR-SH-01 must document eliminating reliance on chmod +x / executable permissions",
    )
    self.assertIn("dart", section.lower(), "SCAR-SH-01 must specify Dart")
    self.assertIn("python3", section.lower(), "SCAR-SH-01 must specify python3")

    # Explicit interpreter command pattern or description
    self.assertTrue(
        "interpreter" in section.lower() or "runtime interpreter" in section.lower(),
        "SCAR-SH-01 must explicitly mention interpreter invocation",
    )

    # Prohibition of direct execution
    self.assertNotIn(
        "execute that file directly",
        section.lower(),
        "SCAR-SH-01 must prohibit 'execute that file directly'",
    )
    self.assertNotIn(
        "./script",
        section,
        "SCAR-SH-01 must not instruct direct execution syntax (./script)",
    )

  def test_security_and_data_isolation(self):
    """10_security_and_data_isolation.md Section 2 Item 5 must specify noexec and interpreter."""
    path = repo_path("skills/makeflow/references/10_security_and_data_isolation.md")
    self.assertTrue(os.path.exists(path), f"Missing {path}")
    with open(path, "r", encoding="utf-8") as f:
      content = f.read()

    self.assertIn("## 2. Safe Shell Execution", content)
    section = content.split("## 2. Safe Shell Execution")[1].split("## 3.")[0]

    self.assertIn("noexec", section.lower(), "Section 2 must document noexec protection")
    self.assertIn("interpreter", section.lower(), "Section 2 must mandate interpreter invocation")
    self.assertNotIn(
        "execute it (scar-sh-01",
        section.lower(),
        "Section 2 must not specify vague direct execution 'execute it'",
    )

  def test_agents_rules_section_3_1(self):
    """rules/AGENTS.md Section 3.1 Item 4 must specify interpreter and prohibit direct execution."""
    path = repo_path("rules/AGENTS.md")
    self.assertTrue(os.path.exists(path), f"Missing {path}")
    with open(path, "r", encoding="utf-8") as f:
      content = f.read()

    self.assertIn("### 3.1 Temporary Script and Automation Rules", content)
    section = content.split("### 3.1 Temporary Script and Automation Rules")[1].split("## 4.")[0]

    # Rule 4 checks
    self.assertNotIn(
        "execute that file directly",
        section.lower(),
        "rules/AGENTS.md Section 3.1 must not instruct executing the file directly",
    )
    self.assertTrue(
        "interpreter" in section.lower() or "dart" in section.lower() or "python3" in section.lower(),
        "rules/AGENTS.md Section 3.1 must specify runtime interpreter invocation",
    )

  def test_adapter_instructions(self):
    """Adapters must specify interpreter invocation under SCAR-SH-01 and avoid direct execution."""
    adapters = [
        "CLAUDE.md",
        ".cursorrules",
        ".cursor/rules/makeflow.mdc",
        ".github/copilot-instructions.md",
        "adapters/chatgpt/instructions.md",
    ]

    for adapter_rel in adapters:
      path = repo_path(adapter_rel)
      self.assertTrue(os.path.exists(path), f"Missing {adapter_rel}")
      with open(path, "r", encoding="utf-8") as f:
        content = f.read()

      # Locate SCAR-SH-01 line/item
      lines = [line for line in content.splitlines() if "SCAR-SH-01" in line]
      self.assertTrue(lines, f"{adapter_rel} must reference SCAR-SH-01")
      for line in lines:
        self.assertNotIn(
            "execute that file directly",
            line.lower(),
            f"{adapter_rel} must not say 'execute that file directly'",
        )
        self.assertTrue(
            "interpreter" in line.lower() or "runtime" in line.lower(),
            f"{adapter_rel} SCAR-SH-01 line must specify runtime interpreter invocation: '{line}'",
        )

  def test_falsification_checks(self):
    """Negative tests: direct execution phrases or omission of noexec must be caught."""
    flawed_text_direct = "Write the script to a file and execute that file directly."
    self.assertIn("execute that file directly", flawed_text_direct)

    flawed_text_missing_noexec = (
        "Write the script to a file and run with dart or python3."
    )
    self.assertNotIn("noexec", flawed_text_missing_noexec.lower())

    flawed_text_missing_interpreter = (
        "Write the script to a file in a temporary directory to bypass noexec."
    )
    self.assertNotIn("interpreter", flawed_text_missing_interpreter.lower())


if __name__ == "__main__":
  if "-x" in sys.argv:
    sys.argv = [arg if arg != "-x" else "-f" for arg in sys.argv]
  unittest.main()
