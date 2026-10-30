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
  if is_database_command(cmd):
    prod_match = PROD_TOKEN_RE.search(cmd)
    if prod_match:
      token = prod_match.group(1)
      return {
          "decision": "deny",
          "reason": (
              f"Blocked database command with production name '{token}'. "
              "Do not connect to live databases. "
              "Point tests to a *_test database or an in-memory mock."
          ),
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
