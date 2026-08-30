# AgentSpec for DeepSeek Harness (`agentspec-dsh`)

[DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness) (`dsh`)
distribution of the AgentSpec Spec-Driven Development workflow. It is a **dsh
bundle**: two Cordis plugins mounted over `dsh-base`, making AgentSpec's
commands runnable in a DeepSeek Harness profile.

## What it adds

| Surface | Mechanism | Commands |
|---|---|---|
| **Skills** (model-invoked) | `ctx.skills.registerProvider()` — serves all 49 bundled `SKILL.md` bundles | `sdd-workflow`, `source-command-*` (all 42 commands), `agent-router`, `component-model`, `kb-build`, `github-*`, … |
| **Native slash commands** | `ctx.commands.register()` — handlers `agent.inject()` the command template | `brainstorm`, `define`, `design`, `build`, `continue`, `ship`, `iterate`, `create-pr`, `work`, `define-m`, `design-m`, `status`, `memory`, `sync-context`, `readme-maker`, `meeting`, `build-slides` |
| **Content** | Bundled assets: SDD templates, `WORKFLOW_CONTRACTS.yaml`, workflow agents | read by the command handlers at runtime |

Skills are self-contained (no `CLAUDE_PLUGIN_ROOT`): the provider reads the
bundled `assets/` via `import.meta.url`. SDD output documents are still written
to the workspace under `.claude/sdd/{features,reports,archive}` exactly as in
Claude Code / Codex.

## Layout

```text
plugin-dsh/
├── package.json          # dsh.bundle.patch -> ./cordis.patch.yml
├── cordis.patch.yml      # inserts the two plugin rows
├── lib/
│   ├── skills.js         # SkillProvider over assets/skills
│   └── commands.js       # ctx.commands handlers over assets/commands
├── assets/               # generated from .claude/ by scripts/generate-dsh-bundle.py
│   ├── skills/           # 49 SKILL.md bundles (from plugin/skills)
│   ├── sdd/              # templates + WORKFLOW_CONTRACTS.yaml
│   ├── commands/         # flattened command templates
│   └── agents/workflow/  # 9 workflow agents
└── verify.mjs            # smoke test against the installed dsh services
```

`lib/` is plain ESM JavaScript (no build step) — valid for the Cordis loader
(named `name`/`inject`/`apply` exports, no default export). Chosen over
TypeScript because the harness ships as a built binary without `tsc`; the JS
imports resolve against the profile's installed `@deepseek-ai/dsh-*` packages.

## Regenerate assets

```bash
make dsh          # sync plugin-dsh/assets/ from .claude/
make dsh-verify   # smoke-test the plugins against the installed dsh services
```

`make check` also runs the dsh generator in `--check` (drift) mode.

## Install into a profile

A profile stacks bundles; this package declares itself via `dsh.bundle`.

**Quick (working) path — symlink into the profile store:**

```bash
# profile under $DSH_HOME/profiles/agentspec
mkdir -p ~/.dsh/profiles/agentspec ~/.dsh/profiles/node_modules/@agentspec
ln -sfn "$(pwd)/plugin-dsh" ~/.dsh/profiles/node_modules/@agentspec/agentspec-dsh
ln -sfn ~/.dsh/profiles/node_modules plugin-dsh/node_modules   # resolve dsh deps
# profiles/agentspec/package.json bundles: [@deepseek-ai/dsh-base, @deepseek-ai/dsh-web-app, @agentspec/agentspec-dsh]
```

**Proper (npm/pnpm) path:**

```bash
cd ~/.dsh/profiles/agentspec
dsh plugin add @agentspec/agentspec-dsh   # or a local path after publishing/bundling
```

## Run

```bash
dsh --profile agentspec --no-open --port 0
```

Then in the Web UI: type `/brainstorm <idea>` (native slash command) or just
describe the work — the model loads the matching `source-command-*` skill via
the `skill` tool.

## Verification

`node verify.mjs` exercises both plugins against the real dsh services:
49 skills registered (kebab-case, model-invocable, bodies load) and 17 native
commands registered. A full profile boot (`dsh --profile agentspec ...`) mounts
both rows with no load errors.
