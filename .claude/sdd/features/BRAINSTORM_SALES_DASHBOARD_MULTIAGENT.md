# BRAINSTORM: Sales Dashboard Real-Time (Multi-Agent)

> Sessao exploratoria para dashboard de vendas real-time com Next.js + Kafka

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | SALES_DASHBOARD |
| **Data** | 2026-03-29 |
| **Autor** | brainstorm-multiagent |
| **Status** | Pronto para Define |
| **Modo** | Multi-agent (Rodada B do teste comparativo) |

---

## Ideia Inicial

**Entrada Bruta:** "Quero construir um dashboard de vendas real-time com Next.js consumindo dados de um pipeline Kafka"

**Contexto Coletado:**
- Projeto end-to-end: pipeline Kafka + processamento + dashboard
- Dois publicos: operacional (real-time) e analytics (historico/gestao)
- Volume alto: 100K+ eventos de vendas por dia
- Latencia aceitavel: near real-time (5-30 segundos)
- Stack frontend: Next.js

**Contexto Tecnico Observado (para o Define):**

| Aspecto | Observacao | Implicacao |
|---------|------------|------------|
| Localizacao Provavel | Monorepo: `pipeline/` + `dashboard/` | Dois modulos separados |
| Dominios KB Relevantes | streaming, react, nextjs, frontend-patterns, sql-patterns | Cross-domain: DE + frontend (5 dominios) |
| Padroes IaC | A definir | Docker Compose para dev, cloud para prod |

---

## Perguntas de Descoberta e Respostas

| # | Pergunta | Resposta | Impacto |
|---|----------|----------|---------|
| 1 | Qual o objetivo principal do dashboard? | Ambos: monitoramento operacional + analytics para gestao | Precisa de dois modos de visualizacao, dois perfis de dados |
| 2 | Qual o volume estimado de eventos? | Alto (100K+ eventos/dia) | Precisa de agregacao pre-computada, cache layer, nao pode fazer queries direto no raw |
| 3 | O pipeline Kafka ja existe? | Nao, precisa construir tudo | Escopo end-to-end: producers + Kafka + consumers + processamento + dashboard |
| 4 | Qual latencia aceitavel? | Near real-time (5-30s) | SSE viavel. Nao precisa de WebSocket. Polling tambem funciona mas SSE e melhor UX |
| 5 | Tem dados de exemplo? | Nao, nenhum | Vamos definir schema no Define |

---

## Inventario de Dados de Exemplo

| Tipo | Localizacao | Quantidade | Notas |
|------|-------------|------------|-------|
| Arquivos de entrada | N/A | 0 | Schema de eventos a definir no /define |
| Exemplos de saida | N/A | 0 | Mockup do dashboard a criar |
| Ground truth | N/A | 0 | Nenhum dado verificado |
| Codigo relacionado | N/A | 0 | Projeto do zero |

---

## Deteccao de Dominios

**Keywords detectados:** Kafka, streaming, real-time, Next.js, dashboard, SSE, Redis, Postgres, agregacao, 100K eventos

**Dominios KB matched (5):**

| # | Dominio | Match Keywords |
|---|---------|---------------|
| 1 | `streaming` | Kafka, real-time, streaming |
| 2 | `nextjs` | Next.js, SSE, dashboard |
| 3 | `react` | Dashboard components, state |
| 4 | `frontend-patterns` | API integration, performance |
| 5 | `sql-patterns` | Postgres, agregacao |

**Resultado:** 5 dominios >= 3 — Multi-agent confirmado.

---

## Consulta Multi-Agente

### Especialistas Consultados

| Agente | kb_domains | Confidence | Veredicto |
|--------|-----------|------------|-----------|
| `@streaming-engineer` | streaming, spark, sql-patterns | 0.88 | Flink SQL com dual-path: janela curta → Redis, janela longa → Postgres. Schema Registry + Avro desde o dia 1 |
| `@spark-streaming-architect` | spark, streaming, lakehouse | 0.90 | Spark SS e superdimensionado (~1-2 evt/s); Flink SQL ou consumer Python simples |
| `@frontend-architect` | nextjs, frontend-patterns | 0.82 | Dual-mode App Router: Client Components (ops) + RSC/ISR/PPR (analytics). SSE exige Node.js custom, nao serverless |
| `@react-developer` | react, nextjs | 0.88 | Zustand + useSSEStream hook para real-time; RSC + Suspense para analytics. Dynamic imports para charting |

### Pontos de Concordancia

- **Flink SQL > Spark SS** — Ambos streaming specialists concordam que 100K eventos/dia (~1-2 evt/s) nao justifica o overhead de um cluster Spark
- **Dual-mode architecture** — Ambos frontend specialists recomendam separar ops (Client Components + SSE) de analytics (Server Components + ISR/PPR)
- **SSE > WebSocket** — Todos concordam: dados unidirecionais, SSE mais simples e suficiente
- **Agregacao pre-computada obrigatoria** — Nenhum especialista recomenda queries direto no raw

### Pontos de Conflito

| Tema | Posicao A | Posicao B |
|------|-----------|-----------|
| Processador streaming | `@streaming-engineer`: Flink SQL obrigatorio para flexibilidade | `@spark-streaming-architect`: Consumer Python simples pode bastar se ETL for trivial |
| Confianca no SSE com Next.js | `@react-developer` (0.88): Padrao bem estabelecido | `@frontend-architect` (0.82): SSE nao e cidadao de primeira classe no Next.js, risco alto em serverless |

### Bloqueios Detectados

| Bloqueio | Especialista | Severidade | Mitigacao |
|----------|-------------|------------|-----------|
| SSE incompativel com serverless (Vercel timeout) | `@frontend-architect` | **Alto** | Custom Node.js server ou Edge Runtime com cuidado |
| Schema evolution sem Schema Registry | `@streaming-engineer` | **Alto** | Avro + Schema Registry desde o dia 1 |
| DLQ ausente derruba pipeline inteiro | `@streaming-engineer` | **Alto** | DLQ obrigatoria desde o dia 1 |
| State TTL nao configurado no Flink | `@spark-streaming-architect` | **Alto** | Watermarks + TTL obrigatorio |
| Memory leak com EventSource no React | `@react-developer` | **Medio** | Cleanup no useEffect + backoff exponencial |
| Bundle bloat com charting libs (~300KB) | `@react-developer` + `@frontend-architect` | **Medio** | Dynamic imports com `next/dynamic` |

---

## Abordagens Exploradas

### Abordagem A: Flink SQL + Redis/Postgres + Next.js Dual-Mode ⭐ Recomendada

**Base:** Combinacao de `@streaming-engineer` + `@frontend-architect` + `@react-developer`

**Descricao:** Kafka recebe eventos com Schema Registry (Avro). Flink SQL agrega em duas janelas: TUMBLE 10s → Redis (operacional) e TUMBLE 1h → Postgres (analytics). DLQ desde o dia 1. Next.js App Router com duas arvores de rota (`/ops` e `/analytics`). Rota ops: Client Components + Zustand + hook `useSSEStream` consumindo Route Handler `/api/events/stream`. Rota analytics: Server Components + ISR/PPR + Suspense boundaries por widget. Deploy em Node.js custom server (nao serverless).

**Pros:**
- Flink SQL e o processador ideal para esse volume (evento-por-evento, sem overhead de microbatch)
- Schema Registry previne retrabalho quando campos evoluem
- Dual-mode no Next.js separa claramente concerns: real-time vs analytics
- Zustand evita re-renders em arvore (subscricao granular por slice)
- DLQ + watermarks garantem resiliencia desde o dia 1

**Contras:**
- Flink SQL tem curva de aprendizado (DataStream API removida no 2.0)
- Mais componentes que a Abordagem B (Flink + Schema Registry + Redis + Postgres)
- SSE exige deploy com Node.js custom server, nao Vercel padrao

**Confidence media:** 0.87

**Insight unico dos especialistas:** Campo de desconto adicionado pela area comercial quebra o deserializador sem Schema Registry. DLQ e a diferenca entre "pipeline falha silenciosamente" e "falha detectavel e recuperavel".

---

### Abordagem B: Consumer Python Leve + Redis/Postgres + Next.js Dual-Mode

**Base:** `@spark-streaming-architect` (alternativa simplificada) + `@frontend-architect` + `@react-developer`

**Descricao:** Substitui Flink SQL por um consumer Python simples (`confluent-kafka` + `asyncio`). Faz as mesmas agregacoes em janelas em codigo Python puro. Grava em Redis (hot) e Postgres (historico). Frontend identico a Abordagem A (Next.js dual-mode com SSE + RSC).

**Pros:**
- Menos componentes: sem Flink, sem Schema Registry
- Codigo Python puro — mais facil de debugar e testar
- Menor custo operacional (sem cluster Flink)
- Time potencialmente mais familiar com Python que com Flink SQL

**Contras:**
- Menos flexivel para logica de transformacao complexa
- Windowing e watermarks manuais (Flink faz isso nativamente)
- State management na mao do desenvolvedor
- Nao escala horizontalmente tao facilmente quanto Flink

**Confidence media:** 0.85

**Trade-off chave:** Viavel apenas se ETL for simples (agregacoes basicas). Se precisar de enriquecimento, joins entre streams, ou logica de janela complexa, Flink SQL e necessario.

---

### Abordagem C: Kafka + Processador Streaming + Redis/Postgres + Next.js SSE (da Rodada A)

**Descricao:** Abordagem original da Rodada A, mantida para referencia. Kafka → processador (Flink ou Spark Structured Streaming) → Redis (hot) + Postgres (historico) → Next.js SSE. Sem especificidade sobre frontend architecture ou detalhes do processador.

**Nota:** A Rodada B refinou esta abordagem em A e B acima, com insights especificos de cada especialista.

---

## Contexto de Data Engineering

### Sistemas de Origem

| Origem | Tipo | Volume Estimado | Frequencia |
|--------|------|-----------------|------------|
| Eventos de vendas | Kafka topic | 100K+ eventos/dia (~1-2 evt/s media, bursts 5-10x) | Real-time (continuo) |

### Esboco do Fluxo de Dados (Abordagem A)

```text
[App/POS] → [Kafka Producer] → [Schema Registry (Avro)]
                                         │
                                         ▼
                              [Kafka Topic: sales-events]
                              (min 6 particoes, chave por store_id)
                                         │
                                         ├─── [DLQ Topic: sales-events-dlq]
                                         │
                                         ▼
                              [Flink SQL]
                              ├─ TUMBLE(10s) → [Redis] (hot data, operacional)
                              └─ TUMBLE(1h)  → [Postgres] (historico, analytics)
                                         │         │
                                         ▼         ▼
                              [Next.js App Router]
                              ├─ /ops      → Client Components + SSE + Zustand
                              └─ /analytics → Server Components + ISR/PPR + Suspense
```

### Questoes de Dados Exploradas

| # | Questao | Resposta | Fonte |
|---|---------|----------|-------|
| 1 | Volume de dados? | 100K+ evt/dia ≈ 1-2 evt/s media | `@spark-streaming-architect` |
| 2 | Spark SS e adequado? | Superdimensionado para este volume | `@spark-streaming-architect` (0.90) |
| 3 | Processador ideal? | Flink SQL (ou consumer Python se ETL simples) | `@streaming-engineer` + `@spark-streaming-architect` |
| 4 | Schema evolution? | Schema Registry + Avro obrigatorio | `@streaming-engineer` (0.88) |
| 5 | Deploy do frontend? | Node.js custom server (SSE incompativel com serverless) | `@frontend-architect` (0.82) |

---

## Abordagem Selecionada

| Atributo | Valor |
|----------|-------|
| **Escolhida** | Abordagem A: Flink SQL + Redis/Postgres + Next.js Dual-Mode |
| **Confirmacao do Usuario** | 2026-03-29 |
| **Justificativa** | Maior flexibilidade para transformacoes, Schema Registry previne retrabalho, Flink SQL ideal para o volume. Confidence media mais alta (0.87) |

---

## Principais Decisoes Tomadas

| # | Decisao | Justificativa | Fonte | Alternativa Rejeitada |
|---|---------|---------------|-------|----------------------|
| 1 | Flink SQL (nao Spark SS) | 100K/dia e ~1-2 evt/s, Spark SS e superdimensionado | `@streaming-engineer` + `@spark-streaming-architect` | Spark Structured Streaming (overhead injustificado) |
| 2 | Schema Registry + Avro | Schema evolui; sem registry, campo novo quebra deserializador | `@streaming-engineer` | Schema inline (fragil) |
| 3 | DLQ desde o dia 1 | Mensagem malformada sem DLQ derruba pipeline inteiro | `@streaming-engineer` | Sem DLQ (risco critico) |
| 4 | Node.js custom server | SSE incompativel com serverless (Vercel timeout) | `@frontend-architect` | Vercel serverless (SSE nao funciona) |
| 5 | Zustand (nao Context) | Subscricao granular por slice evita re-renders em arvore | `@react-developer` | React Context (re-render cascade) |
| 6 | Dual-mode App Router | Separacao clara: `/ops` (Client) vs `/analytics` (RSC) | `@frontend-architect` + `@react-developer` | SPA unico (concerns misturados) |
| 7 | Dois bancos (Redis + Postgres) | Hot data (real-time) vs cold data (analytics) | Consenso de todos | Postgres unico (performance insuficiente para real-time) |
| 8 | SSE (nao WebSocket) | Dados unidirecionais, SSE mais simples | Consenso de todos | WebSocket (bidirecional desnecessario) |

---

## Features Removidas (YAGNI)

| Feature Sugerida | Motivo da Remocao | Pode Adicionar Depois? |
|------------------|-------------------|----------------------|
| Alertas automaticos (Slack/email) | Nao essencial para MVP, dashboard ja mostra os dados | Sim |
| Export CSV/PDF | Nice-to-have, nao bloqueia uso do dashboard | Sim |
| Multi-tenancy | Comecar com uma empresa, escalar depois | Sim |

---

## Validacoes Incrementais

| Secao | Apresentada | Feedback do Usuario | Ajustada? |
|-------|-------------|---------------------|-----------|
| Deteccao de Dominios (5) | ✅ | Confirmado | Nao |
| Consulta Multi-Agente (4 especialistas) | ✅ | Recebida | Nao |
| Abordagens Consolidadas (A/B/C) | ✅ | Selecionou A | Nao |
| YAGNI | ✅ | Concordou com remocao dos 3 | Nao |

---

## Requisitos Sugeridos para /define

### Declaracao do Problema (Rascunho)
O time de vendas nao tem visibilidade real-time sobre metricas de venda, e a gestao nao consegue analisar tendencias historicas de forma consolidada.

### Usuarios-Alvo (Rascunho)

| Usuario | Dor |
|---------|-----|
| Time de vendas | Precisa reagir rapido a mudancas, hoje so ve dados no fim do dia |
| Gestao comercial | Precisa comparar periodos e identificar tendencias, hoje depende de planilhas |

### Criterios de Sucesso (Rascunho)
- [ ] Dashboard exibe metricas de vendas com latencia < 30 segundos
- [ ] Modo analytics permite comparacao entre periodos (hoje vs ontem, semana vs semana)
- [ ] Suporta 100K+ eventos/dia sem degradacao de performance
- [ ] Autenticacao implementada (dashboard nao e publico)
- [ ] Schema Registry garante compatibilidade backward de eventos
- [ ] DLQ captura eventos malformados sem derrubar pipeline

### Restricoes Identificadas
- Near real-time (5-30s), nao real-time absoluto (< 1s)
- Next.js como stack frontend (decisao do usuario)
- Deploy em Node.js custom server (SSE incompativel com serverless)
- Projeto end-to-end (nao existe nada ainda)
- Flink SQL como processador streaming (nao Spark SS)

### Fora do Escopo (Confirmado)
- Alertas automaticos (Slack/email)
- Export CSV/PDF
- Multi-tenancy
- App mobile

### Agentes Recomendados para Design/Build

| Fase | Agentes | Motivo |
|------|---------|--------|
| Design (streaming) | `@streaming-engineer`, `@spark-streaming-architect` | Arquitetura Flink SQL + Kafka |
| Design (frontend) | `@frontend-architect`, `@react-developer` | Next.js dual-mode + SSE |
| Design (schema) | `@schema-designer` | Schema de eventos de venda |
| Build (streaming) | `@streaming-engineer` | Implementacao Flink SQL |
| Build (frontend) | `@react-developer`, `@frontend-architect` | Next.js components + SSE hook |
| Build (data quality) | `@data-quality-analyst` | Validacao de eventos |

---

## Resumo da Sessao

| Metrica | Valor |
|---------|-------|
| Perguntas Feitas | 5 |
| Dominios Detectados | 5 |
| Especialistas Consultados | 4 |
| Abordagens Exploradas | 3 (2 consolidadas + 1 referencia) |
| Features Removidas (YAGNI) | 3 |
| Bloqueios Detectados | 6 |
| Validacoes Concluidas | 4 |
| Confidence Media | 0.87 |

---

## Proximo Passo

**Pronto para:** `/define .claude/sdd/features/BRAINSTORM_SALES_DASHBOARD_MULTIAGENT.md`
