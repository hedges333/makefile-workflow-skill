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


def get_workflow_config(workspace_paths):
  cfg = {}
  source = None

  for ws in workspace_paths:
    local_cfg = os.path.join(ws, ".workflow", "config.json")
    if os.path.isfile(local_cfg):
      try:
        with open(local_cfg, "r", encoding="utf-8") as f:
          cfg = json.load(f)
          source = local_cfg
          break
      except Exception:
        pass

  if source is None:
    cwd_cfg = os.path.join(os.getcwd(), ".workflow", "config.json")
    global_cfg = os.path.expanduser("~/.gemini/config/makefile-workflow.json")
    if os.path.isfile(cwd_cfg):
      try:
        with open(cwd_cfg, "r", encoding="utf-8") as f:
          cfg = json.load(f)
          source = cwd_cfg
      except Exception:
        pass
    elif os.path.isfile(global_cfg):
      try:
        with open(global_cfg, "r", encoding="utf-8") as f:
          cfg = json.load(f)
          source = "~/.gemini/config/makefile-workflow.json"
      except Exception:
        pass

  env_applied = []
  for env_var, agent_key in ENV_MAPPINGS.items():
    val = os.getenv(env_var)
    if val:
      cfg.setdefault("models", {})[agent_key] = val.strip()
      env_applied.append(env_var)

  if env_applied:
    env_label = "env (" + ", ".join(env_applied) + ")"
    source = (source + " + " + env_label) if source else env_label

  return cfg, source


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

    workspace_paths = payload.get("workspacePaths") or []
    artifact_dir = payload.get("artifactDirectoryPath", "")

    state_dir = find_state_dir(workspace_paths, artifact_dir)
    cfg, cfg_source = get_workflow_config(workspace_paths)
    models = cfg.get("models", {})
    critic_model = models.get("adversarial-critic", "pro")
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
      notes.append(
          f"Makefile Workflow loaded configuration from {cfg_source} "
          f"(critic={critic_model}, tdd={tdd_model})."
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
