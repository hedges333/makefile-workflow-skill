#!/usr/bin/env python3
"""Test suite for SessionStart and PreToolUse hook scripts."""

import importlib.util
import json
import os
import subprocess
import sys
import tempfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRE_TOOL = os.path.join(REPO_ROOT, "scripts", "pre_tool_guard.py")
SESSION_START = os.path.join(REPO_ROOT, "scripts", "session_start.py")
MCP_SERVER = os.path.join(REPO_ROOT, "mcp", "server.py")


def run_hook(script_path, payload, cwd=None, env=None):
  proc = subprocess.run(
      [sys.executable, script_path],
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

    # 10. Destructive Git command guards (SCAR-GIT-25): deny work-discarding & force-push, force_ask rebase & branch -D, allow normal workflow Git commands
    for denied_git_cmd in (
        "git reset --hard",
        "git reset --hard HEAD~1",
        "git reset --merge",
        "git reset --keep",
        "git clean -f",
        "git clean -fd",
        "git clean -xfd",
        "git clean --force",
        "git checkout -- README.md",
        "git checkout HEAD -- scripts/pre_tool_guard.py",
        "git checkout .",
        "git checkout ./scripts",
        "git checkout HEAD README.md",
        "git checkout -f main",
        "git checkout --force main",
        "git switch -f main",
        "git switch --force main",
        "git switch --discard-changes main",
        "git restore README.md",
        "git restore .",
        "git restore -W README.md",
        "git restore --staged --worktree README.md",
        "git restore -SW README.md",
        "git stash drop",
        "git stash drop stash@{0}",
        "git stash clear",
        "git filter-branch --tree-filter 'rm -f passwords.txt' HEAD",
        "git filter-repo --path README.md",
        "git reflog delete HEAD@{1}",
        "git reflog expire --expire=now --all",
        "git update-ref -d refs/heads/feat/old",
        "git push --force origin feat/2-test",
        "git push -f origin feat/2-test",
        "git push -uf origin feat/2-test",
        "git push --force-with-lease origin feat/2-test",
        "git push --force-with-lease=feat/2-test:abcdef origin feat/2-test",
        "git push --force-if-includes origin feat/2-test",
        "git push origin +HEAD:feat/2-test",
        "git push origin +feat/2-test",
        "git -C /tmp reset --hard",
        "git -C/tmp reset --hard",
        "GIT_PAGER=cat git clean -fd",
        "env GIT_TERMINAL_PROMPT=0 git reset --hard",
        "git status && git reset --hard",
        "git rebase main && git reset --hard",
        'echo "$(git reset --hard)"',
        'bash -c "git clean -fd"',
        'bash -euo pipefail -c "git reset --hard"',
        "(cd /tmp && git reset --hard)",
        "timeout 30 git reset --hard",
        "nice -n 10 git clean -fd",
        "git checkout '*.py'",
        "git update-ref --stdin",
        "git clean -i",
        "git clean --interactive",
        "git checkout -p",
        "git checkout --patch",
        "git checkout --discard-changes main",
        "git push --mirror origin",
        # BLOCKER-1 regressions
        "git -- reset --hard",
        "git -- clean -fd",
        "git -- push --force origin main",
        "git clean -n --no-dry-run -fd",
        "git restore --staged --no-staged README.md",
        "git checkout --ours README.md",
        "git checkout --theirs README.md",
        "git checkout -2 README.md",
        "git checkout -3 README.md",
        "git checkout --pathspec-from-file=paths.txt",
        "git checkout --pathspec-from-file paths.txt",
        "git -c clean.requireForce=false clean -d",
        "git -cclean.requireForce=0 clean -d",
        "git -c remote.origin.push=+HEAD:main push origin",
        # BLOCKER-2 redirection bypass regressions
        "git 2>&1 reset --hard",
        "psql 2>&1 -h prod.db.internal myapp",
        ">/dev/null git reset --hard",
        "> /dev/null git clean -fd",
        "git 2>/dev/null reset --hard",
        # BLOCKER-3 compound shell keywords, sh -c flag order, eval, env -S
        'for f in README.md; do git checkout -- "$f"; done',
        "if ! make test; then git reset --hard; fi",
        "if false; then :; else git clean -fd; fi",
        "! git reset --hard",
        'sh -c -- "git reset --hard"',
        'bash -c -e "git reset --hard"',
        'bash -co pipefail "git reset --hard"',
        'bash -O extglob -c "git reset --hard"',
        'eval "git reset --hard"',
        "eval git reset --hard",
        'env -S "git reset --hard"',
        'env -S"git reset --hard"',
        'env --split-string="git reset --hard"',
        'env --split-string "git reset --hard"',
        # BLOCKER-4 multiline comments with apostrophes, ANSI-C quotes, unspaced fallback
        "# Don't fail if dirty\ngit reset --hard",
        "# it's step 1\ngit reset --hard\n# it's step 2",
        "echo $'a\\'b';git reset --hard",
        'echo "unterminated;git reset --hard',
        'bash -c "psql -h prod.db.internal myapp"',
        'git commit -m "unterminated && git reset --hard',
    ):
      res_git_deny = run_hook(
          PRE_TOOL,
          {
              "workspacePaths": [ws_dir],
              "toolCall": {
                  "name": "run_command",
                  "args": {"CommandLine": denied_git_cmd},
              },
          },
          cwd=hook_cwd,
      )
      assert res_git_deny["decision"] == "deny", (
          f"Expected deny for '{denied_git_cmd}', got {res_git_deny}"
      )

    for ask_git_cmd in (
        "git rebase main",
        "git rebase origin/main",
        "git -C /tmp rebase main",
        "git branch -D feat/old",
        "git branch -df feat/old",
        "git branch -d -f feat/old",
        "git branch --delete --force feat/old",
        "git branch -f main HEAD~2",
        "git branch -M old main",
        "git branch -C old main",
        'git -- commit -m "feat: test"',
        "echo ok && git rebase main",
        'git commit -m "block git reset --hard and git clean -fd"',
    ):
      res_git_ask = run_hook(
          PRE_TOOL,
          {
              "workspacePaths": [ws_dir],
              "toolCall": {
                  "name": "run_command",
                  "args": {"CommandLine": ask_git_cmd},
              },
          },
          cwd=hook_cwd,
      )
      assert res_git_ask["decision"] == "force_ask", (
          f"Expected force_ask for '{ask_git_cmd}', got {res_git_ask}"
      )

    for safe_git_cmd in (
        "git status --short",
        "git diff --staged",
        "git add -A",
        "git write-tree",
        "git checkout main",
        "git checkout main 2>/dev/null",
        "git checkout main 2>&1",
        "git checkout main > ./checkout.log",
        "git checkout main &>/dev/null",
        "git checkout main 2>/dev/null || git checkout -b main",
        "git restore -W --no-worktree -S README.md",
        "git checkout feat/2-git-command-protections",
        "git checkout -b feat/2-git-command-protections",
        "git checkout -b feat/2-git-command-protections origin/main",
        "git switch main",
        "git switch -c feat/2-git-command-protections",
        "git reset HEAD README.md",
        "git reset --soft HEAD~1",
        "git restore --staged README.md",
        "git restore -S .",
        "git clean -n",
        "git clean -nd",
        "git clean -n -fd",
        "git clean -n -efoo",
        "git stash",
        "git stash pop",
        "git stash list",
        "git branch -d feat/1-done",
        "git branch -d feat/1-Destroy",
        "git merge --ff-only feat/1-done",
        "git merge-tree $(git merge-base HEAD origin/main) HEAD origin/main",
        'echo "do not run git reset --hard or git push --force"',
        "echo 'never run $(git reset --hard) or git commit'",
    ):
      res_git_safe = run_hook(
          PRE_TOOL,
          {
              "workspacePaths": [ws_dir],
              "toolCall": {
                  "name": "run_command",
                  "args": {"CommandLine": safe_git_cmd},
              },
          },
          cwd=hook_cwd,
      )
      assert res_git_safe["decision"] == "allow", (
          f"Expected allow for '{safe_git_cmd}', got {res_git_safe}"
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

    # 4. SimpleEnglish plugin discovery advisory
    fake_home = tempfile.mkdtemp(prefix="fake_home_")
    env_no_se = dict(os.environ)
    env_no_se["HOME"] = fake_home
    res_no_se = run_hook(
        SESSION_START,
        {"workspacePaths": [ws_dir]},
        cwd=hook_cwd,
        env=env_no_se,
    )
    msg_no_se = res_no_se["injectSteps"][0]["systemMessage"]["systemMessage"]
    assert "simple-english plugin is recommended" in msg_no_se

    se_plugin_dir = os.path.join(fake_home, ".gemini", "config", "plugins", "simple-english")
    os.makedirs(se_plugin_dir, exist_ok=True)
    with open(os.path.join(se_plugin_dir, "plugin.json"), "w") as f:
      f.write('{"name": "simple-english"}')
    res_with_se = run_hook(
        SESSION_START,
        {"workspacePaths": [ws_dir]},
        cwd=hook_cwd,
        env=env_no_se,
    )
    msg_with_se = res_with_se["injectSteps"][0]["systemMessage"]["systemMessage"]
    assert "simple-english plugin is recommended" not in msg_with_se

  print("✔ SessionStart hook assertions passed.")


def _load_module(name, path):
  spec = importlib.util.spec_from_file_location(name, path)
  mod = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(mod)
  return mod


def test_hook_mcp_parity():
  guard_mod = _load_module("pre_tool_guard", PRE_TOOL)
  mcp_mod = _load_module("mcp_server", MCP_SERVER)

  parity_commands = (
      "git reset --hard",
      "git -- reset --hard",
      "git clean -fd",
      "git clean -n --no-dry-run -fd",
      "git clean -nd",
      "git checkout -- README.md",
      "git checkout --ours README.md",
      "git checkout main 2>&1",
      "git checkout main 2>/dev/null",
      "git 2>&1 reset --hard",
      "git restore README.md",
      "git restore --staged README.md",
      "git restore --staged --no-staged README.md",
      "git stash drop",
      "git update-ref --stdin",
      "git push --force origin feat/2-test",
      "git push --mirror origin",
      "git push -u origin feat/2-test",
      "git rebase main",
      "git branch -D feat/old",
      "git branch -M old main",
      "git branch -d feat/1-done",
      'git commit -m "feat: add guard"',
      "gh pr merge 2 --squash",
      'for f in README.md; do git checkout -- "$f"; done',
      'sh -c -- "git reset --hard"',
      'eval "git reset --hard"',
      'env -S "git reset --hard"',
      "# Don't fail\ngit reset --hard",
      "echo $'a\\'b';git reset --hard",
  )

  for cmd in parity_commands:
    hook_res = guard_mod.evaluate_git_command(cmd, has_review=True)
    mcp_safe, mcp_reason = mcp_mod.evaluate_git_safety(cmd)
    assert (hook_res["decision"] == "deny") == (not mcp_safe), (
        f"Deny parity mismatch on '{cmd}': hook={hook_res}, mcp=({mcp_safe}, {mcp_reason})"
    )
    assert (hook_res["decision"] == "force_ask") == (
        mcp_safe and mcp_reason.startswith("Requires human operator approval")
    ), (
        f"Gate parity mismatch on '{cmd}': hook={hook_res}, mcp=({mcp_safe}, {mcp_reason})"
    )

  print("✔ Hook and MCP Git guard parity assertions passed.")


if __name__ == "__main__":
  test_pre_tool_guard()
  test_session_start()
  test_hook_mcp_parity()
