---
name: design-m
description: Multi-agent architecture design with specialist validation (Phase 2 enhanced)
---

# Design-M Command (Multi-Agent)

<!-- phase-routing: mode=session role=slow -->
> **Model routing:** this phase runs in the main session (it consults specialists in parallel, and a subagent cannot spawn subagents).
> Recommended: start it with `omp --model @slow` (Claude Code: `/model opus`). Record the session model in the
> **Gerado por** metadata row of the documents it writes.

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

This is the **multi-agent variant** of `/design` (Phase 2). Plain `/design` already picks this variant on its own when the spec needs it (agent selection rubric); call `/design-m` to force it.

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
3. **Select Specialists** — the phase LLM picks up to 4 specialists with the agent selection rubric (see Specialist Selection)
4. **Consult** — Send draft architecture to 3-4 domain specialists in parallel
5. **Synthesize** — Integrate specialist risks, blockers, and pattern recommendations
6. **Finalize** — Update decisions with specialist validation, complete file manifest

## Specialist Selection

An explicit `/design-m` locks the multiagent variant — it never falls back to `/design`.
Pick the specialists by applying the SPECIALISTS part of `.claude/sdd/architecture/AGENT_SELECTION_RUBRIC.md` to the input
(at most 4, names exactly as in the catalog). Then **always run** the second-opinion snippet — it
does nothing unless `JEV_SECOND_OPINION=1` is set:

```bash
[ "${JEV_SECOND_OPINION:-}" = "1" ] && python3 "${AGENTSPEC_SCRIPTS:-scripts}/jev_select.py" <<'JSON' || echo "JEV second opinion: not run"
{"phase": "design", "summary": "<≤4000-char summary of the input>", "kb_domains": ["<entries of the Domínios KB line, verbatim>"], "variant_locked": "multiagent"}
JSON
```

Record its specialists next to yours when it prints JSON; the rubric decision stands. Write the **Seleção de Agentes** section into the
generated document using the template's table.

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

## Living Memory

Same protocol as `/design` (see its "Step 7: Save — Document + Blackboard" and the agent's
`## Phase Memory` section). On entry:

```bash
MI="${CLAUDE_PLUGIN_ROOT}/scripts/memory-index.py"             # plugin: path filled in at load
[ -f "$MI" ] || MI="${AGENTSPEC_MEMORY_INDEX:-}"                 # exported by the SessionStart hook
[ -f "$MI" ] || MI="plugin-extras/scripts/memory-index.py"     # AgentSpec source repo
python3 "$MI" gate {FEATURE} --to design || exit 1   # 1 → 🔴 blocks · 2 → fix unreadable rows, re-run
python3 "$MI" brief {FEATURE} --phase design
```

A 🔴 closes only with the user's answer (🟢, answer in `Resolução`) or via `/iterate` — never
with your own assumption, not even in a non-interactive run: if you cannot ask, stop and report.

On exit — in the same step that writes the DESIGN document, not after the summary —
record the phase entries on `BLACKBOARD_{FEATURE}.md`, created from
`Read(.claude/sdd/templates/BLACKBOARD_TEMPLATE.md)` with its headers copied as they are
(specialist-sourced entries carry the specialist as `Agente` / `Levantado por`), then:

```bash
test -f .claude/sdd/features/BLACKBOARD_{FEATURE}.md || echo "⛔ BLACKBOARD_{FEATURE}.md missing — design is not done"
python3 "$MI" build   # exit 2 → rows it cannot read: fix sections/columns to match the template
```

The final message lists the Blackboard IDs this phase added, next to the DESIGN path.

---

## References

- Agent: `.claude/agents/workflow/design-multiagent.md`
- Single-agent variant: `.claude/commands/workflow/design.md`
- Template: `.claude/sdd/templates/DESIGN_TEMPLATE.md`
- Contracts: `.claude/sdd/architecture/WORKFLOW_CONTRACTS.yaml`
