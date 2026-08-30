# AgentSpec for Grok Build

Grok Build TUI distribution of the AgentSpec Spec-Driven Development workflow.
Generated from `.claude/` (single source of truth) by
`scripts/generate-grok-plugin.py`.

## What it adds

| Surface | Mechanism |
|---|---|
| **Slash commands** | Flat `commands/*.md` — `/brainstorm`, `/define`, `/design`, `/build`, `/ship`, … |
| **Skills** | `sdd-workflow`, `agent-router`, `data-engineering-guide`, authoring and GitHub skills |
| **Agents** | 73 flattened specialist agents, invoked with `spawn_subagent` |
| **KB + SDD** | Vendored `kb/` and `sdd/{templates,architecture}` under `${GROK_PLUGIN_ROOT}` |
| **SessionStart** | `hooks/hooks.json` runs `scripts/init-workspace.sh` (creates `.claude/sdd/` dirs) |

SDD output documents stay workspace-relative under
`.claude/sdd/{features,reports,archive}` and are written in pt-BR — identical to
the Claude Code, Codex, and DeepSeek Harness distributions.

## Install

From this repository (local marketplace):

```bash
make grok
grok plugin marketplace add .
grok plugin install agentspec --trust
grok plugin enable agentspec
```

From GitHub, after this repo is the marketplace source:

```bash
grok plugin marketplace add marcoleloam/agentspec
grok plugin install agentspec --trust
```

Or point Grok at the plugin directory directly:

```bash
grok plugin install ./plugin-grok --trust
```

## Use

```text
/brainstorm "daily orders ETL from Postgres to Snowflake"
/define ORDERS_PIPELINE
/design ORDERS_PIPELINE
/build ORDERS_PIPELINE
/ship ORDERS_PIPELINE
```

Delegate specialists explicitly:

> Use the dbt-specialist agent to build the staging model.
> Spawn two agents in parallel: schema-designer and data-quality-analyst.

## Name collisions

Grok keeps the built-in when a skill or command reuses a built-in name. AgentSpec
still remains invocable under the plugin prefix:

| AgentSpec command | Bare name owner | Type this instead |
|---|---|---|
| `/memory` | Grok built-in | `/agentspec:memory` |
| `/status` | Grok `/session-info` alias | `/agentspec:status` |
| `/review` | Grok bundled skill | `/agentspec:review` |

`/brainstorm`, `/define`, `/design`, `/build`, `/ship`, `/work`, `/iterate`
are unique and keep the bare name.

## Regeneration

```bash
make grok          # rewrite plugin-grok/ generated dirs + .grok/{agents,commands}
make grok-verify   # grok plugin validate plugin-grok (requires grok CLI)
make check         # includes generate-grok-plugin.py --check
```

Edit agents and commands under `.claude/`. Do not hand-edit `plugin-grok/agents`,
`plugin-grok/commands`, or `.grok/agents`.

`plugin.json` and this README are static and survive regeneration.
