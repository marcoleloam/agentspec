# Living Memory — The Feature's Second Brain

Phase documents (DEFINE, DESIGN, BUILD_REPORT) record the **result** of each phase. Living
Memory records the **trajectory**: the questions that were answered, the alternatives that
were rejected, the assumptions that were made, and every change of course. That record is
fed back to the next phase, to future features in the same domain, and to your next session.

It uses plain files and one stdlib script. There is no MCP server, no database and no network.

## The Three Gaps It Closes

| Gap | Before | With Living Memory |
|---|---|---|
| **Between phases** | Define and Design read only the previous document; the "why" stayed in chat | Each phase appends its trajectory to the blackboard and reads a ≤15-line brief on entry |
| **Between features** | A new feature never saw what past features decided in the same domain | The brief includes decisions and lessons from features that share a KB domain |
| **Between sessions** | Resuming a feature meant re-explaining it | SessionStart shows the last 5 entries of the `.active` feature |

## Where It Lives

```text
.claude/sdd/features/BLACKBOARD_{FEATURE}.md   ← trajectory, Brainstorm → Ship (written by agents)
.claude/sdd/archive/{FEATURE}/                 ← archived blackboards, DESIGNs, SHIPPED lessons
.claude/sdd/MEMORY.md                          ← curated project lessons (/ship, /memory)
.claude/sdd/MEMORY_INDEX.md                    ← derived index for humans/grep (gitignored)
```

The blackboard is the same file the Build phase already used for coordination. It is now
created in `/brainstorm` (or in `/define` when you skip brainstorming) and extended by every
phase. The Build phase **extends** an existing blackboard. It never overwrites one.

## Entry Types

| ID | Table | Written by | Example |
|---|---|---|---|
| `D-###` | Log de Decisões | every phase | "Output in YAML — consumer already reads YAML" · rejected: JSON · `Substitui` D-002 |
| `Q-###` | Perguntas Abertas e Bloqueadores | every phase | "Who owns the source data?" 🔴 |
| `A-###` | Premissas | Define, validated by Design/Build | "Volume stays under 1k rows/day" ⏳ |
| `M-###` | Melhorias / Iterações | `/work` | "improve the error message" |

Every row carries a `Fase` column. Decisions are **never edited**. A new row replaces an old
one through `Substitui`, which is how a build-time deviation from the DESIGN stays visible.
Rows hold a pointer (`Onde Ler`) and one sentence of why. They never copy the phase document.

### Question status

| Status | Meaning |
|---|---|
| 🔴 Aberto | Nobody can answer it yet. **Blocks** Define→Design and Design→Build |
| 🟡 Delegada ao {fase} | Passed on purpose to the next phase, which must close it as 🟢 citing a `D-###` |
| 🟢 Resolvido | Closed. `Resolução` holds the answer or the decision that answers it |

## The Script

`memory-index.py` (shipped in the plugin's `scripts/`) does all of the aggregated reading.
Agents only write Markdown rows.

```bash
MI="${CLAUDE_PLUGIN_ROOT}/scripts/memory-index.py"             # plugin: path filled in at load
[ -f "$MI" ] || MI="${AGENTSPEC_MEMORY_INDEX:-}"                 # exported by the SessionStart hook
[ -f "$MI" ] || MI="plugin-extras/scripts/memory-index.py"     # AgentSpec source repo

python3 "$MI" brief ORDERS_ETL --phase design      # ≤15-line brief on phase entry
python3 "$MI" gate  ORDERS_ETL --to design         # exit 1 when a 🔴 question blocks
python3 "$MI" tail                                 # last 5 entries of the .active feature
python3 "$MI" build                                # write .claude/sdd/MEMORY_INDEX.md
```

Claude Code fills in `${CLAUDE_PLUGIN_ROOT}` only in that exact form, and only when it
loads a plugin command. The Bash tool does not export the variable, so `${CLAUDE_PLUGIN_ROOT:-.}`
would resolve to `./scripts/…` in a user project. That is why the second line exists: the
SessionStart hook writes `AGENTSPEC_MEMORY_INDEX` to `$CLAUDE_ENV_FILE`.

`gate` and `build` exit **2** when a blackboard has entry rows they cannot read (for example a
table in a section the template does not have). They say which IDs were lost, and the fix
is to use the sections and columns of `BLACKBOARD_TEMPLATE.md`. The ID column may be
headed `#` or `ID`.

### What the brief shows, in order

1. 🔴 open questions of the feature
2. 🟡 questions delegated to the phase being entered
3. ⚠ earlier phases that recorded nothing (a capture gap)
4. Current decisions, excluding superseded ones (max 6)
5. ⏳ unvalidated assumptions (max 3)
6. Decisions and lessons from other features that share a KB domain or are linked via
   `Relacionada a` (max 4)
7. A footer with the number of omitted entries, when anything was cut

A feature's KB domains come from the blackboard's `Domínios KB` field. If that is empty, they
come from the `Domínios KB` row of the DEFINE or BRAINSTORM. If that is also missing, the
script scans the DEFINE text for domain names from `.claude/kb/_index.yaml`. That fallback is
what lets features archived before Living Memory still take part.

## Hooks (Claude Code plugin)

A real end-to-end run showed that agents write the blackboard when the command tells them
to, but often skip the script calls, and one run reported a gate it never ran. So the plugin
makes those calls itself through `scripts/memory-hook.py`:

| Hook | When | What it does |
|------|------|--------------|
| `UserPromptSubmit` | the prompt is a phase command with a feature (`/design X`, `/agentspec:workflow:define …/BRAINSTORM_X.md`) | injects the `brief` as context |
| `PreToolUse` (`Write`) | a new `features/DESIGN_{F}.md` is about to be created | runs `gate --to design`; a 🔴 or unreadable rows **block** the write |
| `PostToolUse` (`Write\|Edit`) | any `BLACKBOARD_*.md` changes | rebuilds `MEMORY_INDEX.md`; unreadable rows go back to the agent |

The commands still describe the same calls, so non-Claude harnesses (Codex, Grok, dsh) and
the AgentSpec source repo keep working through the prompt alone. Editing an existing DESIGN
is not gated, because `/iterate` is how a 🔴 gets resolved. The Design→Build gate stays
prompt-driven, since Build writes no single file the hook could key on. Every hook exits 0
on any unexpected error, so a broken memory never breaks a session.

## A Feature's Life

```text
/brainstorm X  → creates BLACKBOARD_X.md: Q 🟢 answers, D chosen + rejected approaches
/define X      → brief ─► DEFINE ─► A assumptions, Q 🔴/🟡/🟢, D scope changes
/design X      → gate ─[🔴? stop]─► brief ─► DESIGN ─► D per inline decision, 🟡 → 🟢
/build X       → gate ─► extend blackboard ─► D for every deviation (Substitui)
/iterate, /work, /continuar → D with Substitui, M
/ship X        → lessons to MEMORY.md ─► archive ─► memory-index.py build
next session   → SessionStart: MEMORY.md index + last 5 entries of .active
next feature Y → its brief includes X's decisions if they share a KB domain
```

## Boundaries

- **External knowledge** (how a library works) belongs in the KB domains and Context7. When a
  decision depends on external docs, the blackboard stores the source and date as a pointer.
- **Eval results** are recorded as a verdict plus a pointer to the eval report. Running evals
  is out of scope here.
- **Model or agent selection per phase** is out of scope. The parser reads tables by column
  name, so extra columns such as `Modelo` are tolerated.

## Compatibility

- Blackboards in the old Build-only format keep working. Rows without `Fase` are read as
  phase `build`.
- The ID column may be headed `#` (template) or `ID`. Only the `Status` / `Resolução` cells
  of Q and A entries change in place; everything else is append-only.
- A missing blackboard, missing entries or a missing `python3` never blocks a phase. Local
  agent overrides that ignore the protocol still run.
- Set `AGENTSPEC_MEMORY_SILENT=1` to disable the SessionStart injection, including the tail.
  Set `AGENTSPEC_MEMORY_TAIL=N` to change how many entries it shows.

## References

- Contract: `.claude/sdd/architecture/WORKFLOW_CONTRACTS.yaml` → `living_memory`
- Template: `.claude/sdd/templates/BLACKBOARD_TEMPLATE.md`
- Script: `plugin-extras/scripts/memory-index.py` (tests: `tests/test_memory_index.py`)
- Related: [agent-overrides.md](agent-overrides.md), `/memory`, `/work`
