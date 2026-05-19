<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/banner.svg">
  <source media="(prefers-color-scheme: light)" srcset="assets/banner.svg">
  <img alt="AgentSpec — Spec-Driven Development" src="assets/banner.svg" width="100%">
</picture>

<br/>

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Compatible-purple.svg)](https://docs.anthropic.com/en/docs/claude-code)
[![Version](https://img.shields.io/badge/version-3.2.0-green.svg)](CHANGELOG.md)
[![Agents](https://img.shields.io/badge/agents-73-orange.svg)](.claude/agents/)
[![Commands](https://img.shields.io/badge/commands-41-blue.svg)](.claude/commands/)
[![KB Domains](https://img.shields.io/badge/KB%20domains-39-blue.svg)](.claude/kb/)
[![Skills](https://img.shields.io/badge/skills-5-purple.svg)](.claude/skills/)

[Quick Start](#quick-start) | [Commands](#commands) | [Documentation](docs/) | [Contributing](CONTRIBUTING.md)

</div>

---

## The Problem

AI-assisted development without structure produces inconsistent results: hallucinated solutions, spec drift between sessions, code that doesn't match what was agreed upon, and decisions that get lost. Each conversation starts from scratch without accumulated context.

## The Solution

AgentSpec brings **Spec-Driven Development (SDD)** to Claude Code — a 5-phase workflow backed by 39 knowledge base domains, 73 specialized agents, 41 slash commands, and 5 skills. Every decision is captured in formal documents. Every phase has a quality gate. Nothing gets lost.

```text
/brainstorm  →  /define  →  /design  →  /build  →  /ship
  (Explore)    (Capture)  (Architect)  (Execute)  (Archive)
                  │            │            │
            Clarity Score  File Manifest  Agent Delegation
            MoSCoW Goals   ADRs inline    TodoWrite tracking
            Data Contracts  KB-First      BUILD_REPORT
```

Generated documents (BRAINSTORM, DEFINE, DESIGN, BUILD_REPORT, SHIPPED) are produced in **Portuguese-BR (pt-BR)** automatically.

Optional cross-model validation: **Judge Layer** via OpenRouter (`--judge`) catches hallucinations Claude's self-review misses.

---

## Quick Start

### Install via Plugin (only path)

```bash
claude plugin marketplace add marcoleloam/agentspec
claude plugin install agentspec
claude plugin enable agentspec
```

That's it. All 73 agents, 41 commands, 39 KB domains, and 5 skills become available globally. Updates propagate via:

```bash
claude plugin update agentspec
```

### Customize per project (optional)

AgentSpec v3.2.0 supports **local-first agent overrides**. To customize a specific agent in your project without forking:

```bash
# 1. Copy the agent you want to override
cp $CLAUDE_PLUGIN_ROOT/agents/workflow/build-agent.md \
   .claude/agents/workflow/build-agent.md

# 2. Edit (keep the name: field identical to the plugin version)
$EDITOR .claude/agents/workflow/build-agent.md
```

Claude Code's loader picks your local copy over the plugin's. See [docs/concepts/agent-overrides.md](docs/concepts/agent-overrides.md).

---

## Workflow

### 5-Phase SDD with Quality Gates

| Phase | Command | What It Does | Quality Gate |
|-------|---------|--------------|--------------|
| **Brainstorm** | `/brainstorm` | Explore approaches, YAGNI, 1 question at a time | 3+ questions, 2+ approaches |
| **Define** | `/define` | Requirements + MoSCoW goals + data contracts | Clarity Score >= 12/15 |
| **Design** | `/design` | Architecture + ADRs + file manifest with agent assignment | Complete manifest |
| **Build** | `/build` | Execute + agent delegation + verification | All tests pass |
| **Ship** | `/ship` | Archive with lessons learned | Acceptance verified |

**Didn't finish the build?** Use `/continue` for gap analysis — implements only what's missing without restarting.

**Requirements changed mid-stream?** Use `/iterate` to update any phase document with automatic cascade detection.

**Want a second opinion?** Add `--judge` to any phase command for cross-model validation via OpenRouter.

---

## Commands

### SDD Workflow (8)

| Command | Purpose |
|---------|---------|
| `/brainstorm` | Explore ideas (Phase 0) |
| `/define` | Capture requirements (Phase 1) |
| `/design` | Create architecture (Phase 2) |
| `/build` | Execute implementation (Phase 3) |
| `/continue` | Resume incomplete build (Phase 3+) |
| `/ship` | Archive completed work (Phase 4) |
| `/iterate` | Update docs mid-stream (Cross-phase) |
| `/create-pr` | Create pull request |

### Data Engineering (8)

| Command | What It Does | Primary Agent |
|---------|-------------|---------------|
| `/pipeline` | Scaffold Airflow/Dagster DAGs | pipeline-architect |
| `/schema` | Design star schemas, Data Vault, SCD | schema-designer |
| `/data-quality` | Generate GE suites, dbt tests | data-quality-analyst |
| `/lakehouse` | Iceberg/Delta setup, catalog config | lakehouse-architect |
| `/sql-review` | SQL anti-patterns, PII detection | sql-optimizer |
| `/ai-pipeline` | RAG, embeddings, feature stores | ai-data-engineer |
| `/data-contract` | ODCS contracts, SLAs | data-contracts-engineer |
| `/migrate` | Legacy ETL to modern stack | dbt-specialist |

### Core & Utilities (10)

| Command | Purpose |
|---------|---------|
| `/review` | Code review before PR |
| `/judge` | Cross-model second opinion via OpenRouter |
| `/status` | Project status (active SDD, git, health) |
| `/create-kb` | Add a KB domain |
| `/ingest-kb` | Update KB domain via Context7 |
| `/lint-kb` | Audit KB domain quality |
| `/meeting` | Extract decisions from meeting notes |
| `/memory` | Save session insights |
| `/sync-context` | Update CLAUDE.md |
| `/readme-maker` | Generate README |

### Multi-agent variants

`/define-m` and `/design-m` — invoke domain specialists in parallel for cross-domain work (3+ KB domains).

---

## Agents

73 specialized agents automatically matched to tasks during `/build`:

| Category | Count | Examples |
|----------|-------|---------|
| **Workflow** | 9 | brainstorm, define, design, build, ship, iterate (incl. multi-agent variants) |
| **Architect** | 8 | schema-designer, pipeline-architect, medallion-architect, lakehouse-architect |
| **Cloud** | 10 | aws-data-architect, gcp-data-architect, lambda-builder, ci-cd-specialist |
| **Platform** | 6 | fabric-architect, fabric-pipeline-developer, fabric-ai-specialist |
| **Frontend** | 5 | react-developer, css-specialist, ux-designer, frontend-architect, a11y-specialist |
| **Python** | 6 | python-developer, code-reviewer, code-cleaner, llm-specialist |
| **Test** | 3 | test-generator, data-quality-analyst, data-contracts-engineer |
| **Data Engineering** | 16 | dbt-specialist, spark-engineer, airflow-specialist, sql-optimizer, streaming-engineer, n8n-specialist |
| **Dev** | 5 | prompt-crafter, codebase-explorer, shell-script-specialist, meeting-analyst, kb-evolution-agent |

---

## Knowledge Base

39 KB domains consulted by agents before generating any recommendation:

| Category | Domains |
|----------|---------|
| **Core DE** | `dbt`, `spark`, `sql-patterns`, `airflow`, `streaming`, `n8n` |
| **Data Design** | `data-modeling`, `data-quality`, `medallion` |
| **Infrastructure** | `lakehouse`, `lakeflow`, `cloud-platforms`, `terraform` |
| **Cloud** | `aws`, `gcp`, `microsoft-fabric`, `supabase` |
| **AI & Modern Stack** | `ai-data-engineering`, `modern-stack`, `genai`, `prompt-engineering` |
| **Frontend** | `react`, `nextjs`, `tailwind-css`, `accessibility`, `design-systems`, `frontend-patterns` |
| **Foundations** | `pydantic`, `python`, `testing` |

Keep KBs fresh with `/ingest-kb <domain>` (uses Context7 MCP) and audit quality with `/lint-kb`.

---

## Project Structure

```text
agentspec/
├── .claude-plugin/         # Marketplace manifest (Claude Code entrypoint)
├── .claude/
│   ├── agents/             # 73 specialized agents (9 categories)
│   ├── commands/           # 41 slash commands (5 categories)
│   ├── skills/             # 5 skills (incl. agent-router)
│   ├── kb/                 # 39 Knowledge Base domains
│   └── sdd/
│       ├── architecture/   # WORKFLOW_CONTRACTS.yaml (agent_resolution)
│       ├── templates/      # 5 phase templates (pt-BR)
│       ├── features/       # Active: BRAINSTORM_, DEFINE_, DESIGN_
│       ├── reports/        # BUILD_REPORT_
│       └── archive/        # Shipped features
│
├── plugin/                 # Distributable plugin (built from .claude/)
│   └── .claude-plugin/     # plugin.json + marketplace.json
├── plugin-extras/          # Plugin-only content (skills, hooks, init scripts)
│
├── scripts/                # judge.py, generate-agent-router.py
├── tests/                  # pytest suite (27 tests)
├── docs/                   # Concepts, tutorials, reference
├── tasks/backlog.md        # Roadmap
├── Makefile                # Developer entry points
└── build-plugin.sh         # Rebuild plugin/ from .claude/
```

---

## Documentation

| Guide | Description |
|-------|-------------|
| [Getting Started](docs/getting-started/) | Install and build your first feature |
| [Core Concepts](docs/concepts/) | SDD pillars and how agents work |
| [Agent Overrides](docs/concepts/agent-overrides.md) | Customize agents per project |
| [Judge Setup](docs/getting-started/judge-setup.md) | Enable cross-model second opinion |
| [Tutorials](docs/tutorials/) | dbt, star schema, data quality, Spark, streaming |
| [Reference](docs/reference/) | Full catalog: agents, commands, KB domains |

---

## Contributing

Contributions welcome — see [CONTRIBUTING.md](CONTRIBUTING.md).

- **New Agents** — add specialists for your domain
- **KB Domains** — share knowledge base patterns
- **Commands** — new slash commands for common workflows
- **Bug Fixes** — improve stability
- **Documentation** — clarify and expand docs

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

**[Documentation](docs/) | [Contributing](CONTRIBUTING.md) | [Changelog](CHANGELOG.md)**

Built with [Claude Code](https://docs.anthropic.com/en/docs/claude-code)

</div>
