---
name: design
description: Create architecture and technical specification (Phase 2)
---

# Design Command

> Create architecture and technical specification in one pass (Phase 2)

## Usage

```bash
/design <define-file> [--judge[=MODE]]
```

## Examples

```bash
/design .claude/sdd/features/DEFINE_NOTIFICATION_SYSTEM.md
/design DEFINE_USER_AUTH.md
/design .claude/sdd/features/DEFINE_SEARCH_API.md

# With cross-model judge for architectural soundness (opt-in)
/design DEFINE_AUTH.md --judge                  # advisory, default openai/gpt-4o
/design DEFINE_AUTH.md --judge=strict           # gated — FAIL blocks completion
/design DEFINE_AUTH.md --judge=openai/o3        # custom model (advisory)
/design DEFINE_AUTH.md --judge=strict:openai/gpt-4o  # gated + custom model
```

---

## Overview

This is **Phase 2** of the 5-phase AgentSpec workflow:

```text
Phase 0: /brainstorm → .claude/sdd/features/BRAINSTORM_{FEATURE}.md (optional)
Phase 1: /define     → .claude/sdd/features/DEFINE_{FEATURE}.md
Phase 2: /design     → .claude/sdd/features/DESIGN_{FEATURE}.md (THIS COMMAND)
Phase 3: /build      → Code + .claude/sdd/reports/BUILD_REPORT_{FEATURE}.md
Phase 4: /ship       → .claude/sdd/archive/{FEATURE}/SHIPPED_{DATE}.md
```

The `/design` command combines what used to be Plan + Spec + ADRs into a single document with architecture decisions inline.

---

## What This Command Does

1. **Analyze** - Understand requirements from DEFINE
2. **Architect** - Design high-level solution with diagrams
3. **Decide** - Document key decisions with rationale (inline ADRs)
4. **Specify** - Create file manifest and code patterns
5. **Plan Testing** - Define testing strategy

---

## Process

### Step 1: Load Context

```markdown
Read(.claude/sdd/features/DEFINE_{FEATURE}.md)
Read(${CLAUDE_PLUGIN_ROOT}/sdd/templates/DESIGN_TEMPLATE.md)
Read(CLAUDE.md)

# Explore codebase for patterns:
Glob(**/*.py) | head -20
Grep("class |def ") | sample
```

### Step 1b: Agent Selection

Decide the variant for this phase and the specialists to consult by applying the rubric in
`${CLAUDE_PLUGIN_ROOT}/sdd/architecture/AGENT_SELECTION_RUBRIC.md` yourself, to the DEFINE document.

1. Read the rubric and the catalog: the agents in `${CLAUDE_PLUGIN_ROOT}/skills/agent-router/routing.json` outside
   the `workflow` and `domain` categories (the `agent-router` skill lists the same agents).
2. Answer from the content of the document. Do not decide by counting the "Domínios KB" line
   (that rule scored 0.46 variant accuracy; an LLM applying this rubric scored 0.85–0.89).
3. Follow the decision:
   - `single` → continue with this command as written.
   - `multiagent` → continue with the `/design-m` process, consulting exactly the specialists you chose.
4. Optional second opinion: when `JEV_SECOND_OPINION=1` is set, also run
   `python3 ${CLAUDE_PLUGIN_ROOT:-.}/scripts/jev_select.py` (input format in
   `docs/concepts/jev-agent-selection.md`, `"phase": "design"`) and record its variant and specialists
   next to yours. It never overrides the rubric decision.
5. Write the **Seleção de Agentes** section: the variant with a one-line justification, each specialist
   with a one-line reason, `fonte: llm (rubrica)`, and the JEV second opinion when it was run.

### Step 2: Create Architecture

Design the solution:

| Component | Content |
|-----------|---------|
| **Overview** | ASCII diagram of system |
| **Components** | List of modules/services |
| **Data Flow** | How data moves through system |
| **Integration Points** | External dependencies |

### Step 3: Document Decisions (Inline ADRs)

For each significant choice:

```markdown
### Decision: {Name}

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | YYYY-MM-DD |

**Context:** Why this decision was needed

**Choice:** What we're doing

**Rationale:** Why this approach

**Alternatives Rejected:**
1. Option A - rejected because X
2. Option B - rejected because Y

**Consequences:**
- Trade-off we accept
- Benefit we gain
```

### Step 4: Create File Manifest

List all files to create/modify:

| # | File | Action | Purpose | Dependencies |
|---|------|--------|---------|--------------|
| 1 | `path/to/file.py` | Create | Main handler | None |
| 2 | `path/to/config.yaml` | Create | Configuration | None |
| 3 | `path/to/handler.py` | Create | Request handler | 1, 2 |

### Step 5: Define Code Patterns

Provide copy-paste ready code snippets for key patterns.

### Step 6: Plan Testing Strategy

| Test Type | Scope | Tools |
|-----------|-------|-------|
| Unit | Functions | pytest |
| Integration | API | pytest + requests |
| E2E | Full flow | Manual/automated |

### Step 7: Save

```markdown
Write(.claude/sdd/features/DESIGN_{FEATURE_NAME}.md)
```

### Step 8: Optional Judge Pass (`--judge`)

Runs only if the user invoked with `--judge[=MODE]`. Cross-model second
opinion on the design, focused on architectural soundness — hallucinated
APIs, wrong invariants, unsafe defaults, missing edge cases, unjustified
decisions.

**Flag parsing (parse from the user's command args):**

| Input | Mode | Model |
|-------|------|-------|
| `--judge` | advisory | phase default (openai/gpt-4o for design) |
| `--judge=strict` | gated | phase default |
| `--judge=MODEL_SLUG` | advisory | MODEL_SLUG |
| `--judge=strict:MODEL_SLUG` | gated | MODEL_SLUG |

**Execution (after the DESIGN file is written):**

```bash
MODEL=""   # empty → judge.py picks phase default
STRICT_FLAG=""
[[ "$mode" == "strict" ]] && STRICT_FLAG="--strict"

python3 ${CLAUDE_PLUGIN_ROOT:-.}/scripts/judge.py \
  ".claude/sdd/features/DESIGN_{FEATURE_NAME}.md" \
  --phase design \
  ${MODEL:+--model "$MODEL"} \
  ${STRICT_FLAG} \
  --context "DESIGN document (Phase 2) — check architectural soundness, edge cases, API correctness, and unsafe defaults. FEATURE: {FEATURE_NAME}"
```

**Interpreting the verdict:**

- **Advisory mode (`--judge` or `--judge=MODEL`):**
  - Show the judge's markdown verdict to the user below the normal phase summary
  - If FAIL: surface concerns + suggested fixes; phase is still marked complete
  - User decides whether to iterate before `/build`
- **Gated mode (`--judge=strict` or `--judge=strict:MODEL`):**
  - If PASS: phase is complete, proceed to suggest `/build`
  - If FAIL: phase is NOT marked complete. Surface concerns + suggested fixes.
    Tell the user: "DESIGN did not pass the judge. Address the concerns and
    re-run /design, or override with --judge=strict --force to treat FAIL as
    advisory."

**Budget / error handling:**

- Exit 3 (budget exhausted): surface ledger, continue as if `--judge` was not passed
- Exit 2 (config error): surface setup pointer to `docs/getting-started/judge-setup.md`, continue
- Exit 4 (network/API error): surface, continue advisory

---

## Output

| Artifact | Location |
|----------|----------|
| **DESIGN** | `.claude/sdd/features/DESIGN_{FEATURE_NAME}.md` |

**Next Step:** `/build .claude/sdd/features/DESIGN_{FEATURE_NAME}.md`

---

## Quality Gate

Before saving, verify:

```text
[ ] Architecture diagram is clear
[ ] All major decisions documented with rationale
[ ] File manifest is complete (all files listed)
[ ] Code patterns are copy-paste ready
[ ] Testing strategy covers requirements
[ ] No circular dependencies in architecture
[ ] Seleção de Agentes section written (Step 1b)
```

---

## Tips

1. **Diagram First** - ASCII art clarifies thinking
2. **Decisions Are Permanent** - Document the "why" not just "what"
3. **Self-Contained Files** - Each file should work independently
4. **Config Over Code** - Use YAML for tunables, not hardcoded values
5. **Test Early** - Design for testability from the start

---

## References

- Agent: `${CLAUDE_PLUGIN_ROOT}/agents/workflow/design-agent.md`
- Multi-agent variant: `/design-m` (`${CLAUDE_PLUGIN_ROOT}/commands/workflow/design-m.md`)
- Template: `${CLAUDE_PLUGIN_ROOT}/sdd/templates/DESIGN_TEMPLATE.md`
- Contracts: `${CLAUDE_PLUGIN_ROOT}/sdd/architecture/WORKFLOW_CONTRACTS.yaml`
- Next Phase: `${CLAUDE_PLUGIN_ROOT}/commands/workflow/build.md`
