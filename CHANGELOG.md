# Changelog

All notable changes to AgentSpec will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

## [3.6.0] - 2026-09-25

### Added

- **Living Memory (second brain across phases)** — the feature `BLACKBOARD_{FEATURE}.md`
  now spans Brainstorm → Ship. Every phase agent appends its trajectory (decisions with the
  rejected alternative, assumptions, questions, course changes via `Substitui`) on exit.
  New `plugin-extras/scripts/memory-index.py` (stdlib only) serves a ≤15-line `brief` on
  phase entry, a `gate` where a 🔴 open question blocks Define→Design and Design→Build, a
  `tail` of the `.active` feature at SessionStart, and a derived, gitignored
  `.claude/sdd/MEMORY_INDEX.md` spanning active features, `archive/` and `MEMORY.md`.
  Contract: `WORKFLOW_CONTRACTS.yaml` → `living_memory`. Docs: `docs/concepts/living-memory.md`.
  Plugin hooks (`scripts/memory-hook.py`) make the script calls deterministic: the brief is
  injected on phase commands, creating a `DESIGN_*.md` is blocked while a 🔴 question is open,
  and every blackboard write rebuilds the index. `gate`/`build` exit 2 on blackboard rows they
  cannot read instead of dropping them silently; the ID column may be `#` or `ID`. The
  SessionStart hook exports `AGENTSPEC_MEMORY_INDEX` via `CLAUDE_ENV_FILE`, because the Bash
  tool does not see `CLAUDE_PLUGIN_ROOT`.

### Changed

- **Build no longer overwrites the blackboard** — `build-agent` / `/build` now create
  `BLACKBOARD_{FEATURE}.md` only if missing and otherwise extend it; deviations from the
  DESIGN are recorded as decisions that supersede the design decision.
- `/ship` now also archives `BRAINSTORM_{FEATURE}.md` and rebuilds the memory index.

### Fixed

- **Plugin script paths.** Commands and agents called `eval_runner.py`, `judge.py` and
  `status-dashboard.py` as `${CLAUDE_PLUGIN_ROOT:-.}/scripts/…`. Claude Code never fills in
  that form and the Bash tool does not see `CLAUDE_PLUGIN_ROOT`, so in a user project the
  path was `./scripts/…`; agents only got there by searching for the script. Sources now call
  `"${AGENTSPEC_SCRIPTS:-scripts}/x.py"`: the SessionStart hook exports `AGENTSPEC_SCRIPTS`
  through `CLAUDE_ENV_FILE`, and `build-plugin.sh` (and the Grok generator) rewrite the
  fallback to the exact `${CLAUDE_PLUGIN_ROOT}` form, which the loader fills in. The hook
  exports nothing inside the AgentSpec source repo, so its commands run the repo's own
  scripts. Guarded by `tests/test_plugin_script_paths.py`.

## [3.5.0] - 2026-09-24

### Added

- **LLM phase routing:** `.claude/sdd/architecture/PHASE_MODEL_ROLES.toml` is the single
  source of truth for which model role serves each SDD phase — an OMP `modelRoles` name,
  a Claude Code alias, and a Codex effort per workflow agent, plus `session`/`delegated`
  mode per workflow command. No concrete model ID lives in the repo.
- `scripts/phase_routing.py` (`--check`, `--apply`, `--print-omp-overrides`), wired into
  `make check`, plus `make omp-roles` (prints `task.agentModelOverrides` for
  `~/.omp/agent/config.yml`, stdout only) and `make phase-routing-apply`.
- `/design` and `/ship` now delegate their phase to `design-agent` / `ship-agent`, so the
  routed model applies automatically (OMP via `agentModelOverrides`, Claude Code via the
  agent's `model:`). `/ship` keeps its Step 0 eval gate in the main session. Session
  phases carry a routing marker recommending the role to start with.
- **Gerado por** provenance row (harness · role · model) in the BRAINSTORM, DEFINE,
  DESIGN, BUILD_REPORT, and SHIPPED templates; workflow agents fill it.
- `docs/concepts/phase-model-routing.md`, `tests/test_phase_routing.py`.
- **Project Python environment:** `make venv` creates a gitignored `.venv/` (first Python ≥ 3.11
  found) from the new `requirements-dev.txt`; `make test`/`check`/generators use it automatically
  (`PYTHON` override available). `make install-deps` now builds the venv instead of
  `pip install --user`, which PEP 668 blocks on Homebrew Python. Adds the `make test` target the
  help already advertised. CI installs from `requirements-dev.txt`.
- **Grok Build distribution** — `plugin-grok/` is a Grok-native plugin generated from
  `.claude/`: flattened slash commands (`/brainstorm`, `/define`, `/design`, `/build`,
  `/ship`, …), 73 flattened specialist agents with Claude→Grok tool remapping, vendored
  KB + SDD templates, and a SessionStart workspace hook.
- Project-scoped dogfood trees under `.grok/{agents,commands}` so opening this repo
  with Grok loads AgentSpec without installing the plugin.
- `.grok-plugin/marketplace.json` points Grok's marketplace at `plugin-grok/` (Claude
  Code keeps using `.claude-plugin/` → `plugin/`).
- `scripts/generate-grok-plugin.py`, `make grok`, `make grok-verify`, and a `--check`
  drift gate wired into `make check` and CI.
- **Post-build evals (`/eval`, Phase 3.5):** a `## Evals` TOML contract block in the
  DESIGN — one eval per Acceptance Test at minimum, frozen by digest — closes the gap
  where `archive/KB_EVOLUTION/` shipped with all 6 ATs still marked `⏳ Runtime`. New
  `eval-agent` (no `Edit` tool) and `/eval [feature]` command reexecute the contract
  after `/build` and write a receipt (`agentspec/eval-receipt/v1`) that `/ship` requires.
- `scripts/eval_runner.py` — the deterministic CLI behind the gate:
  `validate/freeze/pre/run/attest/waive/verify/calibrate`. Runs `deterministic` evals
  in isolated bash, dispatches `graded` evals to JEV, and never turns an infrastructure
  failure (missing key, exhausted budget, network error) into a `pass`.
- `scripts/jev_client.py` — stdlib client for TypeSafe's Jev model
  (`typesafe/jev-1.13`) over OpenRouter's decisions endpoint (`/api/v1/systemone`,
  fallback `/api/alpha/decisions`), with a three-way `pass|fail|escalated`
  classification and a calibration gate (`eval_runner.py calibrate`) before Jev's
  verdict becomes authoritative.
- `.claude/sdd/templates/EVAL_REPORT_TEMPLATE.md` — the pt-BR report template rendered
  by `eval_runner.py run` from the receipt (the runner writes the report, not the agent).
- `docs/concepts/post-build-evals.md` and a new JEV section in
  `docs/getting-started/judge-setup.md`.
- `tests/test_eval_runner.py`, `tests/test_jev_client.py`, and fixtures under
  `tests/fixtures/evals/` (including a retroconversion of `KB_EVOLUTION` and
  `FRONTEND_ECOSYSTEM`'s Acceptance Tests into `## Evals` blocks) — the whole suite
  runs offline.

### Changed

- **Breaking (plugin agent names):** `build-plugin.sh` flattens `plugin/agents/` to
  `agents/*.md` because OMP only discovers flat agent files. Claude Code plugin agent
  names drop the category (`agentspec:workflow:design-agent` → `agentspec:design-agent`);
  `README.md`/`_template.md` are no longer shipped as pseudo-agents. The
  `.claude/agents/<category>/` source layout is unchanged.
- Workflow agent models follow the manifest: `brainstorm-agent`, `define-agent`, and
  `iterate-agent` → `opus`; `build-agent` → `inherit`; `ship-agent` → `haiku`.
- `WORKFLOW_CONTRACTS.yaml` no longer carries per-phase `model:` lines (they disagreed
  with the agents on 4 of 6 phases); it points to the manifest instead.
- `generate-codex-plugin.py` takes workflow-agent `model_reasoning_effort` from the
  manifest.
- `build-agent` runs `eval_runner.py pre` before the first build task: a bash error in
  a `deterministic` eval blocks the build, and an eval that already passes only warns.
  Its Acceptance Test table in the BUILD_REPORT is now a self-check, not a substitute
  for `/eval`.
- `ship-agent` requires `eval_runner.py verify` to pass before archiving, refusing with
  a specific code (`NO_RECEIPT`, `VERDICT_FAIL`, `STALE_COMMIT`, `STALE_WORKTREE`,
  `STALE_CONTRACT`, `CONTRACT_TAMPERED`, `LEGACY_NO_EVALS`, ...) when it doesn't; the
  archive now includes the eval receipt, report, attestations, and complementary evals.
- `iterate-agent` reruns `eval_runner.py validate` + `freeze` whenever an Acceptance
  Test or the `## Evals` block changes, and warns that the existing receipt is invalidated.
- `/continuar` reads `EVAL_{F}.json` and treats `fail`/`pending` evals as priority gaps.
- `build-plugin.sh` now copies `judge.py`, `eval_runner.py`, and `jev_client.py` into
  `plugin/scripts/` — fixing `/judge`, which was previously undistributed in plugin
  installs.
- Command count 42 → 43 (`/eval`); agent count 73 → 74 (`eval-agent`).

## [3.4.1] - 2026-08-02

### Fixed

- Added a native Codex plugin manifest and 39 generated `source-command-*` skills, so
  workflow commands such as `brainstorm`, `define`, `design`, `build`, `ship`, and
  `work` no longer disappear when Codex's Claude-command migration exceeds 4 KiB.
- Native command skill names match Codex's migration names. Codex therefore prefers
  the bundled skill for both short and long commands without duplicate invocation paths.
- Commands with incomplete or absent Claude frontmatter are normalized from their file
  paths and receive a safe fallback description.

### Changed

- `scripts/generate-codex-plugin.py` now generates both subagent TOMLs and command skills.
- `build-plugin.sh` packages the generated skills while preserving both Claude and Codex
  manifests.
- CI checks generated Codex artifacts for drift.

## [3.4.0] - 2026-07-28

### Added

- **`tools/spec-linter`** — deterministic contract-validation engine (Pydantic v2, L1–L4 checks),
  returning a `PASS | WARN | FAIL` verdict. Reference prototype from upstream ADR-002.
- **`tools/spec-judge`** — behavioural counterpart: a tiered adversarial panel that asks whether an
  artifact honours its contract, sharing the Linter's `Verdict`. Needs `OPENROUTER_API_KEY`.
- **Component model** (`.claude/kb/shared/component-model.md`) — canonical definitions of what
  agents, skills, commands and KBs are each for, and where new logic belongs.
- **9 skills:** `component-model`, `create-agent`, `create-skill`, `kb-build`, `github-cr-adr`,
  `github-cr-issue`, `github-post-issue`, `meeting-analysis`, `standup-report`. Distributed skills
  go from 5 to 10; four are contributor-only and excluded from the plugin.
- `make spec-lint` / `make spec-judge`, plus a fork-local `make spec-venvs` that bootstraps the
  virtualenvs with stdlib `venv` (upstream documents `uv`).
- CI jobs for both engines, and a plugin-mirror drift check.

### Changed

- `build-plugin.sh` excludes a repo-local skill tier from the distributed plugin.
- The plugin-mirror drift check uses `git status --porcelain` rather than upstream's
  `git diff --exit-code`, which ignores untracked files and would miss a newly added component
  whose mirror was never committed.

### Notes

- Additive sync only. The upstream thin-executor refactor is deliberately **not** included: it
  rewrites the SDD phase agents, where the blackboard, `/work`, the memory tiers and the pt-BR
  output policy live. That migration deserves its own DEFINE/DESIGN pass.
- Two known gaps in the Linter, both upstream limitations rather than defects here: its
  `agent_spec` contract expects standalone YAML (our agents are Markdown with frontmatter), and its
  `sdd_phase` contract matches headings by literal slug, which never matches pt-BR SDD documents.
  The Judge parses our agents fine.

## [3.3.0] - 2026-06-21

### Added

- **Blackboard coordination (Build phase):** per-feature `BLACKBOARD_{FEATURE}.md` shared state
  so delegated specialists coordinate through one file instead of the orchestrator re-explaining
  decisions. Build-agent seeds it from DESIGN and injects a read-first/append-after pointer into
  every delegation — keeps orchestrator context lean. New `BLACKBOARD_TEMPLATE.md`.
- **`/work <FEATURE>` command:** session anchor to an active feature. Records `.claude/sdd/.active`,
  loads DESIGN + BLACKBOARD once, and routes plain improvement requests automatically (code →
  `/continuar`, docs → `/iterate`) so post-build tweaks no longer need re-specifying the feature.
- **File-based memory (cross-session, cross-PC, cross-project):** two tiers — project
  (`.claude/sdd/MEMORY.md`, syncs via the repo's git) and global
  (`${AGENTSPEC_MEMORY_DIR:-~/.agentspec}/MEMORY.md`, syncs via any synced folder). Recalled
  automatically at SessionStart as a compact **index** (block headings), with full detail read
  on demand — pointer-not-payload to keep token cost low. `/memory --global` scope; `/ship`
  consolidates lessons into project memory.

### Changed

- Command count 41 → 42 (`/work`).
- `WORKFLOW_CONTRACTS.yaml`: added `blackboard`, `active_feature`, and `Work` cross-phase sections.
- `ship-agent` archives the blackboard and clears the active-feature pointer.
- SessionStart hook (`init-workspace.sh`): new `surface_memory()` / `memory_index()` that seed and
  inject the memory index. Tunable via `AGENTSPEC_MEMORY_MAX_LINES` and `AGENTSPEC_MEMORY_SILENT`.

### Removed

- MemPalace MCP integration is no longer used; AgentSpec relies on the portable file-based memory
  above (no external server, versionable, distributed with the plugin).

## [2.1.0] - 2026-03-26

### Added

- Multi-cloud agent coverage: 58 agents across 8 categories (was 27 across 5)
- New agent categories: architect/ (8), cloud/ (10), platform/ (6), python/ (6), test/ (3), dev/ (4)
- 11 additional KB domains: aws, gcp, microsoft-fabric, lakeflow, medallion, prompt-engineering, genai, pydantic, python, testing, terraform
- Supabase, Qdrant, and Lambda specialist agents
- Spark ecosystem agents: spark-specialist, spark-streaming-architect, spark-performance-analyzer
- Lakeflow ecosystem agents: lakeflow-architect, lakeflow-expert, lakeflow-pipeline-builder
- Shell script specialist and CI/CD specialist agents

### Changed

- Reorganized 15 agent folders into 8 clean semantic categories
- Eliminated duplicate agents (fabric-architect, fabric-pipeline-developer had inferior copies)
- Dissolved legacy categories: ai-ml/, code-quality/, communication/, exploration/, database/, ci-cd/
- Complete documentation overhaul: all docs pages rewritten for v2.1 accuracy
- SDD README, _index.md, ARCHITECTURE.md, WORKFLOW_CONTRACTS.yaml bumped to v2.1.0
- All root files (README, CLAUDE.md, CONTRIBUTING, SECURITY) aligned with actual counts

### Removed

- `/dev` command (file deleted; prompt-crafter agent still available directly)
- overnight-builder agent (superseded by prompt-crafter)
- adaptive-explainer and linear-project-manager agents
- PLAN_DATA_ENGINEERING_PIVOT.md from features/ (pivot complete)
- tasks/backlog.md and empty tasks/ directory

## [2.0.0] - 2026-03-26

### Added

- Data engineering specialization across the entire framework
- 11 new KB domains: dbt, spark, sql-patterns, airflow, streaming, data-modeling, data-quality, lakehouse, cloud-platforms, ai-data-engineering, modern-stack
- 11 new data engineering agents: dbt-specialist, spark-engineer, pipeline-architect, schema-designer, sql-optimizer, streaming-engineer, lakehouse-architect, data-quality-analyst, ai-data-engineer, data-platform-engineer, data-contracts-engineer
- 8 new data engineering commands: /pipeline, /schema, /data-quality, /lakehouse, /sql-review, /ai-pipeline, /data-contract, /migrate
- Data contract support in DEFINE phase (schema, SLAs, lineage)
- Pipeline architecture section in DESIGN phase (DAG, partitions, incremental strategy)
- Data engineering quality gates in BUILD phase (dbt build, sqlfluff, GE suites)
- DE delegation map in WORKFLOW_CONTRACTS.yaml

### Changed

- SDD templates extended with data engineering sections
- Existing agents (code-reviewer, code-cleaner, test-generator, design, define, build) adapted for DE
- All documentation rewritten with data engineering examples
- README, CLAUDE.md, CONTRIBUTING rebranded for data engineering focus

## [1.1.0] - 2026-02-24

### Added

- Complete documentation overhaul: getting-started, concepts, tutorials, reference guides
- Linear as project source of truth (60 issues, 6 milestones, 9 project documents)

### Changed

- KB domains cleaned — removed project-specific domains, kept framework scaffolding
- Agent prompts sanitized — removed all project-specific references
- `concept.md.template` section renamed from "The Pattern" to "The Concept"
- `test-case.json.template` now documents valid type values
- CLAUDE.md updated with current project status and active tasks
- README, CONTRIBUTING, SECURITY, CHANGELOG rewritten for public release

### Removed

- Project-specific KB domains (agentspec, projects)
- `design/agent-spec-plan-todo-list.md` (migrated to Linear)

### Fixed

- All 60 Linear issues linked to correct milestones
- Duplicate Linear documents consolidated (4 deprecated with redirects)

## [1.0.0] - 2026-02-03

### Initial Release

- Initial release of AgentSpec
- 5-phase SDD workflow (Brainstorm, Define, Design, Build, Ship)
- 16 specialized agents
  - 6 workflow agents (brainstorm, define, design, build, ship, iterate)
  - 4 code-quality agents (reviewer, cleaner, documenter, test-generator)
  - 4 communication agents (adaptive-explainer, linear-project-manager, meeting-analyst, the-planner)
  - 2 exploration agents (codebase-explorer, kb-architect)
- 12 slash commands
- Knowledge Base (KB) framework with 7 templates
- SDD document templates (5 phases)
- Workflow contracts (YAML-based phase transitions)

### Documentation

- README with quick start guide
- CONTRIBUTING guidelines
- Code of Conduct
- Agent reference documentation
- KB framework guide
