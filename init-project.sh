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

# Check if .claude already exists
if [ -d "$TARGET/agents" ]; then
  echo "⚠  .claude/ already exists. Updating..."
  echo ""
fi

# Copy everything
cp -r "$SOURCE/agents" "$TARGET/agents" 2>/dev/null || mkdir -p "$TARGET/agents" && cp -r "$SOURCE/agents/"* "$TARGET/agents/"
cp -r "$SOURCE/commands" "$TARGET/commands" 2>/dev/null || mkdir -p "$TARGET/commands" && cp -r "$SOURCE/commands/"* "$TARGET/commands/"
cp -r "$SOURCE/kb" "$TARGET/kb" 2>/dev/null || mkdir -p "$TARGET/kb" && cp -r "$SOURCE/kb/"* "$TARGET/kb/"
cp -r "$SOURCE/skills" "$TARGET/skills" 2>/dev/null || mkdir -p "$TARGET/skills" && cp -r "$SOURCE/skills/"* "$TARGET/skills/"

# SDD: copy templates + architecture, create local workspace
mkdir -p "$TARGET/sdd/templates" "$TARGET/sdd/architecture"
mkdir -p "$TARGET/sdd/features" "$TARGET/sdd/reports" "$TARGET/sdd/archive"
cp -r "$SOURCE/sdd/templates/"* "$TARGET/sdd/templates/" 2>/dev/null || true
cp -r "$SOURCE/sdd/architecture/"* "$TARGET/sdd/architecture/" 2>/dev/null || true
# Copy SDD index files
for f in _index.md README.md; do
  [ -f "$SOURCE/sdd/$f" ] && cp "$SOURCE/sdd/$f" "$TARGET/sdd/$f"
done

echo "✅ Done!"
echo ""
echo "Installed:"
AGENT_COUNT=$(find "$TARGET/agents" -name "*.md" ! -name "README.md" ! -name "_template.md" 2>/dev/null | wc -l | tr -d ' ')
KB_COUNT=$(find "$TARGET/kb" -maxdepth 1 -type d ! -path "$TARGET/kb" ! -name "_templates" ! -name "shared" 2>/dev/null | wc -l | tr -d ' ')
echo "  $AGENT_COUNT agents"
echo "  $KB_COUNT KB domains"
echo "  5 SDD templates"
echo ""
echo "To update later:"
echo "  bash $SCRIPT_DIR/init-project.sh $(cd "${1:-.}" && pwd)"
