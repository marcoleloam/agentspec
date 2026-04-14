#!/bin/bash
set -e

# ============================================================================
# AgentSpec — Project Setup
# Run this in any project root to configure .claude/ with agentspec
# Symlinks shared content (agents, kb, templates) + creates local workspace
# ============================================================================

# Find agentspec installation
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENTSPEC_CLAUDE="${SCRIPT_DIR}/.claude"

if [ ! -d "$AGENTSPEC_CLAUDE" ]; then
  echo "ERROR: agentspec .claude/ not found at $AGENTSPEC_CLAUDE"
  exit 1
fi

echo "AgentSpec — Project Setup"
echo "========================="
echo "Source: $AGENTSPEC_CLAUDE"
echo "Target: $(pwd)/.claude"
echo ""

# Create local workspace directories
mkdir -p .claude/sdd/features
mkdir -p .claude/sdd/reports
mkdir -p .claude/sdd/archive
echo "→  Created .claude/sdd/{features,reports,archive}/"

# Symlink shared content
for dir in agents commands kb skills; do
  if [ -L ".claude/$dir" ]; then
    echo "↻  $dir: updating symlink"
    rm ".claude/$dir"
  elif [ -d ".claude/$dir" ]; then
    echo "⚠  $dir: directory exists, skipping (remove manually to use symlink)"
    continue
  fi
  ln -s "$AGENTSPEC_CLAUDE/$dir" ".claude/$dir"
  echo "→  $dir → agentspec"
done

# Symlink SDD shared content (templates + architecture)
for subdir in templates architecture; do
  if [ -L ".claude/sdd/$subdir" ]; then
    echo "↻  sdd/$subdir: updating symlink"
    rm ".claude/sdd/$subdir"
  elif [ -d ".claude/sdd/$subdir" ]; then
    echo "⚠  sdd/$subdir: directory exists, skipping"
    continue
  fi
  ln -s "$AGENTSPEC_CLAUDE/sdd/$subdir" ".claude/sdd/$subdir"
  echo "→  sdd/$subdir → agentspec"
done

# Copy SDD index files
for file in _index.md README.md; do
  if [ -f "$AGENTSPEC_CLAUDE/sdd/$file" ] && [ ! -f ".claude/sdd/$file" ]; then
    cp "$AGENTSPEC_CLAUDE/sdd/$file" ".claude/sdd/$file"
    echo "→  Copied sdd/$file"
  fi
done

# Add .claude/ to .gitignore if not already there
if [ -f ".gitignore" ]; then
  if ! grep -q "^\.claude/" .gitignore 2>/dev/null; then
    echo "" >> .gitignore
    echo "# AgentSpec (symlinks to shared install)" >> .gitignore
    echo ".claude/agents" >> .gitignore
    echo ".claude/commands" >> .gitignore
    echo ".claude/kb" >> .gitignore
    echo ".claude/skills" >> .gitignore
    echo ".claude/sdd/templates" >> .gitignore
    echo ".claude/sdd/architecture" >> .gitignore
    echo "→  Updated .gitignore"
  fi
fi

echo ""
echo "✅ Project configured!"
echo ""
echo "Structure:"
echo "  .claude/"
echo "    agents/      → symlink (66 agents)"
echo "    commands/     → symlink (31 commands)"
echo "    kb/           → symlink (28 KB domains)"
echo "    skills/       → symlink (2 skills)"
echo "    sdd/"
echo "      templates/    → symlink (5 templates)"
echo "      architecture/ → symlink (contracts)"
echo "      features/     → LOCAL (your brainstorms, defines, designs)"
echo "      reports/      → LOCAL (build reports)"
echo "      archive/      → LOCAL (shipped features)"
echo ""
echo "Usage: /brainstorm, /define, /design, /build, /ship"
