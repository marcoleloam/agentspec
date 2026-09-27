---
name: "source-command-workflow-define-m"
description: "Multi-agent requirements capture with specialist validation (Phase 1 enhanced)"
---

# source-command-workflow-define-m

Use this skill when the user asks to run the migrated source command `workflow-define-m`.

## Command Template

# Define-M Command (Multi-Agent)

<!-- phase-routing: mode=session role=plan -->
> **Model routing:** this phase runs in the main session (it asks you questions).
> Recommended: start it with `omp --model @plan` (Claude Code: `/model opus`). Record the session model in the
> **Gerado por** metadata row of the documents it writes.

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
Pick the specialists by applying the SPECIALISTS part of `${CLAUDE_PLUGIN_ROOT}/sdd/architecture/AGENT_SELECTION_RUBRIC.md` to the input
(at most 4, names exactly as in the catalog). Then **always run** the second-opinion snippet — it
does nothing unless `JEV_SECOND_OPINION=1` is set:

```bash
[ "${JEV_SECOND_OPINION:-}" = "1" ] && python3 "${AGENTSPEC_SCRIPTS:-${CLAUDE_PLUGIN_ROOT}/scripts}/jev_select.py" <<'JSON' || echo "JEV second opinion: not run"
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

## Living Memory

Same protocol as `/define` (see its "Step 6: Save — Document + Blackboard" and the agent's
`## Phase Memory` section). On entry:

```bash
MI="${CLAUDE_PLUGIN_ROOT}/scripts/memory-index.py"             # plugin: path filled in at load
[ -f "$MI" ] || MI="${AGENTSPEC_MEMORY_INDEX:-}"                 # exported by the SessionStart hook
[ -f "$MI" ] || MI="plugin-extras/scripts/memory-index.py"     # AgentSpec source repo
python3 "$MI" brief {FEATURE} --phase define
```

On exit — in the same step that writes the DEFINE document, not after the summary —
record the phase entries on `BLACKBOARD_{FEATURE}.md`, created from
`Read(${CLAUDE_PLUGIN_ROOT}/sdd/templates/BLACKBOARD_TEMPLATE.md)` with its headers copied as they are
(specialist-sourced entries carry the specialist as `Agente` / `Levantado por`), then:

```bash
test -f .claude/sdd/features/BLACKBOARD_{FEATURE}.md || echo "⛔ BLACKBOARD_{FEATURE}.md missing — define is not done"
python3 "$MI" build   # exit 2 → rows it cannot read: fix sections/columns to match the template
```

The final message lists the Blackboard IDs this phase added, next to the DEFINE path.

---

## References

- Agent: `${CLAUDE_PLUGIN_ROOT}/agents/define-multiagent.md`
- Single-agent variant: `${CLAUDE_PLUGIN_ROOT}/commands/workflow/define.md`
- Template: `${CLAUDE_PLUGIN_ROOT}/sdd/templates/DEFINE_TEMPLATE.md`
- Contracts: `${CLAUDE_PLUGIN_ROOT}/sdd/architecture/WORKFLOW_CONTRACTS.yaml`
