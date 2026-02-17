# AgentSpec Development

> Developing the Spec-Driven Development framework for Claude Code

---

## Project Context

**What is AgentSpec?** A Claude Code plugin that provides structured AI-assisted development through a 5-phase SDD workflow.

**Current Status:** Initial repository setup complete, ready for enhancement and sanitization.

---

## Repository Structure

```
agentspec/
├── .claude/                 # Claude Code integration
│   ├── agents/              # 15 specialized agents
│   │   ├── workflow/        # 6 SDD phase agents
│   │   ├── code-quality/    # 4 code excellence agents
│   │   ├── communication/   # 3 explanation agents
│   │   └── exploration/     # 2 codebase agents
│   │
│   ├── commands/            # Slash commands
│   │   ├── workflow/        # SDD commands
│   │   ├── core/            # Utility commands
│   │   ├── knowledge/       # KB commands
│   │   └── review/          # Review commands
│   │
│   ├── sdd/                 # SDD framework
│   │   ├── architecture/    # Framework design
│   │   ├── templates/       # Document templates
│   │   ├── features/        # Active development
│   │   ├── reports/         # Build reports
│   │   └── archive/         # Shipped features
│   │
│   └── kb/                  # Knowledge Base (8 domains)
│       ├── _templates/      # KB domain templates
│       ├── pydantic/        # Data validation patterns
│       ├── gcp/             # Google Cloud Platform
│       ├── gemini/          # Gemini AI patterns
│       ├── langfuse/        # LLM observability
│       ├── terraform/       # Infrastructure as Code
│       ├── terragrunt/      # Multi-environment IaC
│       ├── crewai/          # Multi-agent orchestration
│       └── openrouter/      # LLM routing
│
├── .claude-plugin/          # Plugin manifest
│   └── plugin.json
│
└── docs/                    # Documentation
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

---

## Active Development Tasks

| Task | Status | Description |
|------|--------|-------------|
| Sanitize agents | Pending | Remove project-specific references |
| Create CLAUDE.md.template | Pending | Template for user projects |
| Add more KB domains | Pending | React, TypeScript, etc. |
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

### KB Domains

- `index.md` - Domain overview
- `quick-reference.md` - Cheat sheet
- `concepts/` - 3-6 concept files
- `patterns/` - 3-6 pattern files with code examples

---

## Commands Available

| Command | Purpose |
|---------|---------|
| `/brainstorm` | Explore ideas (Phase 0) |
| `/define` | Capture requirements (Phase 1) |
| `/design` | Create architecture (Phase 2) |
| `/build` | Execute implementation (Phase 3) |
| `/ship` | Archive completed work (Phase 4) |
| `/iterate` | Update existing docs (Cross-phase) |
| `/create-pr` | Create pull request |
| `/create-kb` | Create KB domain |
| `/review` | Code review |
| `/memory` | Save session insights |
| `/sync-context` | Update CLAUDE.md |
| `/readme-maker` | Generate README |

---

## Key Files to Know

| File | Purpose |
|------|---------|
| `.claude-plugin/plugin.json` | Plugin manifest for Claude Code |
| `.claude/sdd/architecture/WORKFLOW_CONTRACTS.yaml` | Phase transition rules |
| `.claude/sdd/templates/*.md` | Document templates |
| `.claude/kb/_templates/*.template` | KB domain templates |

---

## Version

- **Version:** 1.0.0
- **Status:** Release
- **Last Updated:** 2026-02-17
