#!/bin/bash
set -e

# ============================================================================
# AgentSpec — Project Setup
# Copies .claude/ into the target project for full functionality
# Usage: bash ~/agentspec/init-project.sh [target-dir]
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE="${SCRIPT_DIR}/.claude"
TARGET="${1:-.}/.claude"

if [ ! -d "$SOURCE" ]; then
  echo "ERROR: .claude/ not found at $SOURCE"
  exit 1
fi

echo "AgentSpec — Project Setup"
echo "========================="
echo "Source: $SOURCE"
echo "Target: $(cd "${1:-.}" && pwd)/.claude"
echo ""

# Remove old symlinks or directories (clean slate for shared content)
for dir in agents commands kb skills; do
  if [ -L "$TARGET/$dir" ]; then
    echo "↻  Removing old symlink: $dir"
    rm "$TARGET/$dir"
  elif [ -d "$TARGET/$dir" ]; then
    echo "↻  Removing old copy: $dir"
    rm -rf "$TARGET/$dir"
  fi
done

# Remove old SDD symlinks
for subdir in templates architecture; do
  if [ -L "$TARGET/sdd/$subdir" ]; then
    echo "↻  Removing old symlink: sdd/$subdir"
    rm "$TARGET/sdd/$subdir"
  elif [ -d "$TARGET/sdd/$subdir" ]; then
    rm -rf "$TARGET/sdd/$subdir"
  fi
done

# Create .claude/ if needed
mkdir -p "$TARGET"

# Copy shared content
for dir in agents commands kb skills; do
  cp -r "$SOURCE/$dir" "$TARGET/$dir"
  echo "→  Copied $dir/"
done

# SDD: copy templates + architecture, create local workspace
mkdir -p "$TARGET/sdd/features" "$TARGET/sdd/reports" "$TARGET/sdd/archive"
cp -r "$SOURCE/sdd/templates" "$TARGET/sdd/templates"
cp -r "$SOURCE/sdd/architecture" "$TARGET/sdd/architecture"
echo "→  Copied sdd/templates/"
echo "→  Copied sdd/architecture/"

# Copy SDD index files
for f in _index.md README.md; do
  [ -f "$SOURCE/sdd/$f" ] && cp "$SOURCE/sdd/$f" "$TARGET/sdd/$f"
done

# Summary
echo ""
echo "✅ Done!"
echo ""
AGENT_COUNT=$(find "$TARGET/agents" -name "*.md" ! -name "README.md" ! -name "_template.md" 2>/dev/null | wc -l | tr -d ' ')
KB_COUNT=$(find "$TARGET/kb" -maxdepth 1 -type d ! -path "$TARGET/kb" ! -name "_templates" ! -name "shared" 2>/dev/null | wc -l | tr -d ' ')
echo "  $AGENT_COUNT agents"
echo "  $KB_COUNT KB domains"
echo "  5 SDD templates"
echo ""
echo "To update later: re-run this script (safe to repeat)"
echo "  bash $SCRIPT_DIR/init-project.sh $(cd "${1:-.}" && pwd)"
