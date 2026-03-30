#!/usr/bin/env bash
# ============================================================================
# AgentSpec Workspace Initializer
# Runs on SessionStart — creates SDD directories if in a project context
# Idempotent: safe to run multiple times
# ============================================================================

# Only run if we're in a project context (git repo, CLAUDE.md, or .claude/ dir)
if [ -d ".git" ] || [ -f "CLAUDE.md" ] || [ -d ".claude" ]; then
    mkdir -p .claude/sdd/features || true
    mkdir -p .claude/sdd/reports || true
    mkdir -p .claude/sdd/archive || true
fi
