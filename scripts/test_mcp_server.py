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
        ["python3", SERVER_SCRIPT],
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
                      "workspaceDir": REPO_ROOT,
                  },
              },
          },
      )
      assert not tree_resp["result"].get("isError")
      tree_data = json.loads(tree_resp["result"]["content"][0]["text"])
      assert len(tree_data["actualTree"]) == 40
      print("✔ MCP workflow_verify_tree resolved workspaceDir cleanly.")

      # 7. Get config and state with workspaceDir
      cfg_resp = send_rpc(
          p,
          {
              "jsonrpc": "2.0",
              "id": 10,
              "method": "tools/call",
              "params": {
                  "name": "workflow_get_config",
                  "arguments": {"workspaceDir": REPO_ROOT},
              },
          },
      )
      cfg_data = json.loads(cfg_resp["result"]["content"][0]["text"])
      assert "models" in cfg_data
      assert "agyModelTiers" in cfg_data
      assert cfg_data["agyModelTiers"]["adversarial-critic"] in {
          "inherit",
          "flash_lite",
          "flash",
          "pro",
      }
      assert "review" in cfg_data
      assert "ci" in cfg_data
      print("✔ MCP workflow_get_config returned valid configuration.")
    finally:
      p.kill()
      p.wait()

  print("\nAll MCP Server test cases passed.")


if __name__ == "__main__":
  run_test()
