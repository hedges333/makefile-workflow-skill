#!/usr/bin/env python3
"""Test harness for the Makefile Workflow MCP Server.

Checks JSON-RPC 2.0 communication over standard input/output:
1. initialize
2. tools/list
3. workflow_safety_check (hostname prod, underscore prod_db, safe test command)
4. workflow_advance_target (blocked gate, blocked illegal DAG jump, valid step)
5. workflow_verify_tree with workspaceDir from a non-git working directory
6. workflow_get_state and workflow_get_config with workspaceDir
"""

import json
import os
import subprocess
import sys
import tempfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER_SCRIPT = os.path.join(REPO_ROOT, "mcp", "server.py")


def send_rpc(proc, msg):
  proc.stdin.write(json.dumps(msg) + "\n")
  proc.stdin.flush()
  return json.loads(proc.stdout.readline())


def run_test():
  with tempfile.TemporaryDirectory() as non_git_cwd:
    p = subprocess.Popen(
        [sys.executable, SERVER_SCRIPT],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=non_git_cwd,
        text=True,
    )
    try:
      # 1. Initialize
      init_resp = send_rpc(
          p, {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
      )
      assert init_resp["id"] == 1
      assert (
          init_resp["result"]["serverInfo"]["name"] == "makefile-workflow-guard"
      )
      assert init_resp["result"]["serverInfo"]["version"] == "1.4.1"
      print("✔ MCP initialize handshake passed.")

      # 2. Tools list
      tools_resp = send_rpc(
          p, {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
      )
      tool_names = [t["name"] for t in tools_resp["result"]["tools"]]
      for expected in (
          "workflow_get_state",
          "workflow_advance_target",
          "workflow_verify_tree",
          "workflow_safety_check",
          "workflow_get_config",
      ):
        assert expected in tool_names
      print(f"✔ MCP tools/list returned {len(tool_names)} tools: {tool_names}")

      # 3. Safety check: production hostname and underscore prod_db
      for idx, bad_cmd in enumerate(
          (
              "psql -h production.db.internal myapp",
              "mariadb -u app myapp_prod",
          ),
          start=3,
      ):
        bad_resp = send_rpc(
            p,
            {
                "jsonrpc": "2.0",
                "id": idx,
                "method": "tools/call",
                "params": {
                    "name": "workflow_safety_check",
                    "arguments": {"commandLine": bad_cmd},
                },
            },
        )
        content_bad = json.loads(bad_resp["result"]["content"][0]["text"])
        assert content_bad["safe"] is False
      print("✔ MCP safety check blocked production database commands.")

      # 4. Safety check: safe test command
      good_resp = send_rpc(
          p,
          {
              "jsonrpc": "2.0",
              "id": 5,
              "method": "tools/call",
              "params": {
                  "name": "workflow_safety_check",
                  "arguments": {
                      "commandLine": "pytest tests/ --db=sqlite:///:memory:"
                  },
              },
          },
      )
      content_good = json.loads(good_resp["result"]["content"][0]["text"])
      assert content_good["safe"] is True
      print("✔ MCP safety check allowed safe test command.")

      # 5. Advance target: unapproved plan blocked, illegal T10->T80 jump blocked, valid T10->T15 allowed
      adv_bad = send_rpc(
          p,
          {
              "jsonrpc": "2.0",
              "id": 6,
              "method": "tools/call",
              "params": {
                  "name": "workflow_advance_target",
                  "arguments": {
                      "currentTarget": "T20",
                      "nextTarget": "T30",
                      "evidence": {"humanPlanApproved": False},
                  },
              },
          },
      )
      assert adv_bad["result"]["isError"] is True

      adv_jump = send_rpc(
          p,
          {
              "jsonrpc": "2.0",
              "id": 7,
              "method": "tools/call",
              "params": {
                  "name": "workflow_advance_target",
                  "arguments": {
                      "currentTarget": "T10",
                      "nextTarget": "T80",
                  },
              },
          },
      )
      assert adv_jump["result"]["isError"] is True

      adv_ok = send_rpc(
          p,
          {
              "jsonrpc": "2.0",
              "id": 8,
              "method": "tools/call",
              "params": {
                  "name": "workflow_advance_target",
                  "arguments": {
                      "currentTarget": "T20",
                      "nextTarget": "T30",
                      "evidence": {"humanPlanApproved": True},
                  },
              },
          },
      )
      assert not adv_ok["result"].get("isError")
      print("✔ MCP workflow_advance_target enforced DAG edges and human gates.")

      # 6. Verify tree with workspaceDir when server cwd is not a git repo
      with tempfile.TemporaryDirectory() as tmp_git_ws:
        subprocess.run(
            ["git", "init", "-q"],
            cwd=tmp_git_ws,
            check=True,
        )
        with open(
            os.path.join(tmp_git_ws, "README.md"), "w", encoding="utf-8"
        ) as f:
          f.write("# Test\n")
        subprocess.run(
            ["git", "add", "README.md"],
            cwd=tmp_git_ws,
            check=True,
        )
        tree_resp = send_rpc(
            p,
            {
                "jsonrpc": "2.0",
                "id": 9,
                "method": "tools/call",
                "params": {
                    "name": "workflow_verify_tree",
                    "arguments": {
                        "expectedApprovedTree": "0" * 40,
                        "workspaceDir": tmp_git_ws,
                    },
                },
            },
        )
        assert not tree_resp["result"].get("isError")
        tree_data = json.loads(tree_resp["result"]["content"][0]["text"])
        assert len(tree_data["actualTree"]) == 40
        print("✔ MCP workflow_verify_tree resolved workspaceDir cleanly.")

      # 7. Get config with default workspaceDir
      with tempfile.TemporaryDirectory() as empty_ws:
        cfg_resp = send_rpc(
            p,
            {
                "jsonrpc": "2.0",
                "id": 10,
                "method": "tools/call",
                "params": {
                    "name": "workflow_get_config",
                    "arguments": {"workspaceDir": empty_ws},
                },
            },
        )
        cfg_data = json.loads(cfg_resp["result"]["content"][0]["text"])
        assert "models" in cfg_data
        assert "agyModelTiers" in cfg_data
        for role in (
            "adversarial-critic",
            "archaeology-worker",
            "tdd-worker",
            "triage-worker",
        ):
          assert (
              cfg_data["models"].get(role) == "inherit"
          ), f"Expected default models[{role}] == 'inherit', got {cfg_data['models'].get(role)}"
          assert (
              cfg_data["agyModelTiers"].get(role) == "inherit"
          ), f"Expected default agyModelTiers[{role}] == 'inherit', got {cfg_data['agyModelTiers'].get(role)}"
        assert "review" in cfg_data
        assert "ci" in cfg_data
        assert "database" in cfg_data
        assert "prodDatabases" in cfg_data["database"]
        assert "testDatabases" in cfg_data["database"]
        assert "prodHosts" in cfg_data["database"]
        print("✔ MCP workflow_get_config returned valid default configuration.")

      # 8. Custom database configuration in workspaceDir for workflow_get_config and workflow_safety_check
      with tempfile.TemporaryDirectory() as ws_cfg_dir:
        os.makedirs(os.path.join(ws_cfg_dir, ".workflow"))
        with open(
            os.path.join(ws_cfg_dir, ".workflow", "config.json"),
            "w",
            encoding="utf-8",
        ) as f:
          json.dump(
              {
                  "models": {
                      "adversarial-critic": "gemini-4-argon-high",
                      "archaeology-worker": "gemini-3.8-flash-low",
                      "tdd-worker": "flash_lite",
                      "triage-worker": "pro",
                  },
                  "database": {
                      "prodDatabases": ["billing_live", 1, True, None],
                      "testDatabases": ["billing_sandbox", "billing", 1, False],
                      "prodHosts": ["db.company.internal", None],
                  }
              },
              f,
          )

        ws_cfg_resp = send_rpc(
            p,
            {
                "jsonrpc": "2.0",
                "id": 11,
                "method": "tools/call",
                "params": {
                    "name": "workflow_get_config",
                    "arguments": {"workspaceDir": ws_cfg_dir},
                },
            },
        )
        ws_cfg = json.loads(ws_cfg_resp["result"]["content"][0]["text"])
        assert ws_cfg["models"]["adversarial-critic"] == "gemini-4-argon-high"
        assert ws_cfg["agyModelTiers"]["adversarial-critic"] == "pro"
        assert ws_cfg["models"]["archaeology-worker"] == "gemini-3.8-flash-low"
        assert ws_cfg["agyModelTiers"]["archaeology-worker"] == "flash"
        assert ws_cfg["models"]["tdd-worker"] == "flash_lite"
        assert ws_cfg["agyModelTiers"]["tdd-worker"] == "flash_lite"
        assert ws_cfg["models"]["triage-worker"] == "pro"
        assert ws_cfg["agyModelTiers"]["triage-worker"] == "pro"
        assert ws_cfg["database"]["prodDatabases"] == ["billing_live"]
        assert ws_cfg["database"]["testDatabases"] == ["billing_sandbox", "billing"]
        assert ws_cfg["database"]["prodHosts"] == ["db.company.internal"]

        for req_id, cmd_str, expected_safe in (
            (12, "psql -h localhost billing_live", False),
            (13, "psql -h db.company.internal billing_sandbox", False),
            (
                14,
                "psql -h localhost billing_sandbox -c 'SELECT prod FROM invoices'",
                True,
            ),
            (15, "psql -h production.db.internal billing_sandbox", False),
            (16, "pg_dump myapp_prod | psql billing_sandbox", False),
            (17, 'psql -h "prod.db.internal" billing_sandbox', False),
            (18, "PGHOST=prod.db.internal psql billing_sandbox", False),
            (19, 'psql "host=prod.db.internal dbname=billing_sandbox"', False),
            (20, "psql -h localhost billing-prod", False),
            (21, "pg_restore -d myapp_prod billing_sandbox.dump", False),
            (
                22,
                'psql "postgresql://prod_user:secret@localhost:5432/billing_sandbox" -c "SELECT prod FROM t"',
                True,
            ),
        ):
          sc_resp = send_rpc(
              p,
              {
                  "jsonrpc": "2.0",
                  "id": req_id,
                  "method": "tools/call",
                  "params": {
                      "name": "workflow_safety_check",
                      "arguments": {
                          "commandLine": cmd_str,
                          "workspaceDir": ws_cfg_dir,
                      },
                  },
              },
          )
          sc_data = json.loads(sc_resp["result"]["content"][0]["text"])
          assert sc_data["safe"] is expected_safe, (
              f"Expected safe={expected_safe} for '{cmd_str}', got {sc_data}"
          )
      print("✔ MCP custom database safety checks passed.")

      # 8b. Destructive Git safety checks via workflow_safety_check (SCAR-GIT-25)
      for git_idx, (git_cmd_str, expected_git_safe) in enumerate(
          (
              ("git reset --hard", False),
              ("git -- reset --hard", False),
              ("git clean -fd", False),
              ("git clean -i", False),
              ("git clean -n --no-dry-run -fd", False),
              ("git -c clean.requireForce=false clean -d", False),
              ("git checkout -- README.md", False),
              ("git checkout .", False),
              ("git checkout -p", False),
              ("git checkout --ours README.md", False),
              ("git checkout --theirs README.md", False),
              ("git checkout --pathspec-from-file=paths.txt", False),
              ("git switch --discard-changes main", False),
              ("git restore README.md", False),
              ("git restore --staged --no-staged README.md", False),
              ("git stash drop", False),
              ("git filter-branch --all", False),
              ("git reflog delete HEAD@{1}", False),
              ("git update-ref -d refs/heads/feat/old", False),
              ("git update-ref --stdin", False),
              ("git push --force origin feat/2-test", False),
              ("git push --force-with-lease origin feat/2-test", False),
              ("git push --mirror origin", False),
              ("git push origin +HEAD:feat/2-test", False),
              ("git -c remote.origin.push=+HEAD:main push origin", False),
              ("git status && git reset --hard", False),
              ('echo "$(git clean -fd)"', False),
              ('bash -euo pipefail -c "git reset --hard"', False),
              ('sh -c -- "git reset --hard"', False),
              ('bash -co pipefail "git reset --hard"', False),
              ('eval "git reset --hard"', False),
              ('env -S "git reset --hard"', False),
              ('for f in a; do git checkout -- "$f"; done', False),
              ("git 2>&1 reset --hard", False),
              ("psql 2>&1 -h production.db.internal myapp", False),
              ("# Don't fail\ngit reset --hard", False),
              ("echo $'a\\'b';git reset --hard", False),
              ("(cd /tmp && git reset --hard)", False),
              ("git status --short", True),
              ("git checkout main 2>&1", True),
              ("git checkout main 2>/dev/null", True),
              ("git checkout -b feat/2-test", True),
              ("git restore --staged README.md", True),
              ("git clean -nd", True),
              ("git branch -d feat/1-done", True),
              ('echo "do not run git reset --hard"', True),
              ('git commit -m "block git reset --hard"', True),
          ),
          start=100,
      ):
        git_sc_resp = send_rpc(
            p,
            {
                "jsonrpc": "2.0",
                "id": git_idx,
                "method": "tools/call",
                "params": {
                    "name": "workflow_safety_check",
                    "arguments": {"commandLine": git_cmd_str},
                },
            },
        )
        git_sc_data = json.loads(git_sc_resp["result"]["content"][0]["text"])
        assert git_sc_data["safe"] is expected_git_safe, (
            f"Expected safe={expected_git_safe} for '{git_cmd_str}', got {git_sc_data}"
        )

      for adv_idx, adv_cmd in enumerate(
          (
              "git push -u origin feat/2-test",
              "git rebase main",
              "git branch -D feat/old",
              "git branch -M old main",
              'git commit -m "feat: add safety check"',
              "gh pr merge 2 --squash",
              "echo ok && git rebase main",
          ),
          start=200,
      ):
        adv_sc_resp = send_rpc(
            p,
            {
                "jsonrpc": "2.0",
                "id": adv_idx,
                "method": "tools/call",
                "params": {
                    "name": "workflow_safety_check",
                    "arguments": {"commandLine": adv_cmd},
                },
            },
        )
        adv_sc_data = json.loads(adv_sc_resp["result"]["content"][0]["text"])
        assert adv_sc_data["safe"] is True, f"Expected safe=True on '{adv_cmd}'"
        assert "Requires human operator approval" in adv_sc_data["reason"], (
            f"Expected operator approval reason on '{adv_cmd}', got {adv_sc_data}"
        )
      print("✔ MCP destructive Git command safety checks passed.")
    finally:
      p.kill()
      p.wait()

  # 9. Environment variable database overrides
  with tempfile.TemporaryDirectory() as env_cwd:
    custom_env = dict(os.environ)
    custom_env["MAKEFILE_WORKFLOW_PROD_DBS"] = "ledger_live"
    custom_env["MAKEFILE_WORKFLOW_TEST_DBS"] = "ledger_test"
    custom_env["MAKEFILE_WORKFLOW_PROD_HOSTS"] = "live-cluster.internal"
    custom_env["MAKEFILE_WORKFLOW_CRITIC_MODEL"] = "gemini-4-argon-high"
    custom_env["MAKEFILE_WORKFLOW_WORKER_MODEL"] = "flash_lite"
    custom_env["MAKEFILE_WORKFLOW_TDD_MODEL"] = "pro"
    custom_env["MAKEFILE_WORKFLOW_TRIAGE_MODEL"] = "flash"
    p_env = subprocess.Popen(
        [sys.executable, SERVER_SCRIPT],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=env_cwd,
        env=custom_env,
        text=True,
    )
    try:
      send_rpc(
          p_env, {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
      )
      env_cfg_resp = send_rpc(
          p_env,
          {
              "jsonrpc": "2.0",
              "id": 2,
              "method": "tools/call",
              "params": {
                  "name": "workflow_get_config",
                  "arguments": {"workspaceDir": env_cwd},
              },
          },
      )
      env_cfg = json.loads(env_cfg_resp["result"]["content"][0]["text"])
      assert "ledger_live" in env_cfg["database"]["prodDatabases"]
      assert "ledger_test" in env_cfg["database"]["testDatabases"]
      assert "live-cluster.internal" in env_cfg["database"]["prodHosts"]
      assert env_cfg["models"]["adversarial-critic"] == "gemini-4-argon-high"
      assert env_cfg["agyModelTiers"]["adversarial-critic"] == "pro"
      assert env_cfg["models"]["archaeology-worker"] == "flash_lite"
      assert env_cfg["agyModelTiers"]["archaeology-worker"] == "flash_lite"
      assert env_cfg["models"]["tdd-worker"] == "pro"
      assert env_cfg["agyModelTiers"]["tdd-worker"] == "pro"
      assert env_cfg["models"]["triage-worker"] == "flash"
      assert env_cfg["agyModelTiers"]["triage-worker"] == "flash"

      env_sc_bad = send_rpc(
          p_env,
          {
              "jsonrpc": "2.0",
              "id": 3,
              "method": "tools/call",
              "params": {
                  "name": "workflow_safety_check",
                  "arguments": {
                      "commandLine": "psql -h localhost ledger_live",
                      "workspaceDir": env_cwd,
                  },
              },
          },
      )
      assert json.loads(env_sc_bad["result"]["content"][0]["text"])["safe"] is False

      env_sc_good = send_rpc(
          p_env,
          {
              "jsonrpc": "2.0",
              "id": 4,
              "method": "tools/call",
              "params": {
                  "name": "workflow_safety_check",
                  "arguments": {
                      "commandLine": (
                          "psql -h localhost ledger_test -c 'SELECT prod FROM tx'"
                      ),
                      "workspaceDir": env_cwd,
                  },
              },
          },
      )
      assert json.loads(env_sc_good["result"]["content"][0]["text"])["safe"] is True
      print("✔ MCP environment variable database overrides passed.")
    finally:
      p_env.kill()
      p_env.wait()

  print("\nAll MCP Server test cases passed.")


if __name__ == "__main__":
  run_test()
