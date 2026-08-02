# AgentSpec Development

> Spec-Driven Development framework for Data Engineering on Claude Code

---

## Project Context

**What is AgentSpec?** A Claude Code plugin that provides structured AI-assisted development through a 5-phase SDD workflow, with 73 agents (data engineering + frontend), 42 commands, 39 KB domains, and 10 distributed skills (14 in-repo; 4 are contributor-only).

**Current Status:** v3.3.0 — Adds blackboard coordination (Build phase), the `/work` active-feature anchor, and portable file-based memory (project + global tiers, auto-recalled at SessionStart as a compact index). Builds on v3.2.0 (Judge Layer, local-first overrides, /status, agent-router, stack detection, CI). MemPalace MCP dependency dropped in favor of the file-based memory.

---

## Repository Structure

```text
agentspec/
├── .claude/                 # Claude Code integration
│   ├── agents/              # 64 specialized agents
│   │   ├── architect/       # 8 system-level design agents
│   │   ├── cloud/           # 10 AWS, GCP, cloud services, CI/CD
│   │   ├── platform/        # 6 Microsoft Fabric specialists
│   │   ├── python/          # 6 Python dev, code quality, prompts
│   │   ├── test/            # 3 testing, data quality, contracts
│   │   ├── data-engineering/ # 15 DE implementation specialists
│   │   ├── frontend/        # 5 React, CSS, UX, a11y, architecture
│   │   ├── dev/             # 5 developer tools & productivity
│   │   └── workflow/        # 9 SDD phase agents (incl. 3 multiagent variants)
│   │
│   ├── commands/            # 31 slash commands
│   │   ├── workflow/        # SDD commands (8)
│   │   ├── data-engineering/ # DE commands (8)
│   │   ├── core/            # Utility commands (4)
│   │   ├── knowledge/       # KB commands (3)
│   │   └── review/          # Review commands (1)
│   │
│   ├── sdd/                 # SDD framework
│   │   ├── architecture/    # WORKFLOW_CONTRACTS.yaml, ARCHITECTURE.md
│   │   ├── templates/       # 5 document templates (DE-aware)
│   │   ├── features/        # Active development
│   │   ├── reports/         # Build reports
│   │   └── archive/         # Shipped features
│   │
│   └── kb/                  # Knowledge Base (28 domains)
│       ├── _templates/      # 7 KB domain templates
│       ├── _index.yaml      # Domain registry
│       ├── dbt/             # dbt patterns and concepts
│       ├── spark/           # PySpark, Spark SQL
│       ├── sql-patterns/    # SQL best practices
│       ├── airflow/         # DAG patterns
│       ├── streaming/       # Flink, Kafka, CDC
│       ├── data-modeling/   # Star schema, Data Vault, SCD
│       ├── data-quality/    # GE, Soda, observability
│       ├── lakehouse/       # Iceberg, Delta, catalogs
│       ├── cloud-platforms/ # Snowflake, Databricks, BigQuery
│       ├── ai-data-engineering/ # RAG, vector DBs, features
│       ├── modern-stack/    # DuckDB, Polars, SQLMesh
│       ├── aws/             # Lambda, S3, Glue, SAM
│       ├── gcp/             # Cloud Run, Pub/Sub, BigQuery
│       ├── microsoft-fabric/ # Lakehouse, Warehouse, Pipelines
│       ├── lakeflow/        # Databricks Lakeflow (DLT)
│       ├── medallion/       # Bronze/Silver/Gold architecture
│       ├── prompt-engineering/ # Chain-of-thought, extraction
│       ├── genai/           # Multi-agent systems, guardrails
│       ├── pydantic/        # Validation, LLM output schemas
│       ├── python/          # Python patterns and idioms
│       ├── testing/         # pytest, fixtures, CI testing
│       ├── terraform/       # IaC modules, state, workspaces
│       ├── react/           # Hooks, RSC, composition, data fetching
│       ├── nextjs/          # App Router, SSR/CSR, caching, middleware
│       ├── tailwind-css/    # Utility-first, tokens, responsive, dark mode
│       ├── accessibility/   # WCAG, aria, keyboard, screen readers
│       ├── design-systems/  # Tokens, component API, variants, theming
│       └── frontend-patterns/ # Project structure, auth, performance
│
├── docs/                    # Documentation
│   ├── getting-started/     # Installation and first pipeline
│   ├── concepts/            # SDD pillars through DE lens
│   ├── tutorials/           # dbt, star schema, Spark, streaming tutorials
│   └── reference/           # Full catalog: agents, commands, KB domains
│
├── plugin/                  # Distributable Claude Code plugin
│   ├── .claude-plugin/      # Manifest + marketplace config
│   ├── agents/              # Path-rewritten agents
│   ├── commands/            # Path-rewritten commands
│   ├── skills/              # 10 skills (8 from .claude/ + 2 plugin-only)
│   ├── hooks/               # SessionStart workspace init
│   ├── scripts/             # init-workspace.sh
│   ├── kb/                  # Path-rewritten KB domains
│   └── sdd/                 # Templates + architecture (no workspace)
│
├── plugin-extras/           # Plugin-only content (merged by build)
│   ├── skills/              # sdd-workflow, data-engineering-guide
│   ├── hooks/               # hooks.json
│   └── scripts/             # init-workspace.sh
│
├── .claude-plugin/          # Root marketplace manifest (Claude Code entrypoint)
├── build-plugin.sh          # Packaging script (.claude/ → plugin/)
├── Makefile                 # Developer entry points (make build/test/check)
├── scripts/                 # judge.py, generate-agent-router.py
├── tests/                   # pytest suite (judge + router)
├── tasks/backlog.md         # Roadmap items
├── CHANGELOG.md             # Version history
├── CONTRIBUTING.md          # Contribution guide
├── SECURITY.md              # Security policy
└── README.md                # Project overview
```

---

## Development Workflow

Use AgentSpec's own SDD workflow to develop AgentSpec:

```bash
# Explore an enhancement idea
/brainstorm "Add Judge layer for spec validation"

# Capture requirements
/define JUDGE_LAYER

# Design the architecture
/design JUDGE_LAYER

# Build it
/build JUDGE_LAYER

# Ship when complete
/ship JUDGE_LAYER
```

Data engineering example:

```bash
# Design a star schema
/schema "Star schema for e-commerce analytics"

# Scaffold a pipeline
/pipeline "Daily orders ETL from Postgres to Snowflake"

# Generate quality checks
/data-quality models/staging/stg_orders.sql
```

---

## Language Policy

**Core framework (agents, commands, contracts):** English — aligns with upstream, enables contributions.

**Generated SDD documents (BRAINSTORM, DEFINE, DESIGN, BUILD_REPORT, SHIPPED):** Portuguese-BR (pt-BR) — output documents are in pt-BR via instructions in each workflow agent.

Technical terms (MUST/SHOULD/COULD, Clarity Score, YAGNI, MoSCoW), file paths, code, and commands remain in English in all contexts.

---

## Installation (Use AgentSpec in Any Project)

```bash
claude plugin marketplace add marcoleloam/agentspec
claude plugin install agentspec
claude plugin enable agentspec
```

That's it. All agents, commands, KB domains, and skills are globally available. Updates propagate via `claude plugin update agentspec`.

### Customize per project (optional)

Use **local-first agent overrides** (v3.2.0) to customize an agent without forking:

```bash
cp $CLAUDE_PLUGIN_ROOT/agents/workflow/build-agent.md \
   .claude/agents/workflow/build-agent.md
$EDITOR .claude/agents/workflow/build-agent.md  # keep "name:" identical
```

Claude Code's native loader gives local overrides precedence over the plugin. See `docs/concepts/agent-overrides.md`.

---

## Active Development Tasks

| Task | Status | Description |
|------|--------|-------------|
| Data engineering pivot | Done | 22 KB domains, 58 agents (8 categories), 21 commands |
| Frontend ecosystem | Done | 6 KB domains, 5 agents (frontend category), stack detection |
| Sync with upstream v2.1.0 | Done | Adopted native .claude/ model, dropped plugin wrapper |
| pt-BR in output docs only | Done | 5 SDD templates + workflow agents updated |
| /continuar command | Done | Gap analysis + resume incomplete builds |
| Removed legacy installers | Done 2026-05-19 | install.sh, init-project.sh, CLAUDE.md.template removed; plugin system is sole install path |
| Plugin distribution (upstream v3.0.0) | Done | build-plugin.sh, manifests, 2 skills, SessionStart hook |
| KB Evolution (ingest-kb + lint-kb) | Shipped 2026-04-23 | kb-evolution-agent + 2 commands for KB freshness via Context7 |
| Sync upstream v3.2.0 features | Done 2026-05-19 | Judge Layer, local-first overrides, /status, agent-router, stack detection, CI |
| Blackboard coordination (Build) | Done 2026-06-21 | BLACKBOARD_{FEATURE}.md shared state; specialists coordinate via file, not orchestrator re-explaining |
| /work active-feature anchor | Done 2026-06-21 | .active pointer; routes post-build tweaks to /continuar or /iterate without re-specifying |
| File-based memory (2 tiers) | Done 2026-06-21 | Project + global MEMORY.md, recalled at SessionStart as index; dropped MemPalace MCP |
| Migrate to plugin global install | Planned | Use local-first overrides to drop per-project cp pattern |
| Add telemetry | Planned | Local usage tracking |

---

## Coding Standards

### Markdown Files

- ATX-style headers (`#`, `##`, `###`)
- Fenced code blocks with language identifiers
- Tables properly aligned

### Agent Prompts

- Specific trigger conditions
- Clear capabilities list
- Concrete examples
- Defined output format
- `kb_domains` field for DE and frontend agents

### KB Domains

- `index.md` - Domain overview
- `quick-reference.md` - Cheat sheet
- `concepts/` - 3-6 concept files
- `patterns/` - 3-6 pattern files with code examples

---

## Commands Available

### SDD Workflow (8)

| Command | Purpose |
|---------|---------|
| `/brainstorm` | Explore ideas (Phase 0) |
| `/define` | Capture requirements (Phase 1) |
| `/design` | Create architecture (Phase 2) |
| `/build` | Execute implementation (Phase 3) |
| `/continuar` | Resume incomplete build (Phase 3+) |
| `/ship` | Archive completed work (Phase 4) |
| `/iterate` | Update existing docs (Cross-phase) |
| `/create-pr` | Create pull request |

### Data Engineering (8)

| Command | Purpose |
|---------|---------|
| `/pipeline` | DAG/pipeline scaffolding |
| `/schema` | Interactive schema design |
| `/data-quality` | Quality rules generation |
| `/lakehouse` | Table format + catalog guidance |
| `/sql-review` | SQL-specific code review |
| `/ai-pipeline` | RAG/embedding scaffolding |
| `/data-contract` | Contract authoring (ODCS) |
| `/migrate` | Legacy ETL migration |

### Core & Utilities (10)

| Command | Purpose |
|---------|---------|
| `/create-kb` | Create KB domain |
| `/ingest-kb` | Update KB domain via Context7 (KB Evolution) |
| `/lint-kb` | Audit KB domain quality (KB Evolution) |
| `/review` | Code review |
| `/judge` | Cross-model second opinion via OpenRouter (Judge Layer) |
| `/status` | Comprehensive project status report (active SDD work, git, health) |
| `/meeting` | Meeting transcript analysis |
| `/memory` | Save session insights |
| `/sync-context` | Update CLAUDE.md |
| `/readme-maker` | Generate README |

---

## Key Files to Know

| File | Purpose |
|------|---------|
| `.claude/sdd/architecture/WORKFLOW_CONTRACTS.yaml` | Phase transition rules |
| `.claude/sdd/templates/*.md` | Document templates (DE-aware) |
| `.claude/kb/_templates/*.template` | KB domain templates |
| `.claude/kb/_index.yaml` | KB domain registry (28 domains) |
| `.claude/agents/README.md` | Agent routing + escalation map |
| `.claude/agents/architect/` | System-level design agents (schema, pipeline, lakehouse) |
| `.claude/agents/cloud/` | AWS, GCP, CI/CD, deployment agents |
| `.claude/agents/platform/` | Microsoft Fabric specialists |
| `.claude/agents/frontend/` | React, CSS/Tailwind, UX, a11y, architecture |
| `.claude/agents/python/` | Python dev, code quality, prompt engineering |
| `.claude/agents/test/` | Testing, data quality, data contracts |
| `.claude/agents/dev/` | Prompt crafter, codebase explorer, shell scripts, meeting analyst, KB evolution |
| `build-plugin.sh` | Packages .claude/ into plugin/ with path rewriting |
| `plugin/.claude-plugin/plugin.json` | Plugin manifest (name, version, metadata) |
| `plugin-extras/skills/` | Plugin-only skills (sdd-workflow, data-engineering-guide) |
| `plugin-extras/hooks/hooks.json` | SessionStart hook (creates SDD dirs) |

---

## Version

- **Version:** 3.4.1
- **Status:** Release — Upstream wave 1: spec-linter and spec-judge engines, the component model, and 9 authoring/GitHub skills. 73 agents, 39 KB domains, 10 distributed skills, 42 commands.
- **Upstream Base:** luanmorenommaciel/agentspec @ d577ec5 (2026-07-15)
- **Last Sync:** 2026-07-27 (wave 1 — additive only; thin-executor refactor deferred)
- **Last Updated:** 2026-07-28
