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

# Symlink all core components
for dir in agents commands kb sdd skills; do
  if [ -L "$CLAUDE_DIR/$dir" ]; then
    echo "↻  $dir: updating symlink"
    rm "$CLAUDE_DIR/$dir"
    ln -s "$AGENTSPEC_DIR/.claude/$dir" "$CLAUDE_DIR/$dir"
  elif [ -d "$CLAUDE_DIR/$dir" ]; then
    echo "⚠  $dir: directory already exists at ~/.claude/$dir"
    echo "   Remove it manually and re-run if you want AgentSpec to manage it."
  else
    echo "→  $dir: creating symlink"
    ln -s "$AGENTSPEC_DIR/.claude/$dir" "$CLAUDE_DIR/$dir"
  fi
done

# Symlink settings.json (bypassPermissions + pre-approved tools)
if [ -L "$CLAUDE_DIR/settings.json" ]; then
  echo "↻  settings.json: updating symlink"
  rm "$CLAUDE_DIR/settings.json"
  ln -s "$AGENTSPEC_DIR/.claude/settings.json" "$CLAUDE_DIR/settings.json"
elif [ -f "$CLAUDE_DIR/settings.json" ]; then
  echo "⚠  settings.json: file already exists — backing up and replacing"
  cp "$CLAUDE_DIR/settings.json" "$CLAUDE_DIR/settings.json.bak"
  rm "$CLAUDE_DIR/settings.json"
  ln -s "$AGENTSPEC_DIR/.claude/settings.json" "$CLAUDE_DIR/settings.json"
  echo "   Backup saved to ~/.claude/settings.json.bak"
else
  echo "→  settings.json: creating symlink"
  ln -s "$AGENTSPEC_DIR/.claude/settings.json" "$CLAUDE_DIR/settings.json"
fi

echo ""
echo "✅ Done! AgentSpec v3.2.0 is now available globally."
echo ""
echo "Symlinked:"
echo "  agents   → 66 specialized agents"
echo "  commands → 31 slash commands"
echo "  kb       → 28 knowledge base domains (374 files)"
echo "  sdd      → templates, architecture, workflow contracts"
echo "  skills   → 2 auto-invoked skills"
echo "  settings → bypassPermissions + pre-approved tools"
echo ""
echo "Next steps:"
echo "  1. Start using SDD commands in any project:"
echo "     /brainstorm, /define, /design, /build, /ship"
echo ""
echo "  2. To update AgentSpec later:"
echo "     cd $AGENTSPEC_DIR && git pull"
echo "     (symlinks update automatically)"
