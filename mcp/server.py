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

URI_USERINFO_RE = re.compile(r"(://)[^/\s'\";@]+@")

HOST_VALUE_RE = re.compile(
    r"(?:"
    r"(?:^|\s)-(?:h|S)\s*['\"]?|"
    r"--host(?:=|\s+)['\"]?|"
    r"\b(?:DB_HOST|PGHOST|MYSQL_HOST|MARIADB_HOST|REDIS_HOST|MONGO_HOST|HOST)=['\"]?|"
    r"://|"
    r"@"
    r")([a-zA-Z0-9._-]+)",
    re.IGNORECASE,
)

QUOTED_ARG_PAT = r"(?:'[^']*'|\"(?:\\.|[^\"\\])*\")"

INLINE_QUERY_RE = re.compile(
    rf"(?:(?<=^)|(?<=\s))(?:-c|-e|--command|--execute|--eval)(?:=|\s*){QUOTED_ARG_PAT}",
    re.IGNORECASE,
)

SQLITE_CMD_RE = re.compile(
    rf"(\bsqlite3\b[^\n]*?\s){QUOTED_ARG_PAT}\s*$",
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


def _normalize_str_list(items):
  if not isinstance(items, list):
    return []
  return [x.strip() for x in items if isinstance(x, str) and x.strip()]


def _parse_csv_env(env_name):
  raw = os.getenv(env_name, "")
  if not raw:
    return []
  return [item.strip() for item in raw.split(",") if item.strip()]


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
      "database": {
          "prodDatabases": [],
          "testDatabases": [],
          "prodHosts": [],
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
            for m_key, m_val in loaded["models"].items():
              if isinstance(m_key, str) and isinstance(m_val, str) and m_val.strip():
                config["models"][m_key] = m_val.strip()
          if isinstance(loaded.get("review"), dict):
            config["review"].update(loaded["review"])
          if isinstance(loaded.get("ci"), dict):
            config["ci"].update(loaded["ci"])
          if isinstance(loaded.get("database"), dict):
            db_loaded = loaded["database"]
            for db_key in ("prodDatabases", "testDatabases", "prodHosts"):
              if db_key in db_loaded:
                config["database"][db_key] = _normalize_str_list(
                    db_loaded[db_key]
                )
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

  db_env_mappings = {
      "MAKEFILE_WORKFLOW_PROD_DBS": "prodDatabases",
      "MAKEFILE_WORKFLOW_TEST_DBS": "testDatabases",
      "MAKEFILE_WORKFLOW_PROD_HOSTS": "prodHosts",
  }
  for env_var, db_key in db_env_mappings.items():
    vals = _parse_csv_env(env_var)
    if vals:
      merged = list(config["database"][db_key])
      for v in vals:
        if v not in merged:
          merged.append(v)
      config["database"][db_key] = merged
      config["envOverrides"].append(f"{env_var}={','.join(vals)}")

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


def _split_shell_subcommands(cmd):
  """Splits a shell command string on unquoted |, ||, &&, ;, and newline."""
  parts = []
  buf = []
  quote = None
  escaped = False
  i = 0
  n = len(cmd)
  while i < n:
    ch = cmd[i]
    if escaped:
      buf.append(ch)
      escaped = False
      i += 1
      continue
    if ch == "\\" and quote != "'":
      buf.append(ch)
      escaped = True
      i += 1
      continue
    if quote:
      buf.append(ch)
      if ch == quote:
        quote = None
      i += 1
      continue
    if ch in ("'", '"'):
      quote = ch
      buf.append(ch)
      i += 1
      continue
    if ch in (";", "\n"):
      seg = "".join(buf).strip()
      if seg:
        parts.append(seg)
      buf = []
      i += 1
      continue
    if ch in ("|", "&"):
      seg = "".join(buf).strip()
      if seg:
        parts.append(seg)
      buf = []
      if i + 1 < n and cmd[i + 1] == ch:
        i += 2
      else:
        i += 1
      continue
    buf.append(ch)
    i += 1
  tail = "".join(buf).strip()
  if tail:
    parts.append(tail)
  return parts or [cmd]


def _contains_identifier(cmd, name):
  sep = r"[^a-zA-Z0-9_-]"
  pattern = rf"(?:^|{sep}){re.escape(name)}(?:$|{sep})"
  return re.search(pattern, cmd, re.IGNORECASE) is not None


def _strip_identifier(cmd, name):
  pattern = rf"(?i)(?:(?<=^)|(?<=[^a-zA-Z0-9_-])){re.escape(name)}(?=$|[^a-zA-Z0-9_-])"
  return re.sub(pattern, " ", cmd)


def _has_prod_host_token(cmd):
  for match in HOST_VALUE_RE.finditer(cmd):
    if PROD_TOKEN_RE.search(match.group(1)):
      return True
  return False


def _evaluate_single_subcommand(subcmd, db_cfg):
  if not is_database_command(subcmd):
    return True, "OK"

  clean_cmd = URI_USERINFO_RE.sub(r"\1", subcmd)

  for host in db_cfg.get("prodHosts") or []:
    if host and _contains_identifier(clean_cmd, host):
      return False, f"Production database host detected: {host}"

  for db_name in db_cfg.get("prodDatabases") or []:
    if db_name and _contains_identifier(clean_cmd, db_name):
      return False, f"Production database name detected: {db_name}"

  if _has_prod_host_token(clean_cmd):
    return False, "Production database host detected"

  matched_test_dbs = [
      test_db
      for test_db in (db_cfg.get("testDatabases") or [])
      if test_db and _contains_identifier(clean_cmd, test_db)
  ]
  if matched_test_dbs:
    scrubbed = INLINE_QUERY_RE.sub(" ", clean_cmd)
    scrubbed = SQLITE_CMD_RE.sub(r"\1", scrubbed)
    for test_db in matched_test_dbs:
      scrubbed = _strip_identifier(scrubbed, test_db)
    prod_rem = PROD_TOKEN_RE.search(scrubbed)
    if prod_rem:
      return False, f"Production database name detected: {prod_rem.group(1)}"
    return True, f"Allowed configured test database: {matched_test_dbs[0]}"

  prod_match = PROD_TOKEN_RE.search(clean_cmd)
  if prod_match:
    return False, f"Production database name detected: {prod_match.group(1)}"

  return True, "OK"


def evaluate_database_safety(cmd, db_cfg=None):
  db_cfg = db_cfg or {}
  last_reason = "OK"
  for subcmd in _split_shell_subcommands(cmd):
    is_safe, reason = _evaluate_single_subcommand(subcmd, db_cfg)
    if not is_safe:
      return False, reason
    if reason != "OK":
      last_reason = reason
  return True, last_reason


def handle_initialize(request_id):
  return {
      "jsonrpc": "2.0",
      "id": request_id,
      "result": {
          "protocolVersion": "2024-11-05",
          "capabilities": {"tools": {}},
          "serverInfo": {
              "name": "makefile-workflow-guard",
              "version": "1.4.0",
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
                  },
                  "workspaceDir": {
                      "type": "string",
                      "description": "Optional project root directory",
                  },
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
    ws = resolve_workspace_dir(arguments)
    cfg = resolve_workflow_config(ws)
    is_safe, reason = evaluate_database_safety(cmd, cfg.get("database"))
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps({"safe": is_safe, "reason": reason}),
                }
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
