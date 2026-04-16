# AgentSpec Development

> Spec-Driven Development framework for Data Engineering on Claude Code

---

## Project Context

**What is AgentSpec?** A Claude Code plugin that provides structured AI-assisted development through a 5-phase SDD workflow, with 72 agents (data engineering + frontend), 34 commands, 39 KB domains, and 4 skills.

**Current Status:** v3.2.0 — Plugin distribution system adopted from upstream v3.0.0. Linear is the project tracker (source of truth).

---

## Repository Structure

```text
agentspec/
├── .claude/                 # Claude Code integration
│   ├── agents/              # 63 specialized agents
│   │   ├── architect/       # 8 system-level design agents
│   │   ├── cloud/           # 10 AWS, GCP, cloud services, CI/CD
│   │   ├── platform/        # 6 Microsoft Fabric specialists
│   │   ├── python/          # 6 Python dev, code quality, prompts
│   │   ├── test/            # 3 testing, data quality, contracts
│   │   ├── data-engineering/ # 15 DE implementation specialists
│   │   ├── frontend/        # 5 React, CSS, UX, a11y, architecture
│   │   ├── dev/             # 4 developer tools & productivity
│   │   └── workflow/        # 9 SDD phase agents (incl. 3 multiagent variants)
│   │
│   ├── commands/            # 29 slash commands
│   │   ├── workflow/        # SDD commands (8)
│   │   ├── data-engineering/ # DE commands (8)
│   │   ├── core/            # Utility commands (4)
│   │   ├── knowledge/       # KB commands (1)
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
│   ├── skills/              # 4 skills (2 original + 2 plugin-only)
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
├── build-plugin.sh          # Packaging script (.claude/ → plugin/)
├── install.sh               # Legacy symlink installer (Unix)
├── install-win.ps1          # Legacy symlink installer (Windows)
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

### Option A: Plugin (Recommended)

```bash
# Build the plugin
git clone https://github.com/marcoleloam/agentspec.git ~/agentspec
cd ~/agentspec && bash build-plugin.sh

# Install via plugin system
claude plugin marketplace add marcoleloam/agentspec
claude plugin install agentspec

# Or test locally
claude --plugin-dir ~/agentspec/plugin
```

### Option B: Legacy Symlinks

```bash
# Unix/macOS
bash ~/agentspec/install.sh

# Windows PowerShell
~/agentspec/install-win.ps1
```

Then copy `CLAUDE.md.template` to each new project and customize it.

---

## Active Development Tasks

| Task | Status | Description |
|------|--------|-------------|
| Data engineering pivot | Done | 22 KB domains, 58 agents (8 categories), 21 commands |
| Frontend ecosystem | Done | 6 KB domains, 5 agents (frontend category), stack detection |
| Sync with upstream v2.1.0 | Done | Adopted native .claude/ model, dropped plugin wrapper |
| pt-BR in output docs only | Done | 5 SDD templates + workflow agents updated |
| /continuar command | Done | Gap analysis + resume incomplete builds |
| Create CLAUDE.md.template | Done | Template for user projects |
| Plugin distribution (upstream v3.0.0) | Done | build-plugin.sh, manifests, 2 skills, SessionStart hook |
| Implement Judge layer | Planned | Spec validation via external LLM |
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

### Core & Utilities (6)

| Command | Purpose |
|---------|---------|
| `/create-kb` | Create KB domain |
| `/review` | Code review |
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
| `.claude/agents/dev/` | Prompt crafter, codebase explorer, shell scripts, meeting analyst |
| `build-plugin.sh` | Packages .claude/ into plugin/ with path rewriting |
| `plugin/.claude-plugin/plugin.json` | Plugin manifest (name, version, metadata) |
| `plugin-extras/skills/` | Plugin-only skills (sdd-workflow, data-engineering-guide) |
| `plugin-extras/hooks/hooks.json` | SessionStart hook (creates SDD dirs) |

---

## Version

- **Version:** 3.2.0
- **Status:** Release — Plugin distribution + frontend ecosystem, 72 agents, 39 KB domains, 4 skills
- **Upstream Base:** luanmorenommaciel/agentspec v3.0.0
- **Last Updated:** 2026-03-30
