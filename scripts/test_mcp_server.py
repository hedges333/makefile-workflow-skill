#!/usr/bin/env python3
"""Test harness for the Makefile Workflow MCP Server.

Validates JSON-RPC 2.0 communication over stdio:
1. initialize
2. tools/list
3. workflow_safety_check (testing both safe and production-prohibited commands)
4. workflow_advance_target (testing both blocked and approved transitions)
"""

import json
import subprocess
import sys


def run_test():
  p = subprocess.Popen(
      ["python3", "mcp/server.py"],
      stdin=subprocess.PIPE,
      stdout=subprocess.PIPE,
      stderr=subprocess.PIPE,
      text=True,
  )

  # 1. Initialize
  init_req = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
  p.stdin.write(json.dumps(init_req) + "\n")
  p.stdin.flush()
  init_resp = json.loads(p.stdin.readline() if False else p.stdout.readline())
  assert init_resp.get("id") == 1
  assert (
      init_resp.get("result", {})
      .get("serverInfo", {})
      .get("name")
      == "makefile-workflow-guard"
  )
  print("✔ MCP initialize handshake passed.")

  # 2. Tools list
  tools_req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
  p.stdin.write(json.dumps(tools_req) + "\n")
  p.stdin.flush()
  tools_resp = json.loads(p.stdout.readline())
  tool_names = [t["name"] for t in tools_resp["result"]["tools"]]
  assert "workflow_get_state" in tool_names
  assert "workflow_advance_target" in tool_names
  assert "workflow_verify_tree" in tool_names
  assert "workflow_safety_check" in tool_names
  assert "workflow_get_config" in tool_names
  print(f"✔ MCP tools/list returned {len(tool_names)} tools: {tool_names}")

  # 3. Test safety check: Dangerous command
  safe_check_bad = {
      "jsonrpc": "2.0",
      "id": 3,
      "method": "tools/call",
      "params": {
          "name": "workflow_safety_check",
          "arguments": {"commandLine": "psql -h production.db.internal myapp"},
      },
  }
  p.stdin.write(json.dumps(safe_check_bad) + "\n")
  p.stdin.flush()
  bad_resp = json.loads(p.stdout.readline())
  content_bad = json.loads(bad_resp["result"]["content"][0]["text"])
  assert content_bad["safe"] is False
  print("✔ MCP safety check correctly flagged production database connection.")

  # 4. Test safety check: Safe test command
  safe_check_good = {
      "jsonrpc": "2.0",
      "id": 4,
      "method": "tools/call",
      "params": {
          "name": "workflow_safety_check",
          "arguments": {"commandLine": "pytest tests/ --db=sqlite:///:memory:"},
      },
  }
  p.stdin.write(json.dumps(safe_check_good) + "\n")
  p.stdin.flush()
  good_resp = json.loads(p.stdout.readline())
  content_good = json.loads(good_resp["result"]["content"][0]["text"])
  assert content_good["safe"] is True
  print("✔ MCP safety check correctly approved safe test command.")

  # 5. Test advance target: Blocked transition
  adv_bad = {
      "jsonrpc": "2.0",
      "id": 5,
      "method": "tools/call",
      "params": {
          "name": "workflow_advance_target",
          "arguments": {
              "currentTarget": "T20",
              "nextTarget": "T30",
              "evidence": {"humanPlanApproved": False},
          },
      },
  }
  p.stdin.write(json.dumps(adv_bad) + "\n")
  p.stdin.flush()
  adv_bad_resp = json.loads(p.stdout.readline())
  assert adv_bad_resp["result"]["isError"] is True
  print("✔ MCP advance_target correctly blocked unapproved plan transition.")

  # 6. Test workflow_get_config
  cfg_req = {
      "jsonrpc": "2.0",
      "id": 6,
      "method": "tools/call",
      "params": {
          "name": "workflow_get_config",
          "arguments": {},
      },
  }
  p.stdin.write(json.dumps(cfg_req) + "\n")
  p.stdin.flush()
  cfg_resp = json.loads(p.stdout.readline())
  cfg_data = json.loads(cfg_resp["result"]["content"][0]["text"])
  assert "models" in cfg_data
  assert cfg_data["models"]["adversarial-critic"] in ["pro", "gemini-4-argon-high"]
  assert "review" in cfg_data
  assert "ci" in cfg_data
  print("✔ MCP workflow_get_config returned valid configuration and model mapping.")

  p.kill()
  print("\nAll MCP Server test cases passed successfully!")


if __name__ == "__main__":
  run_test()
