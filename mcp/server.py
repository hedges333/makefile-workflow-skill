#!/usr/bin/env python3
"""Makefile Workflow MCP Server.

Implements Model Context Protocol (MCP) JSON-RPC 2.0 over standard I/O.
Provides deterministic workflow state queries, prerequisite validation,
tree lock verification, and safety pre-flight checks.
"""

import json
import os
import re
import subprocess
import sys


def resolve_workflow_config(workspace_dir=None):
  """Resolves workflow configuration from project, global config, or env."""
  ws = workspace_dir or os.getcwd()
  local_cfg_path = os.path.join(ws, ".workflow", "config.json")
  global_cfg_path = os.path.expanduser("~/.gemini/config/makefile-workflow.json")

  config = {
      "models": {
          "adversarial-critic": "pro",
          "archaeology-worker": "flash",
          "tdd-worker": "inherit",
          "triage-worker": "flash",
      },
      "review": {
          "maxReviewRounds": 3,
          "strictSixPillars": True,
      },
      "ci": {
          "pollIntervalSeconds": 30,
          "quiescenceSeconds": 180,
      },
      "configSource": "defaults",
      "envOverrides": [],
  }

  if os.path.isfile(local_cfg_path):
    try:
      with open(local_cfg_path, "r", encoding="utf-8") as f:
        loaded = json.load(f)
        if isinstance(loaded, dict):
          if "models" in loaded and isinstance(loaded["models"], dict):
            config["models"].update(loaded["models"])
          if "review" in loaded and isinstance(loaded["review"], dict):
            config["review"].update(loaded["review"])
          if "ci" in loaded and isinstance(loaded["ci"], dict):
            config["ci"].update(loaded["ci"])
          config["configSource"] = local_cfg_path
    except Exception:
      pass
  elif os.path.isfile(global_cfg_path):
    try:
      with open(global_cfg_path, "r", encoding="utf-8") as f:
        loaded = json.load(f)
        if isinstance(loaded, dict):
          if "models" in loaded and isinstance(loaded["models"], dict):
            config["models"].update(loaded["models"])
          if "review" in loaded and isinstance(loaded["review"], dict):
            config["review"].update(loaded["review"])
          if "ci" in loaded and isinstance(loaded["ci"], dict):
            config["ci"].update(loaded["ci"])
          config["configSource"] = global_cfg_path
    except Exception:
      pass

  # Check environment variable overrides
  env_mappings = {
      "MAKEFILE_WORKFLOW_CRITIC_MODEL": "adversarial-critic",
      "MAKEFILE_WORKFLOW_WORKER_MODEL": "archaeology-worker",
      "MAKEFILE_WORKFLOW_TDD_MODEL": "tdd-worker",
      "MAKEFILE_WORKFLOW_TRIAGE_MODEL": "triage-worker",
  }
  for env_var, agent_key in env_mappings.items():
    val = os.getenv(env_var)
    if val:
      config["models"][agent_key] = val.strip()
      config["envOverrides"].append(f"{env_var}={val.strip()}")

  return config


def handle_initialize(request_id):
  return {
      "jsonrpc": "2.0",
      "id": request_id,
      "result": {
          "protocolVersion": "2024-11-05",
          "capabilities": {"tools": {}},
          "serverInfo": {
              "name": "makefile-workflow-guard",
              "version": "1.3.0",
          },
      },
  }


def handle_tools_list(request_id):
  tools = [
      {
          "name": "workflow_get_state",
          "description": (
              "Inspects the active Memento state files to determine ticket ID,"
              " branch name, active target, and completed milestones."
          ),
          "inputSchema": {
              "type": "object",
              "properties": {
                  "stateDir": {
                      "type": "string",
                      "description": (
                          "Path to the state directory (defaults to"
                          " .workflow/state or active brain state directory)"
                      ),
                  }
              },
          },
      },
      {
          "name": "workflow_advance_target",
          "description": (
              "Validates whether prerequisites are satisfied to advance from"
              " currentTarget to nextTarget in the Makefile DAG."
          ),
          "inputSchema": {
              "type": "object",
              "properties": {
                  "currentTarget": {
                      "type": "string",
                      "description": (
                          "Current active target ID (e.g. 'T20', 'T30', 'T40',"
                          " 'T50', 'T75')"
                      ),
                  },
                  "nextTarget": {
                      "type": "string",
                      "description": (
                          "Desired next target ID (e.g. 'T30', 'T40', 'T50',"
                          " 'T60', 'T80')"
                      ),
                  },
                  "evidence": {
                      "type": "object",
                      "description": (
                          "Proof of prerequisite satisfaction (e.g. test exit"
                          " code, approval note, critic verdict)"
                      ),
                  },
              },
              "required": ["currentTarget", "nextTarget"],
          },
      },
      {
          "name": "workflow_verify_tree",
          "description": (
              "Computes the current Git Merkle tree hash via 'git write-tree'"
              " and compares it against expectedApprovedTree."
          ),
          "inputSchema": {
              "type": "object",
              "properties": {
                  "expectedApprovedTree": {
                      "type": "string",
                      "description": (
                          "Expected 40-character Git Merkle tree hash"
                      ),
                  }
              },
              "required": ["expectedApprovedTree"],
          },
      },
      {
          "name": "workflow_safety_check",
          "description": (
              "Audits a proposed command line or connection string to ensure no"
              " production database or live data files are accessed."
          ),
          "inputSchema": {
              "type": "object",
              "properties": {
                  "commandLine": {
                      "type": "string",
                      "description": "Shell command line to be evaluated",
                  }
              },
              "required": ["commandLine"],
          },
      },
      {
          "name": "workflow_get_config",
          "description": (
              "Retrieves active workflow configuration and resolved model"
              " assignments for subagents and interactive IDE reminders."
          ),
          "inputSchema": {
              "type": "object",
              "properties": {
                  "workspaceDir": {
                      "type": "string",
                      "description": (
                          "Optional project root directory (defaults to current"
                          " working directory)"
                      ),
                  }
              },
          },
      },
  ]
  return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": tools}}


def handle_tools_call(request_id, tool_name, arguments):
  if tool_name == "workflow_get_state":
    state_dir = arguments.get("stateDir", ".workflow/state")
    if not os.path.isdir(state_dir):
      # Fallback to check if .workflow exists
      return {
          "jsonrpc": "2.0",
          "id": request_id,
          "result": {
              "content": [{
                  "type": "text",
                  "text": (
                      f"State directory '{state_dir}' does not exist."
                      " Ready for Target 10 intake."
                  ),
              }]
          },
      }

    files = sorted([f for f in os.listdir(state_dir) if f.endswith(".md")])
    summary = f"Found {len(files)} state cards in {state_dir}:\n" + "\n".join(
        f"- {f}" for f in files
    )
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {"content": [{"type": "text", "text": summary}]},
    }

  elif tool_name == "workflow_advance_target":
    current = arguments.get("currentTarget", "")
    next_t = arguments.get("nextTarget", "")
    evidence = arguments.get("evidence", {})

    # Rule checks
    if current == "T20" and next_t == "T30":
      if not evidence.get("humanPlanApproved"):
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "isError": True,
                "content": [{
                    "type": "text",
                    "text": (
                        "BLOCKED: Cannot advance T20 -> T30 without"
                        " humanPlanApproved = true."
                    ),
                }],
            },
        }

    if current == "T40" and next_t in ["T45", "T50"]:
      blockers = evidence.get("blockersCount", 1)
      if blockers > 0:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "isError": True,
                "content": [{
                    "type": "text",
                    "text": (
                        f"BLOCKED: Critic reported {blockers} blocker(s). Must"
                        " route to T42 triaged-blockers before commit."
                    ),
                }],
            },
        }

    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "content": [{
                "type": "text",
                "text": (
                    f"SUCCESS: Target transition {current} -> {next_t}"
                    " certified."
                ),
            }]
        },
    }

  elif tool_name == "workflow_verify_tree":
    expected = arguments.get("expectedApprovedTree", "").strip()
    try:
      res = subprocess.run(
          ["git", "write-tree"], capture_output=True, text=True, check=True
      )
      actual = res.stdout.strip()
      match = actual == expected
      return {
          "jsonrpc": "2.0",
          "id": request_id,
          "result": {
              "content": [{
                  "type": "text",
                  "text": json.dumps({
                      "matched": match,
                      "actualTree": actual,
                      "expectedTree": expected,
                  }),
              }]
          },
      }
    except Exception as e:
      return {
          "jsonrpc": "2.0",
          "id": request_id,
          "result": {
              "isError": True,
              "content": [{"type": "text", "text": f"git write-tree error: {e}"}],
          },
      }

  elif tool_name == "workflow_safety_check":
    cmd = arguments.get("commandLine", "")
    prod_match = re.search(r"\b(prod|production)\b", cmd, re.IGNORECASE)
    db_ops = (
        any(x in cmd for x in ["psql", "mysql", "mongo", "flyway"])
        or "DATABASE_URL" in cmd
    )

    if db_ops and prod_match:
      return {
          "jsonrpc": "2.0",
          "id": request_id,
          "result": {
              "content": [{
                  "type": "text",
                  "text": json.dumps({
                      "safe": False,
                      "reason": (
                          "Production database keywords detected:"
                          f" {prod_match.group(0)}"
                      ),
                  }),
              }]
          },
      }

    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "content": [
                {"type": "text", "text": json.dumps({"safe": True, "reason": "OK"})}
            ]
        },
    }

  elif tool_name == "workflow_get_config":
    ws = arguments.get("workspaceDir")
    cfg = resolve_workflow_config(ws)
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "content": [{
                "type": "text",
                "text": json.dumps(cfg, indent=2),
            }]
        },
    }

  return {
      "jsonrpc": "2.0",
      "id": request_id,
      "error": {"code": -32601, "message": f"Method {tool_name} not found"},
  }


def main():
  for line in sys.stdin:
    if not line.strip():
      continue
    try:
      req = json.loads(line)
      req_id = req.get("id")
      method = req.get("method")

      if method == "initialize":
        resp = handle_initialize(req_id)
        sys.stdout.write(json.dumps(resp) + "\n")
        sys.stdout.flush()
      elif method == "notifications/initialized":
        # Notification; no response required
        pass
      elif method == "tools/list":
        resp = handle_tools_list(req_id)
        sys.stdout.write(json.dumps(resp) + "\n")
        sys.stdout.flush()
      elif method == "tools/call":
        params = req.get("params", {})
        name = params.get("name")
        args = params.get("arguments", {})
        resp = handle_tools_call(req_id, name, args)
        sys.stdout.write(json.dumps(resp) + "\n")
        sys.stdout.flush()
      else:
        if req_id is not None:
          resp = {
              "jsonrpc": "2.0",
              "id": req_id,
              "error": {"code": -32601, "message": f"Unknown method: {method}"},
          }
          sys.stdout.write(json.dumps(resp) + "\n")
          sys.stdout.flush()
    except Exception as e:
      err_resp = {
          "jsonrpc": "2.0",
          "id": None,
          "error": {"code": -32700, "message": f"Parse error: {e}"},
      }
      sys.stdout.write(json.dumps(err_resp) + "\n")
      sys.stdout.flush()


if __name__ == "__main__":
  main()
