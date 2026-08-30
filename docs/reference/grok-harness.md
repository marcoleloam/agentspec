# AgentSpec on Grok Build

> Port of AgentSpec to [Grok Build](https://docs.x.ai/build/overview), xAI's
> coding harness (TUI + ACP). Skills, slash commands, and plugin agents are
> first-class.

This is the fourth distribution of AgentSpec. It mirrors the Claude Code, OpenAI
Codex, and DeepSeek Harness distributions but ships a **Grok-native plugin**
under `plugin-grok/` plus project-scoped dogfood files under `.grok/`.

| Distribution | Mechanism |
|---|---|
| Claude Code | `.claude/` slash commands + agents + KB domains |
| OpenAI Codex | `.codex/` + generated `source-command-*` skills |
| DeepSeek Harness | `plugin-dsh/` bundle: `ctx.skills` provider + `ctx.commands` |
| **Grok Build** | `plugin-grok/` plugin: flat commands + flattened agents + skills |

## How it works

`.claude/` remains the single source of truth.
`scripts/generate-grok-plugin.py` produces two trees:

```text
.claude/  ── scripts/generate-grok-plugin.py ─┬─ plugin-grok/     (installable plugin)
                                              └─ .grok/agents + .grok/commands  (this repo)
```

Grok discovers plugin components from standard directories (`commands/`,
`agents/`, `skills/`, `hooks/hooks.json`). Three adaptations are required
that Claude Code does not need:

1. **Flat commands.** Grok registers slash commands from `commands/*.md`
   (filename stem = `/name`). Nested `commands/workflow/brainstorm.md` would
   not become `/brainstorm`, so the generator flattens every command.
2. **Flat agents.** Plugin agents load from `agents/*.md`. Category folders
   (`agents/data-engineering/dbt-specialist.md`) are flattened to
   `agents/dbt-specialist.md` so `spawn_subagent(subagent_type="dbt-specialist")`
   resolves.
3. **Tool names.** Command and agent bodies are rewritten from Claude tool
   names (`Read`, `Write`, `Edit`, `Bash`, `Task`, `TodoWrite`,
   `AskUserQuestion`) to Grok tools (`read_file`, `write`, `search_replace`,
   `run_terminal_command`, `spawn_subagent`, `todo_write`,
   `ask_user_question`). Frontmatter `tools:` lists are remapped the same way.
   `model: opus|sonnet` is dropped so each agent inherits the session model.

Content paths inside the plugin are rewritten to `${GROK_PLUGIN_ROOT}`
(Grok also sets the `CLAUDE_PLUGIN_ROOT` alias). Workspace SDD paths
(`.claude/sdd/{features,reports,archive}`) stay project-relative — the same
contract as the other distributions.

The project-local `.grok/{agents,commands}` copy keeps `.claude/kb/` and
`.claude/sdd/` paths, because this repository already has those trees. Opening
the AgentSpec repo with Grok therefore loads specialists and `/brainstorm`
without installing the plugin.

## What runs

**Slash commands (39):** every command under `.claude/commands/` flattened to
its filename stem — `brainstorm`, `define`, `design`, `build`, `continue`,
`ship`, `iterate`, `create-pr`, `work`, `define-m`, `design-m`, plus data
engineering, knowledge, review, visual-explainer, and core utilities.

**Skills (10 distributed):** `sdd-workflow`, `data-engineering-guide`,
`agent-router`, `component-model`, `kb-build`, `github-cr-adr`,
`github-cr-issue`, `github-post-issue`, `visual-explainer`,
`excalidraw-diagram`. Contributor-only skills (`create-agent`, `create-skill`,
`meeting-analysis`, `standup-report`) stay out of the plugin, matching
`build-plugin.sh`.

**Agents (73):** every specialist under `.claude/agents/{category}/`, flattened.
Grok fields added: `prompt_mode: full`, `agents_md: true`, `permission_mode`
(`plan` when the Claude source has no write tools, otherwise `default`).
Plugin-illegal `mcp_servers` frontmatter is stripped.

**SDD output** stays under `.claude/sdd/{features,reports,archive}` and is
written in pt-BR.

## Install

Prereqs: [Grok Build](https://docs.x.ai/build/overview) installed (`grok`).

```bash
# 1. Regenerate the plugin from .claude/
make grok

# 2a. This repository as a marketplace
grok plugin marketplace add .
grok plugin install agentspec --trust
grok plugin enable agentspec

# 2b. Direct path (no marketplace)
grok plugin install ./plugin-grok --trust

# 2c. GitHub
grok plugin marketplace add marcoleloam/agentspec
grok plugin install agentspec --trust
```

`--trust` is required for project-scoped plugins: hooks (SessionStart workspace
init) stay inactive until the plugin is trusted. Plugins under `~/.grok/plugins/`
are trusted automatically.

Confirm what loaded:

```bash
grok plugin details agentspec
grok inspect
```

## Verify

```bash
make grok-verify   # grok plugin validate plugin-grok
make check         # includes python3 scripts/generate-grok-plugin.py --check
```

## Layout

```text
plugin-grok/
├── plugin.json         # Grok plugin manifest (static)
├── README.md           # this distribution's install notes (static)
├── LICENSE
├── agents/             # 73 flattened, tool-rewritten agents
├── commands/           # 39 flattened, tool-rewritten slash commands
├── skills/             # 10 distributed skills
├── kb/                 # vendored KB domains
├── sdd/                # templates + WORKFLOW_CONTRACTS.yaml
├── hooks/hooks.json    # SessionStart -> scripts/init-workspace.sh
└── scripts/            # init-workspace.sh, status-dashboard.py, judge.py

.grok/
├── agents/             # dogfood copy (this repo)
└── commands/           # dogfood copy (this repo)

.grok-plugin/
└── marketplace.json    # Grok marketplace index -> ./plugin-grok
```

Grok also accepts `.claude-plugin/` marketplace indexes. This repo keeps the
Claude index pointing at `plugin/` and the Grok index pointing at `plugin-grok/`.

## Regeneration

`scripts/generate-grok-plugin.py` syncs generated dirs from `.claude/`.
`make grok` regenerates; `make check` runs it in `--check` (drift) mode.
AgentSpec content changes land in `.claude/` and are re-bundled with `make grok`.

`plugin-grok/plugin.json` and `plugin-grok/README.md` are not regenerated.

## Name collisions

Grok keeps the built-in when a command reuses a built-in name. The AgentSpec
command stays available under the plugin prefix:

| Command | Collision | Invoke as |
|---|---|---|
| `/memory` | Grok built-in `/memory` | `/agentspec:memory` |
| `/status` | alias of `/session-info` | `/agentspec:status` |
| `/review` | Grok bundled `review` skill | `/agentspec:review` |

## Notes and limitations

- **No live model session in CI.** Drift is checked by regenerating into a temp
  tree and diffing. `grok plugin validate plugin-grok` needs the Grok CLI.
- **KB is vendored.** Unlike the Codex generator (which only *names* KB domains)
  this plugin copies `.claude/kb/` so a Grok install is self-contained.
- **Claude compatibility is not the distribution.** Grok can scan `.claude/`
  when `compat.claude` is on, but nested commands and Claude tool names are why
  `plugin-grok/` exists. Prefer the plugin (or the generated `.grok/` trees in
  this repo) over relying on compatibility scanning.
- **Local-first overrides** still work: copy an agent from
  `${GROK_PLUGIN_ROOT}/agents/` into `.grok/agents/` (or
  `.claude/agents/{category}/`) keeping `name:` identical. Grok prefers the
  higher-priority location.
