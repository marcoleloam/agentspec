# DESIGN: Frontend Ecosystem

> Design técnico para criar 5 agentes frontend + 6 KB domains no AgentSpec, espelhando a arquitetura DE existente.

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | FRONTEND_ECOSYSTEM |
| **Data** | 2026-03-29 |
| **Autor** | design-agent |
| **DEFINE** | [DEFINE_FRONTEND_ECOSYSTEM.md](./DEFINE_FRONTEND_ECOSYSTEM.md) |
| **Status** | ✅ Complete (Built) |

---

## Visão Geral da Arquitetura

```text
┌─────────────────────────────────────────────────────────────────────┐
│                    FRONTEND ECOSYSTEM — OVERVIEW                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  .claude/agents/frontend/           .claude/kb/                      │
│  ┌─────────────────────┐           ┌──────────────────┐             │
│  │ react-developer     │──reads──→ │ react/           │             │
│  │ css-specialist      │──reads──→ │ tailwind-css/    │             │
│  │ ux-designer         │──reads──→ │ design-systems/  │             │
│  │ frontend-architect  │──reads──→ │ nextjs/          │             │
│  │ a11y-specialist     │──reads──→ │ accessibility/   │             │
│  └────────┬────────────┘           │ frontend-patterns│             │
│           │                        └────────┬─────────┘             │
│           │ MCP fallback                    │                        │
│           ▼                                 │                        │
│  ┌─────────────────────┐                    │                        │
│  │ context7 + exa      │    (já existem)    │                        │
│  └─────────────────────┘                    │                        │
│                                              │                        │
│  Integração SDD:                             │                        │
│  ┌──────────────────────────────────────────┘                        │
│  │                                                                    │
│  │  /define → detecta stack → sugere KB domains frontend             │
│  │  /design → glob agents/ → match → File Manifest com @frontend-*  │
│  │  /build  → le manifest → Task(@react-developer) → código         │
│  │  /review → @a11y-specialist + @css-specialist → revisão           │
│  │                                                                    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Componentes

| Componente | Propósito | Tecnologia |
|------------|-----------|------------|
| 5 Agent files | Agentes especializados frontend | Markdown (T2 `_template.md`) |
| 6 KB domains | Knowledge Base por tecnologia | Markdown (index + quick-ref + concepts + patterns) |
| `_index.yaml` update | Registro dos novos domínios | YAML |
| `agents/README.md` update | Categoria frontend no mapa | Markdown |
| `CLAUDE.md` update | Documentar novos agentes | Markdown |
| `WORKFLOW_CONTRACTS.yaml` update | `frontend_delegation` no Build | YAML |

---

## Decisões Principais

### Decisão 1: T2 para todos os agentes (não T3)

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-03-29 |

**Contexto:** Agentes podem ser T1 (utility), T2 (domain expert), ou T3 (platform specialist com MCP servers dedicados).

**Escolha:** Todos os 5 agentes frontend são T2.

**Justificativa:** T2 é o tier dos agentes DE (dbt-specialist, spark-engineer). Inclui KB-First, Agreement Matrix, confidence scoring, stop conditions e escalation rules. T3 adicionaria Error Recovery e Extension Points que não são necessários para a primeira versão.

**Alternativas Rejeitadas:**
1. T3 — Mais completo mas excessivo. MCP servers dedicados para frontend não existem.
2. T1 — Muito simples. Sem stop conditions nem escalation rules.

**Consequências:**
- Se precisar de Error Recovery ou MCP servers dedicados no futuro, upgrade para T3 via `/iterate`.

---

### Decisão 2: KB populada via `/create-kb` com MCP, não manualmente

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-03-29 |

**Contexto:** 6 KB domains com ~8 arquivos cada = ~48 arquivos de conteúdo. Escrever manualmente é inviável.

**Escolha:** Usar o comando `/create-kb` existente, que consulta MCP context7 para buscar docs oficiais e popular cada domínio.

**Justificativa:** O `/create-kb` já gera index.md, quick-reference.md, concepts/ e patterns/ seguindo os templates. Testado e funcional com os 22 domínios DE.

**Alternativas Rejeitadas:**
1. Escrita manual — Inviável para 48+ arquivos. Propenso a erros.
2. Web scraping — Complexo e frágil. context7 já resolve.

**Consequências:**
- Qualidade depende do MCP context7 retornar docs atualizados (premissa A-001 do DEFINE).
- Build executa 6x `/create-kb`: react, nextjs, tailwind-css, accessibility, design-systems, frontend-patterns.

---

### Decisão 3: ux-designer com model opus (não sonnet)

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-03-29 |

**Contexto:** ux-designer e frontend-architect lidam com decisões de alto nível. Os demais são implementação.

**Escolha:** ux-designer e frontend-architect usam Opus. react-developer, css-specialist e a11y-specialist usam Sonnet.

**Justificativa:** Mesmo padrão do SDD: design-agent e build-agent usam Opus; agentes de implementação usam Sonnet. UX decisions e architecture decisions precisam de raciocínio mais profundo.

**Alternativas Rejeitadas:**
1. Todos Sonnet — Mais barato mas UX decisions são complexas e criativas.
2. Todos Opus — Desnecessário para css-specialist e a11y-specialist que seguem patterns claros.

---

### Decisão 4: Escalation rules cross-frontend

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-03-29 |

**Contexto:** Agentes frontend precisam saber quando escalar para outro agente frontend ou para agentes existentes.

**Escolha:** Cada agente frontend tem escalation rules para outros agentes frontend E para agentes existentes (code-reviewer, test-generator).

**Justificativa:** Evita que um agente tente fazer o trabalho de outro. O react-developer não deve tentar resolver problemas de acessibilidade — escala para a11y-specialist.

---

## Manifesto de Arquivos

| # | Arquivo | Ação | Propósito | Agente | Dependências |
|---|---------|------|-----------|--------|--------------|
| 1 | `.claude/agents/frontend/react-developer.md` | Criar | Agente React/Next.js components | (direto) | Nenhuma |
| 2 | `.claude/agents/frontend/css-specialist.md` | Criar | Agente Tailwind/design systems | (direto) | Nenhuma |
| 3 | `.claude/agents/frontend/ux-designer.md` | Criar | Agente UX/user flows | (direto) | Nenhuma |
| 4 | `.claude/agents/frontend/frontend-architect.md` | Criar | Agente arquitetura frontend | (direto) | Nenhuma |
| 5 | `.claude/agents/frontend/a11y-specialist.md` | Criar | Agente acessibilidade | (direto) | Nenhuma |
| 6 | `.claude/kb/react/index.md` | Criar | KB index React | @kb-architect | Nenhuma |
| 7 | `.claude/kb/react/quick-reference.md` | Criar | Quick ref React | @kb-architect | 6 |
| 8 | `.claude/kb/react/concepts/hooks-patterns.md` | Criar | Concept hooks | @kb-architect | 6 |
| 9 | `.claude/kb/react/concepts/server-components.md` | Criar | Concept RSC | @kb-architect | 6 |
| 10 | `.claude/kb/react/concepts/state-management.md` | Criar | Concept state | @kb-architect | 6 |
| 11 | `.claude/kb/react/concepts/rendering-patterns.md` | Criar | Concept rendering | @kb-architect | 6 |
| 12 | `.claude/kb/react/patterns/component-composition.md` | Criar | Pattern composition | @kb-architect | 6 |
| 13 | `.claude/kb/react/patterns/form-handling.md` | Criar | Pattern forms | @kb-architect | 6 |
| 14 | `.claude/kb/react/patterns/data-fetching.md` | Criar | Pattern fetching | @kb-architect | 6 |
| 15 | `.claude/kb/react/patterns/testing-components.md` | Criar | Pattern testing | @kb-architect | 6 |
| 16 | `.claude/kb/nextjs/index.md` | Criar | KB index Next.js | @kb-architect | Nenhuma |
| 17 | `.claude/kb/nextjs/quick-reference.md` | Criar | Quick ref Next.js | @kb-architect | 16 |
| 18 | `.claude/kb/nextjs/concepts/app-router.md` | Criar | Concept App Router | @kb-architect | 16 |
| 19 | `.claude/kb/nextjs/concepts/rendering-strategies.md` | Criar | Concept SSR/CSR | @kb-architect | 16 |
| 20 | `.claude/kb/nextjs/concepts/caching.md` | Criar | Concept caching | @kb-architect | 16 |
| 21 | `.claude/kb/nextjs/concepts/middleware.md` | Criar | Concept middleware | @kb-architect | 16 |
| 22 | `.claude/kb/nextjs/patterns/api-routes.md` | Criar | Pattern API routes | @kb-architect | 16 |
| 23 | `.claude/kb/nextjs/patterns/auth-patterns.md` | Criar | Pattern auth | @kb-architect | 16 |
| 24 | `.claude/kb/nextjs/patterns/image-optimization.md` | Criar | Pattern images | @kb-architect | 16 |
| 25 | `.claude/kb/nextjs/patterns/deployment.md` | Criar | Pattern deploy | @kb-architect | 16 |
| 26 | `.claude/kb/tailwind-css/index.md` | Criar | KB index Tailwind | @kb-architect | Nenhuma |
| 27 | `.claude/kb/tailwind-css/quick-reference.md` | Criar | Quick ref Tailwind | @kb-architect | 26 |
| 28 | `.claude/kb/tailwind-css/concepts/utility-first.md` | Criar | Concept utility | @kb-architect | 26 |
| 29 | `.claude/kb/tailwind-css/concepts/design-tokens.md` | Criar | Concept tokens | @kb-architect | 26 |
| 30 | `.claude/kb/tailwind-css/concepts/responsive-design.md` | Criar | Concept responsive | @kb-architect | 26 |
| 31 | `.claude/kb/tailwind-css/patterns/component-styling.md` | Criar | Pattern styling | @kb-architect | 26 |
| 32 | `.claude/kb/tailwind-css/patterns/dark-mode.md` | Criar | Pattern dark mode | @kb-architect | 26 |
| 33 | `.claude/kb/tailwind-css/patterns/animations.md` | Criar | Pattern animations | @kb-architect | 26 |
| 34 | `.claude/kb/tailwind-css/patterns/cn-utility.md` | Criar | Pattern cn/clsx | @kb-architect | 26 |
| 35 | `.claude/kb/accessibility/index.md` | Criar | KB index a11y | @kb-architect | Nenhuma |
| 36 | `.claude/kb/accessibility/quick-reference.md` | Criar | Quick ref a11y | @kb-architect | 35 |
| 37 | `.claude/kb/accessibility/concepts/wcag-guidelines.md` | Criar | Concept WCAG | @kb-architect | 35 |
| 38 | `.claude/kb/accessibility/concepts/aria-patterns.md` | Criar | Concept ARIA | @kb-architect | 35 |
| 39 | `.claude/kb/accessibility/concepts/keyboard-navigation.md` | Criar | Concept keyboard | @kb-architect | 35 |
| 40 | `.claude/kb/accessibility/patterns/form-accessibility.md` | Criar | Pattern forms a11y | @kb-architect | 35 |
| 41 | `.claude/kb/accessibility/patterns/modal-dialog.md` | Criar | Pattern modal a11y | @kb-architect | 35 |
| 42 | `.claude/kb/accessibility/patterns/table-accessibility.md` | Criar | Pattern table a11y | @kb-architect | 35 |
| 43 | `.claude/kb/design-systems/index.md` | Criar | KB index DS | @kb-architect | Nenhuma |
| 44 | `.claude/kb/design-systems/quick-reference.md` | Criar | Quick ref DS | @kb-architect | 43 |
| 45 | `.claude/kb/design-systems/concepts/token-architecture.md` | Criar | Concept tokens | @kb-architect | 43 |
| 46 | `.claude/kb/design-systems/concepts/component-api.md` | Criar | Concept API | @kb-architect | 43 |
| 47 | `.claude/kb/design-systems/concepts/documentation.md` | Criar | Concept docs | @kb-architect | 43 |
| 48 | `.claude/kb/design-systems/patterns/variant-pattern.md` | Criar | Pattern variants | @kb-architect | 43 |
| 49 | `.claude/kb/design-systems/patterns/shadcn-patterns.md` | Criar | Pattern shadcn | @kb-architect | 43 |
| 50 | `.claude/kb/design-systems/patterns/theme-switching.md` | Criar | Pattern themes | @kb-architect | 43 |
| 51 | `.claude/kb/frontend-patterns/index.md` | Criar | KB index FE patterns | @kb-architect | Nenhuma |
| 52 | `.claude/kb/frontend-patterns/quick-reference.md` | Criar | Quick ref FE | @kb-architect | 51 |
| 53 | `.claude/kb/frontend-patterns/concepts/project-structure.md` | Criar | Concept structure | @kb-architect | 51 |
| 54 | `.claude/kb/frontend-patterns/concepts/error-handling.md` | Criar | Concept errors | @kb-architect | 51 |
| 55 | `.claude/kb/frontend-patterns/concepts/performance.md` | Criar | Concept perf | @kb-architect | 51 |
| 56 | `.claude/kb/frontend-patterns/patterns/api-integration.md` | Criar | Pattern API | @kb-architect | 51 |
| 57 | `.claude/kb/frontend-patterns/patterns/auth-flow.md` | Criar | Pattern auth | @kb-architect | 51 |
| 58 | `.claude/kb/frontend-patterns/patterns/optimistic-updates.md` | Criar | Pattern optimistic | @kb-architect | 51 |
| 59 | `.claude/kb/_index.yaml` | Editar | Registrar 6 novos domínios | (direto) | 6-58 |
| 60 | `.claude/agents/README.md` | Editar | Adicionar categoria frontend | (direto) | 1-5 |
| 61 | `CLAUDE.md` | Editar | Documentar novos agentes/KB | (direto) | 1-58 |
| 62 | `.claude/sdd/architecture/WORKFLOW_CONTRACTS.yaml` | Editar | Adicionar frontend_delegation | (direto) | 1-5 |

**Total de Arquivos:** 62 (58 criar + 4 editar)

---

## Justificativa de Atribuição de Agentes

| Agente | Arquivos Atribuídos | Por Que Este Agente |
|--------|---------------------|---------------------|
| @kb-architect | 6-58 (53 arquivos KB) | Especialista em criação de KB domains. Usa `/create-kb` internamente com MCP context7. |
| (direto) | 1-5, 59-62 (9 arquivos) | Agentes são markdown seguindo template conhecido. Edições são mecânicas. |

**Descoberta de Agentes:**
- Escaneado: `.claude/agents/**/*.md`
- @kb-architect matched por: KB domain creation, domínio `kb/`, propósito de scaffolding

---

## Padrões de Código

### Padrão 1: Estrutura de Agente Frontend (T2)

```markdown
---
name: {agent-name}
tier: T2
description: |
  {One-line description}.
  Use PROACTIVELY when {trigger conditions}.

  Example 1:
  - Context: {situation}
  - user: "{message}"
  - assistant: "I'll use the {agent-name} agent to {action}."

  Example 2:
  - Context: {different situation}
  - user: "{message}"
  - assistant: "Let me invoke the {agent-name} agent."

tools: [Read, Write, Edit, Grep, Glob, Bash, TodoWrite]
kb_domains: [{domain1}, {domain2}]
color: {color}
model: {sonnet|opus}
stop_conditions:
  - "{condition} — escalate to {agent}"
escalation_rules:
  - trigger: "{what triggers}"
    target: "{agent-name}"
    reason: "{why escalation}"
anti_pattern_refs: [shared-anti-patterns]
---

# {Agent Name}

## Identity

> **Identity:** {purpose}
> **Domain:** {areas}
> **Threshold:** {0.85-0.95} — {STANDARD|IMPORTANT}

---

## Knowledge Resolution

**Strategy:** JUST-IN-TIME — Load KB artifacts only when task demands them.

**Lightweight Index:**
On activation, read ONLY:
- Read: `.claude/kb/{domain}/index.md` — Scan topic headings
- DO NOT read patterns/* or concepts/* unless task matches

### Agreement Matrix

{Same as _template.md — KB vs MCP matrix}

### Confidence Modifiers

| Modifier | Value | When |
|----------|-------|------|
| Codebase component found | +0.10 | Existing component in project |
| Design system file exists | +0.05 | tailwind.config or tokens file |
| No working examples | -0.05 | Theory only |
| {domain-specific} | {value} | {condition} |

---

## Capabilities

### Capability 1: {Primary}

**When:** {triggers}

**Process:**
1. Read `.claude/kb/{domain}/{file}.md`
2. If found: Apply pattern, calculate confidence
3. If uncertain: Single MCP query (context7)
4. Execute if confidence >= threshold

**Output:** {description}

{Additional capabilities...}

---

## Stop Conditions and Escalation

**Hard Stops:**
- Confidence below 0.40 — STOP
- Detected PII in output — STOP

**Escalation Rules:**
{From frontmatter}

---

## Quality Gate

PRE-FLIGHT CHECK
├── [ ] KB index scanned
├── [ ] Confidence calculated from evidence
├── [ ] Impact tier identified
├── [ ] Threshold met
└── [ ] Sources ready to cite

---

## Anti-Patterns

| Never Do | Why | Instead |
|----------|-----|---------|
| {domain-specific} | {reason} | {correct approach} |

---

## Remember

> **"{motto}"**

**Mission:** {mission}

**Core Principle:** KB first. Confidence always. Ask when uncertain.
```

### Padrão 2: Estrutura de KB Domain

```text
.claude/kb/{domain}/
├── index.md              ← Seguir index.md.template
├── quick-reference.md    ← Seguir quick-reference.md.template
├── concepts/
│   ├── {concept-1}.md    ← Seguir concept.md.template (< 150 linhas)
│   ├── {concept-2}.md
│   └── {concept-3}.md
└── patterns/
    ├── {pattern-1}.md    ← Seguir pattern.md.template (< 200 linhas)
    ├── {pattern-2}.md
    └── {pattern-3}.md
```

### Padrão 3: Entry no `_index.yaml`

```yaml
  react:
    name: react
    description: "React development patterns — hooks, Server Components, state management, composition"
    path: react/
    mcp_validated: "2026-03-29"
    entry_points:
      index: index.md
      quick_reference: quick-reference.md
    concepts:
      - name: hooks-patterns
        path: concepts/hooks-patterns.md
        confidence: 0.90
      - name: server-components
        path: concepts/server-components.md
        confidence: 0.90
      # ...
    patterns:
      - name: component-composition
        path: patterns/component-composition.md
        confidence: 0.90
      # ...
```

### Padrão 4: `frontend_delegation` no WORKFLOW_CONTRACTS

```yaml
  frontend_delegation:
    description: "When DESIGN contains frontend architecture, Build delegates to frontend agents"
    agent_map:
      react_components: "react-developer"
      css_styling: "css-specialist"
      ux_flows: "ux-designer"
      frontend_architecture: "frontend-architect"
      accessibility_audit: "a11y-specialist"
```

---

## Fluxo de Dados

```text
1. /define detecta stack frontend no CLAUDE.md do projeto
   │
   ▼
2. define-agent sugere KB domains: react, nextjs, tailwind-css, etc.
   │
   ▼
3. /design faz glob em .claude/agents/frontend/*.md
   │
   ▼
4. design-agent cria File Manifest com @react-developer, @css-specialist
   │
   ▼
5. /build le manifest → Task(@react-developer, "Criar component.tsx")
   │
   ▼
6. react-developer lê .claude/kb/react/patterns/ → gera código KB-grounded
   │
   ▼
7. build-agent verifica output → BUILD_REPORT com attribution
```

---

## Pontos de Integração

| Sistema Externo | Tipo de Integração | Autenticação |
|----------------|-------------------|--------------|
| MCP context7 | SDK (já configurado) | Nenhuma (local) |
| MCP exa | SDK (já configurado) | API key existente |

---

## Estratégia de Testes

| Tipo de Teste | Escopo | Como Verificar | Meta |
|---------------|--------|----------------|------|
| Structural | Agentes seguem `_template.md` | Verificar frontmatter, seções obrigatórias | 5/5 agentes |
| Structural | KB domains seguem templates | Verificar index.md, quick-ref, concepts/, patterns/ | 6/6 domínios |
| Functional | design-agent matchea agentes frontend | Rodar `/design` com DEFINE de feature frontend | AT-001 |
| Functional | build-agent delega via Task | Rodar `/build` com DESIGN contendo `@react-developer` | AT-002 |
| Functional | KB-First resolution funciona | Verificar que agente lê KB antes de gerar | AT-003 |
| Integration | MCP context7 retorna docs frontend | `/create-kb react` retorna conteúdo válido | A-001 |

---

## Ordem de Build

```text
Fase A — Agentes (sem dependências entre si):
  [1] react-developer.md
  [2] css-specialist.md
  [3] ux-designer.md
  [4] frontend-architect.md
  [5] a11y-specialist.md

Fase B — KB Domains (6 execuções de /create-kb, paralelas):
  [6-15]  react/
  [16-25] nextjs/
  [26-34] tailwind-css/
  [35-42] accessibility/
  [43-50] design-systems/
  [51-58] frontend-patterns/

Fase C — Integrações (dependem de A e B):
  [59] _index.yaml ← registrar 6 domínios
  [60] agents/README.md ← adicionar categoria frontend
  [61] CLAUDE.md ← documentar novos agentes
  [62] WORKFLOW_CONTRACTS.yaml ← frontend_delegation
```

---

## Histórico de Revisões

| Versão | Data | Autor | Mudanças |
|--------|------|-------|----------|
| 1.0 | 2026-03-29 | design-agent | Versão inicial — 62 arquivos, 3 fases de build |

---

## Próximo Passo

**Pronto para:** `/build .claude/sdd/features/DESIGN_FRONTEND_ECOSYSTEM.md`
