# AgentSpec on OpenAI Codex CLI

AgentSpec's source of truth is `.claude/`. That tree feeds two targets:

```text
.claude/  ──┬─ build-plugin.sh                     ─→ plugin/   (Claude Code)
            └─ scripts/generate-codex-plugin.py    ─→ .codex/   (Codex CLI)
                                                      AGENTS.md
```

Codex CLI reached subagent GA in March 2026, so the 73 specialist agents port over
directly — they are not flattened or dropped. This repo runs its own generated agents:
open it with Codex and they are already loaded.

Regenerate after editing any agent under `.claude/agents/`:

```bash
make codex
```

`make check` runs the generator in `--check` mode and fails on drift.

## Mapping

| Claude Code | Codex CLI |
|---|---|
| `.claude/agents/**/*.md` (YAML frontmatter + markdown body) | `.codex/agents/*.toml` (`name`, `description`, `developer_instructions`) |
| `model: opus` / `sonnet` | `model_reasoning_effort = "high"` / `"medium"` |
| `tools: [...]` includes Write/Edit | `sandbox_mode = "workspace-write"`, else `"read-only"` |
| `kb_domains: [...]` | appended as a Knowledge Base note in `developer_instructions` |
| `CLAUDE.md` | `AGENTS.md` |

`model` is deliberately **not** emitted: Codex model ids (`gpt-5.x`) drift and are
account-dependent, so agents inherit the session model — the documented default.

## Editing the outputs

`.codex/agents/*.toml` is fully generated — the directory is wiped and rewritten on
every run. Edit the source agent under `.claude/agents/` instead.

`AGENTS.md` is **partially** generated. Only the region between the markers is
rewritten:

```markdown
<!-- agentspec:start -->
...generated SDD workflow + agent catalog...
<!-- agentspec:end -->
```

Anything outside the markers is preserved across `make codex` and ignored by
`--check`, so repo-specific notes can live in the same file.

## Use in another project

Project-scoped (Codex auto-loads `.codex/agents/`):

```bash
mkdir -p .codex/agents
cp path/to/agentspec/.codex/agents/*.toml .codex/agents/
cp path/to/agentspec/AGENTS.md ./AGENTS.md   # or copy just the marked block
```

Personal (available in every project):

```bash
cp path/to/agentspec/.codex/agents/*.toml ~/.codex/agents/
```

Then delegate explicitly — Codex spawns subagents only when asked:

> "Use the dbt-specialist agent to build the staging model."
> "Spawn two agents in parallel: schema-designer and data-quality-analyst."

## Why the TOMLs are needed at all

Codex CLI (verified on 0.146.0) reads the Claude plugin format directly: adding this
repo as a marketplace installs `plugin/` and gives Codex the SDD commands, skills, KB
and SessionStart hook with no translation.

```bash
codex plugin marketplace add https://github.com/marcoleloam/agentspec.git
codex plugin add agentspec@agentspec
```

What that path does **not** deliver is the agents: Codex resolves subagents only from
TOML under `.codex/agents/` or `~/.codex/agents/`, so the markdown agents in the plugin
are invisible to it. That gap is what this generator fills — commands and skills come
from the plugin, agents come from the TOMLs.

## Not yet ported

- **Codex-native plugin manifest.** Codex also has its own manifest format
  (`.codex-plugin/`). We do not emit it, because the Claude marketplace format already
  works; bundling the agent TOMLs into a single installable plugin would remove the
  manual copy step and is the obvious next step.
- **KB domains.** `.claude/kb/` is referenced by name inside `developer_instructions`
  but is not copied by the generator; agents reach it through the installed plugin, or
  assume it is present in the consuming project.

## Known caveat

With the full plugin plus 73 agents installed, Codex reports
`Skill descriptions were shortened to fit the 2% skills context budget`. Every skill is
still visible, but descriptions are truncated. Disable unused plugins if routing quality
degrades.
