# Phase Model Routing — Which Model Runs Each SDD Phase

AgentSpec phases need different models: `/design` benefits from the deepest reasoning
you have, `/ship` only archives and summarizes. Phase routing declares, once, which
**model role** serves each phase, and lets your harness resolve the role to a
concrete model. No model ID is ever pinned in this repository.

## The Problem It Solves

Typing `/design` loads the command into the **main session**, so the phase ran on
whatever model the session had. The `model:` field of `design-agent` only applied
when that agent ran as a subagent — which the workflow commands never did. On top of
that, `WORKFLOW_CONTRACTS.yaml` and the agent frontmatter disagreed on 4 of 6 phases.

## Single Source of Truth

`.claude/sdd/architecture/PHASE_MODEL_ROLES.toml` maps:

- each workflow **agent** → an OMP role (`omp_role`), a Claude Code alias
  (`claude_model`, written to the agent frontmatter), and a Codex effort
  (`codex_effort`, read by `scripts/generate-codex-plugin.py`);
- each workflow **command** → a mode: `session` (runs inline) or `delegated` (runs in
  its phase agent).

| Phase / command | Mode | OMP role | Claude Code | Why |
|-----------------|------|----------|-------------|-----|
| `/brainstorm`, `/define`, `/define-m`, `/iterate` | session | `plan` (start the session with it) | `/model opus` | They ask you questions; a subagent cannot |
| `/design` | **delegated** → `design-agent` | `slow` | `opus` | Architecture decisions are the most expensive to get wrong |
| `/design-m` | session | `slow` | `/model opus` | Consults specialists in parallel; a subagent cannot spawn subagents |
| `/build`, `/continuar`, `/work` | session | `default` | current model | The orchestrator delegates to specialists, which keep their own `model:` |
| `/eval` | session | `default` | current model | Asks owners for attestations; independence comes from `eval_runner.py` + JEV |
| `/ship` | **delegated** → `ship-agent` (Step 0 `verify` stays in the session) | `smol` | `haiku` | Archiving and summarizing is cheap work |
| `--judge` | external (OpenRouter) | `REVIEWER` (optional) | — | Keep reviews on a different model family than `plan`/`slow` |

Each workflow command carries one marker that `--check` verifies, for example
`<!-- phase-routing: mode=delegated agent=design-agent -->`.

## Using It in OMP

OMP resolves roles through `modelRoles` in `~/.omp/agent/config.yml` and lets
`task.agentModelOverrides` pin a role per agent name. The override wins over the
agent's `model:` frontmatter, so the shared plugin keeps Claude-valid aliases while
OMP gets roles.

```bash
make omp-roles        # prints the snippet; never reads or writes ~/.omp
```

Merge the printed entries **under your existing** `task.agentModelOverrides` key:

```yaml
task:
  agentModelOverrides:
    design-agent: "@slow"
    ship-agent: "@smol"
    # ...one line per workflow agent
```

Make sure `plan`, `slow`, `smol`, and `default` exist in your `modelRoles`. For
session phases, start OMP on the recommended role, e.g. `omp --model @plan` before
`/brainstorm`.

Verified behavior (OMP v18.2.11, 2026-09-23):

- OMP only discovers `agents/*.md` — not `agents/<category>/*.md`. The build therefore
  flattens `plugin/agents/` (see below).
- `task.agentModelOverrides.<agent-name>` beats the agent's `model:`; the saved session
  records `resolvedModel`.
- Claude tool names in `tools:` (`Read`, `Write`, …) map to OMP tools.
- Commands ignore `model:`, `context: fork`, and `agent:`. Delegation therefore lives
  in the command body as an instruction to use the task tool.
- OMP does **not** scan `.claude/agents/`, so local-first overrides there do not apply
  in OMP; use `.omp/agents/` or `task.agentModelOverrides` instead.

## Using It in Claude Code

`/design` and `/ship` delegate through the Task tool to `design-agent` (`opus`) and
`ship-agent` (`haiku`). For session phases, pick the model with `/model` before
running the command.

## Flattened Plugin Agents

`build-plugin.sh` ships agents as `plugin/agents/*.md` (the `.claude/agents/<category>/`
source layout is unchanged). Consequences:

- Claude Code plugin agent names lose the category: `agentspec:workflow:design-agent`
  becomes `agentspec:design-agent`. Update any reference to the qualified name.
- `README.md` and `_template.md` are no longer shipped as pseudo-agents.
- `${CLAUDE_PLUGIN_ROOT}/agents/<category>/x.md` references are rewritten to
  `${CLAUDE_PLUGIN_ROOT}/agents/x.md`.

## Provenance: "Gerado por"

Every SDD document (BRAINSTORM, DEFINE, DESIGN, BUILD_REPORT, SHIPPED) carries a
**Gerado por** metadata row: harness · routed role (or `sessão`) · model id (or
`desconhecido`). It is the data that future calibration of this table relies on.

## Changing the Routing

```bash
$EDITOR .claude/sdd/architecture/PHASE_MODEL_ROLES.toml
make phase-routing-apply   # rewrites agent `model:` lines and command markers
make build                 # regenerates plugin/, Codex, Grok, DSH
make check                 # fails on any drift (also in CI)
```

`--check` fails when: the manifest is invalid or contains a concrete model ID; an
agent or command is missing on either side; an agent's `model:` differs from
`claude_model`; a command's marker differs from its mode; `WORKFLOW_CONTRACTS.yaml`
regains a Claude-alias `model:` line; or `plugin/agents/` has subdirectories.

## Limits

- Session phases do not switch models by themselves. No harness lets a command change
  the main session's model for more than one turn.
- Specialist agents keep their own `model:`; per-specialist roles are out of scope.
- Choosing models from benchmarks (e.g. JEV) belongs to a separate effort; this
  feature only provides the roles and the provenance data.
