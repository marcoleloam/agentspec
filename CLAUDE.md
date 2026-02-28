# AgentSpec Development

> Developing the Spec-Driven Development framework for Claude Code

---

## Project Context

**What is AgentSpec?** A Claude Code plugin that provides structured AI-assisted development through a 5-phase SDD workflow.

**Current Status:** Framework ready, Linear is the project tracker (source of truth).

**Idioma:** Todos os documentos gerados e interações com o usuário são em **Português-BR (pt-BR)**.

---

## Repository Structure

```text
agentspec/
├── .claude/                 # Claude Code integration
│   ├── agents/              # 16 specialized agents
│   │   ├── workflow/        # 6 SDD phase agents
│   │   ├── code-quality/    # 4 code excellence agents
│   │   ├── communication/   # 4 communication agents
│   │   └── exploration/     # 2 codebase agents
│   │
│   ├── skills/              # 14 slash commands (skills)
│   │   └── {skill-name}/    # Cada skill em pasta própria com SKILL.md
│   │
│   ├── sdd/                 # SDD framework
│   │   ├── architecture/    # WORKFLOW_CONTRACTS.yaml, ARCHITECTURE.md
│   │   ├── templates/       # 5 document templates (pt-BR)
│   │   ├── features/        # Active development
│   │   ├── reports/         # Build reports
│   │   └── archive/         # Shipped features
│   │
│   └── kb/                  # Knowledge Base
│       ├── _templates/      # 7 KB domain templates
│       ├── _index.yaml      # Domain registry
│       └── {domain}/        # User-created KB domains (via /create-kb)
│
├── docs/                    # Documentation
│   ├── getting-started/     # Installation and first feature
│   ├── concepts/            # SDD mental model and pillars
│   ├── tutorials/           # Workflow walkthroughs
│   └── reference/           # Command, agent, template catalog
│
├── CHANGELOG.md             # Version history
├── CONTRIBUTING.md          # Contribution guide
├── SECURITY.md              # Security policy
└── README.md                # Project overview
```

---

## Development Workflow

Use AgentSpec's own SDD workflow to develop AgentSpec:

```bash
# Explorar uma ideia de melhoria
/explorar "Adicionar camada Judge para validação de spec"

# Capturar requisitos
/definir CAMADA_JUDGE

# Projetar a arquitetura
/projetar CAMADA_JUDGE

# Construir
/construir CAMADA_JUDGE

# Entregar quando completo
/entregar CAMADA_JUDGE
```

---

## Active Development Tasks

| Task | Status | Description |
|------|--------|-------------|
| Sanitize agents | Done | Removed project-specific references |
| Clean KB domains | Done | Removed project-specific KB domains, kept framework scaffolding |
| Linear project setup | Done | 60 issues, 6 milestones, 9 strategic docs in Linear |
| Framework readiness review | Done | SDD 9.2, KB 9.4, Commands 8.5, Agents 7.2 |
| Documentation overhaul | Done | Getting started, concepts, tutorials, reference, README, community files |
| Migração para pt-BR | Done | Templates, agentes, comandos e contratos 100% em português |
| Migração commands → skills | Done | 12 commands migrados para .claude/skills/ com SKILL.md |
| Tradução completa pt-BR | Done | Todos os 16 agentes e 12 skills traduzidos para pt-BR |
| Reorganização skills | Done | review e create-kb movidos para workflow/, core mantido |
| Flatten skills structure | Done | Skills movidos de workflow/ e core/ para .claude/skills/ (flat) |
| Create CLAUDE.md.template | Pending | Template for user projects |
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

## Skills Available

| Skill | Objetivo | Localização |
|-------|----------|-------------|
| `/explorar` | Explorar ideias (Fase 0) | `.claude/skills/explorar/` |
| `/definir` | Capturar requisitos (Fase 1) | `.claude/skills/definir/` |
| `/projetar` | Criar arquitetura (Fase 2) | `.claude/skills/projetar/` |
| `/construir` | Executar implementação (Fase 3) | `.claude/skills/construir/` |
| `/entregar` | Arquivar trabalho concluído (Fase 4) | `.claude/skills/entregar/` |
| `/iterar` | Atualizar docs existentes (Cross-phase) | `.claude/skills/iterar/` |
| `/create-pr` | Criar pull request | `.claude/skills/create-pr/` |
| `/create-kb` | Criar domínio KB | `.claude/skills/create-kb/` |
| `/review` | Revisão de código | `.claude/skills/review/` |
| `/start` | Tela de boas-vindas e status do projeto | `.claude/skills/start/` |
| `/memory` | Salvar insights da sessão | `.claude/skills/memory/` |
| `/sync-context` | Atualizar CLAUDE.md | `.claude/skills/sync-context/` |
| `/readme-maker` | Gerar README | `.claude/skills/readme-maker/` |

---

## File Naming Convention

| Fase | Prefixo | Exemplo |
|------|---------|---------|
| Fase 0 | `00_` | `00_BRAINSTORM_AUTH.md` |
| Fase 1 | `01_` | `01_DEFINE_AUTH.md` |
| Fase 2 | `02_` | `02_DESIGN_AUTH.md` |
| Build Report | (sem prefixo) | `BUILD_REPORT_AUTH.md` |
| Shipped | (sem prefixo) | `SHIPPED_2026-02-27.md` |

---

## Key Files to Know

| File | Purpose |
|------|---------|
| `.claude/sdd/architecture/WORKFLOW_CONTRACTS.yaml` | Phase transition rules |
| `.claude/sdd/templates/*.md` | Document templates (pt-BR) |
| `.claude/kb/_templates/*.template` | KB domain templates |

---

## Version

- **Version:** 2.1.0
- **Status:** Release
- **Last Updated:** 2026-02-27
