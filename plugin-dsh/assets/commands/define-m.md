---
name: define-m
description: Multi-agent requirements capture with specialist validation (Phase 1 enhanced)
---

# Define-M Command (Multi-Agent)

> Capture requirements with specialist validation — catches missing requirements, hidden constraints, and unrealistic criteria

## Usage

```bash
/define-m <input>
```

## Examples

```bash
# From a BRAINSTORM document (recommended)
/define-m .claude/sdd/features/BRAINSTORM_SALES_DASHBOARD.md

# From raw input
/define-m "Build a real-time dashboard with Kafka + Next.js"
```

---

## Overview

This is the **multi-agent variant** of `/define` (Phase 1). Plain `/define` already picks this variant on its own when the spec needs it (agent selection rubric); call `/define-m` to force it.

```text
/define   → single-agent  → extracts requirements from input
/define-m → multi-agent   → extracts + consults 3-4 specialists for completeness
```

**When to use `/define-m` instead of `/define`:**
- Cross-domain systems (DE + frontend, streaming + ML, etc.)
- Production systems where missing requirements are expensive
- Unfamiliar domains where you don't know what you don't know

**When `/define` is enough:**
- Single-domain features
- Well-understood problems
- Prototypes and MVPs

---

## What This Command Does

1. **Extract** — Pull requirements from input (same as `/define`)
2. **Select Specialists** — the phase LLM picks up to 4 specialists with the agent selection rubric (see Specialist Selection)
3. **Draft** — Create preliminary DEFINE document
4. **Consult** — Send draft to 3-4 domain specialists in parallel
5. **Synthesize** — Merge specialist feedback: missing requirements, hidden constraints, adjusted criteria
6. **Score** — Recalculate clarity score with specialist additions

## Specialist Selection

An explicit `/define-m` locks the multiagent variant — it never falls back to `/define`.
Pick the specialists by applying the SPECIALISTS part of `.claude/sdd/architecture/AGENT_SELECTION_RUBRIC.md` to the input
(at most 4, names exactly as in the catalog). Then **always run** the second-opinion snippet — it
does nothing unless `JEV_SECOND_OPINION=1` is set:

```bash
[ "${JEV_SECOND_OPINION:-}" = "1" ] && python3 ${CLAUDE_PLUGIN_ROOT:-.}/scripts/jev_select.py <<'JSON' || echo "JEV second opinion: not run"
{"phase": "define", "summary": "<≤4000-char summary of the input>", "kb_domains": ["<entries of the Domínios KB line, verbatim>"], "variant_locked": "multiagent"}
JSON
```

Record its specialists next to yours when it prints JSON; the rubric decision stands. Write the **Seleção de Agentes** section into the
generated document using the template's table.

---

## What Specialists Add

| Contribution | Example |
|-------------|---------|
| Missing requirements | "MUST: watermark strategy for event-time processing" |
| Hidden constraints | "Middleware Next.js intercepts SSE route — exclude from matcher" |
| Unrealistic criteria | "'Zero duplicatas' requires exactly-once, not declared" |
| Quantified criteria | "LCP < 2.5s, consumer lag < 1000 offsets, DLQ rate < 0.1%" |

---

## Cost

~3x tokens compared to `/define`. The extra cost buys:
- +9 MUST requirements (tested: 5 → 14)
- +8 technical constraints
- +14 quantified success criteria
- Clarity score improvement (tested: 13/15 → 15/15)

---

## Output

| Artifact | Location |
|----------|----------|
| **DEFINE** | `.claude/sdd/features/DEFINE_{FEATURE_NAME}.md` |

The document includes a **Validacao Multi-Agente** section with specialist attribution for every added requirement, constraint, and adjusted criterion.

**Next Step:** `/design-m .claude/sdd/features/DEFINE_{FEATURE_NAME}.md`

---

## References

- Agent: `.claude/agents/workflow/define-multiagent.md`
- Single-agent variant: `.claude/commands/workflow/define.md`
- Template: `.claude/sdd/templates/DEFINE_TEMPLATE.md`
- Contracts: `.claude/sdd/architecture/WORKFLOW_CONTRACTS.yaml`
