#!/usr/bin/env python3
"""PreToolUse hook script for Antigravity.

Blocks production database commands and gates git commit, git push, and gh pr merge.
"""

import json
import os
import re
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


def _normalize_str_list(items):
  if not isinstance(items, list):
    return []
  return [x.strip() for x in items if isinstance(x, str) and x.strip()]


def _parse_csv_env(env_name):
  raw = os.getenv(env_name, "")
  if not raw:
    return []
  return [item.strip() for item in raw.split(",") if item.strip()]


def load_database_config(payload):
  """Loads database isolation rules from workspace config, global config, and env."""
  db_cfg = {
      "prodDatabases": [],
      "testDatabases": [],
      "prodHosts": [],
  }

  candidates = []
  for ws in payload.get("workspacePaths") or []:
    candidates.append(os.path.join(ws, ".workflow", "config.json"))
  candidates.append(os.path.join(os.getcwd(), ".workflow", "config.json"))
  candidates.append(os.path.expanduser("~/.gemini/config/makefile-workflow.json"))

  for cfg_path in candidates:
    if os.path.isfile(cfg_path):
      try:
        with open(cfg_path, "r", encoding="utf-8") as f:
          loaded = json.load(f)
        if isinstance(loaded, dict) and isinstance(loaded.get("database"), dict):
          raw_db = loaded["database"]
          for key in ("prodDatabases", "testDatabases", "prodHosts"):
            if key in raw_db:
              db_cfg[key] = _normalize_str_list(raw_db[key])
        break
      except Exception:
        pass

  env_mappings = {
      "MAKEFILE_WORKFLOW_PROD_DBS": "prodDatabases",
      "MAKEFILE_WORKFLOW_TEST_DBS": "testDatabases",
      "MAKEFILE_WORKFLOW_PROD_HOSTS": "prodHosts",
  }
  for env_var, key in env_mappings.items():
    vals = _parse_csv_env(env_var)
    if vals:
      merged = list(db_cfg[key])
      for v in vals:
        if v not in merged:
          merged.append(v)
      db_cfg[key] = merged

  return db_cfg


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
    return True, ""

  clean_cmd = URI_USERINFO_RE.sub(r"\1", subcmd)

  for host in db_cfg.get("prodHosts") or []:
    if host and _contains_identifier(clean_cmd, host):
      return (
          False,
          f"Blocked database command targeting live host '{host}'. "
          "Do not connect to live databases. "
          "Point tests to a *_test database or an in-memory mock.",
      )

  for db_name in db_cfg.get("prodDatabases") or []:
    if db_name and _contains_identifier(clean_cmd, db_name):
      return (
          False,
          f"Blocked database command with live database name '{db_name}'. "
          "Do not connect to live databases. "
          "Point tests to a *_test database or an in-memory mock.",
      )

  if _has_prod_host_token(clean_cmd):
    return (
        False,
        "Blocked database command targeting a production host. "
        "Do not connect to live databases. "
        "Point tests to a *_test database or an in-memory mock.",
    )

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
      token = prod_rem.group(1)
      return (
          False,
          f"Blocked database command with production name '{token}'. "
          "Do not connect to live databases. "
          "Point tests to a *_test database or an in-memory mock.",
      )
    return True, ""

  prod_match = PROD_TOKEN_RE.search(clean_cmd)
  if prod_match:
    token = prod_match.group(1)
    return (
        False,
        f"Blocked database command with production name '{token}'. "
        "Do not connect to live databases. "
        "Point tests to a *_test database or an in-memory mock.",
    )

  return True, ""


def evaluate_database_safety(cmd, db_cfg):
  for subcmd in _split_shell_subcommands(cmd):
    is_safe, deny_reason = _evaluate_single_subcommand(subcmd, db_cfg)
    if not is_safe:
      return False, deny_reason
  return True, ""


def resolve_state_dir(payload):
  """Finds the active state directory from workspacePaths or artifactDirectoryPath."""
  workspace_paths = payload.get("workspacePaths") or []
  for ws in workspace_paths:
    candidate = os.path.join(ws, ".workflow", "state")
    if os.path.isdir(candidate):
      return candidate

  artifact_dir = payload.get("artifactDirectoryPath", "")
  if artifact_dir:
    brain_state = os.path.join(artifact_dir, "state")
    if os.path.isdir(brain_state):
      return brain_state

  if workspace_paths:
    return os.path.join(workspace_paths[0], ".workflow", "state")

  return os.path.join(os.getcwd(), ".workflow", "state")


def is_database_command(cmd):
  if "DATABASE_URL" in cmd or "DB_HOST" in cmd:
    return True
  for tool in DB_TOOLS:
    if re.search(rf"(?:^|[^a-zA-Z0-9_-]){re.escape(tool)}(?:$|[^a-zA-Z0-9_-])", cmd):
      return True
  return False


def evaluate_tool_call(payload):
  tool_call = payload.get("toolCall", {})
  tool_name = tool_call.get("name", "")
  args = tool_call.get("args", {})

  if tool_name != "run_command":
    return {"decision": "allow"}

  cmd = args.get("CommandLine", "").strip()
  if not cmd:
    return {"decision": "allow"}

  # 1. Production database guard
  db_cfg = load_database_config(payload)
  is_safe, deny_reason = evaluate_database_safety(cmd, db_cfg)
  if not is_safe:
    return {
        "decision": "deny",
        "reason": deny_reason,
    }

  # 2. Block force-push to main or master
  if re.search(r"\bgit\s+push\b", cmd) and re.search(r"(--force\b|-f\b)", cmd):
    if re.search(r"\b(main|master)\b", cmd):
      return {
          "decision": "deny",
          "reason": (
              "Blocked force-push to the default branch. "
              "Push to a ticket branch instead."
          ),
      }

  state_dir = resolve_state_dir(payload)
  review_card = os.path.join(state_dir, "45_review_approved.md")
  has_review = os.path.isfile(review_card)

  # 3. Target 50 Human Commit Gate
  if re.search(r"\bgit\s+commit\b", cmd):
    if has_review:
      reason = (
          "Target 50 Commit Gate: 45_review_approved.md is present. "
          "Approve to create the commit."
      )
    else:
      reason = (
          "Target 50 Commit Gate: 45_review_approved.md is missing in .workflow/state/. "
          "Make sure that Target 45 review passed before you approve."
      )
    return {"decision": "force_ask", "reason": reason}

  # 4. Target 60 Human Push Gate
  if re.search(r"\bgit\s+push\b", cmd):
    if has_review:
      reason = (
          "Target 60 Push Gate: 45_review_approved.md is present. "
          "Make sure that the branch merges cleanly before you approve."
      )
    else:
      reason = (
          "Target 60 Push Gate: 45_review_approved.md is missing in .workflow/state/. "
          "Make sure that review and commit gates passed before you approve."
      )
    return {"decision": "force_ask", "reason": reason}

  # 5. Target 75 Human Landing Gate
  if re.search(r"\bgh\s+pr\s+merge\b", cmd):
    return {
        "decision": "force_ask",
        "reason": (
            "Target 75 Landing Gate: gh pr merge requires operator approval. "
            "Make sure that CI is green and the 180-second quiet period passed."
        ),
    }

  return {"decision": "allow"}


def main():
  try:
    input_text = sys.stdin.read()
    if not input_text.strip():
      print(json.dumps({"decision": "allow"}))
      return

    payload = json.loads(input_text)
    result = evaluate_tool_call(payload)
    print(json.dumps(result))
  except Exception as exc:
    print(json.dumps({"decision": "allow", "reason": f"Hook error: {exc}"}))


if __name__ == "__main__":
  main()
