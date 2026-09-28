---
name: "source-command-workflow-design"
description: "Create architecture and technical specification (Phase 2)"
---

# source-command-workflow-design

Use this skill when the user asks to run the migrated source command `workflow-design`.

## Running in Codex

This phase is **delegated**: spawn the `design-agent` subagent as the command's Phase Routing section says. It runs on the session model with `model_reasoning_effort = "high"` from its TOML, so you do not change anything by hand.

- **Task tool / `Agent` tool / OMP `task` tool** do not exist in Codex. To delegate, spawn
  the named subagent explicitly ("Use the <agent-name> agent to ..."); Codex loads it from
  `.codex/agents/<name>.toml` or `~/.codex/agents/<name>.toml`. If it is not installed,
  say so and run the step inline.
- **`AskUserQuestion`** → ask the user in chat and wait for the answer.
- **`TodoWrite`** → keep the checklist in your plan.
- **`/model <alias>`** and **`omp --model @<role>`** lines are for Claude Code and OMP.
  In Codex the model is always the session model; only the reasoning effort changes.

## Command Template

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
/design DEFINE_AUTH.md --judge                  # advisory, phase default model (judge.py)
/design DEFINE_AUTH.md --judge=strict           # gated — FAIL blocks completion
/design DEFINE_AUTH.md --judge=openai/o3        # custom model (advisory)
/design DEFINE_AUTH.md --judge=strict:<openrouter-slug>  # gated + custom model
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

## Phase Routing (delegated)

<!-- phase-routing: mode=delegated agent=design-agent -->

This phase runs in the **`design-agent` subagent**, so it uses the model routed to the
design phase (Claude Code: `model: opus`; Codex: session model at
`model_reasoning_effort=high`; OMP: `task.agentModelOverrides` → `@slow`).
Do not do the design work in the main session.

1. **In the main session first**, run the Step 1 gate block (`rc=3; … case $rc in …`).
   Exit 1 → list the 🔴 questions, ask the user, and stop; do not delegate (the subagent
   cannot ask the user). Exit 2 → fix the rows it names and re-run. Any other code →
   Living Memory is unavailable: say so in one line and continue.
2. Get the memory brief: if this turn already carries a
   `=== Living Memory (injected by the AgentSpec hook …) ===` block, use that text as is;
   otherwise keep the `brief` output the gate block printed on exit 0. The hook injects
   the brief into the main session only, so the subagent never sees it unless you pass it.
   If Living Memory is unavailable, pass `Living Memory brief: (indisponível)`.
3. Delegate exactly once:
   - Claude Code: Task tool, `subagent_type: design-agent` (plugin name `agentspec:design-agent`).
   - Codex: there is no Task tool. Spawn the `design-agent` subagent by name
     ("Use the design-agent agent to …"); it runs on the session model with the effort
     set in `.codex/agents/design-agent.toml`.
   - OMP: `task` tool, agent `design-agent`.
4. Put in the delegation prompt: the DEFINE path, the FEATURE name, the brief from step 2
   verbatim under a `Living Memory brief:` heading (or `Living Memory brief: (vazio)`), and
   this instruction: "The brief is above — do not re-run `brief`; honor its decisions and
   pending assumptions. Fill the
   **Gerado por** metadata row with your harness, the routed role, and your model id
   (or `desconhecido`)."
5. When the subagent returns the DESIGN path, run Step 8 (`--judge`) here in the main
   session if the flag was given.
6. If the subagent is unavailable, say so, run Steps 1–7 inline as a fallback, and
   record the session model in **Gerado por**.

---

## Process

### Step 1: Load Context

```markdown
Read(.claude/sdd/features/DEFINE_{FEATURE}.md)
Read(${CLAUDE_PLUGIN_ROOT}/sdd/templates/DESIGN_TEMPLATE.md)
Read(${CLAUDE_PLUGIN_ROOT}/sdd/templates/BLACKBOARD_TEMPLATE.md)   # Living Memory: exact sections/columns
Read(CLAUDE.md)

# Explore codebase for patterns:
Glob(**/*.py) | head -20
Grep("class |def ") | sample
```

Gate and memory brief — a 🔴 open question on the blackboard **blocks** this phase.
A 🔴 closes only with the user's answer (🟢, answer in `Resolução`) or via `/iterate` — never
with your own assumption, not even in a non-interactive run: if you cannot ask, stop and report.

```bash
MI="${CLAUDE_PLUGIN_ROOT}/scripts/memory-index.py"             # plugin: path filled in at load
[ -f "$MI" ] || MI="${AGENTSPEC_MEMORY_INDEX:-}"                 # exported by the SessionStart hook
[ -f "$MI" ] || MI="plugin-extras/scripts/memory-index.py"     # AgentSpec source repo
rc=3; [ -f "$MI" ] && command -v python3 >/dev/null && { python3 "$MI" gate {FEATURE} --to design; rc=$?; }
case $rc in
  0) python3 "$MI" brief {FEATURE} --phase design ;;  # nothing blocks
  1) exit 1 ;;   # 🔴 blocks: list them, ask the user, stop
  2) exit 2 ;;   # unreadable rows: fix the columns it names, re-run
  *) echo "Living Memory unavailable (memory-index.py, python3 or .claude/sdd not found) — continuing without gate/brief" ;;
esac
```

### Step 1b: Agent Selection

Decide the variant for this phase and the specialists to consult by applying the rubric in
`${CLAUDE_PLUGIN_ROOT}/sdd/architecture/AGENT_SELECTION_RUBRIC.md` yourself, to the DEFINE document.

1. Read the rubric and the catalog: the agents in `${CLAUDE_PLUGIN_ROOT}/skills/agent-router/routing.json` outside
   the `workflow` and `domain` categories (the `agent-router` skill lists the same agents).
2. Answer from the content of the document. Do not decide by counting the "Domínios KB" line
   (that rule scored 0.46 variant accuracy; Codex applying this rubric scored 0.89, retrospective on 46 specs).
3. Follow the decision:
   - `single` → continue with this command as written.
   - `multiagent` → continue with the `/design-m` process, consulting exactly the specialists you chose.
4. Second opinion (opt-in): **always run** this snippet — it does nothing unless
   `JEV_SECOND_OPINION=1` is set, so you do not need to check the environment yourself:

   ```bash
   [ "${JEV_SECOND_OPINION:-}" = "1" ] && python3 "${AGENTSPEC_SCRIPTS:-${CLAUDE_PLUGIN_ROOT}/scripts}/jev_select.py" <<'JSON' || echo "JEV second opinion: not run"
   {"phase": "design", "summary": "<≤4000-char summary of the input>", "kb_domains": ["<entries of the Domínios KB line, verbatim>"], "variant_locked": null}
   JSON
   ```

   When it prints JSON, record its `variant` and `specialists` next to your decision. It never
   overrides the rubric decision.
5. Write the **Seleção de Agentes** section using the template's table (one row per field): the variant with a one-line justification, each specialist
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

### Step 6b: Author the Eval Contract

Turn every acceptance test of the DEFINE into at least one eval in the DESIGN's `## Evals` section
(marker `<!-- agentspec:evals:contract -->` + one ```` ```toml ```` block — skeleton in the template).
Deterministic first; `graded` only for subjective criteria (≤ 50%); `human` for runtime-agent or external-service ATs.

### Step 7: Save — Document + Blackboard, Validate, Freeze

Both files are written in this step; the phase ends only after both are updated
and the eval contract is frozen.

```markdown
Write(.claude/sdd/features/DESIGN_{FEATURE_NAME}.md)
```

Then append to `.claude/sdd/features/BLACKBOARD_{FEATURE}.md` (create it from
`BLACKBOARD_TEMPLATE.md` if it is still missing), with `Fase` = `design`:

- one `D-###` per inline decision — one-sentence why, rejected alternative,
  `Onde Ler` = `DESIGN_{FEATURE}.md#<decision anchor>` (never copy the body)
- close every `🟡 Delegada ao design` as 🟢 citing its `D-###`
- mark assumptions ✅ Validada / ❌ Derrubada

Copy the table headers from `BLACKBOARD_TEMPLATE.md` as they are (ID column `#`, sections
`## Log de Decisões` / `## Premissas` / `## Perguntas Abertas e Bloqueadores`) — the index reads
only those. Full rules: `WORKFLOW_CONTRACTS.yaml` → `living_memory`. Append-only (only the Status /
Resolução cells of Q and A change in place), pointer + one sentence, pt-BR content.

```bash
test -f .claude/sdd/features/BLACKBOARD_{FEATURE}.md || echo "⛔ BLACKBOARD_{FEATURE}.md missing — design is not done"
if [ -f "$MI" ]; then python3 "$MI" build; else echo "Living Memory unavailable — MEMORY_INDEX.md not rebuilt"; fi   # exit 2 → rows it cannot read: fix sections/columns to match the template · exit 3 → no .claude/sdd: skip
```

```bash
"${AGENTSPEC_PYTHON:-python3}" "${AGENTSPEC_SCRIPTS:-${CLAUDE_PLUGIN_ROOT}/scripts}/eval_runner.py" validate {FEATURE_NAME}
"${AGENTSPEC_PYTHON:-python3}" "${AGENTSPEC_SCRIPTS:-${CLAUDE_PLUGIN_ROOT}/scripts}/eval_runner.py" freeze {FEATURE_NAME}
```

Fix every `validate` error (exit 3) before freezing. `freeze` writes the **Evals Digest** metadata row.
The first `freeze` also starts `EVAL_{FEATURE_NAME}.freeze.log`. Freeze once, after `validate` passes: re-freezing a changed contract requires `--reason "<why>"` (≥ 30 chars) and is recorded as a re-freeze.

### Step 8: Optional Judge Pass (`--judge`)

Runs only if the user invoked with `--judge[=MODE]`. Cross-model second
opinion on the design, focused on architectural soundness — hallucinated
APIs, wrong invariants, unsafe defaults, missing edge cases, unjustified
decisions.

**Flag parsing (parse from the user's command args):**

| Input | Mode | Model |
|-------|------|-------|
| `--judge` | advisory | phase default (`PHASE_MODEL_DEFAULTS["design"]` in `scripts/judge.py`) |
| `--judge=strict` | gated | phase default |
| `--judge=MODEL_SLUG` | advisory | MODEL_SLUG |
| `--judge=strict:MODEL_SLUG` | gated | MODEL_SLUG |

**Execution (after the DESIGN file is written):**

```bash
MODEL=""   # empty → judge.py picks phase default
STRICT_FLAG=""
[[ "$mode" == "strict" ]] && STRICT_FLAG="--strict"

python3 "${AGENTSPEC_SCRIPTS:-${CLAUDE_PLUGIN_ROOT}/scripts}/judge.py" \
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
| **Blackboard** | `.claude/sdd/features/BLACKBOARD_{FEATURE}.md` — list the IDs this phase added |

Report the Blackboard row in your final message. If you cannot name the IDs design added,
the phase is not complete — go back to the save step.

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
[ ] Every AT has a contract eval (eval_runner.py validate exit 0)
[ ] Evals Digest frozen (eval_runner.py freeze exit 0)
[ ] No circular dependencies in architecture
[ ] Gate passed (no 🔴 on the blackboard) and one D-### per inline decision recorded
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

- Agent: `${CLAUDE_PLUGIN_ROOT}/agents/design-agent.md`
- Multi-agent variant: `/design-m` (`${CLAUDE_PLUGIN_ROOT}/commands/workflow/design-m.md`)
- Template: `${CLAUDE_PLUGIN_ROOT}/sdd/templates/DESIGN_TEMPLATE.md`
- Contracts: `${CLAUDE_PLUGIN_ROOT}/sdd/architecture/WORKFLOW_CONTRACTS.yaml`
- Next Phase: `${CLAUDE_PLUGIN_ROOT}/commands/workflow/build.md`
