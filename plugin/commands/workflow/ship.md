---
name: ship
description: Archive completed feature with lessons learned (Phase 4)
---

# Ship Command

> Archive completed feature with lessons learned (Phase 4)

## Usage

```bash
/ship <define-file>
```

## Examples

```bash
/ship .claude/sdd/features/DEFINE_NOTIFICATION_SYSTEM.md
/ship DEFINE_USER_AUTH.md
```

---

## Overview

This is **Phase 4** of the 5-phase AgentSpec workflow:

```text
Phase 0: /brainstorm → .claude/sdd/features/BRAINSTORM_{FEATURE}.md (optional)
Phase 1: /define     → .claude/sdd/features/DEFINE_{FEATURE}.md
Phase 2: /design     → .claude/sdd/features/DESIGN_{FEATURE}.md
Phase 3: /build      → Code + .claude/sdd/reports/BUILD_REPORT_{FEATURE}.md
Phase 3.5: /eval     → .claude/sdd/reports/EVAL_{FEATURE}.json + EVAL_REPORT_{FEATURE}.md
Phase 4: /ship       → .claude/sdd/archive/{FEATURE}/SHIPPED_{DATE}.md (THIS COMMAND)
```

The `/ship` command archives all feature artifacts and captures lessons learned.

---

## What This Command Does

1. **Gate** - `eval_runner.py verify` must return OK (blocking — see Step 0)
2. **Verify** - Confirm all artifacts exist and build passed
3. **Archive** - Move feature documents to archive folder
4. **Document** - Create SHIPPED summary with lessons learned
5. **Clean** - Remove working files from features folder

---

## Phase Routing (delegated)

<!-- phase-routing: mode=delegated agent=ship-agent -->

Steps 1–8 run in the **`ship-agent` subagent**, so they use the model routed to the
ship phase (OMP: `task.agentModelOverrides` → `@smol`; Claude Code: `model: haiku`).

1. Run **Step 0 (Eval Gate) here in the main session first.** Stop if it does not
   return OK.
2. Then delegate Steps 1–8 exactly once — Claude Code: Task tool,
   `subagent_type: ship-agent` (plugin name `agentspec:ship-agent`); OMP: `task` tool,
   agent `ship-agent`.
3. Pass: the FEATURE name, the DEFINE path, and this instruction: "Fill the
   **Gerado por** metadata row of SHIPPED with your harness, the routed role, and your
   model id (or `desconhecido`)."
4. If the subagent is unavailable, say so, run Steps 1–8 inline as a fallback, and
   record the session model in **Gerado por**.

---

## Process

### Step 0: Eval Gate (blocking)

Run the post-build eval gate **before** reading, copying, or deleting anything:

```bash
"${AGENTSPEC_PYTHON:-python3}" "${AGENTSPEC_SCRIPTS:-${CLAUDE_PLUGIN_ROOT}/scripts}/eval_runner.py" verify {FEATURE}
```

- Exit `0` (`OK` or `OK_LEGACY_WAIVED`) → continue to Step 1.
- Exit `1` → **STOP. Do not archive.** Show the code and message to the user:

| Code | What to tell the user |
|------|-----------------------|
| `NO_RECEIPT` | Run `/eval {FEATURE}` first |
| `VERDICT_FAIL` | Evals failed or are pending: `/continuar {FEATURE}`, attest pending human evals, or record a named waiver |
| `STALE_COMMIT` / `STALE_WORKTREE` | Code changed after `/eval` — rerun `/eval {FEATURE}` |
| `STALE_CONTRACT` | The eval contract changed after `/eval` — rerun `/eval {FEATURE}` |
| `CONTRACT_TAMPERED` / `CONTRACT_NOT_FROZEN` | The `## Evals` block does not match its Evals Digest — fix it through `/iterate` |
| `LEGACY_NO_EVALS` | DESIGN predates evals — add them via `/iterate`, or record `eval_runner.py waive {FEATURE} --legacy --supervisor <name> --reason <why>` and rerun `/eval` |

- Exit `2` → environment problem (Python < 3.11, not a git repo, missing DESIGN). Surface it; do not archive.

There is no flag to bypass this gate. Waivers are recorded by a named supervisor through `eval_runner.py waive` and appear in the receipt and in SHIPPED.

### Step 1: Verify Completion

```markdown
Read(.claude/sdd/features/DEFINE_{FEATURE}.md)
Read(.claude/sdd/features/DESIGN_{FEATURE}.md)
Read(.claude/sdd/reports/BUILD_REPORT_{FEATURE}.md)
Read(.claude/sdd/reports/EVAL_{FEATURE}.json)      # verdict, waivers, legacy_waiver

# Verify build report shows success
```

### Step 2: Create Archive Folder

```bash
mkdir -p .claude/sdd/archive/{FEATURE_NAME}/
```

### Step 3: Copy Artifacts to Archive

```bash
cp .claude/sdd/features/BRAINSTORM_{FEATURE}.md .claude/sdd/archive/{FEATURE}/ 2>/dev/null || true
cp .claude/sdd/features/DEFINE_{FEATURE}.md .claude/sdd/archive/{FEATURE}/
cp .claude/sdd/features/DESIGN_{FEATURE}.md .claude/sdd/archive/{FEATURE}/
cp .claude/sdd/features/BLACKBOARD_{FEATURE}.md .claude/sdd/archive/{FEATURE}/ 2>/dev/null || true
cp .claude/sdd/reports/BUILD_REPORT_{FEATURE}.md .claude/sdd/archive/{FEATURE}/
cp .claude/sdd/reports/EVAL_{FEATURE}.json .claude/sdd/archive/{FEATURE}/
cp .claude/sdd/reports/EVAL_REPORT_{FEATURE}.md .claude/sdd/archive/{FEATURE}/ 2>/dev/null || true
cp .claude/sdd/reports/EVAL_{FEATURE}.attestations.json .claude/sdd/archive/{FEATURE}/ 2>/dev/null || true
cp .claude/sdd/features/EVALS_EXTRA_{FEATURE}.toml .claude/sdd/archive/{FEATURE}/ 2>/dev/null || true
```

### Step 4: Generate SHIPPED Document

Create summary with:

| Section | Content |
|---------|---------|
| **Summary** | What was built |
| **Timeline** | Start → Ship dates |
| **Metrics** | Lines of code, files created |
| **Lessons Learned** | What went well, what to improve |
| **Eval Gate** | Verdict, contract digest, and every waiver (supervisor + reason) from `EVAL_{FEATURE}.json` |
| **Artifacts** | List of all archived documents |

### Step 5: Update Document Statuses

Update archived documents to "Shipped" status:

```markdown
Edit: archive/{FEATURE}/DEFINE_{FEATURE}.md
  - Status: → "✅ Shipped"
  - Add revision: "Shipped and archived"

Edit: archive/{FEATURE}/DESIGN_{FEATURE}.md
  - Status: → "✅ Shipped"
  - Add revision: "Shipped and archived"
```

### Step 6: Clean Up Working Files

```bash
rm -f .claude/sdd/features/BRAINSTORM_{FEATURE}.md
rm .claude/sdd/features/DEFINE_{FEATURE}.md
rm .claude/sdd/features/DESIGN_{FEATURE}.md
rm -f .claude/sdd/features/BLACKBOARD_{FEATURE}.md
rm .claude/sdd/reports/BUILD_REPORT_{FEATURE}.md
rm -f .claude/sdd/reports/EVAL_{FEATURE}.json .claude/sdd/reports/EVAL_REPORT_{FEATURE}.md
rm -f .claude/sdd/reports/EVAL_{FEATURE}.attestations.json .claude/sdd/features/EVALS_EXTRA_{FEATURE}.toml

# Clear the active-feature pointer if it points to this feature (set by /work and /build)
if [ -f .claude/sdd/.active ] && grep -q "^feature: {FEATURE}$" .claude/sdd/.active; then
  rm .claude/sdd/.active
fi
```

### Step 7: Save SHIPPED Document

```markdown
Write(.claude/sdd/archive/{FEATURE}/SHIPPED_{DATE}.md)
```

### Step 8: Consolidate Lessons into Project Memory

Append the durable lessons from this feature to `.claude/sdd/MEMORY.md` so they survive
after the feature is archived and are recalled automatically at the start of future
sessions (via the SessionStart hook). Create the file if it does not exist; **prepend** the
new block so the newest is on top (the hook injects only the first lines).

```markdown
Edit/Write(.claude/sdd/MEMORY.md) — add at the top, below the title:

## {DATE} — Shipped {FEATURE}

### Decisions
| Decision | Rationale |
| -------- | --------- |
| {key decision from DESIGN/lessons} | {why} |

### Gotchas
- {gotcha discovered during build}: {how to avoid}

### Reusable
- {pattern worth reusing} — if broadly applicable, also run `/memory --global`
```

Keep it to the highest-signal 3-5 items. If a lesson applies to ANY project (not just this
one), also surface it with `/memory --global`.

### Step 9: Rebuild the Memory Index (Living Memory)

Before archiving, `python3 "$MI" brief {FEATURE} --phase ship` shows any
`⚠ sem registro nas fases` gap — mention it under Lessons Learned (Process). After the
archive and MEMORY.md are written, rebuild the cross-feature index so the next feature's
`/define` sees these decisions and lessons:

```bash
MI="${CLAUDE_PLUGIN_ROOT}/scripts/memory-index.py"             # plugin: path filled in at load
[ -f "$MI" ] || MI="${AGENTSPEC_MEMORY_INDEX:-}"                 # exported by the SessionStart hook
[ -f "$MI" ] || MI="plugin-extras/scripts/memory-index.py"     # AgentSpec source repo
python3 "$MI" build
```

---

## Output

| Artifact | Location |
|----------|----------|
| **SHIPPED** | `.claude/sdd/archive/{FEATURE}/SHIPPED_{DATE}.md` |
| **DEFINE** | `.claude/sdd/archive/{FEATURE}/DEFINE_{FEATURE}.md` |
| **DESIGN** | `.claude/sdd/archive/{FEATURE}/DESIGN_{FEATURE}.md` |
| **BUILD_REPORT** | `.claude/sdd/archive/{FEATURE}/BUILD_REPORT_{FEATURE}.md` |

**Next Step:** Start new feature with `/define`

---

## Quality Gate

Before shipping, verify:

```text
[ ] BUILD_REPORT shows all tasks completed
[ ] No critical issues in build report
[ ] All tests passing
[ ] Code deployed (if applicable)
[ ] Lessons consolidated into .claude/sdd/MEMORY.md
[ ] Memory index rebuilt after archiving (memory-index.py build)
[ ] Active-feature pointer (.active) cleared
```

---

## When to Ship

Ship when:
- All acceptance tests from DEFINE pass
- Build report shows 100% completion
- No blocking issues remain

---

## Lessons Learned Categories

Document lessons in these areas:

| Category | Example |
|----------|---------|
| **Process** | "Breaking tasks into smaller chunks helped" |
| **Technical** | "Config files work better than env vars" |
| **Communication** | "Early clarification saved rework" |
| **Tools** | "Using X library simplified Y" |

---

## Tips

1. **Don't Skip This** - Lessons learned prevent future mistakes
2. **Be Honest** - Document what didn't work too
3. **Be Specific** - "Better planning" → "Create architecture diagram before coding"
4. **Archive Everything** - Future you will thank present you

---

## References

- Agent: `${CLAUDE_PLUGIN_ROOT}/agents/ship-agent.md`
- Template: `${CLAUDE_PLUGIN_ROOT}/sdd/templates/SHIPPED_TEMPLATE.md`
- Contracts: `${CLAUDE_PLUGIN_ROOT}/sdd/architecture/WORKFLOW_CONTRACTS.yaml`
- Previous Phase: `${CLAUDE_PLUGIN_ROOT}/commands/workflow/build.md`
