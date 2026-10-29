#!/usr/bin/env bash
set -euo pipefail

# Makefile Workflow Installer
# Usage:
#   ./install.sh                # Install locally
#   ./install.sh --dry-run      # Validate without installing
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

echo "=== Installing Makefile Workflow Plugin ==="

# Check for agy CLI
if command -v agy >/dev/null 2>&1; then
  echo "Found Antigravity CLI (agy)."
  
  # If running from inside the cloned repo
  if [ -f "plugin.json" ] && [ -d "skills/makefile-workflow" ]; then
    echo "Running validation from current directory..."
    agy plugin validate . --strict
    if [ "$DRY_RUN" = true ]; then
      echo "Dry run completed successfully. Skipping install."
      exit 0
    fi
    echo "Installing plugin via 'agy plugin install .'..."
    agy plugin install .
  else
    if [ "$DRY_RUN" = true ]; then
      echo "Dry run: would run agy plugin install ${REPO_URL}"
      exit 0
    fi
    echo "Installing directly from git repository..."
    agy plugin install "${REPO_URL}"
  fi
else
  echo "agy CLI not found in PATH. Performing manual file installation."
  if [ "$DRY_RUN" = true ]; then
    echo "Dry run: would copy files to ${TARGET_DIR}."
    exit 0
  fi
  mkdir -p "${TARGET_DIR}"
  if [ -f "plugin.json" ]; then
    cp -R ./* "${TARGET_DIR}/"
  else
    TEMP_DIR=$(mktemp -d)
    git clone --depth 1 "${REPO_URL}" "${TEMP_DIR}"
    cp -R "${TEMP_DIR}/"* "${TARGET_DIR}/"
    rm -rf "${TEMP_DIR}"
  fi
  echo "Copied files to ${TARGET_DIR}."
fi

# Make sure SimpleEnglish is also available for documentation rules
if command -v agy >/dev/null 2>&1; then
  if ! agy plugin list | grep -q "simple-english"; then
    echo "Notice: SimpleEnglish plugin not found. Installing SimpleEnglish dependency..."
    agy plugin install "https://github.com/AminBlg/SimpleEnglish" || true
  fi
fi

echo "=== Makefile Workflow Installation Complete ==="
echo "Restart your agent session or reload your workspace to activate the plugin."
