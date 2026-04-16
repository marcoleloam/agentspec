# DESIGN: Sales Dashboard Real-Time

> Design tecnico para implementar o Sales Dashboard Real-Time com pipeline Kafka e frontend Next.js

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | SALES_DASHBOARD |
| **Data** | 2026-03-29 |
| **Autor** | design-agent |
| **BRAINSTORM** | [BRAINSTORM_SALES_DASHBOARD.md](./BRAINSTORM_SALES_DASHBOARD.md) |
| **Status** | Pronto para Build |
| **Confianca KB** | 0.95 (KB patterns + agent match encontrados para todos os dominios) |
| **Modo** | Single-agent (Rodada A do teste comparativo) |

---

## Visao Geral da Arquitetura

```text
┌──────────────────────────────────────────────────────────────────────────────────┐
│                         SALES DASHBOARD REAL-TIME                                │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌──────────┐    ┌──────────────┐    ┌───────────────────────────┐               │
│  │ App/POS  │───→│ Kafka        │───→│ Processador Streaming     │               │
│  │ Producer │    │ Topic:       │    │ (Flink SQL)               │               │
│  │          │    │ sales-events │    │                           │               │
│  └──────────┘    └──────────────┘    │ ┌───────────────────────┐ │               │
│                         │            │ │ Janela 5s   (hot)     │─┼──→ Redis      │
│                         │            │ │ Janela 1min (warm)    │─┼──→ Redis      │
│                         │            │ │ Janela 1h   (cold)    │─┼──→ Postgres   │
│                         │            │ └───────────────────────┘ │               │
│                         │            └───────────────────────────┘               │
│                         │                                                        │
│                         ▼                                                        │
│              ┌────────────────────┐                                               │
│              │ DLQ: sales-events- │    ┌───────────┐    ┌──────────────────┐     │
│              │ dlq (poison msgs)  │    │  Redis     │───→│ Next.js API      │     │
│              └────────────────────┘    │  (hot)     │    │ Route: /api/     │     │
│                                        └───────────┘    │ metrics/realtime │     │
│                                                          │ (SSE endpoint)   │     │
│                                        ┌───────────┐    │                  │     │
│                                        │ Postgres   │───→│ Route: /api/     │     │
│                                        │ (historico)│    │ metrics/analytics│     │
│                                        └───────────┘    └────────┬─────────┘     │
│                                                                   │               │
│                                                                   ▼               │
│                                        ┌──────────────────────────────────┐       │
│                                        │        Next.js Dashboard         │       │
│                                        │  ┌────────────┬───────────────┐  │       │
│                                        │  │ Real-Time  │  Analytics    │  │       │
│                                        │  │ (SSE)      │  (API + ISR)  │  │       │
│                                        │  │            │               │  │       │
│                                        │  │ - KPIs 5s  │ - Comparacao  │  │       │
│                                        │  │ - Ticker   │   de periodos │  │       │
│                                        │  │ - Charts   │ - Tendencias  │  │       │
│                                        │  └────────────┴───────────────┘  │       │
│                                        └──────────────────────────────────┘       │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────┐       │
│  │ Autenticacao: NextAuth.js v5 + middleware.ts protege /dashboard/*     │       │
│  └────────────────────────────────────────────────────────────────────────┘       │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## Componentes

| Componente | Proposito | Tecnologia |
|------------|-----------|------------|
| Kafka Producer | Publica eventos de venda no topico `sales-events` | confluent-kafka (Python) |
| Kafka Broker | Backbone de eventos, KRaft mode | Apache Kafka 4.0 (KRaft) |
| Schema Registry | Validacao de schema dos eventos | Confluent Schema Registry (JSON Schema) |
| Flink SQL | Agregacao em janelas de tempo (5s, 1min, 1h) | Apache Flink 2.0 |
| Redis | Armazenamento de metricas hot (real-time, TTL curto) | Redis 7+ |
| Postgres | Armazenamento de metricas historicas e dados analytics | PostgreSQL 16+ |
| Next.js API (SSE) | Endpoint de Server-Sent Events para real-time | Next.js 15 Route Handler |
| Next.js API (REST) | Endpoints de consulta para analytics | Next.js 15 Route Handler |
| Dashboard UI | Interface com dois modos (real-time + analytics) | Next.js 15 + React 19 + Tailwind |
| Auth Layer | Autenticacao e protecao de rotas | NextAuth.js v5 (Auth.js) |

---

## Decisoes Principais

### Decisao 1: Flink SQL como processador streaming (ao inves de Spark Structured Streaming)

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-03-29 |

**Contexto:** O brainstorm menciona "Flink ou Spark Structured Streaming" como opcao para o processador. Precisamos definir qual usar para as agregacoes em janelas de 5s, 1min e 1h.

**Escolha:** Flink SQL com watermarks e tumbling windows.

**Justificativa:** Conforme KB `streaming/quick-reference.md`, Flink 2.0 oferece latencia em milissegundos contra segundos do Spark Streaming. Para janelas de 5 segundos, o Spark Structured Streaming com `processingTime="30s"` nao consegue atender o SLA. O Flink SQL permite definir pipelines inteiramente em SQL (mais acessivel para DE teams), com suporte nativo a watermarks e exactly-once via checkpointing Chandy-Lamport.

**Alternativas Rejeitadas:**
1. Spark Structured Streaming - Rejeitada porque latencia minima e de segundos com `processingTime`, e o trigger `continuous` e experimental. Conforme KB, o menor trigger pratico e 30s.
2. ksqlDB - Rejeitada no brainstorm por vendor lock-in com Confluent e menor flexibilidade.

**Consequencias:**
- Flink 2.0 usa ForSt (state backend disagregado) que requer storage remoto (S3/MinIO)
- Time precisa de conhecimento em Flink SQL (curva de aprendizado)
- Ganhamos exactly-once semantics e latencia sub-segundo

---

### Decisao 2: SSE ao inves de WebSocket para push de dados real-time

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-03-29 |

**Contexto:** O dashboard precisa receber atualizacoes de metricas a cada 5 segundos. O fluxo de dados e unidirecional (servidor para cliente).

**Escolha:** Server-Sent Events (SSE) via Next.js Route Handler com `ReadableStream`.

**Justificativa:** Conforme brainstorm, os dados sao unidirecionais. SSE e mais simples que WebSocket, funciona nativamente com HTTP/2 (multiplexing sem custo extra de conexao), e o Next.js suporta SSE via Route Handlers com `ReadableStream`. WebSocket seria over-engineering para um canal unidirecional.

**Alternativas Rejeitadas:**
1. WebSocket - Rejeitada porque bidirecionalidade e desnecessaria. Adiciona complexidade de reconexao, heartbeat e state management sem beneficio.
2. Polling de 5s - Rejeitada porque gera requests desnecessarios e nao escala bem com muitos clientes simultaneos.

**Consequencias:**
- SSE tem limite de 6 conexoes simultaneas por dominio no HTTP/1.1 (mitigado com HTTP/2)
- Reconexao automatica nativa do `EventSource` API do browser
- Precisa tratar limpeza de conexoes orfas no servidor (memory leak risk)

---

### Decisao 3: Kafka 4.0 com KRaft (sem ZooKeeper)

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-03-29 |

**Contexto:** Projeto greenfield, nao existe infraestrutura Kafka previa. Precisamos escolher versao e modo de coordenacao.

**Escolha:** Kafka 4.0 em modo KRaft puro.

**Justificativa:** Conforme KB `streaming/concepts/kafka-fundamentals.md`, o Kafka 4.0 removeu completamente o suporte a ZooKeeper. Como e um projeto do zero, nao ha necessidade de backward compatibility. KRaft simplifica a operacao (menos componentes) e melhora o tempo de rebalanceamento com o novo consumer group protocol (KIP-848).

**Alternativas Rejeitadas:**
1. Kafka 3.x com ZooKeeper - Rejeitada porque a versao 4.0 ja esta disponivel e removeriam o ZK eventualmente.
2. Redpanda - Rejeitada porque, embora tenha melhor p99 latency (~2ms vs ~10ms), o ecossistema Flink tem melhor integracao com Kafka nativo.

**Consequencias:**
- Deploy mais simples (sem cluster ZooKeeper separado)
- Novo consumer group protocol pode ter tooling menos maduro
- Share groups disponiveis para futuras expansoes

---

### Decisao 4: Dois datastores separados (Redis + Postgres) ao inves de Postgres unico

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-03-29 |

**Contexto:** O dashboard atende dois publicos com perfis de acesso distintos: time de vendas (real-time, leitura frequente de metricas quentes) e gestao (analytics, queries historicas complexas).

**Escolha:** Redis para dados hot (metricas dos ultimos 5min-1h com TTL) e Postgres para dados historicos (analytics de longo prazo).

**Justificativa:** Conforme brainstorm, com 100K+ eventos/dia as materialized views do Postgres sozinho poderiam ficar lentas para atualizacoes a cada 5 segundos. Redis fornece leitura em O(1) para metricas pre-computadas. Postgres oferece flexibilidade SQL para queries analytics ad-hoc.

**Alternativas Rejeitadas:**
1. Postgres unico com materialized views - Rejeitado por performance insuficiente para real-time. Refresh de materialized views e blocking.
2. Redis unico - Rejeitado porque Redis nao e adequado para queries analytics complexas (joins, aggregacoes historicas, comparacao de periodos).

**Consequencias:**
- Dois bancos para manter, monitorar e fazer backup
- Precisa sincronizar TTL do Redis com retencao no Postgres
- Cada banco otimizado para seu caso de uso especifico

---

### Decisao 5: Next.js 15 com App Router e estrategia de rendering hibrida

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-03-29 |

**Contexto:** O dashboard tem dois modos com necessidades de rendering diferentes: real-time (atualiza a cada 5s) e analytics (dados mudam menos frequentemente).

**Escolha:** App Router com SSR (`force-dynamic`) para pagina real-time e ISR (`revalidate: 300`) para pagina analytics. Componentes de chart carregados com `dynamic()` import e `ssr: false`.

**Justificativa:** Conforme KB `nextjs/concepts/rendering-strategies.md`, SSR garante dados frescos na pagina real-time. ISR com revalidate de 5min no analytics reduz carga no Postgres sem sacrificar atualidade dos dados. Charts sao client-only (Canvas API), entao `ssr: false` evita erros de hydration.

**Alternativas Rejeitadas:**
1. CSR puro (SPA) - Rejeitado porque perde SEO e tempo de first paint e maior.
2. SSR em tudo - Rejeitado porque analytics nao precisa de dados a cada request, gerando carga desnecessaria.

**Consequencias:**
- Complexidade de gerenciar multiplas estrategias de rendering
- ISR no analytics pode mostrar dados ate 5min antigos (aceitavel para gestao)
- Charts em dynamic import aumentam interatividade percebida (shell renderiza antes)

---

### Decisao 6: Estrutura monorepo com dois modulos independentes

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-03-29 |

**Contexto:** O brainstorm indica monorepo com `pipeline/` e `dashboard/`. Precisamos definir a estrategia de organizacao e deploy.

**Escolha:** Monorepo com dois modulos self-contained: `pipeline/` (Python, Docker) e `dashboard/` (Node.js, Next.js). Sem dependencias compartilhadas entre os dois.

**Justificativa:** Conforme principios de design SDD, cada modulo deve ser self-contained e deployavel independentemente. O pipeline e o dashboard compartilham apenas o contrato de dados (schemas no Schema Registry + schema de tabelas Redis/Postgres), nunca codigo.

**Alternativas Rejeitadas:**
1. Repositorios separados - Rejeitado porque complica o desenvolvimento no inicio; pode migrar depois se necessario.
2. Monorepo com shared lib - Rejeitado porque cria acoplamento entre Python e TypeScript sem beneficio.

**Consequencias:**
- Docker Compose unifica o ambiente de dev (todos os servicos)
- Deploy independente: pipeline pode escalar sem redeployar dashboard
- Contrato de dados e o unico ponto de acoplamento (bem definido)

---

## Manifesto de Arquivos

### Modulo: `pipeline/` (Data Engineering)

| # | Arquivo | Acao | Proposito | Agente | Dependencias |
|---|---------|------|-----------|--------|--------------|
| 1 | `pipeline/src/producer/sales_event_producer.py` | Criar | Kafka producer de eventos de venda com idempotencia | @streaming-engineer | Nenhuma |
| 2 | `pipeline/src/producer/event_schema.py` | Criar | Pydantic model do evento de venda + JSON Schema export | @python-developer | Nenhuma |
| 3 | `pipeline/src/schemas/sales_event.json` | Criar | JSON Schema para Schema Registry | @data-quality-analyst | 2 |
| 4 | `pipeline/src/flink/sql/create_sources.sql` | Criar | DDL Flink: tabela source Kafka com watermark | @streaming-engineer | 3 |
| 5 | `pipeline/src/flink/sql/windowed_aggregations.sql` | Criar | Agregacoes: tumbling windows 5s, 1min, 1h | @streaming-engineer | 4 |
| 6 | `pipeline/src/flink/sql/sink_redis.sql` | Criar | DDL Flink: sink para Redis (metricas hot) | @streaming-engineer | 5 |
| 7 | `pipeline/src/flink/sql/sink_postgres.sql` | Criar | DDL Flink: sink para Postgres (metricas historicas) | @streaming-engineer | 5 |
| 8 | `pipeline/src/consumer/dlq_handler.py` | Criar | Consumer do topico DLQ com logging e reprocessamento | @streaming-engineer | 1 |
| 9 | `pipeline/config/kafka.yaml` | Criar | Configuracao do Kafka (bootstrap servers, topics, partitions) | (direto) | Nenhuma |
| 10 | `pipeline/config/flink.yaml` | Criar | Configuracao do Flink (checkpointing, parallelism) | (direto) | Nenhuma |
| 11 | `pipeline/config/redis.yaml` | Criar | Configuracao do Redis (host, port, TTLs por key pattern) | (direto) | Nenhuma |
| 12 | `pipeline/config/postgres.yaml` | Criar | Configuracao do Postgres (connection, pool size) | (direto) | Nenhuma |
| 13 | `pipeline/sql/init/001_create_tables.sql` | Criar | DDL Postgres: tabelas de metricas historicas | @sql-optimizer | Nenhuma |
| 14 | `pipeline/sql/init/002_create_indexes.sql` | Criar | Indices para queries analytics (date ranges, aggregacoes) | @sql-optimizer | 13 |
| 15 | `pipeline/tests/test_producer.py` | Criar | Testes unitarios do producer (mock Kafka) | @test-generator | 1, 2 |
| 16 | `pipeline/tests/test_event_schema.py` | Criar | Testes de validacao do schema Pydantic | @test-generator | 2 |
| 17 | `pipeline/tests/test_dlq_handler.py` | Criar | Testes do handler DLQ | @test-generator | 8 |
| 18 | `pipeline/Dockerfile` | Criar | Imagem Docker do pipeline (Python 3.12) | @python-developer | Nenhuma |
| 19 | `pipeline/requirements.txt` | Criar | Dependencias Python | @python-developer | Nenhuma |

### Modulo: `dashboard/` (Frontend)

| # | Arquivo | Acao | Proposito | Agente | Dependencias |
|---|---------|------|-----------|--------|--------------|
| 20 | `dashboard/src/app/layout.tsx` | Criar | Root layout com providers (auth, query client, theme) | @frontend-architect | Nenhuma |
| 21 | `dashboard/src/app/page.tsx` | Criar | Landing page com redirect para /dashboard | @react-developer | 20 |
| 22 | `dashboard/src/app/login/page.tsx` | Criar | Pagina de login (NextAuth.js) | @react-developer | 29 |
| 23 | `dashboard/src/app/dashboard/layout.tsx` | Criar | Layout do dashboard com sidebar e nav | @react-developer | 20 |
| 24 | `dashboard/src/app/dashboard/realtime/page.tsx` | Criar | Pagina real-time com SSE subscription | @react-developer | 23, 30 |
| 25 | `dashboard/src/app/dashboard/analytics/page.tsx` | Criar | Pagina analytics com ISR (revalidate: 300) | @react-developer | 23, 31 |
| 26 | `dashboard/src/app/dashboard/realtime/loading.tsx` | Criar | Skeleton de loading para pagina real-time | @css-specialist | 24 |
| 27 | `dashboard/src/app/dashboard/analytics/loading.tsx` | Criar | Skeleton de loading para pagina analytics | @css-specialist | 25 |
| 28 | `dashboard/src/app/dashboard/error.tsx` | Criar | Error boundary do dashboard | @react-developer | 23 |
| 29 | `dashboard/src/lib/auth.ts` | Criar | Configuracao NextAuth.js v5 (providers, callbacks) | @frontend-architect | Nenhuma |
| 30 | `dashboard/src/app/api/metrics/realtime/route.ts` | Criar | SSE endpoint: stream de metricas do Redis | @react-developer | Nenhuma |
| 31 | `dashboard/src/app/api/metrics/analytics/route.ts` | Criar | REST endpoint: query Postgres para analytics | @react-developer | Nenhuma |
| 32 | `dashboard/src/app/api/auth/[...nextauth]/route.ts` | Criar | NextAuth.js route handler | @react-developer | 29 |
| 33 | `dashboard/src/lib/api.ts` | Criar | Fetch wrapper tipado com Zod validation | @react-developer | Nenhuma |
| 34 | `dashboard/src/lib/redis.ts` | Criar | Cliente Redis (ioredis) para API routes | @react-developer | Nenhuma |
| 35 | `dashboard/src/lib/db.ts` | Criar | Cliente Postgres (pg ou Drizzle ORM) para API routes | @react-developer | Nenhuma |
| 36 | `dashboard/src/hooks/useSSE.ts` | Criar | Custom hook para EventSource com reconexao automatica | @react-developer | Nenhuma |
| 37 | `dashboard/src/hooks/useMetrics.ts` | Criar | Hook React Query para metricas analytics | @react-developer | 33 |
| 38 | `dashboard/src/components/ui/kpi-card.tsx` | Criar | Componente de KPI card (valor, delta, trend) | @react-developer | Nenhuma |
| 39 | `dashboard/src/components/ui/metric-chart.tsx` | Criar | Wrapper de chart com dynamic import (ssr: false) | @react-developer | Nenhuma |
| 40 | `dashboard/src/components/ui/date-range-picker.tsx` | Criar | Seletor de periodo para analytics | @react-developer | Nenhuma |
| 41 | `dashboard/src/components/ui/skeleton.tsx` | Criar | Componente skeleton reutilizavel | @css-specialist | Nenhuma |
| 42 | `dashboard/src/components/dashboard/realtime-panel.tsx` | Criar | Painel real-time: KPIs + charts com SSE data | @react-developer | 36, 38, 39 |
| 43 | `dashboard/src/components/dashboard/analytics-panel.tsx` | Criar | Painel analytics: comparacao de periodos, tendencias | @react-developer | 37, 38, 39, 40 |
| 44 | `dashboard/src/components/dashboard/sales-ticker.tsx` | Criar | Ticker de vendas em tempo real (ultimas transacoes) | @react-developer | 36 |
| 45 | `dashboard/src/types/metrics.ts` | Criar | TypeScript types e Zod schemas das metricas | @react-developer | Nenhuma |
| 46 | `dashboard/src/types/events.ts` | Criar | TypeScript types do evento de venda (espelho do schema Python) | @react-developer | Nenhuma |
| 47 | `dashboard/middleware.ts` | Criar | Middleware NextAuth para proteger rotas /dashboard/* | @frontend-architect | 29 |
| 48 | `dashboard/tailwind.config.ts` | Criar | Configuracao Tailwind com design tokens do projeto | @css-specialist | Nenhuma |
| 49 | `dashboard/next.config.ts` | Criar | Configuracao Next.js (env vars, image domains) | @frontend-architect | Nenhuma |
| 50 | `dashboard/package.json` | Criar | Dependencias Node.js | @frontend-architect | Nenhuma |
| 51 | `dashboard/Dockerfile` | Criar | Imagem Docker do dashboard (Node.js 20, multi-stage) | @frontend-architect | Nenhuma |

### Infra / Raiz

| # | Arquivo | Acao | Proposito | Agente | Dependencias |
|---|---------|------|-----------|--------|--------------|
| 52 | `docker-compose.yml` | Criar | Orquestracao local: Kafka, Flink, Redis, Postgres, app | (direto) | Nenhuma |
| 53 | `docker-compose.override.yml` | Criar | Overrides de dev (volumes, hot reload, debug ports) | (direto) | 52 |
| 54 | `.env.example` | Criar | Template de variaveis de ambiente | (direto) | Nenhuma |
| 55 | `data-contracts/sales-event-contract.yaml` | Criar | Data contract ODCS v3.1 do evento de venda | @data-quality-analyst | 2 |

**Total de Arquivos:** 55

---

## Justificativa de Atribuicao de Agentes

> Agentes descobertos em `.claude/agents/` - a fase de Build invoca os especialistas correspondentes.

| Agente | Arquivos Atribuidos | Por Que Este Agente |
|--------|---------------------|---------------------|
| @streaming-engineer | 1, 4, 5, 6, 7, 8 | Especialista em Kafka, Flink SQL, stream processing. KB: streaming, spark, sql-patterns |
| @python-developer | 2, 18, 19 | Arquiteto Python: dataclasses, Pydantic, type hints. KB: python, pydantic |
| @react-developer | 21, 22, 23, 24, 25, 28, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 42, 43, 44, 45, 46 | Especialista React/Next.js: hooks, Server Components, data fetching. KB: react, nextjs |
| @frontend-architect | 20, 29, 47, 49, 50, 51 | Arquiteto frontend: decisoes de rendering strategy, middleware, deploy. KB: nextjs, frontend-patterns |
| @css-specialist | 26, 27, 41, 48 | Especialista Tailwind: skeletons, design tokens, responsividade. KB: tailwind-css, design-systems |
| @sql-optimizer | 13, 14 | Especialista SQL: DDL, indices, performance tuning. KB: sql-patterns, data-modeling |
| @test-generator | 15, 16, 17 | Gerador de testes: pytest, fixtures, mocks. KB: testing, data-quality |
| @data-quality-analyst | 3, 55 | Especialista em schemas, data contracts ODCS. KB: data-quality, data-modeling |
| (direto) | 9, 10, 11, 12, 52, 53, 54 | Configs YAML e Docker Compose sao padrao, sem necessidade de especialista |

**Descoberta de Agentes:**
- Escaneado: `.claude/agents/**/*.md`
- Correspondido por: Tipo de arquivo, palavras-chave de proposito, padroes de caminho, dominios KB

---

## Padroes de Codigo

### Padrao 1: Kafka Producer Idempotente (Python)

```python
# Conforme KB: streaming/patterns/kafka-producer-consumer.md
from confluent_kafka import Producer
import json

producer_config = {
    "bootstrap.servers": "kafka:9092",
    "enable.idempotence": True,        # exactly-once por particao
    "acks": "all",                     # espera todos os ISR replicas
    "compression.type": "zstd",        # melhor ratio para throughput
    "linger.ms": 10,                   # batch para throughput
}

producer = Producer(producer_config)

def produce_sale_event(event: dict) -> None:
    producer.produce(
        topic="sales-events",
        key=str(event["store_id"]).encode("utf-8"),  # particao por loja
        value=json.dumps(event).encode("utf-8"),
        on_delivery=lambda err, msg: logger.error(f"Delivery failed: {err}") if err else None,
    )
    producer.poll(0)
```

### Padrao 2: Flink SQL - Tumbling Window com Watermark

```sql
-- Conforme KB: streaming/patterns/flink-sql-patterns.md
CREATE TABLE raw_sales (
    sale_id     STRING,
    store_id    STRING,
    product_id  STRING,
    amount      DECIMAL(12,2),
    quantity    INT,
    sale_ts     TIMESTAMP(3),
    WATERMARK FOR sale_ts AS sale_ts - INTERVAL '10' SECOND
) WITH (
    'connector' = 'kafka',
    'topic' = 'sales-events',
    'properties.bootstrap.servers' = 'kafka:9092',
    'scan.startup.mode' = 'latest-offset',
    'format' = 'json',
    'json.timestamp-format.standard' = 'ISO-8601'
);

-- Agregacao de 5 segundos para metricas real-time
INSERT INTO realtime_metrics_5s
SELECT
    window_start,
    window_end,
    COUNT(*)        AS sale_count,
    SUM(amount)     AS total_revenue,
    AVG(amount)     AS avg_ticket
FROM TABLE(
    TUMBLE(TABLE raw_sales, DESCRIPTOR(sale_ts), INTERVAL '5' SECOND)
)
GROUP BY window_start, window_end;
```

### Padrao 3: SSE Endpoint (Next.js Route Handler)

```typescript
// Conforme KB: nextjs/patterns/api-routes.md + streaming
// dashboard/src/app/api/metrics/realtime/route.ts
import { NextRequest } from "next/server";
import { redis } from "@/lib/redis";

export const dynamic = "force-dynamic";

export async function GET(request: NextRequest) {
  const encoder = new TextEncoder();

  const stream = new ReadableStream({
    async start(controller) {
      const interval = setInterval(async () => {
        try {
          const metrics = await redis.hgetall("metrics:realtime:5s");
          const data = `data: ${JSON.stringify(metrics)}\n\n`;
          controller.enqueue(encoder.encode(data));
        } catch (error) {
          controller.enqueue(encoder.encode(`event: error\ndata: ${JSON.stringify({ error: "fetch failed" })}\n\n`));
        }
      }, 5000);

      request.signal.addEventListener("abort", () => {
        clearInterval(interval);
        controller.close();
      });
    },
  });

  return new Response(stream, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache, no-transform",
      Connection: "keep-alive",
    },
  });
}
```

### Padrao 4: Custom Hook SSE (React)

```typescript
// Conforme KB: react/patterns/data-fetching.md
// dashboard/src/hooks/useSSE.ts
"use client";
import { useEffect, useRef, useState } from "react";

interface UseSSEOptions<T> {
  url: string;
  onMessage?: (data: T) => void;
}

export function useSSE<T>({ url, onMessage }: UseSSEOptions<T>) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const sourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    const source = new EventSource(url);
    sourceRef.current = source;

    source.onopen = () => setIsConnected(true);
    source.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data) as T;
        setData(parsed);
        onMessage?.(parsed);
      } catch (e) {
        setError(new Error("Failed to parse SSE data"));
      }
    };
    source.onerror = () => {
      setIsConnected(false);
      setError(new Error("SSE connection lost"));
    };

    return () => source.close();
  }, [url]); // eslint-disable-line react-hooks/exhaustive-deps

  return { data, error, isConnected };
}
```

### Padrao 5: Configuracao YAML

```yaml
# pipeline/config/kafka.yaml
kafka:
  bootstrap_servers: "${KAFKA_BOOTSTRAP_SERVERS:-kafka:9092}"
  schema_registry_url: "${SCHEMA_REGISTRY_URL:-http://schema-registry:8081}"
  topics:
    sales_events:
      name: "sales-events"
      partitions: 6
      replication_factor: 3
      retention_ms: 604800000  # 7 dias
    sales_events_dlq:
      name: "sales-events-dlq"
      partitions: 3
      replication_factor: 3
      retention_ms: 2592000000  # 30 dias
  producer:
    enable_idempotence: true
    acks: "all"
    compression_type: "zstd"
    linger_ms: 10
```

---

## Fluxo de Dados

```text
1. App/POS gera evento de venda (JSON) e envia ao Kafka Producer
   │
   ▼
2. Producer valida schema (Pydantic) e publica no topico "sales-events"
   │  ├── Evento valido → topico principal
   │  └── Evento invalido → log + descarte (nunca chega ao Kafka)
   │
   ▼
3. Flink SQL consome do topico com watermark de 10 segundos
   │
   ├──→ Janela 5s:  agregacao rapida → sink Redis (key: metrics:realtime:5s, TTL: 5min)
   ├──→ Janela 1min: agregacao media → sink Redis (key: metrics:realtime:1m, TTL: 1h)
   └──→ Janela 1h:  agregacao lenta → sink Postgres (tabela: hourly_metrics)
   │
   ▼
4. Mensagens que falham no Flink → DLQ topic "sales-events-dlq"
   │  └── DLQ handler loga, armazena e pode reprocessar
   │
   ▼
5. Next.js API Route (SSE) le metricas do Redis a cada 5s
   │  └── Envia via EventSource para os browsers conectados
   │
   ▼
6. Next.js API Route (REST) consulta Postgres para dados analytics
   │  └── ISR com revalidate de 5 minutos
   │
   ▼
7. Dashboard renderiza dois modos:
   ├── Real-Time: KPI cards atualizando via SSE, ticker de vendas, charts ao vivo
   └── Analytics: Comparacao de periodos, tendencias, graficos historicos
```

---

## Pontos de Integracao

| Sistema Externo | Tipo de Integracao | Autenticacao |
|----------------|-------------------|--------------|
| Kafka 4.0 (KRaft) | Protocolo Kafka (producer/consumer) | SASL/SCRAM (prod) / Plaintext (dev) |
| Schema Registry | REST API (HTTP) | Basic auth (prod) / Nenhuma (dev) |
| Flink 2.0 | Flink SQL CLI / Job submission API | Nenhuma (cluster interno) |
| Redis 7+ | Protocolo Redis (ioredis / redis-py) | Password (prod) / Nenhuma (dev) |
| PostgreSQL 16+ | Wire protocol (pg / psycopg) | Password + SSL (prod) / Password (dev) |
| NextAuth.js v5 | OAuth / Credentials (HTTP) | Provider-specific (GitHub, Google, etc.) |

---

## Estrategia de Testes

| Tipo de Teste | Escopo | Arquivos | Ferramentas | Meta de Cobertura |
|---------------|--------|----------|-------------|-------------------|
| Unitario (pipeline) | Producer, schema validation, DLQ handler | `pipeline/tests/test_*.py` | pytest + pytest-mock + confluent-kafka MockProducer | 80% |
| Unitario (dashboard) | Hooks, utils, API client | `dashboard/__tests__/` | Vitest + @testing-library/react | 80% |
| Integracao (pipeline) | Producer → Kafka → Consumer end-to-end | `pipeline/tests/integration/` | pytest + testcontainers (Kafka, Redis, Postgres) | Caminhos principais |
| Integracao (dashboard) | API routes → Redis/Postgres | `dashboard/__tests__/api/` | Vitest + MSW (Mock Service Worker) | Caminhos principais |
| Componente (dashboard) | React components com dados mock | `dashboard/__tests__/components/` | Vitest + @testing-library/react | KPI card, chart, ticker |
| E2E | Fluxo completo: evento → pipeline → dashboard | Manual / Playwright | Playwright (futuro) | Caminho feliz |
| Data Quality | Validacao de schema, nulls, ranges | Flink assertions + data contract checks | Soda Core / dbt tests | 100% em PKs |

---

## Tratamento de Erros

| Tipo de Erro | Estrategia de Tratamento | Retry? |
|-------------|-------------------------|--------|
| Kafka producer delivery failure | Callback de erro + retry nativo (5 tentativas) | Sim (automatico via config) |
| Schema validation failure (producer) | Log + rejeicao do evento antes do Kafka | Nao (dados invalidos) |
| Flink processing failure | Rota mensagem para DLQ topic | Nao (vai para DLQ) |
| Redis connection timeout (API SSE) | SSE envia event:error, cliente reconecta automaticamente | Sim (EventSource nativo) |
| Postgres query timeout (API analytics) | Retorna HTTP 504 + error.tsx renderiza retry button | Sim (manual pelo usuario) |
| SSE connection drop | EventSource reconecta automaticamente | Sim (automatico pelo browser) |
| Auth failure (NextAuth) | Redirect para /login via middleware | Nao |
| Dashboard render crash | error.tsx Error Boundary com retry button | Sim (reset via Error Boundary) |

---

## Configuracao

| Chave de Config | Tipo | Padrao | Descricao |
|----------------|------|--------|-----------|
| `KAFKA_BOOTSTRAP_SERVERS` | string | `kafka:9092` | Enderecos dos brokers Kafka |
| `SCHEMA_REGISTRY_URL` | string | `http://schema-registry:8081` | URL do Schema Registry |
| `REDIS_URL` | string | `redis://redis:6379` | URL de conexao Redis |
| `DATABASE_URL` | string | `postgresql://...` | Connection string Postgres |
| `NEXTAUTH_SECRET` | string | - | Secret para NextAuth.js (obrigatorio) |
| `NEXTAUTH_URL` | string | `http://localhost:3000` | URL base da aplicacao |
| `SSE_INTERVAL_MS` | int | `5000` | Intervalo de push SSE em milissegundos |
| `REDIS_METRICS_TTL_5S` | int | `300` | TTL das metricas 5s no Redis (em segundos) |
| `REDIS_METRICS_TTL_1M` | int | `3600` | TTL das metricas 1min no Redis (em segundos) |
| `ANALYTICS_REVALIDATE_S` | int | `300` | Intervalo ISR da pagina analytics |
| `FLINK_CHECKPOINT_INTERVAL_MS` | int | `60000` | Intervalo de checkpointing Flink |
| `FLINK_PARALLELISM` | int | `4` | Paralelismo default dos jobs Flink |

---

## Consideracoes de Seguranca

- **Autenticacao obrigatoria:** Todas as rotas `/dashboard/*` protegidas via middleware NextAuth.js. Dashboard nao e publico (criterio de sucesso do brainstorm).
- **NEXTAUTH_SECRET:** Deve ser gerado com `openssl rand -base64 32`. Nunca commitar no repositorio.
- **Kafka SASL:** Em producao, habilitar SASL/SCRAM-SHA-512 para autenticacao de producers e consumers. Em dev, plaintext e aceitavel.
- **Redis AUTH:** Em producao, habilitar `requirepass`. Conexao via TLS.
- **Postgres SSL:** Em producao, `sslmode=verify-full` para conexoes de API routes.
- **Rate limiting:** O SSE endpoint nao tem rate limit nativo. Em producao, adicionar via middleware ou CDN (Cloudflare, Vercel Edge).
- **CORS:** API routes devem restringir `Access-Control-Allow-Origin` ao dominio do dashboard.
- **Variaveis de ambiente:** Usar `.env.local` para segredos. `.env.example` contem apenas templates sem valores reais.

---

## Observabilidade

| Aspecto | Implementacao |
|---------|---------------|
| Logging (pipeline) | Logging estruturado em JSON via `structlog` (Python). Campos: `event`, `level`, `timestamp`, `correlation_id` |
| Logging (dashboard) | `pino` para structured logging em API routes. `console.error` para client-side com error boundary |
| Metricas (Kafka) | JMX metrics do Kafka: consumer lag, producer throughput, partition count |
| Metricas (Flink) | Flink Web UI + metricas de checkpointing, backpressure, records processed |
| Metricas (Redis) | `INFO` command: connected clients, memory usage, keyspace hits/misses |
| Metricas (Postgres) | `pg_stat_statements`: slow queries, connection pool usage |
| Metricas (Dashboard) | Core Web Vitals via `next/web-vitals` + analytics (LCP, INP, CLS) |
| Tracing | Nao incluido no MVP. SHOULD: OpenTelemetry para distributed tracing em versao futura |
| Alertas | Nao incluido (YAGNI do brainstorm). Monitoramento visual via dashboards de infra |

---

## Arquitetura de Pipeline

### Diagrama do DAG

```text
[App/POS] ──produce──→ [Kafka: sales-events] ──consume──→ [Flink SQL]
                              │                               │
                              │                          ┌────┼────┐
                              ▼                          │    │    │
                     [Schema Registry]               5s  1m   1h
                     (validacao JSON)                 │    │    │
                                                      ▼    ▼    ▼
                                                   [Redis] [Redis] [Postgres]
                                                   TTL:5m  TTL:1h  Permanente
                                                      │       │       │
                                                      ▼       ▼       ▼
                                                   [Next.js SSE]  [Next.js REST]
                                                      │               │
                                                      ▼               ▼
                                                   [Dashboard RT] [Dashboard Analytics]

                     [Kafka: sales-events-dlq] ←── [Flink] (mensagens com erro)
                              │
                              ▼
                     [DLQ Handler] → [Log + Reprocessamento]
```

### Estrategia de Particionamento

| Tabela/Key | Chave de Particao | Granularidade | Justificativa |
|------------|-------------------|---------------|---------------|
| Kafka: sales-events | `store_id` | N/A (key-based) | Garante ordenacao de eventos por loja. Permite escalar consumers por loja |
| Redis: metrics:realtime:5s | Nenhuma (hash key) | N/A | Key unica com hash de metricas atuais. TTL 5 min |
| Redis: metrics:realtime:1m | Nenhuma (sorted set) | Por timestamp | Sorted set para queries range por tempo |
| Postgres: hourly_metrics | `metric_hour` | Hourly | Queries analytics sempre filtram por range de datas. Particionamento mensal via PARTITION BY RANGE |
| Postgres: daily_summary | `metric_date` | Daily | Materialized view agregando hourly para daily. Refresh a cada hora |

### Estrategia Incremental

| Modelo | Estrategia | Coluna-Chave | Lookback |
|--------|------------|--------------|----------|
| hourly_metrics | Append-only (via Flink sink) | metric_hour | N/A (streaming continuo) |
| daily_summary | Materialized view refresh | metric_date | Recalcula ultimas 24h |
| Redis 5s | Overwrite (HSET com TTL) | N/A | TTL 5 min |
| Redis 1m | Append (ZADD sorted set) | timestamp score | TTL 1h (ZREMRANGEBYSCORE) |

### Plano de Evolucao de Schema

| Tipo de Mudanca | Tratamento | Rollback |
|----------------|------------|----------|
| Nova coluna no evento | Adicionar campo opcional no JSON Schema (backward compatible). Flink SQL ignora campos desconhecidos. Postgres: `ALTER TABLE ADD COLUMN ... DEFAULT` | Remover campo do schema, manter coluna no Postgres |
| Mudanca de tipo de campo | Versionar JSON Schema no Schema Registry (compatibility mode: BACKWARD). Dual-write: producer emite nos dois formatos durante migracao | Reverter versao do schema no Registry |
| Remocao de campo | 1) Marcar como deprecated no data contract. 2) Producer para de enviar apos 30 dias. 3) Flink SQL adapta query. 4) Postgres mantém coluna (nullable) | Re-adicionar campo no producer |
| Nova metrica agregada | 1) Adicionar nova query no Flink SQL. 2) Novo key pattern no Redis. 3) Nova coluna ou tabela no Postgres | Remover job Flink, limpar keys Redis |

### Gates de Qualidade de Dados

| Gate | Ferramenta | Threshold | Acao em Falha |
|------|------------|-----------|---------------|
| Schema validation no producer | Pydantic (Python) | 0 eventos invalidos passam | Rejeitar evento, log erro |
| Schema compatibility no registry | Confluent Schema Registry | Backward compatible | Bloquear deploy do producer |
| Null check em PKs (sale_id) | Flink SQL assertion | 0 nulls | Rota para DLQ |
| Volume anomaly (hourly_metrics) | SQL check no DLQ handler | < 50% da media = alerta | Log warning, nao bloqueia |
| Freshness check (Redis 5s) | Health check endpoint | Ultimo update < 30s | SSE envia heartbeat/warning |
| Data contract compliance | Soda Core / ODCS v3.1 | Todas as regras passam | Bloquear deploy |

---

## Riscos e Blockers Identificados

### Riscos Tecnicos

| # | Risco | Probabilidade | Impacto | Mitigacao |
|---|-------|---------------|---------|-----------|
| R1 | **Memory leak no SSE endpoint** - Conexoes SSE orfas acumulam no servidor Next.js se clients desconectarem sem fechar | Alta | Alto | Implementar cleanup via `request.signal.addEventListener("abort")`. Monitorar conexoes ativas. Adicionar timeout maximo por conexao (ex: 30min, cliente reconecta) |
| R2 | **Flink checkpointing com ForSt (S3/MinIO)** - Flink 2.0 usa ForSt como state backend disagregado, requerendo storage remoto. Em dev local sem S3, pode ser problematico | Media | Alto | Usar MinIO local no Docker Compose como substituto S3. Alternativa: usar RocksDB local para dev (se Flink 2.0 ainda suportar) |
| R3 | **Consumer lag no Flink** - Se o processamento nao acompanhar os 100K+ eventos/dia, lag acumula e metricas ficam atrasadas | Baixa | Alto | Monitorar consumer lag via JMX. Configurar parallelism adequado. Flink auto-scale se rodando em Kubernetes |
| R4 | **Redis TTL e perda de dados** - Se o Redis reiniciar sem persistencia, todas as metricas real-time somem | Media | Medio | Habilitar AOF (Append Only File) no Redis. Metricas sao recalculadas pelo Flink em poucos segundos apos restart |
| R5 | **Limite de 6 conexoes SSE no HTTP/1.1** - Browsers limitam a 6 conexoes simultaneas por dominio em HTTP/1.1 | Media | Medio | Garantir HTTP/2 no deploy (Vercel, Cloudflare). HTTP/2 multiplexa streams em uma conexao TCP |
| R6 | **Carga no Postgres com refresh de materialized views** - Refresh concorrente pode bloquear queries analytics | Baixa | Medio | Usar `REFRESH MATERIALIZED VIEW CONCURRENTLY` (requer unique index). Agendar refresh em horarios de baixa demanda |
| R7 | **Schema Registry como ponto unico de falha** - Se o Schema Registry cair, producers nao conseguem serializar eventos | Baixa | Alto | Deploy do Schema Registry com replicas (alta disponibilidade). Cache de schemas no producer lado cliente |

### Blockers

| # | Blocker | Impacto | Resolucao Necessaria |
|---|---------|---------|---------------------|
| B1 | **Definicao do schema do evento de venda** - O brainstorm indica "Schema de eventos a definir no /define". Sem o schema, nao e possivel implementar producer, Flink SQL, nem tipos TypeScript | Bloqueia todos os arquivos | DEVE ser o primeiro arquivo implementado (item #2 do manifesto). Proposta de schema minimo incluida nos padroes de codigo |
| B2 | **Escolha do provider de autenticacao** - O brainstorm diz "Autenticacao implementada" mas nao especifica qual provider (GitHub, Google, email/password) | Bloqueia arquivos 22, 29, 32, 47 | Decisao necessaria antes do build. Recomendacao: Credentials provider para MVP, OAuth providers depois |
| B3 | **Escolha da biblioteca de charts** - Dashboard precisa de graficos (KPI trends, line charts, bar charts). Nao definido qual lib | Bloqueia arquivos 39, 42, 43 | Recomendacao: Recharts (leve, React-nativo) ou Chart.js via react-chartjs-2. Ambos compatíveis com dynamic import |
| B4 | **Infraestrutura de producao nao definida** - Docker Compose resolve dev, mas onde deployar em producao? AWS? GCP? Vercel + managed services? | Nao bloqueia MVP | Decisao pode ser adiada. Docker Compose cobre o MVP |

### Restricoes Tecnicas Identificadas pela KB

| # | Restricao | Origem (KB) | Impacto no Design |
|---|-----------|-------------|-------------------|
| C1 | **Flink 2.0 removeu DataSet API e Scala API** | `streaming/quick-reference.md` | Usar apenas DataStream API ou Table API/SQL. Todo pipeline sera em Flink SQL |
| C2 | **Flink 2.0 requer Async State API (State V2)** | `streaming/quick-reference.md` | Se precisar de state customizado alem de SQL, usar async state. Para SQL puro, nao e impactante |
| C3 | **Kafka 4.0 removeu ZooKeeper completamente** | `streaming/concepts/kafka-fundamentals.md` | Nao ha opcao de fallback para ZK. Toda documentacao e config devem ser KRaft-only |
| C4 | **Kafka 4.0: novo consumer group protocol (KIP-848) e default** | `streaming/concepts/kafka-fundamentals.md` | Tooling de monitoramento pode nao reconhecer o novo protocolo. Validar compatibilidade de ferramentas de observabilidade |
| C5 | **Next.js Router Cache dura 30s para rotas dinamicas** | `nextjs/concepts/caching.md` | A pagina real-time com SSE nao sera afetada (client-side). Mas a pagina analytics pode mostrar dados cached. Usar `router.refresh()` apos acao do usuario |
| C6 | **SSE nao funciona com edge runtime do Next.js** | `nextjs/patterns/api-routes.md` | O SSE endpoint DEVE usar `runtime = "nodejs"` (default). Nao migrar para edge |
| C7 | **Charts nao podem usar SSR (Canvas API)** | `frontend-patterns/concepts/performance.md` | Todos os componentes de chart devem usar `dynamic(() => import(...), { ssr: false })` |
| C8 | **Watermark + late data: eventos atrasados > 10s serao descartados** | `streaming/concepts/stream-processing-fundamentals.md` | O watermark de 10s significa que eventos com event_time mais de 10 segundos no passado serao ignorados pelo Flink. Para dispositivos moveis com conectividade intermitente, isso pode causar perda de dados |
| C9 | **Redis nao suporta queries SQL complexas** | Design decision | Analytics com JOINs, GROUP BY, comparacao de periodos DEVEM ir para Postgres. Redis serve apenas metricas pre-computadas via key-value |
| C10 | **useEffect + EventSource: cleanup obrigatorio** | `react/quick-reference.md` | O hook useSSE DEVE fechar o EventSource no cleanup do useEffect para evitar memory leaks no browser |

---

## Historico de Revisoes

| Versao | Data | Autor | Mudancas |
|--------|------|-------|----------|
| 1.0 | 2026-03-29 | design-agent | Versao inicial (Rodada A - single-agent) |

---

## Proximo Passo

**Pronto para:** `/build .claude/sdd/features/DESIGN_SALES_DASHBOARD_TEST_DA.md`
