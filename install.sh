#!/usr/bin/env bash
set -euo pipefail

# Makefile Workflow Installer
# Usage:
#   ./install.sh                # Install locally
#   ./install.sh --dry-run      # Check files without installing
#   curl -fsSL https://raw.githubusercontent.com/hedges333/makefile-workflow-skill/main/install.sh | bash

PLUGIN_NAME="makefile-workflow"
REPO_URL="https://github.com/hedges333/makefile-workflow-skill.git"
TARGET_DIR="${HOME}/.gemini/config/plugins/${PLUGIN_NAME}"

DRY_RUN=false
for arg in "$@"; do
  if [ "$arg" = "--dry-run" ]; then
    DRY_RUN=true
  fi
done

copy_plugin_tree() {
  local src_dir="$1"
  local dst_dir="$2"
  rm -rf "${dst_dir}"
  mkdir -p "${dst_dir}"
  tar -C "${src_dir}" \
    --exclude='./.git' \
    --exclude='./.tmp' \
    --exclude='./.workflow/state' \
    --exclude='./.workflow/config.json' \
    --exclude='./.workflow/plan.md' \
    --exclude='./.workflow/commit_msg.txt' \
    -cf - . | tar -xf - -C "${dst_dir}"
}

echo "=== Installing Makefile Workflow Plugin ==="

if command -v agy >/dev/null 2>&1; then
  echo "Found Antigravity CLI (agy)."

  if [ -f "plugin.json" ] && [ -d "skills/makefile-workflow" ]; then
    echo "Running plugin check from current directory..."
    agy plugin validate . --strict
    if [ "$DRY_RUN" = true ]; then
      echo "Dry run passed. Skipping install."
      exit 0
    fi
    echo "Installing plugin with 'agy plugin install .'..."
    agy plugin install .
  else
    if [ "$DRY_RUN" = true ]; then
      echo "Dry run: will run agy plugin install ${REPO_URL}"
      exit 0
    fi
    echo "Installing plugin from Git repository..."
    agy plugin install "${REPO_URL}"
  fi
else
  echo "agy CLI not found in PATH. Copying plugin files directly."
  if [ "$DRY_RUN" = true ]; then
    echo "Dry run: will copy files to ${TARGET_DIR}."
    exit 0
  fi
  if [ -f "plugin.json" ] && [ -d "skills/makefile-workflow" ]; then
    copy_plugin_tree "." "${TARGET_DIR}"
  else
    TEMP_DIR=$(mktemp -d)
    trap 'rm -rf "${TEMP_DIR}"' EXIT
    git clone --depth 1 "${REPO_URL}" "${TEMP_DIR}"
    copy_plugin_tree "${TEMP_DIR}" "${TARGET_DIR}"
  fi
  echo "Copied plugin files to ${TARGET_DIR}."
fi

if command -v agy >/dev/null 2>&1; then
  if ! agy plugin list | grep -q "simple-english"; then
    echo "SimpleEnglish plugin not found. Installing SimpleEnglish..."
    agy plugin install "https://github.com/AminBlg/SimpleEnglish" || true
  fi
fi

echo "=== Makefile Workflow Installation Complete ==="
echo "Restart your agent session to load the plugin."
