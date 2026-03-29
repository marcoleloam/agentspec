#!/bin/bash
set -e

AGENTSPEC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="$HOME/.claude"

echo "AgentSpec — Global Install"
echo "=========================="
echo "Source: $AGENTSPEC_DIR/.claude"
echo "Target: $CLAUDE_DIR"
echo ""

# Create ~/.claude if it doesn't exist
mkdir -p "$CLAUDE_DIR"

# Symlink agents
if [ -L "$CLAUDE_DIR/agents" ]; then
  echo "↻  agents: updating symlink"
  rm "$CLAUDE_DIR/agents"
  ln -s "$AGENTSPEC_DIR/.claude/agents" "$CLAUDE_DIR/agents"
elif [ -d "$CLAUDE_DIR/agents" ]; then
  echo "⚠  agents: directory already exists at ~/.claude/agents"
  echo "   Remove it manually and re-run if you want AgentSpec to manage it."
else
  echo "→  agents: creating symlink"
  ln -s "$AGENTSPEC_DIR/.claude/agents" "$CLAUDE_DIR/agents"
fi

# Symlink commands
if [ -L "$CLAUDE_DIR/commands" ]; then
  echo "↻  commands: updating symlink"
  rm "$CLAUDE_DIR/commands"
  ln -s "$AGENTSPEC_DIR/.claude/commands" "$CLAUDE_DIR/commands"
elif [ -d "$CLAUDE_DIR/commands" ]; then
  echo "⚠  commands: directory already exists at ~/.claude/commands"
  echo "   Remove it manually and re-run if you want AgentSpec to manage it."
else
  echo "→  commands: creating symlink"
  ln -s "$AGENTSPEC_DIR/.claude/commands" "$CLAUDE_DIR/commands"
fi

# Copy settings.json (permissions) — only if not already present
if [ -f "$CLAUDE_DIR/settings.json" ]; then
  echo "↷  settings.json: already exists, skipping (not overwriting your config)"
else
  echo "→  settings.json: copying permissions config"
  cp "$AGENTSPEC_DIR/.claude/settings.json" "$CLAUDE_DIR/settings.json"
fi

echo ""
echo "✅ Done! AgentSpec v3.1.0 is now available globally."
echo ""
echo "Next steps:"
echo "  1. Copy the project template to any new project:"
echo "     cp $AGENTSPEC_DIR/CLAUDE.md.template /path/to/your-project/CLAUDE.md"
echo ""
echo "  2. Start using SDD commands in Claude Code:"
echo "     /brainstorm, /define, /design, /build, /ship"
echo ""
echo "  To update AgentSpec later:"
echo "     cd $AGENTSPEC_DIR && git pull"
echo "     (symlinks update automatically)"
