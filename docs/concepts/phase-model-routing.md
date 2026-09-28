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
  (`codex_effort`, written to `.codex/agents/<name>.toml` by `scripts/generate-codex-plugin.py`);
- each workflow **command** → a mode: `session` (runs inline, with a `recommended_role`
  and a `codex_effort` to start the session with) or `delegated` (runs in its phase agent,
  which carries the effort).

| Phase / command | Mode | OMP role | Claude Code | Why |
|-----------------|------|----------|-------------|-----|
| `/brainstorm`, `/define`, `/define-m`, `/iterate` | session | `plan` (start the session with it) | `/model opus` | They ask you questions; a subagent cannot |
| `/design` | **delegated** → `design-agent` | `slow` | `opus` | Architecture decisions are the most expensive to get wrong |
| `/design-m` | session | `slow` | `/model opus` | Consults specialists in parallel; a subagent cannot spawn subagents |
| `/build`, `/continuar`, `/work` | session | `default` | current model | The orchestrator delegates to specialists, which keep their own `model:` |
| `/eval` | session | `default` | current model | Asks owners for attestations; independence comes from `eval_runner.py` + JEV |
| `/ship` | **delegated** → `ship-agent` (Step 0 `verify` stays in the session) | `smol` | `haiku` | Archiving and summarizing is cheap work |
| `--judge` | external (OpenRouter) | not routed | — | `scripts/judge.py` calls OpenRouter and picks its model from `PHASE_MODEL_DEFAULTS` / `--model` / `JUDGE_MODEL` |

Each workflow command carries one marker that `--check` verifies, for example
`<!-- phase-routing: mode=delegated agent=design-agent -->`.

The manifest has no `[judge]` table any more. It used to declare `omp_role = "REVIEWER"`,
but nothing read it: `judge.py` never goes through OMP, so the role could not select the
judge's model. Wiring it would mean translating an OMP role into an OpenRouter slug, which
is not a safe one-line change. `--check` now rejects unknown top-level tables.

## Per-Phase Table: Claude Code and Codex

**Automatic** means the harness switches without you doing anything. **Manual** means you
set it before running the command.

| Phase | Claude Code | Codex |
|-------|-------------|-------|
| `/brainstorm`, `/define`, `/define-m`, `/iterate` | Manual: `/model opus` | Manual: `codex -c model_reasoning_effort=high` |
| `/design` | **Automatic**: delegates to `design-agent` (`opus`) | **Automatic**: spawns the `design-agent` subagent (effort `high`, session model) |
| `/design-m` | Manual: `/model opus` | Manual: `codex -c model_reasoning_effort=high` |
| `/build`, `/continuar` | Current model; specialists keep their own `model:` | Manual: `codex -c model_reasoning_effort=high`; specialists keep their TOML effort |
| `/work` | Current model | Manual: `codex -c model_reasoning_effort=medium` |
| `/eval` | Current model | Manual: `codex -c model_reasoning_effort=medium` |
| `/ship` | **Automatic**: Step 0 in the session, Steps 1–8 in `ship-agent` (`haiku`) | **Automatic**: Step 0 in the session, then the `ship-agent` subagent (effort `low`) |

In Codex "automatic" requires the agent TOMLs to be installed (`.codex/agents/` in the
project or `~/.codex/agents/`). The plugin install does not deliver them; see
[Codex CLI](../reference/codex-cli.md).

## Using It in Codex

Codex keeps **one model per session**. The phase can change only the **reasoning effort**:

- **Session phases** run on whatever effort the session started with. Start Codex with
  the phase's effort, e.g. `codex -c model_reasoning_effort=high` before `/brainstorm`, or
  pick the effort with `/model` in the TUI. Each workflow command's header and its
  generated skill state the effort from the manifest.
- **Delegated phases** (`/design`, `/ship`) spawn the phase subagent. It inherits the
  session model and applies the `model_reasoning_effort` from its TOML. The generator never
  writes `model =`: Codex model IDs depend on the account, so pinning them would break.
- **Tool names.** Command bodies are written for Claude Code and copied verbatim into
  `.codex/skills/source-command-*/SKILL.md`. They mention the Task tool, `subagent_type`,
  the OMP `task` tool, `AskUserQuestion`, `TodoWrite` and `/model <alias>`. None of these
  exist in Codex. Each generated skill that uses them starts with a **Running in Codex**
  section that translates them: spawn the subagent by name, ask in chat, keep the
  checklist in the plan, and ignore alias and role lines. The delegation blocks in
  `/design` and `/ship` also carry an explicit Codex bullet.

The effort in the command text is checked: `--check` fails when a routed command does not
contain `model_reasoning_effort=<its effort>`.

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

**Current role mapping.** Grok is no longer supported. The expected setup maps every
role to the same OpenAI Codex model through the `openai-codex` provider and varies only the
effort suffix: `smol` → `:low`, `plan` → `:high`, `slow` → `:max`. The concrete model ID
lives only in `~/.omp/agent/config.yml`. Since the model is the same everywhere, only the
effort differs between phases, just like in Codex.

> **Re-attestation needed.** The LLM_PHASE_ROUTING acceptance tests AT-002 (`/ship` runs
> `ship-agent` on `@smol`) and AT-003 (without overrides the phase still finishes and
> **Gerado por** shows the real model) were attested on 2026-09-24 **with Grok roles only**
> (`EVAL_REPORT_LLM_PHASE_ROUTING.md`). They have not been re-run on the Codex-backed roles.
> Until the owner re-runs them and records the new `resolvedModel`, treat both as
> unverified for the current setup. Nobody has re-attested them.

Verified behavior (OMP v18.2.11, 2026-09-23; the model-resolution points were observed with Grok roles):

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

**Living Memory across delegation.** The `UserPromptSubmit` hook injects the memory brief
into the **main session**, and a subagent does not see it. So `/design` runs the 🔴 gate in
the main session (the subagent cannot ask the user) and then passes the brief verbatim in
the delegation prompt under `Living Memory brief:`. `/ship` does the same after Step 0.
The phase agents use that section and run `memory-index.py brief` only when it is missing.

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
make build                 # regenerates plugin/ and Codex (make dsh for DSH)
make check                 # fails on any drift (also in CI)
```

`--check` fails when:

- the manifest is invalid, has an unknown top-level table, or contains a concrete model ID;
- an agent or command is missing on either side;
- an agent's `model:` differs from `claude_model`, in `.claude/agents/workflow/` or in the
  generated `plugin/agents/` mirror (the mirror check is skipped when `plugin/` is absent);
- a workflow command or agent quotes a concrete model ID such as `gpt-4o` or
  `claude-opus-4`. Use a role, an alias, or `<openrouter-slug>`. If a line really must
  quote an ID, end it with `<!-- allow-model-id -->`; no current source needs this;
- a command's marker differs from its mode, or its text lacks `model_reasoning_effort=<effort>`;
- `WORKFLOW_CONTRACTS.yaml` regains a Claude-alias `model:` line;
- `plugin/agents/` has subdirectories.

## Limits

- Session phases do not switch models by themselves. No harness lets a command change
  the main session's model for more than one turn.
- Specialist agents keep their own `model:`; per-specialist roles are out of scope.
- Choosing models from benchmarks (e.g. JEV) belongs to a separate effort; this
  feature only provides the roles and the provenance data.
