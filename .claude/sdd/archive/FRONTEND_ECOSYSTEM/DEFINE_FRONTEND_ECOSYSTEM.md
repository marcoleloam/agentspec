# DEFINE: Frontend Ecosystem

> Criar ecossistema completo de agentes e Knowledge Base para desenvolvimento frontend no AgentSpec, espelhando a arquitetura existente de Data Engineering.

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | FRONTEND_ECOSYSTEM |
| **Data** | 2026-03-29 |
| **Autor** | define-agent |
| **Status** | ✅ Complete (Built) |
| **Clarity Score** | 14/15 |

---

## Declaração do Problema

O AgentSpec SDD possui 58 agentes e 22 KB domains exclusivamente para Data Engineering e backend. Projetos frontend não se beneficiam de agentes especializados durante as fases de Design e Build — os agentes genéricos (`code-reviewer`, `code-cleaner`) existem mas não entendem design systems, component patterns ou convenções de framework. Isso resulta em output genérico que não segue best practices de React/Next.js/Tailwind e impede que o SDD funcione como first-class para projetos frontend.

---

## Usuários-Alvo

| Usuário | Papel | Dor |
|---------|-------|-----|
| Desenvolvedor solo | Cria sites do zero com IA usando AgentSpec | Agentes não entendem RSC, hooks, Tailwind. Output genérico que precisa de revisão manual constante. |
| Usuário do SDD com projeto fullstack | Usa /define, /design, /build para features que têm frontend | O File Manifest no /design não atribui agentes frontend. Build delega para genérico. |
| Contribuidor do AgentSpec | Quer expandir o framework para novos domínios | Não existe modelo de como criar categoria de agentes + KB para domínio não-DE. Frontend seria o primeiro. |

---

## Objetivos

| Prioridade | Objetivo |
|------------|----------|
| **MUST** | Criar 5 agentes frontend em `.claude/agents/frontend/` seguindo `_template.md` (T2) |
| **MUST** | Criar 6 KB domains em `.claude/kb/` seguindo templates existentes: react, nextjs, tailwind-css, accessibility, design-systems, frontend-patterns |
| **MUST** | Registrar os 6 domínios no `_index.yaml` com entry_points, concepts e patterns |
| **MUST** | Agentes devem usar MCP existente (context7 + exa) — zero infra nova |
| **SHOULD** | Atualizar design-agent para detectar stack frontend e matchear agentes no File Manifest |
| **SHOULD** | Atualizar define-agent para stack detection (Next.js/React no CLAUDE.md → sugerir KB domains frontend) |
| **SHOULD** | Atualizar `agents/README.md` com nova categoria frontend e mapa de escalação |
| **SHOULD** | Atualizar `CLAUDE.md` do projeto com novos agentes e comandos |
| **COULD** | Integrar ux-designer nas fases 0-2 do SDD (Brainstorm, Define, Design) como consultor multi-agent |
| **COULD** | Atualizar `WORKFLOW_CONTRACTS.yaml` com `frontend_delegation` no build (paralelo ao `data_engineering_delegation`) |

---

## Critérios de Sucesso

- [ ] 5 agentes criados e funcionais: react-developer, css-specialist, ux-designer, frontend-architect, a11y-specialist
- [ ] 6 KB domains criados com index.md, quick-reference.md, 3+ concepts/, 3+ patterns/ cada
- [ ] `_index.yaml` contém os 6 novos domínios com confidence scores
- [ ] design-agent atribui `@react-developer`, `@css-specialist` etc. no File Manifest ao detectar projeto frontend
- [ ] build-agent delega a agentes frontend via Task quando manifest contém `@frontend-*`
- [ ] Agentes consultam KB-First antes de qualquer decisão (mesmo padrão dos agentes DE)
- [ ] MCP context7 retorna docs de React, Next.js, Tailwind quando consultado pelos agentes

---

## Testes de Aceitação

| ID | Cenário | Dado | Quando | Então |
|----|---------|------|--------|-------|
| AT-001 | Design com projeto Next.js | CLAUDE.md menciona Next.js + React + Tailwind | `/design` roda com DEFINE de feature frontend | File Manifest contém `@react-developer` e `@css-specialist` nos arquivos .tsx |
| AT-002 | Build delega a react-developer | DESIGN tem arquivo .tsx com `@react-developer` | `/build` executa | build-agent delega via Task ao react-developer, que consulta KB react/ antes de gerar |
| AT-003 | KB-First no react-developer | react-developer recebe task para criar componente | Agente inicia execução | Primeiro lê `.claude/kb/react/patterns/component-composition.md`, depois gera código |
| AT-004 | MCP fallback funciona | KB react/ não tem pattern para Server Actions | react-developer precisa do pattern | Consulta context7 para docs oficiais de React Server Actions |
| AT-005 | a11y-specialist no review | Código frontend gerado pelo build | `/review` roda em projeto frontend | a11y-specialist verifica aria labels, contraste, keyboard navigation |

---

## Fora do Escopo

- **Vue, Angular, Svelte** — Escopo inicial é React + Next.js + Tailwind. Outros frameworks podem ser adicionados depois via `/create-kb`.
- **Backend/API agentes** — Já cobertos pelos agentes cloud/ e python/ existentes.
- **FRONTEND_CONVENTIONS.md** — Não será criado. Agentes usam KB genérica + leitura do codebase + CLAUDE.md do projeto (mesmo padrão do lado DE).
- **Agentes de teste E2E** — Playwright/Cypress ficam para uma segunda fase. O `test-generator` existente cobre testes unitários.
- **Design visual/Figma** — O ux-designer foca em user flows e information architecture, não em design visual pixel-perfect.
- **Party Mode / Multi-agent brainstorm** — Feature separada. O COULD de integrar ux-designer nas fases 0-2 é via Task individual, não Party Mode.

---

## Restrições

| Tipo | Restrição | Impacto |
|------|-----------|---------|
| Estrutural | Agentes devem seguir `_template.md` existente (T2 tier) | Garante consistência com os 58 agentes atuais. Sem exceções na estrutura. |
| Estrutural | KB domains devem seguir templates de `.claude/kb/_templates/` | Mesma estrutura: index.md, quick-reference.md, concepts/, patterns/. |
| MCP | Usar context7 e exa existentes — zero MCP novo | Sem custo de infra. context7 já suporta docs React/Next.js/Tailwind. |
| Naming | Agentes em `.claude/agents/frontend/` | Nova categoria paralela a `data-engineering/`, `cloud/`, etc. |
| Compatibilidade | Não quebrar agentes DE existentes | Adição pura — zero edição em agentes de data-engineering/. |

---

## Contexto Técnico

| Aspecto | Valor | Notas |
|---------|-------|-------|
| **Localização de Deploy** | `.claude/agents/frontend/` + `.claude/kb/{6 domains}/` | Nova categoria de agentes + 6 KB domains |
| **Domínios KB** | react, nextjs, tailwind-css, accessibility, design-systems, frontend-patterns | 6 novos domínios, populados via `/create-kb` com MCP context7 |
| **Impacto IaC** | Nenhum | Adição de arquivos markdown apenas. Zero mudança de infra. |

---

## Premissas

| ID | Premissa | Se Errada, Impacto | Validada? |
|----|----------|-------------------|-----------|
| A-001 | MCP context7 retorna docs atualizados de React 19, Next.js 15, Tailwind v4 | KB populada com info desatualizada — agentes geram código com patterns antigos | [ ] |
| A-002 | A estrutura `_template.md` T2 é suficiente para agentes frontend (não precisa T3) | Se frontend precisar de MCP servers dedicados ou Error Recovery, precisa de T3 | [x] |
| A-003 | 5 agentes são suficientes para cobrir o domínio frontend | Se faltarem agentes (ex: testing-specialist frontend), precisa criar mais depois | [x] |
| A-004 | design-agent consegue matchear agentes frontend via glob + keyword sem mudança estrutural | Se o matching for insuficiente, precisa de trigger_keywords no frontmatter | [ ] |

---

## Especificação dos 5 Agentes

| Agente | Tier | Model | KB Domains | MCP | Triggers |
|--------|------|-------|------------|-----|----------|
| `react-developer` | T2 | sonnet | react, nextjs | context7, exa | component, hook, useState, RSC, "use client", render |
| `css-specialist` | T2 | sonnet | tailwind-css, design-systems | context7 | tailwind, css, responsive, animation, dark mode, spacing, design token |
| `ux-designer` | T2 | opus | design-systems, frontend-patterns | exa | user flow, wireframe, UX, usability, navigation, layout, information architecture |
| `frontend-architect` | T2 | opus | nextjs, frontend-patterns | context7, exa | architecture, performance, bundle, SSR, CSR, cache, deploy, monorepo |
| `a11y-specialist` | T2 | sonnet | accessibility | context7 | accessibility, a11y, aria, WCAG, keyboard, screen reader, contrast |

---

## Especificação dos 6 KB Domains

| Domain | Equivalente DE | Concepts (min 3) | Patterns (min 3) |
|--------|---------------|-------------------|-------------------|
| `react/` | spark/ | hooks-patterns, server-components, state-management, rendering-patterns | component-composition, form-handling, data-fetching, testing-components |
| `nextjs/` | dbt/ | app-router, rendering-strategies, caching, middleware | api-routes, auth-patterns, image-optimization, deployment |
| `tailwind-css/` | sql-patterns/ | utility-first, design-tokens, responsive-design | component-styling, dark-mode, animations, cn-utility |
| `accessibility/` | data-quality/ | wcag-guidelines, aria-patterns, keyboard-navigation | form-accessibility, modal-dialog, table-accessibility |
| `design-systems/` | data-modeling/ | token-architecture, component-api, documentation | variant-pattern, shadcn-patterns, theme-switching |
| `frontend-patterns/` | medallion/ | project-structure, error-handling, performance | api-integration, auth-flow, optimistic-updates |

---

## Mapa de Escalação entre Agentes Frontend

```text
react-developer ←→ css-specialist
    ↕                    ↕
frontend-architect   ux-designer
         ↕
    a11y-specialist

Escalações:
  react-developer → css-specialist: "Styling question beyond component logic"
  react-developer → frontend-architect: "Architecture decision needed"
  css-specialist → ux-designer: "UX flow question, not styling"
  frontend-architect → react-developer: "Implementation detail, not architecture"
  a11y-specialist → react-developer: "Need to fix component for a11y compliance"
```

---

## Detalhamento do Clarity Score

| Elemento | Score (0-3) | Notas |
|----------|-------------|-------|
| Problema | 3/3 | Claro: SDD é data-centric, zero suporte frontend, agentes genéricos não entendem o domínio |
| Usuários | 3/3 | Três personas identificadas com dores específicas e mensuráveis |
| Objetivos | 3/3 | MoSCoW completo: 4 MUST, 4 SHOULD, 2 COULD. Cada um acionável. |
| Sucesso | 3/3 | 7 critérios mensuráveis com verificação objetiva |
| Escopo | 2/3 | Fora do escopo claro mas A-001 (docs atualizados no MCP) precisa validação |
| **Total** | **14/15** | |

---

## Questões em Aberto

1. **A-001 não validada:** Confirmar que MCP context7 retorna docs de React 19, Next.js 15 e Tailwind v4 (não versões antigas). Validar rodando `/create-kb react` e verificando output.
2. **A-004 não validada:** Testar se o design-agent consegue matchear agentes frontend via glob + keyword matching existente ou se precisa de campo `trigger_keywords` no frontmatter do `_template.md`.

---

## Histórico de Revisões

| Versão | Data | Autor | Mudanças |
|--------|------|-------|----------|
| 1.0 | 2026-03-29 | define-agent | Versão inicial — baseada em brainstorm informal + análise BMAD vs SDD + simulação single vs multi-agent |

---

## Próximo Passo

**Pronto para:** `/design .claude/sdd/features/DEFINE_FRONTEND_ECOSYSTEM.md`
