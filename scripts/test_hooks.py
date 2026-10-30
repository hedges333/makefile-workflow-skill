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

    # 7. Configured prodDatabases, prodHosts, and testDatabases in .workflow/config.json
    with open(
        os.path.join(ws_dir, ".workflow", "config.json"),
        "w",
        encoding="utf-8",
    ) as f:
      json.dump(
          {
              "database": {
                  "prodDatabases": ["billing_live"],
                  "testDatabases": ["myapp_test"],
                  "prodHosts": ["db.company.internal"],
              }
          },
          f,
      )

    r8_custom_prod = run_hook(
        PRE_TOOL,
        {
            "workspacePaths": [ws_dir],
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "psql -h localhost billing_live"},
            },
        },
        cwd=hook_cwd,
    )
    assert r8_custom_prod["decision"] == "deny"

    r9_custom_host = run_hook(
        PRE_TOOL,
        {
            "workspacePaths": [ws_dir],
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "psql -h db.company.internal myapp_test"},
            },
        },
        cwd=hook_cwd,
    )
    assert r9_custom_host["decision"] == "deny"

    r10_test_db_prod_col = run_hook(
        PRE_TOOL,
        {
            "workspacePaths": [ws_dir],
            "toolCall": {
                "name": "run_command",
                "args": {
                    "CommandLine": (
                        "psql -h localhost myapp_test -c 'SELECT prod FROM items'"
                    )
                },
            },
        },
        cwd=hook_cwd,
    )
    assert r10_test_db_prod_col["decision"] == "allow"

    r10_prod_host_still_denied = run_hook(
        PRE_TOOL,
        {
            "workspacePaths": [ws_dir],
            "toolCall": {
                "name": "run_command",
                "args": {
                    "CommandLine": (
                        "psql -h prod.db.internal myapp_test -c 'SELECT 1'"
                    )
                },
            },
        },
        cwd=hook_cwd,
    )
    assert r10_prod_host_still_denied["decision"] == "deny"

    # 8. Environment variable database overrides
    custom_env = dict(os.environ)
    custom_env["MAKEFILE_WORKFLOW_PROD_DBS"] = "core_live,analytics_main"
    custom_env["MAKEFILE_WORKFLOW_TEST_DBS"] = "analytics_sandbox"
    custom_env["MAKEFILE_WORKFLOW_PROD_HOSTS"] = "rds.live.internal"

    r11_env_prod = run_hook(
        PRE_TOOL,
        {
            "workspacePaths": [ws_dir],
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "psql -h localhost core_live"},
            },
        },
        cwd=hook_cwd,
        env=custom_env,
    )
    assert r11_env_prod["decision"] == "deny"

    r11_env_host = run_hook(
        PRE_TOOL,
        {
            "workspacePaths": [ws_dir],
            "toolCall": {
                "name": "run_command",
                "args": {
                    "CommandLine": "psql -h rds.live.internal analytics_sandbox"
                },
            },
        },
        cwd=hook_cwd,
        env=custom_env,
    )
    assert r11_env_host["decision"] == "deny"

    r11_env_test = run_hook(
        PRE_TOOL,
        {
            "workspacePaths": [ws_dir],
            "toolCall": {
                "name": "run_command",
                "args": {
                    "CommandLine": (
                        "psql -h localhost analytics_sandbox -c 'SELECT prod FROM events'"
                    )
                },
            },
        },
        cwd=hook_cwd,
        env=custom_env,
    )
    assert r11_env_test["decision"] == "allow"

    # 9. Compound commands, quoted/PGHOST/host= flags, hyphenated names, multi-DB args, URI userinfo@, and non-string JSON items
    with open(
        os.path.join(ws_dir, ".workflow", "config.json"),
        "w",
        encoding="utf-8",
    ) as f:
      json.dump(
          {
              "database": {
                  "prodDatabases": [1, True, None, "billing-live"],
                  "testDatabases": [1, False, None, "myapp_test", "billing"],
                  "prodHosts": [1, None, "db.company.internal"],
              }
          },
          f,
      )

    for blocked_cmd in (
        "pg_dump myapp_prod | psql myapp_test",
        "psql myapp_test -c 'SELECT 1' && psql myapp_prod -c 'DROP TABLE users'",
        'psql -h "prod.db.internal" myapp_test',
        "psql --host='prod.db.internal' myapp_test",
        "PGHOST=prod.db.internal psql myapp_test",
        "psql -hprod.db.internal myapp_test",
        'psql "host=prod.db.internal dbname=myapp_test"',
        "psql -h localhost billing-prod",
        "psql -h localhost billing-live",
        "pg_restore -d myapp_prod myapp_test.dump",
        'sqlite3 prod.db ".backup myapp_test.db"',
        "psql -h 127.0.0.1 myapp_prod",
    ):
      res_blocked = run_hook(
          PRE_TOOL,
          {
              "workspacePaths": [ws_dir],
              "toolCall": {
                  "name": "run_command",
                  "args": {"CommandLine": blocked_cmd},
              },
          },
          cwd=hook_cwd,
      )
      assert res_blocked["decision"] == "deny", (
          f"Expected deny for '{blocked_cmd}', got {res_blocked}"
      )

    for allowed_cmd in (
        'psql "postgresql://prod_user:secret@localhost:5432/myapp_test" -c "SELECT prod FROM items"',
        "psql -h 127.0.0.1 myapp_test -c 'SELECT 1; SELECT prod FROM items'",
        'sqlite3 myapp_test.db "SELECT prod FROM items"',
    ):
      res_allowed = run_hook(
          PRE_TOOL,
          {
              "workspacePaths": [ws_dir],
              "toolCall": {
                  "name": "run_command",
                  "args": {"CommandLine": allowed_cmd},
              },
          },
          cwd=hook_cwd,
      )
      assert res_allowed["decision"] == "allow", (
          f"Expected allow for '{allowed_cmd}', got {res_allowed}"
      )

  print("✔ PreToolUse hook assertions passed.")


def test_session_start():
  with tempfile.TemporaryDirectory() as ws_dir, tempfile.TemporaryDirectory() as hook_cwd:
    # 1. Valid config with models and database lists
    state_dir = os.path.join(ws_dir, ".workflow", "state")
    os.makedirs(state_dir)
    with open(os.path.join(state_dir, "10_ticket.md"), "w", encoding="utf-8") as f:
      f.write("# Ticket 1\n")
    with open(
        os.path.join(ws_dir, ".workflow", "config.json"),
        "w",
        encoding="utf-8",
    ) as f:
      json.dump(
          {
              "models": {"adversarial-critic": "gemini-4-argon-high"},
              "database": {
                  "prodDatabases": ["billing_live", 1, None],
                  "testDatabases": ["billing_test"],
              },
          },
          f,
      )

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
    assert "billing_live" in msg
    assert "None" not in msg

    # 2. Environment variable database overrides in SessionStart
    env_override = dict(os.environ)
    env_override["MAKEFILE_WORKFLOW_PROD_DBS"] = "warehouse_live"
    env_override["MAKEFILE_WORKFLOW_TEST_DBS"] = "warehouse_test"
    env_override["MAKEFILE_WORKFLOW_PROD_HOSTS"] = "warehouse.internal"
    res_env = run_hook(
        SESSION_START,
        {"workspacePaths": [ws_dir]},
        cwd=hook_cwd,
        env=env_override,
    )
    msg_env = res_env["injectSteps"][0]["systemMessage"]["systemMessage"]
    assert "warehouse_live" in msg_env
    assert "warehouse_test" in msg_env
    assert "warehouse.internal" in msg_env

    # 3. Malformed or non-dict config values must never drop Target 00 state card restoration
    for bad_cfg_raw in (
        "{not valid json",
        json.dumps(["not", "a", "dict"]),
        json.dumps({"models": None, "database": "invalid_string"}),
        json.dumps({"models": "bad", "database": {"prodDatabases": "not_a_list"}}),
    ):
      with open(
          os.path.join(ws_dir, ".workflow", "config.json"),
          "w",
          encoding="utf-8",
      ) as f:
        f.write(bad_cfg_raw)
      res_bad = run_hook(
          SESSION_START,
          {"workspacePaths": [ws_dir]},
          cwd=hook_cwd,
          env=env_override,
      )
      steps_bad = res_bad.get("injectSteps", [])
      assert len(steps_bad) == 1, f"Dropped state card prompt on {bad_cfg_raw}"
      assert "1 state card(s)" in steps_bad[0]["systemMessage"]["systemMessage"]

  print("✔ SessionStart hook assertions passed.")


if __name__ == "__main__":
  test_pre_tool_guard()
  test_session_start()
