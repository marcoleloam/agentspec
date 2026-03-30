#!/usr/bin/env bash
# ============================================================================
# AgentSpec Plugin Builder
# Packages .claude/ (source) into plugin/ (distributable Claude Code plugin)
# Adapted from upstream luanmorenommaciel/agentspec v3.0.0
# Extended for: 63 agents, 28 KB domains, frontend ecosystem, pt-BR support
# ============================================================================

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="${SCRIPT_DIR}/.claude"
PLUGIN_DIR="${SCRIPT_DIR}/plugin"
EXTRAS_DIR="${SCRIPT_DIR}/plugin-extras"

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  AgentSpec Plugin Builder v3.2.0${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# ── Step 0: Preflight checks ────────────────────────────────────────────────
if [ ! -d "${SOURCE_DIR}" ]; then
    echo -e "${RED}ERROR: .claude/ directory not found${NC}"
    exit 1
fi

if [ ! -f "${PLUGIN_DIR}/.claude-plugin/plugin.json" ]; then
    echo -e "${RED}ERROR: plugin/.claude-plugin/plugin.json not found${NC}"
    echo "Create the plugin manifest first."
    exit 1
fi

echo -e "${GREEN}[1/6] Preflight checks passed${NC}"

# ── Step 1: Clean previous build (preserve .claude-plugin/ and README.md) ──
echo -e "${YELLOW}[2/6] Cleaning previous build...${NC}"

# Remove previous build artifacts, keep plugin metadata
find "${PLUGIN_DIR}" -mindepth 1 -maxdepth 1 \
    ! -name '.claude-plugin' \
    ! -name 'README.md' \
    -exec rm -rf {} + 2>/dev/null || true

# ── Step 2: Copy source components ──────────────────────────────────────────
echo -e "${YELLOW}[3/6] Copying source components...${NC}"

# Core components
for dir in agents commands skills kb; do
    if [ -d "${SOURCE_DIR}/${dir}" ]; then
        cp -r "${SOURCE_DIR}/${dir}" "${PLUGIN_DIR}/${dir}"
        echo "  Copied ${dir}/"
    fi
done

# SDD (templates + architecture only, not workspace files)
if [ -d "${SOURCE_DIR}/sdd" ]; then
    mkdir -p "${PLUGIN_DIR}/sdd"
    # Copy templates and architecture
    for subdir in templates architecture; do
        if [ -d "${SOURCE_DIR}/sdd/${subdir}" ]; then
            cp -r "${SOURCE_DIR}/sdd/${subdir}" "${PLUGIN_DIR}/sdd/${subdir}"
            echo "  Copied sdd/${subdir}/"
        fi
    done
    # Copy index and readme
    for file in _index.md README.md; do
        if [ -f "${SOURCE_DIR}/sdd/${file}" ]; then
            cp "${SOURCE_DIR}/sdd/${file}" "${PLUGIN_DIR}/sdd/${file}"
            echo "  Copied sdd/${file}"
        fi
    done
fi

# Remove workspace-specific directories (not distributable)
rm -rf "${PLUGIN_DIR}/sdd/features" "${PLUGIN_DIR}/sdd/reports" "${PLUGIN_DIR}/sdd/archive"

# ── Step 2b: Merge plugin-extras ────────────────────────────────────────────
if [ -d "${EXTRAS_DIR}" ]; then
    echo -e "${YELLOW}  Merging plugin-extras...${NC}"
    for subdir in skills hooks scripts; do
        if [ -d "${EXTRAS_DIR}/${subdir}" ]; then
            cp -r "${EXTRAS_DIR}/${subdir}/." "${PLUGIN_DIR}/${subdir}/" 2>/dev/null || \
            cp -r "${EXTRAS_DIR}/${subdir}" "${PLUGIN_DIR}/${subdir}"
            echo "    Merged ${subdir}/"
        fi
    done
fi

# ── Step 3: Path rewriting ──────────────────────────────────────────────────
echo -e "${YELLOW}[4/6] Rewriting paths (.claude/ → \${CLAUDE_PLUGIN_ROOT}/)...${NC}"

REWRITE_COUNT=0
while IFS= read -r -d '' file; do
    # Count replacements before applying
    count=$(grep -c '\.claude/' "$file" 2>/dev/null | tail -1 || echo "0")
    if [ "${count:-0}" -gt 0 ] 2>/dev/null; then
        # Rewrite .claude/ paths to plugin root variable
        sed -i '' \
            -e 's|\.claude/kb/|${CLAUDE_PLUGIN_ROOT}/kb/|g' \
            -e 's|\.claude/agents/|${CLAUDE_PLUGIN_ROOT}/agents/|g' \
            -e 's|\.claude/commands/|${CLAUDE_PLUGIN_ROOT}/commands/|g' \
            -e 's|\.claude/skills/|${CLAUDE_PLUGIN_ROOT}/skills/|g' \
            -e 's|\.claude/sdd/templates/|${CLAUDE_PLUGIN_ROOT}/sdd/templates/|g' \
            -e 's|\.claude/sdd/architecture/|${CLAUDE_PLUGIN_ROOT}/sdd/architecture/|g' \
            -e 's|\.claude/sdd/_index\.md|${CLAUDE_PLUGIN_ROOT}/sdd/_index.md|g' \
            -e 's|\.claude/sdd/README\.md|${CLAUDE_PLUGIN_ROOT}/sdd/README.md|g' \
            "$file"
        REWRITE_COUNT=$((REWRITE_COUNT + count))
    fi
done < <(find "${PLUGIN_DIR}" -type f \( -name '*.md' -o -name '*.yaml' -o -name '*.yml' -o -name '*.json' -o -name '*.py' -o -name '*.sh' \) -print0)

echo "  Rewrote ${REWRITE_COUNT} path references"

# ── Step 4: Clean absolute paths ────────────────────────────────────────────
echo -e "${YELLOW}[5/6] Cleaning absolute paths...${NC}"

# Strip any hardcoded absolute paths preceding plugin root references
while IFS= read -r -d '' file; do
    sed -i '' -E 's|/[^ ]*/(agents/|kb/|commands/|skills/|sdd/)|\${CLAUDE_PLUGIN_ROOT}/\1|g' "$file" 2>/dev/null || true
done < <(find "${PLUGIN_DIR}" -type f \( -name '*.md' -o -name '*.yaml' -o -name '*.yml' \) -print0)

# Restore executable permissions on scripts
find "${PLUGIN_DIR}" -type f -name '*.sh' -exec chmod +x {} +

# ── Step 5: Verification ────────────────────────────────────────────────────
echo -e "${YELLOW}[6/6] Verifying build...${NC}"

# Check for stale .claude/ references (excluding workspace dirs that intentionally keep .claude/)
STALE=$(grep -rl '\.claude/' "${PLUGIN_DIR}" \
    --include='*.md' --include='*.yaml' --include='*.yml' --include='*.json' \
    2>/dev/null | \
    grep -v 'sdd/features' | \
    grep -v 'sdd/reports' | \
    grep -v 'sdd/archive' | \
    grep -v 'storage' | \
    grep -v '.claude-plugin' || true)

if [ -n "${STALE}" ]; then
    echo -e "${YELLOW}  WARNING: Found stale .claude/ references in:${NC}"
    echo "${STALE}" | while read -r f; do
        echo "    - ${f}"
        grep -n '\.claude/' "$f" | head -3
    done
    echo -e "${YELLOW}  These may be intentional (workspace paths). Review manually.${NC}"
else
    echo -e "${GREEN}  No stale .claude/ references found${NC}"
fi

# ── Summary ──────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  Build Complete!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""

AGENT_COUNT=$(find "${PLUGIN_DIR}/agents" -name '*.md' ! -name 'README.md' ! -name '_template.md' 2>/dev/null | wc -l | tr -d ' ')
COMMAND_COUNT=$(find "${PLUGIN_DIR}/commands" -name '*.md' 2>/dev/null | wc -l | tr -d ' ')
SKILL_COUNT=$(find "${PLUGIN_DIR}/skills" -maxdepth 1 -type d ! -path "${PLUGIN_DIR}/skills" 2>/dev/null | wc -l | tr -d ' ')
KB_COUNT=$(find "${PLUGIN_DIR}/kb" -maxdepth 1 -type d ! -path "${PLUGIN_DIR}/kb" ! -name '_templates' ! -name 'shared' 2>/dev/null | wc -l | tr -d ' ')

echo -e "  Agents:   ${BLUE}${AGENT_COUNT}${NC}"
echo -e "  Commands: ${BLUE}${COMMAND_COUNT}${NC}"
echo -e "  Skills:   ${BLUE}${SKILL_COUNT}${NC}"
echo -e "  KB:       ${BLUE}${KB_COUNT}${NC}"
echo ""
echo -e "  Plugin:   ${PLUGIN_DIR}/"
echo ""
echo -e "${YELLOW}To test locally:${NC}"
echo "  claude --plugin-dir ${PLUGIN_DIR}"
echo ""
echo -e "${YELLOW}To install:${NC}"
echo "  claude plugin marketplace add marcoleloam/agentspec"
echo "  claude plugin install agentspec"
