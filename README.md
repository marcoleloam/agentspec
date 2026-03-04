<div align="center">

# AgentSpec

## Spec-Driven Development para Claude Code

Transforme ideias em features entregues através de um workflow de IA estruturado em 5 fases

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Compatible-purple.svg)](https://docs.anthropic.com/en/docs/claude-code)
[![Version](https://img.shields.io/badge/version-2.4.0-green.svg)](CHANGELOG.md)

[Quick Start](#quick-start) | [Documentação](docs/) | [Contributing](CONTRIBUTING.md)

</div>

---

## O Problema

Desenvolvimento com IA sem estrutura leva a decisões perdidas, spec drift e erros repetidos. Você discute requisitos em uma sessão, esquece na próxima, e termina com código que não bate com o que foi acordado.

## A Solução

AgentSpec traz o **Spec-Driven Development (SDD)** para o Claude Code — um workflow de 5 fases onde cada decisão é capturada, cada design é rastreável e cada lição é preservada:

```text
/explorar  →  /definir  →  /projetar  →  /construir  →  /entregar
 (Explorar)   (Capturar)   (Arquitetar)   (Executar)    (Arquivar)
```

Cada fase produz um documento. Cada transição tem um quality gate. Nada se perde.

---

## Quick Start

### Instalação

```bash
# Clonar o AgentSpec
git clone https://github.com/marcoleloam/agentspec.git

# Instalar como plugin do Claude Code
claude plugin install ./agentspec
```

### Sua Primeira Feature

```bash
# 1. Explorar a ideia
claude> /agentspec:explorar "Adicionar autenticação de usuários com JWT"

# 2. Capturar requisitos (quality gate: clareza >= 12/15)
claude> /agentspec:definir AUTH_USUARIO

# 3. Projetar a arquitetura (agentes associados automaticamente)
claude> /agentspec:projetar 01_DEFINE_AUTH_USUARIO.md

# 4. Construir com verificação incremental
claude> /agentspec:construir 02_DESIGN_AUTH_USUARIO.md

# 5. Resultado não ficou completo? Continue de onde parou
claude> /agentspec:continuar AUTH_USUARIO

# 6. Arquivar com lições aprendidas
claude> /agentspec:entregar AUTH_USUARIO
```

Cinco comandos — rastreabilidade total da ideia à produção.

---

## O Que Você Obtém

### Workflow de 5 Fases com Quality Gates

| Fase           | Skill           | O Que Faz                         | Quality Gate                  |
|----------------|-----------------|-----------------------------------|-------------------------------|
| **Explorar**   | `/explorar`     | Explorar abordagens, comparar     | 3+ perguntas, 2+ abordagens   |
| **Definir**    | `/definir`      | Capturar requisitos formalmente   | Clareza >= 12/15              |
| **Projetar**   | `/projetar`     | Arquitetura, manifesto, ADRs      | Manifesto completo            |
| **Construir**  | `/construir`    | Executar com delegação de agentes | Todos os testes passam        |
| **Entregar**   | `/entregar`     | Arquivar com lições aprendidas    | Aceitação verificada          |

### Iteração Estruturada

Resultado não atendeu as expectativas? Dois comandos cobrem os cenários mais comuns:

| Situação | Skill |
|----------|-------|
| Feature incompleta ou bug na implementação | `/continuar` — retoma o código de onde parou |
| Requisito mudou, design precisa ser atualizado | `/iterar` — atualiza documentos SDD com cascade |

### 16 Agentes Especializados

| Categoria         | Qtd | Exemplos                                              |
|-------------------|-----|-------------------------------------------------------|
| **Workflow**      | 6   | brainstorm, define, design, build, ship, iterate      |
| **Qualidade**     | 4   | code-reviewer, test-generator, code-cleaner           |
| **Comunicação**   | 4   | adaptive-explainer, linear-pm, meeting-analyst        |
| **Exploração**    | 2   | codebase-explorer, kb-architect                       |

Durante o `/construir`, agentes são automaticamente associados às tarefas com base no documento DESIGN.

### Knowledge Base Framework

Fundamente as respostas da IA em padrões verificados ao invés de alucinados:

```bash
# Criar uma KB de domínio específico
claude> /agentspec:create-kb fastapi

# Os agentes vão consultá-la durante /projetar e /construir
```

### 14 Skills Disponíveis

| Skill | Objetivo |
|-------|----------|
| `/agentspec:explorar` | Explorar ideias (Fase 0) |
| `/agentspec:definir` | Capturar requisitos (Fase 1) |
| `/agentspec:projetar` | Criar arquitetura (Fase 2) |
| `/agentspec:construir` | Executar implementação (Fase 3) |
| `/agentspec:continuar` | Retomar build incompleta (Fase 3+) |
| `/agentspec:entregar` | Arquivar feature concluída (Fase 4) |
| `/agentspec:iterar` | Atualizar docs SDD (Cross-phase) |
| `/agentspec:review` | Revisão de código dual AI |
| `/agentspec:create-pr` | Criar pull request estruturado |
| `/agentspec:create-kb` | Criar domínio Knowledge Base |
| `/agentspec:memory` | Salvar insights da sessão |
| `/agentspec:sync-context` | Atualizar CLAUDE.md |
| `/agentspec:readme-maker` | Gerar README profissional |
| `/agentspec:start` | Tela de boas-vindas e status |

---

## Como Funciona

```text
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   /explorar  │────▶│   /definir   │────▶│  /projetar   │
│  (Opcional)  │     │  Requisitos  │     │ Arquitetura  │
└──────────────┘     └──────────────┘     └──────────────┘
                                                │
                                                ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  /entregar   │◀────│  /construir  │◀────│   Matching   │
│   Arquivar   │     │   Executar   │     │  de Agentes  │
└──────────────┘     └──────────────┘     └──────────────┘
                           │
                           ▼ (se incompleto)
                    ┌──────────────┐
                    │  /continuar  │
                    │  Gap Analysis│
                    └──────────────┘
```

**Matching de agentes:** Seu doc DESIGN menciona "Pydantic models" e "pytest" — AgentSpec delega automaticamente ao `test-generator` para testes e `code-reviewer` para qualidade.

**Build incompleta?** Use `/continuar` para análise de gap e retomar apenas o que falta, sem reescrever o que já funciona.

**Requisitos mudaram?** Use `/iterar` para atualizar qualquer documento de fase com detecção automática de cascata para docs dependentes.

---

## Estrutura do Projeto

```text
agentspec/
├── .claude-plugin/          # Manifesto do plugin
│   └── plugin.json
│
├── skills/                  # 14 slash commands
│   ├── explorar/            # Fase 0 - Explorar ideias
│   ├── definir/             # Fase 1 - Capturar requisitos
│   ├── projetar/            # Fase 2 - Criar arquitetura
│   ├── construir/           # Fase 3 - Executar implementação
│   ├── continuar/           # Fase 3+ - Retomar build incompleta
│   ├── entregar/            # Fase 4 - Arquivar feature
│   ├── iterar/              # Cross-phase - Atualizar docs
│   └── ...                  # +7 skills de suporte
│
├── agents/                  # 16 agentes especializados (estrutura flat)
│   ├── brainstorm-agent.md
│   ├── define-agent.md
│   ├── design-agent.md
│   ├── build-agent.md
│   └── ...
│
├── sdd/                     # Framework SDD
│   ├── architecture/        # WORKFLOW_CONTRACTS.yaml
│   ├── templates/           # 5 templates de documento (pt-BR)
│   ├── features/            # Desenvolvimento ativo
│   ├── reports/             # Relatórios de build
│   └── archive/             # Features entregues
│
├── kb/                      # Knowledge Base
│   ├── _templates/          # 7 templates de domínio KB
│   └── _index.yaml          # Registro de domínios
│
└── docs/                    # Documentação
    ├── getting-started/
    ├── concepts/
    ├── tutorials/
    └── reference/
```

---

## Documentação

| Guia | Descrição |
|------|-----------|
| [Getting Started](docs/getting-started/) | Instalação e primeira feature |
| [Conceitos](docs/concepts/) | Como fases, agentes e KB funcionam juntos |
| [Tutoriais](docs/tutorials/) | Walkthroughs passo a passo |
| [Referência](docs/reference/) | Catálogo completo de skills, agentes e templates |

---

## Contributing

Contribuições são bem-vindas! Veja [CONTRIBUTING.md](CONTRIBUTING.md) para diretrizes.

- **Novos Agentes** — adicione agentes especializados para seu domínio
- **Domínios KB** — compartilhe knowledge bases de domínio
- **Bug Fixes** — ajude a melhorar a estabilidade
- **Documentação** — clarifique e expanda a docs

---

## Licença

MIT License — veja [LICENSE](LICENSE) para detalhes.

---

<div align="center">

**[Documentação](docs/) | [Contributing](CONTRIBUTING.md) | [Changelog](CHANGELOG.md)**

Construído com [Claude Code](https://docs.anthropic.com/en/docs/claude-code)

</div>
