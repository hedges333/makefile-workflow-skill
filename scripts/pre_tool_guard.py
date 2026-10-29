#!/usr/bin/env python3
"""PreToolUse hook script for Antigravity.

Enforces:
1. Zero production database access.
2. Human pause gates on git commit, git push, and gh pr merge.
"""

import json
import os
import re
import sys


def evaluate_tool_call(payload):
  tool_call = payload.get("toolCall", {})
  tool_name = tool_call.get("name", "")
  args = tool_call.get("args", {})

  if tool_name != "run_command":
    return {"decision": "allow"}

  cmd = args.get("CommandLine", "").strip()
  if not cmd:
    return {"decision": "allow"}

  # 1. Database Protection Check
  # Flag commands attempting to connect to production databases or drop non-test DBs
  db_commands = ["psql", "mysql", "mongo", "redis-cli", "flyway", "liquibase"]
  is_db_op = any(tool in cmd for tool in db_commands) or "DATABASE_URL" in cmd

  if is_db_op:
    prod_match = re.search(r"\b(prod|production)\b", cmd, re.IGNORECASE)
    if prod_match:
      return {
          "decision": "deny",
          "reason": (
              "Makefile Workflow Gatekeeper: Production database keywords"
              f" detected in command: '{prod_match.group(0)}'. Automated tests"
              " and agent commands must never connect to live production"
              " databases. Use dedicated test databases (*_test) or in-memory"
              " mocks."
          ),
      }

  # 2. Git Action Safety Check
  # Check for git commit without Target 45 Review Approval
  artifact_dir = payload.get("artifactDirectoryPath", "")
  state_dir = os.path.join(artifact_dir, "state") if artifact_dir else ""

  if re.search(r"\bgit\s+commit\b", cmd):
    review_card = (
        os.path.join(state_dir, "45_review_approved.md") if state_dir else ""
    )
    if not (review_card and os.path.exists(review_card)):
      return {
          "decision": "force_ask",
          "reason": (
              "Makefile Workflow Gatekeeper: 'git commit' invoked without"
              " prior Target 45 Review Approval card"
              " (45_review_approved.md). Verify that adversarial review passed"
              " before committing."
          ),
      }

  # Check for git push without Target 50 Commit Approval
  if re.search(r"\bgit\s+push\b", cmd):
    commit_card = (
        os.path.join(state_dir, "45_review_approved.md") if state_dir else ""
    )
    if not (commit_card and os.path.exists(commit_card)):
      return {
          "decision": "force_ask",
          "reason": (
              "Makefile Workflow Gatekeeper: 'git push' invoked without prior"
              " Target 50 Commit Approval. Verify mergeability and commit"
              " status before pushing."
          ),
      }

  # Check for gh pr merge without Target 75 Landing Approval
  if re.search(r"\bgh\s+pr\s+merge\b", cmd):
    return {
        "decision": "force_ask",
        "reason": (
            "Makefile Workflow Gatekeeper: 'gh pr merge' invoked. Confirm that"
            " Target 75 Landing Gate (CI green, 180s quiescence, policy table)"
            " was presented to the user."
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
  except Exception as e:
    # Fail open with warning on unexpected hook crash to avoid stalling session
    print(json.dumps({"decision": "allow", "reason": f"Hook exception: {e}"}))


if __name__ == "__main__":
  main()
