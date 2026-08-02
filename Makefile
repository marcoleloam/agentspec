# ============================================================================
# AgentSpec — developer Makefile
# ============================================================================
# Single entry point for everything a contributor needs to do locally.
# Every target is idempotent and safe to re-run.
#
# Quick start:
#   make help          # show all targets
#   make build         # full plugin build (tests + generate + package)
#   make test          # pytest suite only
#   make check         # drift check (tests + --check on generators)
#   make lint          # shellcheck + markdown warnings
# ============================================================================

# Use bash so we get [[ ]], set -u, etc. — not POSIX sh.
SHELL := /usr/bin/env bash

.DEFAULT_GOAL := help
.PHONY: help build test check lint clean generate codex plugin install-deps spec-lint spec-judge spec-venvs

# ----------------------------------------------------------------------------
# Help
# ----------------------------------------------------------------------------

help: ## Show this help
	@echo "AgentSpec — developer targets"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "  %-18s %s\n", "TARGET", "DESCRIPTION"; printf "  %-18s %s\n", "------", "-----------"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@echo ""
	@echo "Most-used: make build  |  make test  |  make check"

# ----------------------------------------------------------------------------
# Core targets
# ----------------------------------------------------------------------------

build: ## Full plugin build (tests + regenerate agent-router + package)
	@./build-plugin.sh

test: ## Run pytest suite
	@python3 -m pytest tests/ -v

check: ## Drift check — tests + generators in --check mode (fails on drift)
	@python3 -m pytest tests/ -q
	@python3 scripts/generate-agent-router.py --check
	@python3 scripts/generate-codex-plugin.py --check

generate: ## Regenerate agent-router artifacts (SKILL.md + routing.json)
	@python3 scripts/generate-agent-router.py

codex: ## Regenerate the Codex CLI config (.codex/agents/ + AGENTS.md)
	@python3 scripts/generate-codex-plugin.py

plugin: build ## Alias for `make build`

spec-lint: ## Run the spec-linter component test suite (tools/spec-linter)
	@if [ -x tools/spec-linter/.venv/bin/python ]; then \
		( cd tools/spec-linter && .venv/bin/python -m pytest -v ); \
	else \
		( cd tools/spec-linter && python3 -m pytest -v ); \
	fi

spec-judge: ## Run the spec-judge component test suite (tools/spec-judge, offline)
	@if [ -x tools/spec-judge/.venv/bin/python ]; then \
		( cd tools/spec-judge && .venv/bin/python -m pytest -v ); \
	else \
		( cd tools/spec-judge && python3 -m pytest -v ); \
	fi

# Fork-local: upstream documents `uv venv`; this bootstraps the same venvs with
# stdlib venv + pip so contributors without uv can run the engines.
spec-venvs: ## Create/refresh the tools/ virtualenvs (spec-linter + spec-judge)
	@echo "Bootstrapping tools/spec-linter/.venv ..."
	@python3 -m venv tools/spec-linter/.venv
	@tools/spec-linter/.venv/bin/python -m pip install -q --upgrade pip
	@tools/spec-linter/.venv/bin/python -m pip install -q -e 'tools/spec-linter[dev]'
	@echo "Bootstrapping tools/spec-judge/.venv ..."
	@python3 -m venv tools/spec-judge/.venv
	@tools/spec-judge/.venv/bin/python -m pip install -q --upgrade pip
	@tools/spec-judge/.venv/bin/python -m pip install -q -e 'tools/spec-linter' -e 'tools/spec-judge[dev]'
	@echo "Done. Verify with: make spec-lint && make spec-judge"

# ----------------------------------------------------------------------------
# Hygiene
# ----------------------------------------------------------------------------

lint: ## Lint shell scripts via shellcheck (skips gracefully if not installed)
	@if command -v shellcheck >/dev/null 2>&1; then \
		echo "Running shellcheck..."; \
		shellcheck -S warning \
			build-plugin.sh \
			.claude/skills/visual-explainer/scripts/share.sh \
			plugin-extras/scripts/init-workspace.sh; \
	else \
		echo "shellcheck not installed — brew install shellcheck"; \
		exit 0; \
	fi

clean: ## Remove generated plugin/ artifacts (keep .claude-plugin/)
	@find plugin -mindepth 1 -maxdepth 1 \
		! -name '.claude-plugin' \
		! -name 'README.md' \
		-exec rm -rf {} + 2>/dev/null || true
	@echo "Plugin artifacts cleaned. Run 'make build' to rebuild."

install-deps: ## Install optional dev dependencies (pytest, shellcheck)
	@echo "Installing pytest..."
	@python3 -m pip install --user pytest
	@if ! command -v shellcheck >/dev/null 2>&1; then \
		echo ""; \
		echo "shellcheck not installed. On macOS:  brew install shellcheck"; \
		echo "                        On Linux:    apt-get install shellcheck"; \
	fi
