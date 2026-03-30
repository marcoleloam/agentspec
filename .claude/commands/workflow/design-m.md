---
name: design-m
description: Multi-agent architecture design with specialist validation (Phase 2 enhanced)
---

# Design-M Command (Multi-Agent)

> Create architecture with specialist validation — catches cross-domain risks, incompatibilities, and version issues

## Usage

```bash
/design-m <define-file>
```

## Examples

```bash
# From a DEFINE document (recommended after /define-m)
/design-m .claude/sdd/features/DEFINE_SALES_DASHBOARD.md

# Works with single-agent DEFINE too
/design-m .claude/sdd/features/DEFINE_AUTH_SYSTEM.md
```

---

## Overview

This is the **multi-agent variant** of `/design` (Phase 2). Use when the DEFINE lists **3+ KB domains**.

```text
/design   → single-agent  → designs architecture from requirements
/design-m → multi-agent   → designs + consults 3-4 specialists for risk validation
```

**When to use `/design-m` instead of `/design`:**
- Cross-domain architectures (streaming + frontend, cloud + ML)
- Production systems where architectural mistakes are costly
- Technologies the team hasn't used before

**When `/design` is enough:**
- Single-domain features
- Prototypes and experiments
- Well-known architectural patterns

---

## What This Command Does

1. **Analyze** — Read DEFINE and load KB patterns (same as `/design`)
2. **Draft** — Create architecture diagram, decisions, file manifest
3. **Detect Domains** — Count KB domains; if < 3, falls back to `/design`
4. **Consult** — Send draft architecture to 3-4 domain specialists in parallel
5. **Synthesize** — Integrate specialist risks, blockers, and pattern recommendations
6. **Finalize** — Update decisions with specialist validation, complete file manifest

---

## What Specialists Add

| Contribution | Example |
|-------------|---------|
| Architecture risks | "Watermark 10s + TUMBLE 5s = 15s real latency, not 5s" (Alto) |
| Technology concerns | "PPR not recommended — adds complexity without gain here" |
| Pattern recommendations | "Apply `table.exec.state.ttl` from flink-sql-patterns.md" |
| Version incompatibilities | "Flink connector may not support KIP-848 consumer protocol" |
| Missing components | "DLQ not mentioned — verify", "Checkpointing not confirmed" |

---

## Cost

~2x tokens compared to `/design`. The extra cost buys:
- +5 Alto-severity risks (tested: missed by single-agent)
- Cross-domain insights (PPR, JSON Schema limitations, thundering herd)
- Specialist attribution on every risk and recommendation
- Pre-flight checklist validated by domain experts

---

## Output

| Artifact | Location |
|----------|----------|
| **DESIGN** | `.claude/sdd/features/DESIGN_{FEATURE_NAME}.md` |

The document includes a **Consulta Multi-Agente** section with:
- Specialist table (agent, domain, confidence, verdict)
- Risk table with severity and mitigation
- Technical constraints with impact on design
- Recommended KB patterns with application target

**Next Step:** `/build .claude/sdd/features/DESIGN_{FEATURE_NAME}.md`

---

## References

- Agent: `.claude/agents/workflow/design-multiagent.md`
- Single-agent variant: `.claude/commands/workflow/design.md`
- Template: `.claude/sdd/templates/DESIGN_TEMPLATE.md`
- Contracts: `.claude/sdd/architecture/WORKFLOW_CONTRACTS.yaml`
