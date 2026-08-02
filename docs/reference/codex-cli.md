# AgentSpec on OpenAI Codex CLI

AgentSpec's source of truth is `.claude/`. That tree feeds two targets:

```text
.claude/  ──┬─ build-plugin.sh                     ─→ plugin/   (Claude + Codex)
            └─ scripts/generate-codex-plugin.py    ─→ .codex/agents/
                                                      .codex/skills/
                                                      AGENTS.md
```

Codex CLI reached subagent GA in March 2026, so the 73 specialist agents port over
directly — they are not flattened or dropped. This repo runs its own generated agents:
open it with Codex and they are already loaded.

Regenerate after editing an agent or command under `.claude/`:

```bash
make codex
```

`make check` runs the generator in `--check` mode and fails on drift.

## Mapping

| Claude Code | Codex CLI |
|---|---|
| `.claude/agents/**/*.md` (YAML frontmatter + markdown body) | `.codex/agents/*.toml` (`name`, `description`, `developer_instructions`) |
| `.claude/commands/**/*.md` | `.codex/skills/source-command-*/SKILL.md` |
| `model: opus` / `sonnet` | `model_reasoning_effort = "high"` / `"medium"` |
| `tools: [...]` includes Write/Edit | `sandbox_mode = "workspace-write"`, else `"read-only"` |
| `kb_domains: [...]` | appended as a Knowledge Base note in `developer_instructions` |
| `CLAUDE.md` | `AGENTS.md` |

`model` is deliberately **not** emitted: Codex model ids (`gpt-5.x`) drift and are
account-dependent, so agents inherit the session model — the documented default.

## Editing the outputs

`.codex/agents/*.toml` and `.codex/skills/*/SKILL.md` are fully generated — both
directories are wiped and rewritten on every run. Edit the source under
`.claude/agents/` or `.claude/commands/` instead.

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

The recommended path installs the complete plugin, including native command skills:

```bash
codex plugin marketplace add https://github.com/marcoleloam/agentspec.git
codex plugin add agentspec@agentspec
```

The workflow commands are invoked as namespaced skills in Codex, for example:

```text
$agentspec:source-command-workflow-brainstorm
$agentspec:source-command-workflow-define
$agentspec:source-command-workflow-design
$agentspec:source-command-workflow-build
$agentspec:source-command-workflow-ship
```

For project-scoped agents without installing the plugin:

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

## Why native command skills are included

Codex CLI 0.146.0 can install the Claude plugin format, but it converts commands to
skills during installation and skips generated skills larger than 4 KiB. Several
AgentSpec workflow commands exceed that limit, including `brainstorm`, `define`,
`design`, `build`, `ship`, and `work`.

The package therefore includes `.codex-plugin/plugin.json` and native
`source-command-*` skills generated from every command. Codex prefers a native skill
when its name collides with an automatically migrated command, making all commands
available regardless of size.

The plugin installation still does **not** deliver the TOML agents: Codex resolves them
only from
TOML under `.codex/agents/` or `~/.codex/agents/`, so the markdown agents in the plugin
are invisible to it. That gap is what this generator fills — commands and skills come
from the plugin, agents come from the TOMLs.

## Not yet ported

- **Plugin-distributed subagents.** The Codex-native manifest distributes skills, but
  custom subagents still require `.codex/agents/*.toml` in the project or Codex home.
- **KB domains.** `.claude/kb/` is referenced by name inside `developer_instructions`
  but is not copied by the generator; agents reach it through the installed plugin, or
  assume it is present in the consuming project.

## Known caveat

With the full plugin plus 73 agents installed, Codex reports
`Skill descriptions were shortened to fit the 2% skills context budget`. Every skill is
still visible, but descriptions are truncated. Disable unused plugins if routing quality
degrades.
