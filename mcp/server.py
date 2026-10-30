#!/usr/bin/env python3
"""Makefile Workflow MCP Server.

Implements Model Context Protocol (MCP) JSON-RPC 2.0 over standard input/output.
Provides state queries, DAG transition checks, Git tree checks, safety checks,
and user configuration lookup.
"""

import json
import os
import re
import subprocess
import sys

DB_TOOLS = (
    "psql",
    "pg_dump",
    "pg_restore",
    "mysql",
    "mysqldump",
    "mariadb",
    "mongo",
    "mongosh",
    "redis-cli",
    "sqlite3",
    "sqlcmd",
    "flyway",
    "liquibase",
    "alembic",
    "prisma",
    "goose",
    "dbmate",
)

PROD_TOKEN_RE = re.compile(
    r"(?:^|[^a-zA-Z0-9])(prod|production)(?:$|[^a-zA-Z0-9])",
    re.IGNORECASE,
)

ALL_TARGETS = {
    "T00",
    "T10",
    "T15",
    "T20",
    "T30",
    "T40",
    "T42",
    "T45",
    "T50",
    "T60",
    "T70",
    "T75",
    "T80",
    "T90",
}

VALID_TRANSITIONS = {
    "T00": ALL_TARGETS - {"T00"},
    "T10": {"T15"},
    "T15": {"T20"},
    "T20": {"T30"},
    "T30": {"T40", "T20"},
    "T40": {"T42", "T45"},
    "T42": {"T30"},
    "T45": {"T50"},
    "T50": {"T60"},
    "T60": {"T70"},
    "T70": {"T75", "T30"},
    "T75": {"T80"},
    "T80": {"T90"},
    "T90": set(),
}

GATE_EVIDENCE_KEYS = {
    ("T20", "T30"): "humanPlanApproved",
    ("T42", "T30"): "humanBlockerTriageApproved",
    ("T45", "T50"): "humanReviewApproved",
    ("T50", "T60"): "humanCommitApproved",
    ("T60", "T70"): "humanPushApproved",
    ("T75", "T80"): "humanLandingApproved",
}


def resolve_workspace_dir(arguments):
  ws = (arguments or {}).get("workspaceDir")
  if ws:
    return os.path.expanduser(ws)
  env_ws = os.getenv("MAKEFILE_WORKFLOW_WORKSPACE")
  if env_ws:
    return os.path.expanduser(env_ws)
  return os.getcwd()


def map_to_agy_tier(model_value):
  """Maps a concrete model identifier to an Antigravity subagent tier."""
  if not model_value:
    return "inherit"
  val = str(model_value).strip().lower()
  if val in {"inherit", "flash_lite", "flash", "pro"}:
    return val
  if any(tok in val for tok in ("lite", "haiku", "mini", "nano")):
    return "flash_lite"
  if any(tok in val for tok in ("flash", "fast", "low")):
    return "flash"
  if any(tok in val for tok in ("pro", "argon", "opus", "high", "o1", "o3")):
    return "pro"
  return "inherit"


def resolve_workflow_config(workspace_dir=None):
  """Resolves workflow configuration from workspace, global path, or environment."""
  ws = workspace_dir or resolve_workspace_dir({})
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

  for cfg_path in (local_cfg_path, global_cfg_path):
    if os.path.isfile(cfg_path):
      try:
        with open(cfg_path, "r", encoding="utf-8") as f:
          loaded = json.load(f)
        if isinstance(loaded, dict):
          if isinstance(loaded.get("models"), dict):
            config["models"].update(loaded["models"])
          if isinstance(loaded.get("review"), dict):
            config["review"].update(loaded["review"])
          if isinstance(loaded.get("ci"), dict):
            config["ci"].update(loaded["ci"])
          config["configSource"] = cfg_path
          break
      except Exception:
        pass

  env_mappings = {
      "MAKEFILE_WORKFLOW_CRITIC_MODEL": "adversarial-critic",
      "MAKEFILE_WORKFLOW_WORKER_MODEL": "archaeology-worker",
      "MAKEFILE_WORKFLOW_ARCHAEOLOGY_MODEL": "archaeology-worker",
      "MAKEFILE_WORKFLOW_TDD_MODEL": "tdd-worker",
      "MAKEFILE_WORKFLOW_TRIAGE_MODEL": "triage-worker",
  }
  for env_var, agent_key in env_mappings.items():
    val = os.getenv(env_var)
    if val:
      config["models"][agent_key] = val.strip()
      config["envOverrides"].append(f"{env_var}={val.strip()}")

  config["agyModelTiers"] = {
      role: map_to_agy_tier(val) for role, val in config["models"].items()
  }
  return config


def is_database_command(cmd):
  if "DATABASE_URL" in cmd or "DB_HOST" in cmd:
    return True
  for tool in DB_TOOLS:
    if re.search(rf"(?:^|[^a-zA-Z0-9_-]){re.escape(tool)}(?:$|[^a-zA-Z0-9_-])", cmd):
      return True
  return False


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
              "Reads Memento state files in the workspace to find ticket ID,"
              " branch name, active target, and completed milestones."
          ),
          "inputSchema": {
              "type": "object",
              "properties": {
                  "workspaceDir": {
                      "type": "string",
                      "description": "Absolute path to the project repository root",
                  },
                  "stateDir": {
                      "type": "string",
                      "description": (
                          "Path to the state directory (defaults to"
                          " .workflow/state inside workspaceDir)"
                      ),
                  },
              },
          },
      },
      {
          "name": "workflow_advance_target",
          "description": (
              "Checks whether prerequisites pass to move from currentTarget to"
              " nextTarget in the Makefile DAG."
          ),
          "inputSchema": {
              "type": "object",
              "properties": {
                  "currentTarget": {
                      "type": "string",
                      "description": (
                          "Current target ID, for example T20, T30, T40, T50, T75"
                      ),
                  },
                  "nextTarget": {
                      "type": "string",
                      "description": (
                          "Next target ID, for example T30, T45, T60, T80"
                      ),
                  },
                  "evidence": {
                      "type": "object",
                      "description": (
                          "Proof of prerequisite completion, such as"
                          " humanPlanApproved or blockersCount"
                      ),
                  },
              },
              "required": ["currentTarget", "nextTarget"],
          },
      },
      {
          "name": "workflow_verify_tree",
          "description": (
              "Computes the Git Merkle tree hash with 'git write-tree' in"
              " workspaceDir and compares it to expectedApprovedTree."
          ),
          "inputSchema": {
              "type": "object",
              "properties": {
                  "expectedApprovedTree": {
                      "type": "string",
                      "description": "Expected 40-character Git tree hash",
                  },
                  "workspaceDir": {
                      "type": "string",
                      "description": "Absolute path to the Git repository root",
                  },
              },
              "required": ["expectedApprovedTree"],
          },
      },
      {
          "name": "workflow_safety_check",
          "description": (
              "Checks a shell command or connection string to make sure that"
              " it does not connect to a production database."
          ),
          "inputSchema": {
              "type": "object",
              "properties": {
                  "commandLine": {
                      "type": "string",
                      "description": "Shell command line to inspect",
                  }
              },
              "required": ["commandLine"],
          },
      },
      {
          "name": "workflow_get_config",
          "description": (
              "Reads active workflow configuration and model assignments from"
              " workspaceDir, user configuration, or environment variables."
          ),
          "inputSchema": {
              "type": "object",
              "properties": {
                  "workspaceDir": {
                      "type": "string",
                      "description": "Optional project root directory",
                  }
              },
          },
      },
  ]
  return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": tools}}


def _error_result(request_id, message):
  return {
      "jsonrpc": "2.0",
      "id": request_id,
      "result": {
          "isError": True,
          "content": [{"type": "text", "text": message}],
      },
  }


def handle_tools_call(request_id, tool_name, arguments):
  arguments = arguments or {}

  if tool_name == "workflow_get_state":
    ws = resolve_workspace_dir(arguments)
    raw_state_dir = arguments.get("stateDir", ".workflow/state")
    state_dir = (
        raw_state_dir
        if os.path.isabs(raw_state_dir)
        else os.path.join(ws, raw_state_dir)
    )
    if not os.path.isdir(state_dir):
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

    files = sorted(f for f in os.listdir(state_dir) if f.endswith(".md"))
    summary = f"Found {len(files)} state card(s) in {state_dir}:\n" + "\n".join(
        f"- {f}" for f in files
    )
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {"content": [{"type": "text", "text": summary}]},
    }

  elif tool_name == "workflow_advance_target":
    current = arguments.get("currentTarget", "").strip()
    next_t = arguments.get("nextTarget", "").strip()
    evidence = arguments.get("evidence") or {}

    if current not in VALID_TRANSITIONS:
      return _error_result(
          request_id,
          f"BLOCKED: Unknown currentTarget '{current}'. Use T00 through T90.",
      )
    if next_t not in ALL_TARGETS:
      return _error_result(
          request_id,
          f"BLOCKED: Unknown nextTarget '{next_t}'. Use T00 through T90.",
      )
    if next_t not in VALID_TRANSITIONS[current]:
      allowed = sorted(VALID_TRANSITIONS[current])
      return _error_result(
          request_id,
          f"BLOCKED: Transition {current} -> {next_t} is not valid in the"
          f" Makefile DAG. Allowed next targets from {current}: {allowed}.",
      )

    gate_key = GATE_EVIDENCE_KEYS.get((current, next_t))
    if gate_key and not evidence.get(gate_key):
      return _error_result(
          request_id,
          f"BLOCKED: Cannot move {current} -> {next_t} without"
          f" {gate_key} = true.",
      )

    if current == "T40" and next_t == "T45":
      blockers = evidence.get("blockersCount", 1)
      if blockers > 0:
        return _error_result(
            request_id,
            f"BLOCKED: Critic reported {blockers} blocker(s). Route to T42"
            " (triaged-blockers) before T45.",
        )

    if current == "T40" and next_t == "T42":
      blockers = evidence.get("blockersCount", 1)
      if blockers == 0:
        return _error_result(
            request_id,
            "BLOCKED: Critic reported 0 blockers. Route to T45"
            " (approved-review) instead of T42.",
        )

    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "content": [{
                "type": "text",
                "text": f"SUCCESS: Target transition {current} -> {next_t} passed.",
            }]
        },
    }

  elif tool_name == "workflow_verify_tree":
    expected = arguments.get("expectedApprovedTree", "").strip()
    ws = resolve_workspace_dir(arguments)
    try:
      res = subprocess.run(
          ["git", "write-tree"],
          cwd=ws,
          capture_output=True,
          text=True,
          check=True,
      )
      actual = res.stdout.strip()
      return {
          "jsonrpc": "2.0",
          "id": request_id,
          "result": {
              "content": [{
                  "type": "text",
                  "text": json.dumps({
                      "matched": actual == expected,
                      "actualTree": actual,
                      "expectedTree": expected,
                      "workspaceDir": ws,
                  }),
              }]
          },
      }
    except subprocess.CalledProcessError as exc:
      stderr = (exc.stderr or "").strip()
      return _error_result(
          request_id,
          f"git write-tree failed in '{ws}': {stderr}. Pass workspaceDir with"
          " the path to the Git repository.",
      )
    except Exception as exc:
      return _error_result(request_id, f"git write-tree error in '{ws}': {exc}")

  elif tool_name == "workflow_safety_check":
    cmd = arguments.get("commandLine", "")
    if is_database_command(cmd):
      prod_match = PROD_TOKEN_RE.search(cmd)
      if prod_match:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "safe": False,
                        "reason": (
                            "Production database name detected:"
                            f" {prod_match.group(1)}"
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
    ws = resolve_workspace_dir(arguments)
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
    except Exception as exc:
      err_resp = {
          "jsonrpc": "2.0",
          "id": None,
          "error": {"code": -32700, "message": f"Parse error: {exc}"},
      }
      sys.stdout.write(json.dumps(err_resp) + "\n")
      sys.stdout.flush()


if __name__ == "__main__":
  main()
