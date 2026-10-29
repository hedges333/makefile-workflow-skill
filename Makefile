# Makefile Workflow Plugin Management

PLUGIN_NAME = makefile-workflow
INSTALL_DIR = $(HOME)/.gemini/config/plugins/$(PLUGIN_NAME)

.PHONY: all validate install uninstall test test-mcp test-compat test-hooks help

all: validate test

help:
	@echo "Available commands:"
	@echo "  make validate    - Validate plugin manifest and skills with agy plugin validate"
	@echo "  make test        - Run all automated test suites"
	@echo "  make test-mcp    - Test Model Context Protocol (MCP) server over stdio"
	@echo "  make test-compat - Validate Claude, Cursor, Copilot, and ChatGPT adapters"
	@echo "  make test-hooks  - Validate PreToolUse hook assertions"
	@echo "  make install     - Install plugin into ~/.gemini/config/plugins/$(PLUGIN_NAME)"
	@echo "  make uninstall   - Remove plugin from ~/.gemini/config/plugins/$(PLUGIN_NAME)"

validate:
	@if command -v agy >/dev/null 2>&1; then \
		echo "Validating plugin with agy..."; \
		agy plugin validate . --strict; \
	else \
		echo "agy CLI not found in PATH; skipping CLI validation."; \
	fi

test-mcp:
	@echo "Testing MCP server JSON-RPC protocol..."
	@python3 scripts/test_mcp_server.py

test-compat:
	@echo "Testing cross-agent compatibility..."
	@python3 scripts/test_cross_agent_compatibility.py

test-hooks:
	@echo "Testing pre-tool hook assertions..."
	@python3 -c "import json, subprocess; \
	p1 = {'toolCall': {'name': 'run_command', 'args': {'CommandLine': 'psql -h production.db.internal myapp'}}}; \
	r1 = json.loads(subprocess.run(['python3', 'scripts/pre_tool_guard.py'], input=json.dumps(p1), text=True, capture_output=True).stdout); \
	assert r1['decision'] == 'deny'; \
	p2 = {'toolCall': {'name': 'run_command', 'args': {'CommandLine': 'git commit -m test'}}}; \
	r2 = json.loads(subprocess.run(['python3', 'scripts/pre_tool_guard.py'], input=json.dumps(p2), text=True, capture_output=True).stdout); \
	assert r2['decision'] == 'force_ask'; \
	print('✔ Pre-tool hook assertions passed.')"

test: test-compat test-mcp test-hooks
	@echo "Testing file structure..."
	@test -f plugin.json || (echo "Missing plugin.json" && exit 1)
	@test -f hooks.json || (echo "Missing hooks.json" && exit 1)
	@test -f mcp_config.json || (echo "Missing mcp_config.json" && exit 1)
	@test -f skills/makefile-workflow/SKILL.md || (echo "Missing SKILL.md" && exit 1)
	@test -f rules/AGENTS.md || (echo "Missing rules/AGENTS.md" && exit 1)
	@echo "All tests passed successfully."

install: validate test
	@if command -v agy >/dev/null 2>&1; then \
		echo "Installing via agy plugin install . ..."; \
		agy plugin install .; \
	else \
		echo "Copying plugin to $(INSTALL_DIR)..."; \
		mkdir -p $(INSTALL_DIR); \
		cp -R ./* $(INSTALL_DIR)/; \
		echo "Installed to $(INSTALL_DIR)"; \
	fi

uninstall:
	@if command -v agy >/dev/null 2>&1; then \
		agy plugin uninstall $(PLUGIN_NAME) || true; \
	fi
	@rm -rf $(INSTALL_DIR)
	@echo "Uninstalled $(PLUGIN_NAME)."
