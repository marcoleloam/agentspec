---
name: continuar
description: Resume an incomplete or unsatisfactory build by analyzing the gap between what was requested and what was delivered (Phase 3+)
---

# Continuar Command

> Resume an incomplete or unsatisfactory build — identify gaps and implement only what is missing, without restarting from zero.

## Usage

```bash
/continuar                                          # Auto-detect the most recent BUILD_REPORT
/continuar FEATURE_NAME                             # Specific feature
/continuar .claude/sdd/reports/BUILD_REPORT_AUTH.md # Direct path to build report
```

---

## Overview

This command extends **Phase 3** of the AgentSpec workflow:

```text
Phase 0: /brainstorm → .claude/sdd/features/BRAINSTORM_{FEATURE}.md (optional)
Phase 1: /define     → .claude/sdd/features/DEFINE_{FEATURE}.md
Phase 2: /design     → .claude/sdd/features/DESIGN_{FEATURE}.md
Phase 3: /build      → Code + .claude/sdd/reports/BUILD_REPORT_{FEATURE}.md
Phase 3: /continuar  → Gap analysis + missing code (THIS COMMAND)
Phase 4: /ship       → .claude/sdd/archive/{FEATURE}/SHIPPED_{DATE}.md
```

Use `/continuar` when a `/build` was incomplete, had errors, or didn't meet expectations.

---

## When to Use

| Situation | Use `/continuar` | Use `/iterate` |
|-----------|-----------------|----------------|
| Code incomplete, feature not implemented | ✅ | ❌ |
| Bug or error in delivered implementation | ✅ | ❌ |
| Requirement changed, need to update DEFINE/DESIGN | ❌ | ✅ |
| Architecture needs redesign | ❌ | ✅ |

**Rule:** `/continuar` touches code. `/iterate` touches SDD documents.

---

## Process

### Step 1: Load Build Context

```markdown
Read(.claude/sdd/reports/BUILD_REPORT_{FEATURE}.md)  → what was built and what failed
Read(.claude/sdd/features/DEFINE_{FEATURE}.md)        → expected acceptance criteria
Read(.claude/sdd/features/DESIGN_{FEATURE}.md)        → file manifest from design
```

If no BUILD_REPORT exists, identify the feature's code files and assess current state.

### Step 2: Gap Analysis

Compare acceptance criteria from DEFINE with what was delivered in the BUILD_REPORT:

| Gap Type | Action |
|----------|--------|
| Bug or implementation error | Fix inline and re-verify |
| Missing feature that was in DESIGN | Continue build from file manifest |
| Missing feature **not** in DESIGN | Ask: use `/iterate` on DESIGN first? |
| Architecture problem (not code) | Suggest `/iterate .claude/sdd/features/DESIGN_{FEATURE}.md` |
| Changed user expectation | Recommend a new `/define` |

### Step 3: Confirm with User

Present the gap analysis before executing:

```text
Gap Analysis — {FEATURE}
════════════════════════════════════════
Implemented : [list of what was delivered]
Missing     : [list of what is missing]
Gap type    : [classification]

Proposed action: [what will be done]
Proceed? (y/n)
```

### Step 4: Execute Continuation

Follow the same pattern as the build agent:

1. Extract remaining tasks from the DESIGN file manifest
2. Implement only what is missing (do not rewrite what already works)
3. Verify with linting / type checking / tests as applicable
4. Confirm that DEFINE acceptance criteria are met

### Step 5: Update Build Report

Append a section to the existing BUILD_REPORT (do not replace it):

```markdown
---

## Continuation — {DATE}

### Gaps Identified
- [list of gaps found]

### What Was Done
- [list of what was implemented in this continuation]

### Final Status
- Acceptance criteria: [Met / Partially met]
- Modified files: [list]
```

---

## Quality Gate

```text
[ ] BUILD_REPORT loaded and gaps identified
[ ] Gap analysis presented and confirmed by user
[ ] Only missing pieces were implemented
[ ] BUILD_REPORT updated with "Continuation {DATE}" section
[ ] DEFINE acceptance criteria met
```

---

## References

- Agent: `${CLAUDE_PLUGIN_ROOT}/agents/workflow/build-agent.md`
- Contracts: `${CLAUDE_PLUGIN_ROOT}/sdd/architecture/WORKFLOW_CONTRACTS.yaml`
- Related: `${CLAUDE_PLUGIN_ROOT}/commands/workflow/iterate.md` (for SDD document changes)
- Related: `${CLAUDE_PLUGIN_ROOT}/commands/workflow/build.md` (initial build)
