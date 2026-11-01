#!/usr/bin/env python3
"""SessionStart hook script for Antigravity.

Reads Memento state cards and user configuration from the active workspace.
"""

import json
import os
import sys

ENV_MAPPINGS = {
    "MAKEFILE_WORKFLOW_CRITIC_MODEL": "adversarial-critic",
    "MAKEFILE_WORKFLOW_WORKER_MODEL": "archaeology-worker",
    "MAKEFILE_WORKFLOW_TDD_MODEL": "tdd-worker",
    "MAKEFILE_WORKFLOW_TRIAGE_MODEL": "triage-worker",
}

DB_ENV_MAPPINGS = {
    "MAKEFILE_WORKFLOW_PROD_DBS": "prodDatabases",
    "MAKEFILE_WORKFLOW_TEST_DBS": "testDatabases",
    "MAKEFILE_WORKFLOW_PROD_HOSTS": "prodHosts",
}


def _normalize_str_list(items):
  if not isinstance(items, list):
    return []
  return [x.strip() for x in items if isinstance(x, str) and x.strip()]


def get_workflow_config(workspace_paths):
  raw_cfg = {}
  source = None

  candidates = []
  for ws in workspace_paths:
    candidates.append((os.path.join(ws, ".workflow", "config.json"), None))
  candidates.append((os.path.join(os.getcwd(), ".workflow", "config.json"), None))
  candidates.append((
      os.path.expanduser("~/.gemini/config/makefile-workflow.json"),
      "~/.gemini/config/makefile-workflow.json",
  ))

  for cfg_path, label in candidates:
    if os.path.isfile(cfg_path):
      try:
        with open(cfg_path, "r", encoding="utf-8") as f:
          loaded = json.load(f)
        if isinstance(loaded, dict):
          raw_cfg = loaded
          source = label or cfg_path
          break
      except Exception:
        pass

  models = {}
  raw_models = raw_cfg.get("models")
  if isinstance(raw_models, dict):
    for m_key, m_val in raw_models.items():
      if isinstance(m_key, str) and isinstance(m_val, str) and m_val.strip():
        models[m_key] = m_val.strip()

  db_cfg = {
      "prodDatabases": [],
      "testDatabases": [],
      "prodHosts": [],
  }
  raw_db = raw_cfg.get("database")
  if isinstance(raw_db, dict):
    for db_key in ("prodDatabases", "testDatabases", "prodHosts"):
      if db_key in raw_db:
        db_cfg[db_key] = _normalize_str_list(raw_db[db_key])

  env_applied = []
  for env_var, agent_key in ENV_MAPPINGS.items():
    val = os.getenv(env_var)
    if val and val.strip():
      models[agent_key] = val.strip()
      env_applied.append(env_var)

  for env_var, db_key in DB_ENV_MAPPINGS.items():
    val = os.getenv(env_var)
    if val:
      items = [x.strip() for x in val.split(",") if x.strip()]
      if items:
        merged = list(db_cfg[db_key])
        for item in items:
          if item not in merged:
            merged.append(item)
        db_cfg[db_key] = merged
        env_applied.append(env_var)

  if env_applied:
    env_label = "env (" + ", ".join(env_applied) + ")"
    source = (source + " + " + env_label) if source else env_label

  return {"models": models, "database": db_cfg}, source


def check_simple_english(workspace_paths):
  candidates = [
      os.path.expanduser("~/.gemini/config/plugins/simple-english"),
      os.path.expanduser("~/.gemini/plugins/simple-english"),
  ]
  for ws in workspace_paths:
    candidates.append(os.path.join(ws, "plugins", "simple-english"))
    candidates.append(os.path.join(ws, ".agents", "plugins", "simple-english"))
  for p in candidates:
    if os.path.isdir(p) and (
        os.path.exists(os.path.join(p, "plugin.json"))
        or os.path.exists(os.path.join(p, "skills", "simple-english", "SKILL.md"))
    ):
      return True
  return False


def find_state_dir(workspace_paths, artifact_dir):
  for ws in workspace_paths:
    candidate = os.path.join(ws, ".workflow", "state")
    if os.path.isdir(candidate):
      return candidate

  cwd_state = os.path.join(os.getcwd(), ".workflow", "state")
  if os.path.isdir(cwd_state):
    return cwd_state

  if artifact_dir:
    brain_state = os.path.join(artifact_dir, "state")
    if os.path.isdir(brain_state):
      return brain_state

  return ""


def main():
  try:
    input_text = sys.stdin.read()
    payload = json.loads(input_text) if input_text.strip() else {}
    if not isinstance(payload, dict):
      payload = {}

    workspace_paths = payload.get("workspacePaths")
    if not isinstance(workspace_paths, list):
      workspace_paths = []
    workspace_paths = [p for p in workspace_paths if isinstance(p, str) and p]

    artifact_dir = payload.get("artifactDirectoryPath", "")
    if not isinstance(artifact_dir, str):
      artifact_dir = ""

    state_dir = find_state_dir(workspace_paths, artifact_dir)
    cfg, cfg_source = get_workflow_config(workspace_paths)
    models = cfg.get("models") if isinstance(cfg.get("models"), dict) else {}
    critic_model = models.get("adversarial-critic", "inherit")
    tdd_model = models.get("tdd-worker", "inherit")

    notes = []
    if state_dir:
      state_files = sorted(f for f in os.listdir(state_dir) if f.endswith(".md"))
      if state_files:
        notes.append(
            f"Makefile Workflow found {len(state_files)} state card(s) in {state_dir}. "
            "Read all state cards at Target 00 (read-init-d) before taking new action."
        )

    if cfg_source:
      db_cfg = cfg.get("database") if isinstance(cfg.get("database"), dict) else {}
      prod_dbs = db_cfg.get("prodDatabases") or []
      test_dbs = db_cfg.get("testDatabases") or []
      prod_hosts = db_cfg.get("prodHosts") or []
      db_summary = ""
      if prod_dbs or test_dbs or prod_hosts:
        db_summary = (
            f", prodDatabases={prod_dbs}, testDatabases={test_dbs}, prodHosts={prod_hosts}"
        )
      notes.append(
          f"Makefile Workflow loaded configuration from {cfg_source} "
          f"(critic={critic_model}, tdd={tdd_model}{db_summary})."
      )

    has_se = check_simple_english(workspace_paths)
    if not has_se:
      notes.append(
          "Makefile Workflow note: simple-english plugin is recommended for "
          "ASD-STE100 Simplified Technical English compliance but was not found in "
          "~/.gemini/config/plugins/simple-english."
      )

    if notes:
      output = {
          "injectSteps": [{"systemMessage": {"systemMessage": " ".join(notes)}}]
      }
      print(json.dumps(output))
      return

    print(json.dumps({}))
  except Exception:
    print(json.dumps({}))


if __name__ == "__main__":
  main()
