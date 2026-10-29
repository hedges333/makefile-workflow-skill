#!/usr/bin/env python3
"""SessionStart hook script for Antigravity.

Checks for existing Memento state cards and user workflow configuration,
injecting an initialization message.
"""

import json
import os
import sys


def get_workflow_config():
  cwd = os.getcwd()
  local_cfg = os.path.join(cwd, ".workflow", "config.json")
  global_cfg = os.path.expanduser("~/.gemini/config/makefile-workflow.json")

  cfg = {}
  source = None
  if os.path.isfile(local_cfg):
    try:
      with open(local_cfg, "r", encoding="utf-8") as f:
        cfg = json.load(f)
        source = ".workflow/config.json"
    except Exception:
      pass
  elif os.path.isfile(global_cfg):
    try:
      with open(global_cfg, "r", encoding="utf-8") as f:
        cfg = json.load(f)
        source = "~/.gemini/config/makefile-workflow.json"
    except Exception:
      pass

  critic_override = os.getenv("MAKEFILE_WORKFLOW_CRITIC_MODEL")
  if critic_override:
    cfg.setdefault("models", {})["adversarial-critic"] = critic_override
    source = (source + " + env") if source else "env (MAKEFILE_WORKFLOW_CRITIC_MODEL)"

  return cfg, source


def main():
  try:
    input_text = sys.stdin.read()
    payload = json.loads(input_text) if input_text.strip() else {}

    cwd = os.getcwd()
    local_state_dir = os.path.join(cwd, ".workflow", "state")
    artifact_dir = payload.get("artifactDirectoryPath", "")
    brain_state_dir = os.path.join(artifact_dir, "state") if artifact_dir else ""

    state_dir = ""
    if os.path.isdir(local_state_dir):
      state_dir = local_state_dir
    elif brain_state_dir and os.path.isdir(brain_state_dir):
      state_dir = brain_state_dir

    cfg, cfg_source = get_workflow_config()
    models = cfg.get("models", {})
    critic_model = models.get("adversarial-critic", "pro")
    tdd_model = models.get("tdd-worker", "inherit")

    notes = []
    if state_dir and os.path.isdir(state_dir):
      state_files = [f for f in os.listdir(state_dir) if f.endswith(".md")]
      if state_files:
        notes.append(
            f"⚡ Makefile Workflow Active: Found {len(state_files)} Memento state card(s) in {state_dir}. "
            "Resume active ticket at Target 00 (read-init-d)."
        )

    if cfg_source:
      notes.append(
          f"⚙ Configuration loaded from {cfg_source}: critic={critic_model}, tdd={tdd_model}."
      )

    if notes:
      msg = " ".join(notes)
      output = {"injectSteps": [{"systemMessage": {"systemMessage": msg}}]}
      print(json.dumps(output))
      return

    # No state cards or config found; start clean
    print(json.dumps({}))
  except Exception:
    print(json.dumps({}))


if __name__ == "__main__":
  main()
