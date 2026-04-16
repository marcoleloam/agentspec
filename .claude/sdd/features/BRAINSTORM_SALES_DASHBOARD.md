# BRAINSTORM: Sales Dashboard Real-Time

> Sessao exploratoria para dashboard de vendas real-time com Next.js + Kafka

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | SALES_DASHBOARD |
| **Data** | 2026-03-29 |
| **Autor** | brainstorm-agent |
| **Status** | Pronto para Define |
| **Modo** | Single-agent (Rodada A do teste comparativo) |

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
| Dominios KB Relevantes | streaming, react, nextjs, frontend-patterns | Cross-domain: DE + frontend |
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

## Abordagens Exploradas

### Abordagem A: Kafka + Processador Streaming + Redis/Postgres + Next.js SSE ⭐ Recomendada

**Descricao:** Kafka recebe eventos de vendas. Um processador (Flink ou Spark Structured Streaming) agrega em janelas de tempo (5s, 1min, 1h). Metricas real-time vao para Redis (leitura rapida). Historico vai para Postgres. Next.js consome via SSE para real-time e API routes para analytics.

**Pros:**
- Separacao clara: real-time (Redis) vs analytics (Postgres)
- SSE mais simples que WebSocket para dados unidirecionais
- Agregacao pre-computada garante performance com 100K+ eventos
- Cada banco otimizado para seu caso de uso

**Contras:**
- Dois bancos para manter (Redis + Postgres)
- Processador streaming adiciona complexidade de infra
- Mais componentes = mais pontos de falha

**Por que Recomendada:** Com 100K+ eventos/dia e dois publicos (operacional + analytics), a separacao de concerns entre Redis (hot data, real-time) e Postgres (cold data, analytics) e a unica abordagem que nao compromete performance em nenhum dos dois modos.

---

### Abordagem B: Kafka Connect + Postgres + Next.js Polling

**Descricao:** Kafka Connect sink grava direto no Postgres. Dashboard faz polling a cada 10-30s. Agregacoes via materialized views no Postgres.

**Pros:**
- Menos componentes (sem Redis, sem processador)
- Materialized views resolvem agregacao
- Mais simples de operar

**Contras:**
- Postgres com 100K+ eventos/dia e materialized views pode ficar lento
- Polling nao e tao fluido quanto SSE
- Sem cache, cada request bate no banco

---

### Abordagem C: ksqlDB + Postgres + Next.js SSE

**Descricao:** ksqlDB processa streams com SQL. Resultados vao para Postgres via sink connector.

**Pros:**
- SQL sobre streams (mais acessivel que Flink/Spark)
- Menos codigo custom

**Contras:**
- Componente extra no ecossistema Kafka
- Menos flexivel que Flink para logica complexa
- Vendor lock-in com Confluent

---

## Contexto de Data Engineering

### Sistemas de Origem

| Origem | Tipo | Volume Estimado | Frequencia |
|--------|------|-----------------|------------|
| Eventos de vendas | Kafka topic | 100K+ eventos/dia | Real-time (continuo) |

### Esboco do Fluxo de Dados

```text
[App/POS] → [Kafka Producer] → [Kafka Topic: sales-events]
                                         │
                                         ▼
                               [Processador Streaming]
                               (Flink ou Spark SS)
                                    │         │
                                    ▼         ▼
                              [Redis]    [Postgres]
                             (hot data)  (historico)
                                    │         │
                                    ▼         ▼
                              [Next.js Dashboard]
                              SSE (real-time) + API (analytics)
```

### Questoes de Dados Exploradas

| # | Questao | Resposta | Impacto |
|---|---------|----------|---------|
| 1 | Volume de dados? | 100K+ eventos/dia | Agregacao pre-computada obrigatoria |
| 2 | SLA de atualizacao? | 5-30 segundos | SSE viavel, nao precisa WebSocket |
| 3 | Quem consome? | Time de vendas (real-time) + gestao (analytics) | Dois modos no dashboard |

---

## Abordagem Selecionada

| Atributo | Valor |
|----------|-------|
| **Escolhida** | Abordagem A: Kafka + Processador + Redis/Postgres + SSE |
| **Confirmacao do Usuario** | 2026-03-29 |
| **Justificativa** | Unica abordagem que atende os dois publicos sem comprometer performance |

---

## Principais Decisoes Tomadas

| # | Decisao | Justificativa | Alternativa Rejeitada |
|---|---------|---------------|----------------------|
| 1 | Dois bancos (Redis + Postgres) | Cada um otimizado para seu caso de uso | Postgres unico (performance insuficiente para real-time) |
| 2 | SSE ao inves de WebSocket | Dados unidirecionais, SSE e mais simples | WebSocket (bidirecional desnecessario) |
| 3 | Processador streaming para agregacao | 100K+ eventos precisa de pre-computacao | Queries direto no raw (inviavel em escala) |

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
| Abordagens (A/B/C) | ✅ | Selecionou A | Nao |
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

### Restricoes Identificadas
- Near real-time (5-30s), nao real-time absoluto (< 1s)
- Next.js como stack frontend (decisao do usuario)
- Projeto end-to-end (nao existe nada ainda)

### Fora do Escopo (Confirmado)
- Alertas automaticos (Slack/email)
- Export CSV/PDF
- Multi-tenancy
- App mobile

---

## Resumo da Sessao

| Metrica | Valor |
|---------|-------|
| Perguntas Feitas | 5 |
| Abordagens Exploradas | 3 |
| Features Removidas (YAGNI) | 3 |
| Validacoes Concluidas | 2 |

---

## Proximo Passo

**Pronto para:** `/define .claude/sdd/features/BRAINSTORM_SALES_DASHBOARD.md`
