<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/banner.svg">
  <source media="(prefers-color-scheme: light)" srcset="assets/banner.svg">
  <img alt="AgentSpec — Spec-Driven Development" src="assets/banner.svg" width="100%">
</picture>

<br/>

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Compatible-purple.svg)](https://docs.anthropic.com/en/docs/claude-code)
[![Version](https://img.shields.io/badge/version-3.0.0-green.svg)](CHANGELOG.md)
[![Agents](https://img.shields.io/badge/agents-58-orange.svg)](.claude/agents/)
[![Commands](https://img.shields.io/badge/commands-22-blue.svg)](.claude/commands/)
[![KB Domains](https://img.shields.io/badge/KB%20domains-22-blue.svg)](.claude/kb/)

[Quick Start](#quick-start) | [Commands](#commands) | [Documentation](docs/) | [Contributing](CONTRIBUTING.md)

</div>

---

## The Problem

AI-assisted development without structure produces inconsistent results: hallucinated solutions, spec drift between sessions, code that doesn't match what was agreed upon, and decisions that get lost. Each conversation starts from scratch without accumulated context.

## The Solution

AgentSpec brings **Spec-Driven Development (SDD)** to Claude Code — a 5-phase workflow backed by 22 knowledge base domains, 58 specialized agents, and 22 slash commands. Every decision is captured in formal documents. Every phase has a quality gate. Nothing gets lost.

```text
/brainstorm  →  /define  →  /design  →  /build  →  /ship
  (Explore)    (Capture)  (Architect)  (Execute)  (Archive)
                  │            │            │
            Clarity Score  File Manifest  Agent Delegation
            MoSCoW Goals   ADRs inline    TodoWrite tracking
            Data Contracts  KB-First      BUILD_REPORT
```

Generated documents (BRAINSTORM, DEFINE, DESIGN, BUILD_REPORT, SHIPPED) are produced in **Portuguese-BR (pt-BR)** automatically.

---

## Quick Start

### Install — macOS / Linux

```bash
git clone https://github.com/marcoleloam/agentspec.git ~/agentspec
cd ~/agentspec && ./install.sh
```

### Install — Windows

```powershell
git clone https://github.com/marcoleloam/agentspec.git $env:USERPROFILE\agentspec
cd $env:USERPROFILE\agentspec
powershell -ExecutionPolicy Bypass -File install-win.ps1
```

The installer creates symlinks from `~/.claude/` (or `%APPDATA%\Claude\` on Windows) to the cloned repo. All 58 agents and 22 commands become available globally in every project.

**Update anytime:**

```bash
cd ~/agentspec && git pull
# symlinks update automatically — nothing else needed
```

### Add AgentSpec to a Project

```bash
# Add SDD workflow context to your project
cat >> CLAUDE.md << 'EOF'

---

## AgentSpec SDD

Workflow ativo — documentos gerados em pt-BR.

| Command | Quando Usar |
|---------|-------------|
| `/brainstorm` | Explorar ideia nova |
| `/define` | Capturar requisitos |
| `/design` | Planejar arquitetura |
| `/build` | Implementar |
| `/continuar` | Retomar build incompleto |
| `/ship` | Arquivar feature concluída |

SDD docs: `.claude/sdd/features/` | Reports: `.claude/sdd/reports/`

**AgentSpec Version:** 3.0.0
EOF
```

Or start from the template for new projects:

```bash
cp ~/agentspec/CLAUDE.md.template ./CLAUDE.md
# Edit with your project context
```

---

## Workflow

### 5-Phase SDD with Quality Gates

| Phase | Command | What It Does | Quality Gate |
|-------|---------|--------------|--------------|
| **Brainstorm** | `/brainstorm` | Explore approaches, YAGNI, 1 question at a time | 3+ questions, 2+ approaches |
| **Define** | `/define` | Requirements + MoSCoW goals + data contracts | Clarity Score ≥ 12/15 |
| **Design** | `/design` | Architecture + ADRs + file manifest with agent assignment | Complete manifest |
| **Build** | `/build` | Execute + agent delegation + verification | All tests pass |
| **Ship** | `/ship` | Archive with lessons learned | Acceptance verified |

**Didn't finish the build?** Use `/continuar` for gap analysis — implements only what's missing without restarting.

**Requirements changed mid-stream?** Use `/iterate` to update any phase document with automatic cascade detection.

---

## Commands

### SDD Workflow (8)

| Command | Purpose |
|---------|---------|
| `/brainstorm` | Explore ideas (Phase 0) |
| `/define` | Capture requirements (Phase 1) |
| `/design` | Create architecture (Phase 2) |
| `/build` | Execute implementation (Phase 3) |
| `/continuar` | Resume incomplete build (Phase 3+) |
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

### Core & Utilities (6)

| Command | Purpose |
|---------|---------|
| `/review` | Code review before PR |
| `/create-kb` | Add a KB domain |
| `/meeting` | Extract decisions from meeting notes |
| `/memory` | Save session insights |
| `/sync-context` | Update CLAUDE.md |
| `/readme-maker` | Generate README |

---

## Agents

58 specialized agents automatically matched to tasks during `/build`:

| Category | Count | Examples |
|----------|-------|---------|
| **Workflow** | 6 | brainstorm, define, design, build, ship, iterate |
| **Architect** | 8 | schema-designer, pipeline-architect, medallion-architect, lakehouse-architect |
| **Cloud** | 10 | aws-data-architect, gcp-data-architect, lambda-builder, ci-cd-specialist |
| **Platform** | 6 | fabric-architect, fabric-pipeline-developer, fabric-ai-specialist |
| **Python** | 6 | python-developer, code-reviewer, code-cleaner, llm-specialist |
| **Test** | 3 | test-generator, data-quality-analyst, data-contracts-engineer |
| **Data Engineering** | 15 | dbt-specialist, spark-engineer, airflow-specialist, sql-optimizer, streaming-engineer |
| **Dev** | 4 | prompt-crafter, codebase-explorer, shell-script-specialist, meeting-analyst |

---

## Knowledge Base

22 KB domains consulted by agents before generating any recommendation:

| Category | Domains |
|----------|---------|
| **Core DE** | `dbt`, `spark`, `sql-patterns`, `airflow`, `streaming` |
| **Data Design** | `data-modeling`, `data-quality`, `medallion` |
| **Infrastructure** | `lakehouse`, `lakeflow`, `cloud-platforms`, `terraform` |
| **Cloud** | `aws`, `gcp`, `microsoft-fabric` |
| **AI & Modern Stack** | `ai-data-engineering`, `modern-stack`, `genai`, `prompt-engineering` |
| **Foundations** | `pydantic`, `python`, `testing` |

---

## Project Structure

```text
agentspec/
├── install.sh               # macOS/Linux global install
├── install-win.ps1          # Windows global install
├── CLAUDE.md.template       # Template for user projects
│
└── .claude/
    ├── agents/              # 58 specialized agents (8 categories)
    ├── commands/            # 22 slash commands (5 categories)
    ├── kb/                  # 22 Knowledge Base domains
    ├── sdd/
    │   ├── architecture/    # WORKFLOW_CONTRACTS.yaml
    │   ├── templates/       # 5 phase templates (pt-BR)
    │   ├── features/        # Active: BRAINSTORM_, DEFINE_, DESIGN_
    │   ├── reports/         # BUILD_REPORT_
    │   └── archive/         # Shipped features
    └── settings.json        # Claude Code permissions
```

---

## Documentation

| Guide | Description |
|-------|-------------|
| [Getting Started](docs/getting-started/) | Install and build your first feature |
| [Core Concepts](docs/concepts/) | SDD pillars and how agents work |
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
