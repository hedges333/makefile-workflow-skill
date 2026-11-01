# Makefile Workflow Plugin Management

PLUGIN_NAME = makefile-workflow
INSTALL_DIR = $(HOME)/.gemini/config/plugins/$(PLUGIN_NAME)

.PHONY: all validate install uninstall test test-static test-safe-copy test-mcp test-compat test-hooks help

all: validate test

help:
	@echo "Available commands:"
	@echo "  make validate    - Check plugin manifest, skills, agents, and rules with agy"
	@echo "  make test        - Run all automated test suites"
	@echo "  make test-static - Run pre-flight structural static analysis"
	@echo "  make test-safe-copy - Test safe cross-user file promotion (SCAR-SYS-05)"
	@echo "  make test-mcp    - Test Model Context Protocol (MCP) server over stdio"
	@echo "  make test-compat - Check Claude, Cursor, Copilot, and ChatGPT adapters"
	@echo "  make test-hooks  - Test SessionStart and PreToolUse hook scripts"
	@echo "  make install     - Install plugin into ~/.gemini/config/plugins/$(PLUGIN_NAME)"
	@echo "  make uninstall   - Remove plugin from ~/.gemini/config/plugins/$(PLUGIN_NAME)"

validate:
	@if command -v agy >/dev/null 2>&1; then \
		echo "Checking plugin with agy..."; \
		agy plugin validate . --strict; \
	else \
		echo "agy CLI not found in PATH. Skipping CLI check."; \
	fi

test-static:
	@echo "Running pre-flight structural static analysis..."
	@python3 scripts/static_check.py
	@python3 scripts/test_static_analysis.py

test-safe-copy:
	@echo "Testing safe cross-user file promotion..."
	@python3 scripts/test_safe_copy.py

test-mcp:
	@echo "Testing MCP server JSON-RPC protocol..."
	@python3 scripts/test_mcp_server.py

test-compat:
	@echo "Testing cross-agent compatibility..."
	@python3 scripts/test_cross_agent_compatibility.py

test-hooks:
	@echo "Testing SessionStart and PreToolUse hooks..."
	@python3 scripts/test_hooks.py

test: test-static test-safe-copy test-compat test-mcp test-hooks
	@echo "Testing file structure..."
	@test -f plugin.json || (echo "Missing plugin.json" && exit 1)
	@test -f hooks.json || (echo "Missing hooks.json" && exit 1)
	@test -f mcp_config.json || (echo "Missing mcp_config.json" && exit 1)
	@test -f skills/makefile-workflow/SKILL.md || (echo "Missing SKILL.md" && exit 1)
	@test -f rules/AGENTS.md || (echo "Missing rules/AGENTS.md" && exit 1)
	@echo "All tests passed."

install: validate test
	@if command -v agy >/dev/null 2>&1; then \
		echo "Installing with agy plugin install . ..."; \
		agy plugin install .; \
	else \
		echo "Copying plugin to $(INSTALL_DIR)..."; \
		rm -rf $(INSTALL_DIR); \
		mkdir -p $(INSTALL_DIR); \
		tar --exclude='./.git' --exclude='./.tmp' --exclude='./.venv' --exclude='./.workflow/state' --exclude='./.workflow/config.json' --exclude='./.workflow/plan.md' --exclude='./.workflow/commit_msg.txt' -cf - . | tar -xf - -C $(INSTALL_DIR); \
		echo "Installed to $(INSTALL_DIR)"; \
	fi

uninstall:
	@if command -v agy >/dev/null 2>&1; then \
		agy plugin uninstall $(PLUGIN_NAME) || true; \
	fi
	@rm -rf $(INSTALL_DIR)
	@echo "Uninstalled $(PLUGIN_NAME)."
