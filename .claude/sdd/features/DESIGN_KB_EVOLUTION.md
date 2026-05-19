# DESIGN: KB Evolution -- Ingest/Lint para KBs Vivos

> Design tecnico para implementar dois comandos (`/ingest-kb` e `/lint-kb`) que mantem os 39 KB domains do AgentSpec atualizados via Context7 MCP e reescrita por LLM, com auditoria periodica de qualidade.

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | KB_EVOLUTION |
| **Data** | 2026-04-22 |
| **Autor** | design-agent |
| **DEFINE** | [DEFINE_KB_EVOLUTION.md](./DEFINE_KB_EVOLUTION.md) |
| **Status** | ✅ Complete (Built) |

---

## Visao Geral da Arquitetura

```text
┌──────────────────────────────────────────────────────────────────────────┐
│                    KB EVOLUTION -- VISAO DO SISTEMA                      │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  COMANDOS (entry points)                                                │
│  ┌──────────────┐    ┌──────────────┐                                   │
│  │ /ingest-kb   │    │ /lint-kb     │                                   │
│  │  <domain>    │    │  <domain>    │                                   │
│  └──────┬───────┘    │  --all       │                                   │
│         │            └──────┬───────┘                                   │
│         ▼                   ▼                                           │
│  ┌─────────────────────────────────────┐                                │
│  │     kb-evolution-agent              │  Orquestra ambos os fluxos     │
│  │     (novo agent em agents/dev/)     │                                │
│  └──────┬──────────────┬───────────────┘                                │
│         │              │                                                │
│    INGEST FLOW    LINT FLOW                                             │
│         │              │                                                │
│         ▼              ▼                                                │
│  ┌─────────────┐  ┌─────────────┐                                      │
│  │ Context7    │  │ Comparacao  │                                       │
│  │ MCP Tools   │  │ KB vs Docs  │                                       │
│  │ resolve-id  │  │ Oficiais    │                                       │
│  │ query-docs  │  └──────┬──────┘                                      │
│  └──────┬──────┘         │                                              │
│         │                ▼                                              │
│         ▼         ┌─────────────┐                                      │
│  ┌─────────────┐  │ LINT REPORT │                                      │
│  │ LLM Rewrite │  │ .md gerado  │                                      │
│  │ ficheiro a  │  │ em sdd/     │                                      │
│  │ ficheiro    │  │ reports/    │                                       │
│  └──────┬──────┘  └─────────────┘                                      │
│         │                                                               │
│         ▼                                                               │
│  ┌──────────────────────────────┐                                      │
│  │  ATUALIZACOES                │                                       │
│  │  .claude/kb/{domain}/*.md   │  Ficheiros KB reescritos              │
│  │  .claude/kb/{domain}/log.md │  Historico de operacoes               │
│  │  .claude/kb/_index.yaml     │  mcp_validated atualizado             │
│  └──────────────────────────────┘                                      │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Componentes

| Componente | Proposito | Tecnologia |
|------------|-----------|------------|
| `/ingest-kb` command | Entry point para atualizacao de um KB domain via Context7 | Markdown command file (`.claude/commands/knowledge/ingest-kb.md`) |
| `/lint-kb` command | Entry point para auditoria de qualidade de um ou todos os KB domains | Markdown command file (`.claude/commands/knowledge/lint-kb.md`) |
| `kb-evolution-agent` | Orquestra os fluxos de ingest e lint; toma decisoes de rewrite | Agent prompt (`.claude/agents/dev/kb-evolution-agent.md`) |
| Context7 MCP | Fonte de documentacao oficial atualizada | MCP tools: `resolve-library-id`, `query-docs` |
| `log.md` por dominio | Historico imutavel de operacoes (append-only) | Markdown file em `.claude/kb/{domain}/log.md` |
| `_index.yaml` | Registo central de dominios com `mcp_validated` e `last_lint` | YAML existente em `.claude/kb/_index.yaml` |
| Lint report | Relatorio consolidado de auditoria | Markdown file em `.claude/sdd/reports/` |

---

## Decisoes Principais

### Decisao 1: Novo Agent Dedicado vs Extensao do kb-architect

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-04-22 |

**Contexto:** O `kb-architect` existente cria novos KBs e audita estrutura. O ingest/lint e um fluxo diferente: atualizar conteudo existente com dados do Context7, comparar versoes, reescrever seletivamente. Misturar estas responsabilidades num unico agent aumentaria a complexidade do prompt e diluiria a especializacao.

**Escolha:** Criar novo agent `kb-evolution-agent` em `.claude/agents/dev/` dedicado a ingest e lint.

**Justificativa:**
- Separacao de responsabilidades: `kb-architect` cria, `kb-evolution-agent` atualiza e audita conteudo
- O prompt do `kb-evolution-agent` pode ser otimizado para o fluxo Context7 -> compare -> rewrite sem carregar a logica de criacao from scratch
- Tier T2 com model `sonnet` -- suficiente para rewrite de conteudo tecnico

**Alternativas Rejeitadas:**
1. Estender `kb-architect` com Capability 4/5 -- Rejeitada porque o prompt ficaria >400 linhas e diluiria as capabilities existentes
2. Sem agent (logica inline nos commands) -- Rejeitada porque os commands devem ser simples entry points que delegam para agents

**Consequencias:**
- Mais um agent no inventario (passa de 72 para 73)
- Clara separacao: criacao vs evolucao de KBs

---

### Decisao 2: Formato do Lint Report -- Markdown Estruturado

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-04-22 |

**Contexto:** O DEFINE deixou o formato do relatorio de lint como decisao de Design. As opcoes eram Markdown estruturado, YAML ou JSON.

**Escolha:** Markdown estruturado com tabelas, salvo em `.claude/sdd/reports/LINT_KB_{DOMAIN}_{DATE}.md` (dominio unico) ou `.claude/sdd/reports/LINT_KB_ALL_{DATE}.md` (consolidado).

**Justificativa:**
- Consistente com todos os outros artefatos do SDD (BRAINSTORM, DEFINE, DESIGN, BUILD_REPORT sao todos .md)
- Legivel diretamente no editor e em PRs do GitHub
- Estruturado o suficiente para ser parseavel por outros agents se necessario

**Alternativas Rejeitadas:**
1. YAML -- Rejeitada porque nao e legivel para o maintainer sem tooling
2. JSON -- Rejeitada pelo mesmo motivo e porque nao e o padrao do projeto

**Consequencias:**
- Relatorios sao legíveis e versionaveis
- Nao e machine-parseable de forma nativa (aceitavel para MVP)

---

### Decisao 3: log.md Dentro de Cada Dominio KB

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-04-22 |

**Contexto:** O `log.md` precisa registar o historico de operacoes (ingest e lint) para cada dominio. Podia ser centralizado num unico ficheiro ou distribuido.

**Escolha:** Um `log.md` por dominio em `.claude/kb/{domain}/log.md`, formato append-only com entries mais recentes no topo.

**Justificativa:**
- Colocalizado com o conteudo que documenta -- quem le o KB ve o log
- Evita ficheiro central que cresceria para centenas de entries (39 dominios x N operacoes)
- Consistente com o principio "self-contained" de cada KB domain

**Alternativas Rejeitadas:**
1. Ficheiro central `.claude/kb/evolution-log.md` -- Rejeitada porque ficaria enorme e dificil de navegar
2. Entradas no `_index.yaml` -- Rejeitada porque poluiria o manifesto com dados operacionais

**Consequencias:**
- Cada dominio tem o seu historico independente
- O `log.md` deve ser excluido dos limites de linhas do KB (nao e conteudo de conhecimento)

---

### Decisao 4: Estrategia de Rewrite -- Ficheiro a Ficheiro com Diff Semantico

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-04-22 |

**Contexto:** O ingest precisa decidir quais ficheiros atualizar. Reescrever todos os ficheiros a cada ingest e desperdicio de tokens e risco de regressao. Nao reescrever nenhum sem detecao de mudanca e inutil.

**Escolha:** Para cada ficheiro do dominio, o agent: (1) le o conteudo atual, (2) consulta Context7 para o topico desse ficheiro, (3) compara semanticamente se ha informacao nova/alterada, (4) so reescreve se detetou mudanca relevante.

**Justificativa:**
- Reduz custo de tokens (estimativa: ~30K em vez de ~50K quando <50% dos ficheiros mudaram)
- Preserva conteudo curado manualmente que nao precisa de update
- Atende ao AT-005 (idempotencia)

**Alternativas Rejeitadas:**
1. Rewrite completo sempre -- Rejeitada porque desperdiça tokens e pode degradar conteudo curado manualmente
2. Comparacao textual (diff literal) -- Rejeitada porque docs do Context7 tem formato diferente dos KBs, diff literal produziria falsos positivos

**Consequencias:**
- O agent precisa de capacidade de julgamento semantico (comparar conceitos, nao texto)
- Aceita-se que em ~5% dos casos o agent pode nao detetar mudanca relevante (falso negativo aceitavel)

---

### Decisao 5: Fallback Gracioso para Dominios sem Cobertura Context7

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-04-22 |

**Contexto:** Nem todos os 39 dominios mapeiam para uma library no Context7. Dominios como `medallion`, `data-modeling`, `sql-patterns` sao conceptuais e nao tem library-id.

**Escolha:** O agent usa `resolve-library-id` como primeiro passo. Se nao encontrar match, informa o usuario com mensagem explicita e registra no `log.md` como `"status": "skipped - no Context7 coverage"`. Nao altera ficheiros. Sugere alternativa (web search manual ou `/create-kb --audit`).

**Justificativa:**
- Atende AT-002 (fallback gracioso)
- Sem falha silenciosa -- o usuario sabe exatamente o que aconteceu
- Preserva integridade dos KBs sem cobertura

**Alternativas Rejeitadas:**
1. Falhar com erro -- Rejeitada porque a ausencia de cobertura e esperada, nao e um erro
2. Tentar web search automaticamente -- Rejeitada porque introduziria dependencia de resultados imprevisiveis e esta fora do escopo (Out of Scope no DEFINE)

**Consequencias:**
- Alguns dominios nunca serao atualizados via `/ingest-kb` (aceitavel, sao dominios conceptuais estaveis)
- O lint report pode ser usado para esses dominios como alternativa

---

### Decisao 6: Campo `last_lint` no `_index.yaml`

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-04-22 |

**Contexto:** O DEFINE requer que `mcp_validated` seja atualizado apos ingest. Para o lint, tambem e util ter um timestamp da ultima auditoria.

**Escolha:** Adicionar campo opcional `last_lint` ao schema de cada dominio no `_index.yaml`. Campo e aditivo (backwards compatible). Formato: `'YYYY-MM-DD'`.

**Justificativa:**
- Permite ao COULD dashboard mostrar freshness de lint alem de ingest
- Aditivo -- nao quebra nenhum consumer existente do `_index.yaml`

**Alternativas Rejeitadas:**
1. Usar apenas `log.md` para rastrear lint -- Rejeitada porque obriga a parsear ficheiro markdown para obter a data
2. Nao rastrear lint timestamp -- Rejeitada porque o `/lint-kb --all` precisa saber quais dominios foram auditados recentemente

**Consequencias:**
- Schema do `_index.yaml` ganha um campo opcional
- Todos os consumers existentes continuam a funcionar (campo e opcional)

---

## Manifesto de Arquivos

| # | Arquivo | Acao | Proposito | Agente | Dependencias |
|---|---------|------|-----------|--------|--------------|
| 1 | `.claude/agents/dev/kb-evolution-agent.md` | Criar | Agent especializado em ingest e lint de KB domains via Context7 | @prompt-crafter | Nenhuma |
| 2 | `.claude/commands/knowledge/ingest-kb.md` | Criar | Comando `/ingest-kb <domain>` -- entry point para atualizacao | @kb-evolution-agent | 1 |
| 3 | `.claude/commands/knowledge/lint-kb.md` | Criar | Comando `/lint-kb <domain>` e `/lint-kb --all` -- entry point para auditoria | @kb-evolution-agent | 1 |
| 4 | `.claude/kb/_index.yaml` | Modificar | Adicionar campo `last_lint` ao schema; atualizado automaticamente pelo agent | (direto) | Nenhuma |
| 5 | `.claude/agents/architect/kb-architect.md` | Modificar | Adicionar referencia cruzada ao `kb-evolution-agent` na secao de escalation | (direto) | 1 |
| 6 | `CLAUDE.md` | Modificar | Registrar novos comandos `/ingest-kb` e `/lint-kb` na tabela de Knowledge commands; incrementar contagem de agents | (direto) | 1, 2, 3 |

**Total de Arquivos:** 6 (3 criar + 3 modificar)

**Nota sobre `log.md` e lint reports:** Nao constam no manifesto porque sao gerados em runtime pelo agent durante execucao dos comandos, nao durante o Build.

---

## Justificativa de Atribuicao de Agentes

> Agentes descobertos em `.claude/agents/` -- a fase de Build invoca os especialistas correspondentes.

| Agente | Arquivos Atribuidos | Por Que Este Agente |
|--------|---------------------|---------------------|
| @prompt-crafter | 1 | Especialista em construcao de prompts de agent com SDD-lite; o `kb-evolution-agent` e essencialmente um prompt de agent complexo com fluxo multi-step |
| @kb-evolution-agent | 2, 3 | Apos criado (arquivo 1), o proprio agent pode validar a estrutura dos commands que o invocam |
| (direto) | 4, 5, 6 | Modificacoes pontuais em ficheiros existentes (YAML edit, cross-reference, tabela markdown) -- nao justificam especialista |

**Descoberta de Agentes:**
- Escaneado: `.claude/agents/**/*.md` (72 agents encontrados)
- Correspondido por: Tipo de arquivo (`.md` agent prompt), palavras-chave de proposito ("prompt", "KB", "knowledge"), dominios KB (`prompt-engineering`)

---

## Padroes de Codigo

### Padrao 1: Estrutura do Command File (ingest-kb)

```markdown
---
name: ingest-kb
description: Update a KB domain with latest docs from Context7 MCP
---

# Ingest KB Command

> Atualiza um KB domain com documentacao oficial mais recente via Context7.

## Usage

\`\`\`
/ingest-kb <DOMAIN>
\`\`\`

**Examples**: `/ingest-kb dbt`, `/ingest-kb react`, `/ingest-kb airflow`

## What Happens

1. **Validates domain** -- checks domain exists in `_index.yaml`
2. **Resolves Context7 library** -- calls `resolve-library-id` for the domain
3. **Invokes kb-evolution-agent** -- executes full ingest workflow
4. **Reports completion** -- shows files updated, log entry, mcp_validated date

## Fallback

If Context7 has no coverage for the domain, the command:
- Notifies the user with a clear message
- Suggests alternatives: `/lint-kb <domain>` or manual update
- Logs the attempt in `log.md`

## See Also

- **Agent**: `.claude/agents/dev/kb-evolution-agent.md`
- **Lint**: `/lint-kb` for quality auditing
- **Create**: `/create-kb` for new domains from scratch
```

### Padrao 2: Estrutura do Command File (lint-kb)

```markdown
---
name: lint-kb
description: Audit KB domain quality — stale content, contradictions, gaps
---

# Lint KB Command

> Audita a qualidade de um ou todos os KB domains.

## Usage

\`\`\`
/lint-kb <DOMAIN>
/lint-kb --all
\`\`\`

**Examples**: `/lint-kb dbt`, `/lint-kb spark`, `/lint-kb --all`

## What Happens

### Single Domain
1. **Reads domain files** -- all concepts, patterns, index, quick-reference
2. **Invokes kb-evolution-agent** -- executes lint workflow
3. **Generates report** -- saved to `.claude/sdd/reports/LINT_KB_{DOMAIN}_{DATE}.md`
4. **Updates _index.yaml** -- sets `last_lint` date

### All Domains (--all)
1. **Iterates all 39 domains** from `_index.yaml`
2. **Runs lint for each** -- same checks as single domain
3. **Generates consolidated report** -- `.claude/sdd/reports/LINT_KB_ALL_{DATE}.md`
4. **Ranks by severity** -- domains with most/critical issues first

## Issue Categories

| Category | Severity | Description |
|----------|----------|-------------|
| Stale Content | HIGH | APIs deprecated, syntax changed, versions outdated |
| Contradictions | HIGH | Conflicting info between files in same domain |
| Gaps | MEDIUM | Topics missing that official docs cover |
| Format Issues | LOW | Line limits exceeded, missing headers, broken links |

## See Also

- **Agent**: `.claude/agents/dev/kb-evolution-agent.md`
- **Ingest**: `/ingest-kb` for updating content
- **Create**: `/create-kb` for new domains
```

### Padrao 3: Estrutura do Agent Prompt (kb-evolution-agent)

```markdown
---
name: kb-evolution-agent
description: |
  KB evolution specialist for ingesting updates from Context7 MCP and
  auditing quality of existing KB domains. Handles both /ingest-kb and
  /lint-kb workflows.

  <example>
  Context: User wants to update a KB domain
  user: "/ingest-kb dbt"
  assistant: "I'll use the kb-evolution-agent to fetch latest dbt docs
  from Context7 and update the KB."
  </example>

  <example>
  Context: User wants to audit KB quality
  user: "/lint-kb spark"
  assistant: "I'll use the kb-evolution-agent to audit the spark KB domain."
  </example>

tools: [Read, Write, Edit, Grep, Glob, Bash, TodoWrite]
tier: T2
kb_domains: [prompt-engineering, genai]
anti_pattern_refs: [shared-anti-patterns]
color: green
model: sonnet
stop_conditions:
  - "Domain not found in _index.yaml -- inform user"
  - "Context7 has no coverage for domain -- log and inform user"
escalation_rules:
  - trigger: "Need to create a new KB domain from scratch"
    target: "kb-architect"
    reason: "kb-evolution-agent updates existing KBs, not creates new ones"
---

# KB Evolution Agent

> **Identity:** KB evolution specialist for content freshness and quality
> **Domain:** KB ingestion via Context7, quality auditing, change tracking
> **Threshold:** 0.90 (KB content accuracy is critical)

## Capabilities

### Capability 1: Ingest KB Domain

**Triggers:** `/ingest-kb <domain>` command

**Process:**

1. Read `_index.yaml`, validate domain exists
2. Call `resolve-library-id` with domain name
   - If no match → log "skipped", notify user, STOP
3. Call `query-docs` with library-id for each topic area
4. For each file in domain (concepts/*.md, patterns/*.md,
   index.md, quick-reference.md):
   a. Read current file content
   b. Query Context7 for the specific topic
   c. Compare semantically: new APIs? deprecated patterns?
      version changes?
   d. If changes detected → rewrite preserving format and
      headers from _templates/
   e. If no changes → skip, log "no changes for {file}"
5. Update `mcp_validated` in `_index.yaml` to today's date
6. Append entry to `.claude/kb/{domain}/log.md`

### Capability 2: Lint KB Domain

**Triggers:** `/lint-kb <domain>` or `/lint-kb --all`

**Process:**

1. Read all files in domain
2. Check for 4 issue categories:
   - **Stale**: deprecated APIs, old version references,
     outdated syntax
   - **Contradictions**: conflicting info across files
   - **Gaps**: topics in official docs not covered in KB
   - **Format**: line limits, missing headers, broken links
3. Generate structured markdown report
4. Update `last_lint` in `_index.yaml`

## Quality Gate

Before completing ingest:
- [ ] All rewritten files preserve original structure
- [ ] No files deleted without user confirmation
- [ ] log.md updated with operation details
- [ ] _index.yaml mcp_validated updated
- [ ] File line limits respected (concept: 150, pattern: 200)
```

### Padrao 4: Formato do log.md

```markdown
# {Domain} KB Evolution Log

> Historico de operacoes de ingest e lint para este dominio.
> Entries mais recentes no topo.

---

## 2026-04-22 | ingest | dbt

- **Status:** success
- **Context7 Library:** /dbt-labs/dbt-core
- **Detected Version:** dbt Core v1.10
- **Files Updated:** 3/12
  - `concepts/fusion-engine.md` -- novo campo batch_size documentado
  - `patterns/incremental-model.md` -- micro-batch strategy atualizada
  - `quick-reference.md` -- tabela de versoes atualizada
- **Files Unchanged:** 9/12
- **Token Cost:** ~28K tokens

---

## 2026-04-20 | lint | dbt

- **Status:** completed
- **Issues Found:** 2
  - [HIGH] `patterns/snapshot-scd2.md` -- referencia dbt 1.7 syntax
    deprecada
  - [MEDIUM] Gap: missing coverage for `unit tests` (introduced in
    dbt 1.8)
- **Report:** `.claude/sdd/reports/LINT_KB_DBT_2026-04-20.md`
```

### Padrao 5: Formato do Lint Report

```markdown
# Lint Report: {DOMAIN} | {DATE}

> Auditoria de qualidade do KB domain `{domain}`.

## Resumo

| Metrica | Valor |
|---------|-------|
| **Dominio** | {domain} |
| **Data** | {YYYY-MM-DD} |
| **Total Issues** | {N} |
| **Severity Breakdown** | HIGH: {n}, MEDIUM: {n}, LOW: {n} |

## Issues Encontradas

### HIGH

| # | Ficheiro | Tipo | Descricao |
|---|---------|------|-----------|
| 1 | `patterns/snapshot-scd2.md` | Stale | Referencia dbt 1.7 syntax |

### MEDIUM

| # | Ficheiro | Tipo | Descricao |
|---|---------|------|-----------|
| 1 | (gap) | Gap | Unit tests nao cobertos |

### LOW

| # | Ficheiro | Tipo | Descricao |
|---|---------|------|-----------|

## Recomendacoes

1. Executar `/ingest-kb {domain}` para resolver issues HIGH de stale
2. Adicionar cobertura manual para gaps identificados
```

### Padrao 6: Schema Update no `_index.yaml`

```yaml
# Campo adicionado por dominio (aditivo, backwards compatible)
domains:
  dbt:
    name: dbt
    # ... campos existentes preservados ...
    mcp_validated: '2026-04-22'   # atualizado por /ingest-kb
    last_lint: '2026-04-22'       # NOVO -- atualizado por /lint-kb
```

---

## Fluxo de Dados

### Fluxo de Ingest

```text
1. Usuario invoca `/ingest-kb dbt`
   │
   ▼
2. Command valida dominio no _index.yaml
   │
   ▼
3. Agent chama `resolve-library-id` com "dbt"
   │
   ├─ Sem match → Log "skipped", notifica usuario, FIM
   │
   ▼
4. Agent itera ficheiros do dominio (concepts/, patterns/, index, quick-ref)
   │
   ▼
5. Para cada ficheiro:
   │
   ├─ Read conteudo atual
   ├─ Query Context7 para topico especifico (`query-docs`)
   ├─ Compara semanticamente (LLM judgment)
   │
   ├─ Sem mudanca → Skip, log "no changes for {file}"
   │
   ▼
6. Reescreve ficheiro preservando formato (_templates/)
   │
   ▼
7. Atualiza _index.yaml (mcp_validated = today)
   │
   ▼
8. Append entry no log.md do dominio
   │
   ▼
9. Reporta ao usuario: N ficheiros atualizados, N sem mudanca
```

### Fluxo de Lint

```text
1. Usuario invoca `/lint-kb dbt` ou `/lint-kb --all`
   │
   ▼
2. Command valida dominio(s) no _index.yaml
   │
   ▼
3. Agent le todos os ficheiros do dominio
   │
   ▼
4. Verifica 4 categorias de issues:
   │
   ├─ STALE: APIs deprecadas, versoes desatualizadas
   ├─ CONTRADICTIONS: info conflitante entre ficheiros
   ├─ GAPS: topicos oficiais nao cobertos
   └─ FORMAT: limites de linhas, headers, links
   │
   ▼
5. Gera relatorio .md em .claude/sdd/reports/
   │
   ▼
6. Atualiza _index.yaml (last_lint = today)
   │
   ▼
7. Append entry no log.md do dominio
   │
   ▼
8. Se --all: consolida relatorios com ranking por severidade
```

---

## Pontos de Integracao

| Sistema Externo | Tipo de Integracao | Autenticacao |
|----------------|-------------------|--------------|
| Context7 MCP | MCP tools (`resolve-library-id`, `query-docs`) | Nenhuma (MCP ja configurado no ambiente) |
| `_index.yaml` | Leitura/escrita via Read/Edit tools | N/A (ficheiro local) |
| KB files (`.claude/kb/`) | Leitura/escrita via Read/Write/Edit tools | N/A (ficheiros locais) |

---

## Estrategia de Testes

Os testes sao os proprios Acceptance Tests do DEFINE, validados manualmente durante o Build.

| ID | Cenario | Validacao | Mapeamento DEFINE |
|----|---------|-----------|-------------------|
| AT-001 | Ingest com sucesso via Context7 | Executar `/ingest-kb dbt`, verificar: KB atualizado, `log.md` criado, `mcp_validated` atualizado | MUST 1, 3, 4 |
| AT-002 | Dominio sem cobertura Context7 | Executar `/ingest-kb medallion`, verificar: mensagem de fallback, ficheiros intactos | MUST 1 (fallback) |
| AT-003 | Lint deteta conteudo stale | Executar `/lint-kb` num dominio com conteudo desatualizado, verificar: relatorio com issue HIGH | MUST 2 |
| AT-004 | Lint all consolidado | Executar `/lint-kb --all`, verificar: relatorio com ranking de todos os dominios | SHOULD 5 |
| AT-005 | Idempotencia do ingest | Executar `/ingest-kb` duas vezes seguidas, verificar: segunda execucao registra "no changes" | MUST 1 (idempotencia) |
| AT-006 | Preservacao de formato | Apos ingest, verificar: estrutura dirs preservada, nenhum ficheiro removido | MUST 1 (formato) |

---

## Tratamento de Erros

| Tipo de Erro | Estrategia de Tratamento | Retry? |
|-------------|-------------------------|--------|
| Dominio nao encontrado no `_index.yaml` | Mensagem clara: "Domain '{domain}' not found. Run `/create-kb {domain}` first." | Nao |
| `resolve-library-id` sem match | Log no `log.md` como "skipped", notifica usuario com alternativas | Nao |
| `query-docs` retorna vazio | Trata como "no changes detected" para o topico especifico; continua com proximos ficheiros | Nao |
| Context7 MCP indisponivel (timeout) | Mensagem de erro com sugestao de retry manual | Sim (manual) |
| Ficheiro KB com formato inesperado | Agent preserva ficheiro original, loga warning, continua com proximos | Nao |
| `_index.yaml` parse error | Aborta operacao, notifica usuario para verificar YAML syntax | Nao |
| Write/Edit falha (permissoes) | Aborta com mensagem de erro de filesystem | Nao |

---

## Configuracao

Nao ha ficheiro de configuracao dedicado. Os parametros operacionais estao embebidos nos prompts dos commands e do agent:

| Parametro | Localização | Valor | Descricao |
|-----------|-------------|-------|-----------|
| Line limits (concept) | `_index.yaml` > `limits.concept` | 150 | Limite maximo de linhas por concept file |
| Line limits (pattern) | `_index.yaml` > `limits.pattern` | 200 | Limite maximo de linhas por pattern file |
| Line limits (quick-ref) | `_index.yaml` > `limits.quick_reference` | 100 | Limite maximo de linhas por quick-reference |
| Issue severities | `lint-kb.md` command | HIGH, MEDIUM, LOW | Categorias de severidade do lint |
| Lint categories | `kb-evolution-agent.md` | Stale, Contradictions, Gaps, Format | Tipos de issues verificados no lint |

---

## Consideracoes de Seguranca

- **Sem dados sensiveis:** Todos os ficheiros sao markdown publico de documentacao tecnica; nao ha credenciais, tokens ou PII
- **Sem dependencias externas novas:** Apenas Context7 MCP (ja presente e configurado)
- **Sem operacoes destrutivas:** O agent nunca remove ficheiros sem confirmacao explicita do usuario; reescrita preserva formato
- **log.md e append-only:** Historico de operacoes nao pode ser editado retroativamente pelo agent (apenas append)

---

## Observabilidade

| Aspecto | Implementacao |
|---------|---------------|
| **Logging** | `log.md` por dominio em `.claude/kb/{domain}/log.md` -- append-only, formato estruturado com timestamp, status, ficheiros afetados e token cost estimado |
| **Auditoria** | Lint reports em `.claude/sdd/reports/LINT_KB_*.md` -- historico de auditorias com issues categorizadas por severidade |
| **Freshness Tracking** | `mcp_validated` e `last_lint` no `_index.yaml` -- data da ultima operacao bem-sucedida por dominio |
| **Dashboard (COULD)** | Se implementado, o agent pode gerar sumario textual a partir dos campos `mcp_validated` e `last_lint` de todos os dominios no `_index.yaml` |

---

## Historico de Revisoes

| Versao | Data | Autor | Mudancas |
|--------|------|-------|----------|
| 1.0 | 2026-04-22 | design-agent | Versao inicial -- 6 arquivos, 6 decisoes, fluxos de ingest e lint |

---

## Proximo Passo

**Pronto para:** `/ship .claude/sdd/features/DEFINE_KB_EVOLUTION.md`
