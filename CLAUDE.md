# AgentSpec Development

> Developing the Spec-Driven Development framework for Claude Code

---

## Project Context

**What is AgentSpec?** A Claude Code plugin that provides structured AI-assisted development through a 5-phase SDD workflow.

**Current Status:** Plugin ready for distribution.

**Idioma:** Todos os documentos gerados e interações com o usuário são em **Português-BR (pt-BR)**.

---

## Repository Structure

```text
agentspec/
├── .claude-plugin/          # Plugin manifest
│   └── plugin.json          # name, version, author
│
├── skills/                  # 13 slash commands (skills)
│   └── {skill-name}/       # Cada skill em pasta própria com SKILL.md
│
├── agents/                  # 16 specialized agents (flat structure)
│   ├── brainstorm-agent.md  # Phase 0 - Explore ideas
│   ├── define-agent.md      # Phase 1 - Capture requirements
│   ├── design-agent.md      # Phase 2 - Architecture
│   ├── build-agent.md       # Phase 3 - Implementation
│   ├── ship-agent.md        # Phase 4 - Archive
│   ├── iterate-agent.md     # Cross-phase updates
│   └── ...                  # +10 more (code-quality, communication, exploration)
│
├── sdd/                     # SDD framework
│   ├── architecture/        # WORKFLOW_CONTRACTS.yaml, ARCHITECTURE.md
│   ├── templates/           # 5 document templates (pt-BR)
│   ├── features/            # Active development
│   ├── reports/             # Build reports
│   └── archive/             # Shipped features
│
├── kb/                      # Knowledge Base
│   ├── _templates/          # 7 KB domain templates
│   ├── _index.yaml          # Domain registry
│   └── {domain}/            # User-created KB domains (via /create-kb)
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

## Installation

```bash
# Local testing
claude --plugin-dir ./agentspec

# From marketplace (after publishing)
claude plugin install agentspec
```

Skills are namespaced: `/agentspec:explorar`, `/agentspec:definir`, etc.

---

## Development Workflow

Use AgentSpec's own SDD workflow to develop AgentSpec:

```bash
# Explorar uma ideia de melhoria
/agentspec:explorar "Adicionar camada Judge para validação de spec"

# Capturar requisitos
/agentspec:definir CAMADA_JUDGE

# Projetar a arquitetura
/agentspec:projetar CAMADA_JUDGE

# Construir
/agentspec:construir CAMADA_JUDGE

# Entregar quando completo
/agentspec:entregar CAMADA_JUDGE
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
| Migração commands → skills | Done | 12 commands migrados para skills/ com SKILL.md |
| Flatten skills structure | Done | Skills em estrutura flat skills/{nome}/ |
| Plugin packaging | Done | .claude-plugin/plugin.json + skills e agents na raiz |
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
| `/agentspec:explorar` | Explorar ideias (Fase 0) | `skills/explorar/` |
| `/agentspec:definir` | Capturar requisitos (Fase 1) | `skills/definir/` |
| `/agentspec:projetar` | Criar arquitetura (Fase 2) | `skills/projetar/` |
| `/agentspec:construir` | Executar implementação (Fase 3) | `skills/construir/` |
| `/agentspec:entregar` | Arquivar trabalho concluído (Fase 4) | `skills/entregar/` |
| `/agentspec:iterar` | Atualizar docs existentes (Cross-phase) | `skills/iterar/` |
| `/agentspec:create-pr` | Criar pull request | `skills/create-pr/` |
| `/agentspec:create-kb` | Criar domínio KB | `skills/create-kb/` |
| `/agentspec:review` | Revisão de código | `skills/review/` |
| `/agentspec:start` | Tela de boas-vindas e status do projeto | `skills/start/` |
| `/agentspec:memory` | Salvar insights da sessão | `skills/memory/` |
| `/agentspec:sync-context` | Atualizar CLAUDE.md | `skills/sync-context/` |
| `/agentspec:readme-maker` | Gerar README | `skills/readme-maker/` |

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
| `sdd/architecture/WORKFLOW_CONTRACTS.yaml` | Phase transition rules |
| `sdd/templates/*.md` | Document templates (pt-BR) |
| `kb/_templates/*.template` | KB domain templates |

---

## Version

- **Version:** 2.2.0
- **Status:** Plugin Release
- **Last Updated:** 2026-03-02
