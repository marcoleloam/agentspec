---
name: memory
description: Save valuable insights to project or global memory — recalled automatically at session start
---

# Memory Command

> Persist high-signal insights so AgentSpec remembers them across sessions, PCs, and
> projects. Memory is **recalled automatically** at the start of every session by the
> SessionStart hook — you don't have to load it manually.

## Usage

```bash
/memory                            # Save session insights to PROJECT memory
/memory "specific note to save"    # Save a specific note to PROJECT memory
/memory --global                   # Save durable insights to GLOBAL (cross-project) memory
/memory --global "note"            # Save a specific note to GLOBAL memory
```

---

## Two Tiers of Memory

| Tier | File | Scope | Syncs across PCs via | Use for |
|------|------|-------|----------------------|---------|
| **Project** | `.claude/sdd/MEMORY.md` | This repo | the project's own git | Decisions, gotchas, conventions specific to THIS project |
| **Global** | `${AGENTSPEC_MEMORY_DIR:-~/.agentspec}/MEMORY.md` | All projects | a synced folder (see below) | Preferences, reusable patterns, lessons that apply ANYWHERE |

**Rule of thumb:** if it only matters here → project. If you'd want it on every project on
every machine → `--global`.

### Sync global memory across machines

Point `AGENTSPEC_MEMORY_DIR` at a folder that already syncs between your PCs, then commit/sync it:

```bash
# Option A — git (recommended: versioned, conflict-aware)
export AGENTSPEC_MEMORY_DIR="$HOME/agentspec-memory"   # a git repo you clone on each PC

# Option B — cloud drive
export AGENTSPEC_MEMORY_DIR="$HOME/Dropbox/agentspec-memory"
```

Add the export to your shell profile (`~/.zshrc`) on each machine. Project memory needs no
setup — it travels with the project repo.

---

## What It Does

1. **Analyzes** the conversation for valuable insights
2. **Compresses** to high-signal format (decisions, patterns, gotchas)
3. **Appends** a `## {date} — {summary}` block to the chosen file (project by default, global with `--global`)
4. Next session, the SessionStart hook **injects the block's heading as a compact index entry** — the model reads the full block on demand when the topic is relevant

---

## When to Use

- ✅ Non-obvious decisions with rationale
- ✅ Patterns that worked well (reusable → consider `--global`)
- ✅ Gotchas discovered
- ✅ Architecture decisions
- ✅ Terminology / convention clarifications

**Don't save:**

- ❌ Step-by-step implementation details (obvious from code)
- ❌ Temporary debugging info
- ❌ Anything low-signal — memory is injected every session, so keep it small

---

## Output Format

Appends a dated block to the target `MEMORY.md` (project or global):

```markdown
## {YYYY-MM-DD} — {one-line summary}

### Decisions
| Decision | Rationale | Impact |
| -------- | --------- | ------ |
| {what} | {why} | {files / scope affected} |

### Patterns
- {pattern}: {where applied}

### Gotchas
- {gotcha}: {how to avoid}
```

> Append, never overwrite. Each `/memory` adds a new dated `## ` block. **Always use a
> `## {date} — {summary}` heading** — at session start the hook injects only these headings
> (a compact index), not the full content. The model reads the file for detail on demand.
> So a clear, specific heading is what makes a memory findable. Keep newest blocks on top.

---

## Process

```text
1. Determine scope:
   - "--global" flag present → ${AGENTSPEC_MEMORY_DIR:-~/.agentspec}/MEMORY.md
   - otherwise               → .claude/sdd/MEMORY.md

2. Scan conversation for: decisions, patterns, gotchas, conventions

3. Compress ruthlessly (max 5 decisions, 3 patterns, 3 gotchas)

4. Append a dated block to the target file (create file + dirs if missing).
   For global, mkdir -p the AGENTSPEC_MEMORY_DIR first.

5. Confirm what was written and to which tier.
```

---

## Best Practices

| Do | Don't |
| -- | ----- |
| Keep memory small and high-signal | Dump whole sessions |
| Use `--global` for cross-project lessons | Put project-specific paths in global |
| Put newest blocks on top | Let files grow unbounded |
| Sync global dir via git/cloud | Rely on a single PC |

---

## References

- Recall mechanism: `plugin-extras/scripts/init-workspace.sh` (`surface_memory`)
- Project memory: `.claude/sdd/MEMORY.md`
- Global memory: `${AGENTSPEC_MEMORY_DIR:-~/.agentspec}/MEMORY.md`
- Related: `/ship` appends shipped-feature lessons to project memory automatically
