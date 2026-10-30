#!/usr/bin/env python3
"""Test suite for SessionStart and PreToolUse hook scripts."""

import json
import os
import subprocess
import tempfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRE_TOOL = os.path.join(REPO_ROOT, "scripts", "pre_tool_guard.py")
SESSION_START = os.path.join(REPO_ROOT, "scripts", "session_start.py")


def run_hook(script_path, payload, cwd=None, env=None):
  proc = subprocess.run(
      ["python3", script_path],
      input=json.dumps(payload),
      text=True,
      capture_output=True,
      cwd=cwd or REPO_ROOT,
      env=env,
      check=True,
  )
  return json.loads(proc.stdout)


def test_pre_tool_guard():
  # 1. Hostname with 'production' is denied
  r1 = run_hook(
      PRE_TOOL,
      {
          "toolCall": {
              "name": "run_command",
              "args": {"CommandLine": "psql -h production.db.internal myapp"},
          }
      },
  )
  assert r1["decision"] == "deny"

  # 2. Underscore database name 'myapp_prod' with mariadb is denied
  r2 = run_hook(
      PRE_TOOL,
      {
          "toolCall": {
              "name": "run_command",
              "args": {"CommandLine": "mariadb -u root myapp_prod"},
          }
      },
  )
  assert r2["decision"] == "deny"

  # 3. Safe *_test database and 'product' table name are allowed
  r3 = run_hook(
      PRE_TOOL,
      {
          "toolCall": {
              "name": "run_command",
              "args": {
                  "CommandLine": (
                      "psql -h localhost myapp_test -c 'SELECT * FROM product'"
                  )
              },
          }
      },
  )
  assert r3["decision"] == "allow"

  # 4. Force-push to main is denied
  r4 = run_hook(
      PRE_TOOL,
      {
          "toolCall": {
              "name": "run_command",
              "args": {"CommandLine": "git push --force origin main"},
          }
      },
  )
  assert r4["decision"] == "deny"

  # 5. git commit checks workspacePaths/.workflow/state/ even when cwd is /tmp
  with tempfile.TemporaryDirectory() as ws_dir, tempfile.TemporaryDirectory() as hook_cwd:
    r5_missing = run_hook(
        PRE_TOOL,
        {
            "workspacePaths": [ws_dir],
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "git commit -m 'feat: add test'"},
            },
        },
        cwd=hook_cwd,
    )
    assert r5_missing["decision"] == "force_ask"
    assert "missing" in r5_missing["reason"]

    state_dir = os.path.join(ws_dir, ".workflow", "state")
    os.makedirs(state_dir)
    with open(os.path.join(state_dir, "45_review_approved.md"), "w", encoding="utf-8") as f:
      f.write("APPROVED\n")

    r5_present = run_hook(
        PRE_TOOL,
        {
            "workspacePaths": [ws_dir],
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "git commit -m 'feat: add test'"},
            },
        },
        cwd=hook_cwd,
    )
    assert r5_present["decision"] == "force_ask"
    assert "present" in r5_present["reason"]

    # 6. git push and gh pr merge always prompt with force_ask
    r6 = run_hook(
        PRE_TOOL,
        {
            "workspacePaths": [ws_dir],
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "git push -u origin feat/1-test"},
            },
        },
        cwd=hook_cwd,
    )
    assert r6["decision"] == "force_ask"

    r7 = run_hook(
        PRE_TOOL,
        {
            "workspacePaths": [ws_dir],
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "gh pr merge 1 --squash"},
            },
        },
        cwd=hook_cwd,
    )
    assert r7["decision"] == "force_ask"

  print("✔ PreToolUse hook assertions passed.")


def test_session_start():
  with tempfile.TemporaryDirectory() as ws_dir, tempfile.TemporaryDirectory() as hook_cwd:
    # Empty workspace produces empty object when no global config exists
    state_dir = os.path.join(ws_dir, ".workflow", "state")
    os.makedirs(state_dir)
    with open(os.path.join(state_dir, "10_ticket.md"), "w", encoding="utf-8") as f:
      f.write("# Ticket 1\n")
    with open(
        os.path.join(ws_dir, ".workflow", "config.json"),
        "w",
        encoding="utf-8",
    ) as f:
      json.dump({"models": {"adversarial-critic": "gemini-4-argon-high"}}, f)

    res = run_hook(
        SESSION_START,
        {"workspacePaths": [ws_dir]},
        cwd=hook_cwd,
    )
    steps = res.get("injectSteps", [])
    assert len(steps) == 1
    msg = steps[0]["systemMessage"]["systemMessage"]
    assert "1 state card(s)" in msg
    assert "gemini-4-argon-high" in msg

  print("✔ SessionStart hook assertions passed.")


if __name__ == "__main__":
  test_pre_tool_guard()
  test_session_start()
