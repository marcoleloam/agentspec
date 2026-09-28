---
name: "source-command-workflow-build"
description: "Execute implementation with on-the-fly task generation (Phase 3)"
---

# source-command-workflow-build

Use this skill when the user asks to run the migrated source command `workflow-build`.

## Running in Codex

This phase runs **in this session**, on the session model. Start the session with the recommended effort: `codex -c model_reasoning_effort=high` (or pick the effort with `/model` in the TUI before running the command).

- **Task tool / `Agent` tool / OMP `task` tool** do not exist in Codex. To delegate, spawn
  the named subagent explicitly ("Use the <agent-name> agent to ..."); Codex loads it from
  `.codex/agents/<name>.toml` or `~/.codex/agents/<name>.toml`. If it is not installed,
  say so and run the step inline.
- **`AskUserQuestion`** → ask the user in chat and wait for the answer.
- **`TodoWrite`** → keep the checklist in your plan.
- **`/model <alias>`** and **`omp --model @<role>`** lines are for Claude Code and OMP.
  In Codex the model is always the session model; only the reasoning effort changes.

## Command Template

# Build Command

<!-- phase-routing: mode=session role=default -->
> **Model routing:** this phase runs in the main session (it orchestrates the specialist agents).
> Recommended — Claude Code: your current `/model` · Codex: `codex -c model_reasoning_effort=high` (same session model, only the effort changes) · OMP: your default model. Record the session model in the
> **Gerado por** metadata row of the documents it writes.

> Execute implementation with on-the-fly task generation (Phase 3)

## Usage

```bash
/build <design-file> [--judge[=MODE]]
```

## Examples

```bash
/build .claude/sdd/features/DESIGN_NOTIFICATION_SYSTEM.md
/build DESIGN_USER_AUTH.md

# With cross-model judge for code correctness (opt-in, advisory for build)
/build DESIGN_AUTH.md --judge                 # advisory, phase default model (judge.py)
/build DESIGN_AUTH.md --judge=<openrouter-slug>   # e.g. a cheaper code-tuned model
/build DESIGN_AUTH.md --judge=strict          # gated on BUILD_REPORT quality
```

---

## Overview

This is **Phase 3** of the 5-phase AgentSpec workflow:

```text
Phase 0: /brainstorm → .claude/sdd/features/BRAINSTORM_{FEATURE}.md (optional)
Phase 1: /define     → .claude/sdd/features/DEFINE_{FEATURE}.md
Phase 2: /design   → .claude/sdd/features/DESIGN_{FEATURE}.md
Phase 3: /build    → Code + .claude/sdd/reports/BUILD_REPORT_{FEATURE}.md (THIS COMMAND)
Phase 3.5: /eval   → .claude/sdd/reports/EVAL_{FEATURE}.json + EVAL_REPORT_{FEATURE}.md
Phase 4: /ship     → .claude/sdd/archive/{FEATURE}/SHIPPED_{DATE}.md
```

The `/build` command executes the implementation, generating tasks on-the-fly from the file manifest.

---

## What This Command Does

1. **Parse** - Extract file manifest from DESIGN
2. **Prioritize** - Order files by dependencies
3. **Execute** - Create each file with verification
4. **Validate** - Run tests after each significant change
5. **Report** - Generate build report

---

## Process

### Step 1: Load Context

```markdown
Read(.claude/sdd/features/DESIGN_{FEATURE}.md)
Read(.claude/sdd/features/DEFINE_{FEATURE}.md)
Read(CLAUDE.md)
```

Mark this feature as active so post-build improvements stay anchored (see `/work`):

```bash
mkdir -p .claude/sdd/
cat > .claude/sdd/.active <<EOF
feature: {FEATURE}
phase: build
updated: $(date +%Y-%m-%d)
EOF
```

Gate and memory brief — a 🔴 open question on the blackboard **blocks** the build.
A 🔴 closes only with the user's answer (🟢, answer in `Resolução`) or via `/iterate` — never
with your own assumption, not even in a non-interactive run: if you cannot ask, stop and report.

```bash
MI="${CLAUDE_PLUGIN_ROOT}/scripts/memory-index.py"             # plugin: path filled in at load
[ -f "$MI" ] || MI="${AGENTSPEC_MEMORY_INDEX:-}"                 # exported by the SessionStart hook
[ -f "$MI" ] || MI="plugin-extras/scripts/memory-index.py"     # AgentSpec source repo
rc=3; [ -f "$MI" ] && command -v python3 >/dev/null && { python3 "$MI" gate {FEATURE} --to build; rc=$?; }
case $rc in
  0) python3 "$MI" brief {FEATURE} --phase build ;;  # nothing blocks
  1) exit 1 ;;   # 🔴 blocks: list them, ask the user, stop
  2) exit 2 ;;   # unreadable rows: fix the columns it names, re-run
  *) echo "Living Memory unavailable (memory-index.py, python3 or .claude/sdd not found) — continuing without gate/brief" ;;
esac
```

The blackboard usually exists already (created in Brainstorm/Define): **extend it, never
overwrite it**. Every deviation from the DESIGN is recorded as a `D-###` with `Fase` = `build`
and `Substitui` = the design decision it replaces. Run `python3 "$MI" build` at the end.

### Step 1b: Pre-Build Eval Check (blocking)

```bash
"${AGENTSPEC_PYTHON:-python3}" "${AGENTSPEC_SCRIPTS:-scripts}/eval_runner.py" pre {FEATURE}
```

- Exit `0` → proceed (record `ALREADY_PASSING` warnings in the BUILD_REPORT).
- Exit `1` (an eval cannot run) or `3` (structural contract error) → **stop before writing code** and fix the DESIGN through `/iterate`.
- Never edit the `## Evals` block or its **Evals Digest** during the build.
- `pre` persists `.claude/sdd/reports/EVAL_{FEATURE}.pre.json`; skipping it shows up as `NO_PRE_RECEIPT` in the eval report.

### Step 2: Extract Tasks from File Manifest

Convert the file manifest to a task list:

```markdown
From DESIGN file manifest:
| File | Action | Purpose |

Generate:
- [ ] Create/Modify {file1}
- [ ] Create/Modify {file2}
- [ ] ...
```

### Step 3: Order by Dependencies

Analyze imports and dependencies to determine execution order.

### Step 4: Execute Each Task

For each file:

1. **Write** - Create the file following code patterns from DESIGN
2. **Verify** - Run verification command (lint, type check, import test)
3. **Mark Complete** - Update progress

### Step 5: Run Full Validation

After all files created:

```bash
# Lint check
ruff check .

# Type check (if applicable)
mypy .

# Run tests
pytest
```

### Step 6: Generate Build Report

```markdown
Write(.claude/sdd/reports/BUILD_REPORT_{FEATURE}.md)
```

### Step 7: Optional Judge Pass (`--judge`)

Runs only if the user invoked with `--judge[=MODE]`. Cross-model second
opinion on the BUILD_REPORT (which references the actual code written),
focused on concrete bugs — logic errors, concurrency, security, SQL
correctness, IAM/RLS, data loss risks.

**Flag parsing (parse from the user's command args):**

| Input | Mode | Model |
|-------|------|-------|
| `--judge` | advisory | phase default (`PHASE_MODEL_DEFAULTS["build"]` in `scripts/judge.py`) |
| `--judge=strict` | gated | phase default |
| `--judge=MODEL_SLUG` | advisory | MODEL_SLUG |
| `--judge=strict:MODEL_SLUG` | gated | MODEL_SLUG |

**Note on model choice for /build:** a cheaper code-tuned OpenRouter model is
a fine `MODEL_SLUG` for pure-code review. Keep the phase default when the build
touches architecture or spans multiple files. Model slugs live only in
`scripts/judge.py` (`PHASE_MODEL_DEFAULTS`), never in this command.

**Execution (after BUILD_REPORT is written):**

```bash
MODEL=""   # empty → judge.py picks phase default
STRICT_FLAG=""
[[ "$mode" == "strict" ]] && STRICT_FLAG="--strict"

python3 "${AGENTSPEC_SCRIPTS:-scripts}/judge.py" \
  ".claude/sdd/reports/BUILD_REPORT_{FEATURE}.md" \
  --phase build \
  ${MODEL:+--model "$MODEL"} \
  ${STRICT_FLAG} \
  --context "BUILD_REPORT (Phase 3) — check concrete code correctness, security, SQL / IAM / RLS issues, data loss risks. FEATURE: {FEATURE}"
```

**Alternative per-file judging (for large builds):**

For builds that produce many files, consider judging the most critical
files individually instead of the whole report:

```bash
# Judge the single riskiest file (migration, IAM, critical SQL)
python3 "${AGENTSPEC_SCRIPTS:-scripts}/judge.py" \
  "migrations/2026_X_add_roles.sql" \
  --phase build \
  --context "Postgres migration adding NOT NULL column on 50M-row table"
```

**Interpreting the verdict:**

- **Advisory mode:** Show judge verdict, phase still complete, user decides
- **Gated mode:** PASS → complete + suggest `/eval`. FAIL → phase not complete,
  surface concerns, user iterates or forces with `--force`

**Budget / error handling:**

- Exit 3 (budget): surface ledger, continue as if `--judge` was not passed
- Exit 2 (config): surface setup pointer, continue
- Exit 4 (network): surface, continue advisory

---

## Output

| Artifact | Location |
|----------|----------|
| **Code** | As specified in DESIGN file manifest |
| **Build Report** | `.claude/sdd/reports/BUILD_REPORT_{FEATURE}.md` |

**Next Step:** `/eval {FEATURE}` — independent acceptance of the DEFINE's ATs. `/ship` refuses without a PASS eval receipt.

---

## Execution Loop

The build agent follows this loop for each task:

```text
┌─────────────────────────────────────────────────────┐
│                    EXECUTE TASK                      │
├─────────────────────────────────────────────────────┤
│  1. Read task from manifest                         │
│  2. Write code following DESIGN patterns            │
│  3. Run verification command                        │
│     └─ If FAIL → Fix and retry (max 3)             │
│  4. Mark task complete                              │
│  5. Move to next task                               │
└─────────────────────────────────────────────────────┘
```

---

## Quality Gate

Before marking complete, verify:

```text
[ ] All files from manifest created
[ ] All verification commands pass
[ ] Lint check passes
[ ] Tests pass (if applicable)
[ ] No TODO comments left in code
[ ] Build report generated
[ ] Deviations from DESIGN recorded as D-### with Substitui; no 🔴 left on the blackboard
```

---

## Tips

1. **Follow the DESIGN** - Don't improvise, use the code patterns
2. **Verify Incrementally** - Test after each file, not at the end
3. **Fix Forward** - If something breaks, fix it immediately
4. **Self-Contained** - Each file should be independently functional
5. **No Comments** - Code should be self-documenting

---

## Handling Issues During Build

If you encounter issues:

| Issue | Action |
|-------|--------|
| Missing requirement | Use `/iterate` to update DEFINE |
| Architecture problem | Use `/iterate` to update DESIGN |
| Simple bug | Fix immediately and continue |
| Major blocker | Stop and report in build report |

---

## References

- Agent: `.claude/agents/workflow/build-agent.md`
- Template: `.claude/sdd/templates/BUILD_REPORT_TEMPLATE.md`
- Contracts: `.claude/sdd/architecture/WORKFLOW_CONTRACTS.yaml`
- Next Phase: `.claude/commands/workflow/ship.md`
