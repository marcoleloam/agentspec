# DESIGN: Sales Dashboard Real-Time

> Design tecnico para implementar pipeline de dados e dashboard web para monitoramento operacional e analise historica de vendas, com latencia de ate 30 segundos do evento a tela.

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | SALES_DASHBOARD |
| **Data** | 2026-03-29 |
| **Autor** | design-agent |
| **DEFINE** | [DEFINE_SALES_DASHBOARD_PIPELINE_A.md](./DEFINE_SALES_DASHBOARD_PIPELINE_A.md) |
| **Status** | Rascunho |
| **Clarity Score** | 13/15 (herdado do DEFINE) |
| **Modo** | Multi-agent draft (Pipeline C do teste comparativo -- aguardando consulta de especialistas) |
| **Dominos KB** | `streaming`, `react`, `nextjs`, `frontend-patterns`, `data-quality`, `sql-patterns` |
| **Confianca** | 0.92 -- KB patterns carregados (6/6 dominios), agents matched (7 especialistas) |

---

## Visao Geral da Arquitetura

```text
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                         SALES DASHBOARD -- ARQUITETURA END-TO-END                    │
├──────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌──────────┐      ┌────────────────┐      ┌─────────────────────────────────────┐  │
│  │ App/POS  │─────→│ Kafka Producer │─────→│ Kafka Topic: sales-events (6 part) │  │
│  └──────────┘      │ (Python,       │      │ Replication: 3, Retention: 7d      │  │
│                    │  idempotent)   │      │ Compression: zstd                  │  │
│                    └────────────────┘      └──────────────┬──────────────────────┘  │
│                                                           │                         │
│                           ┌───────────────────────────────┼────────────────┐        │
│                           │                               │                │        │
│                           ▼                               ▼                ▼        │
│                ┌─────────────────────┐        ┌──────────────────┐  ┌──────────┐   │
│                │ Flink SQL           │        │ DLQ Topic:       │  │ Schema   │   │
│                │ (Processador)       │        │ sales-events-dlq │  │ Registry │   │
│                │                     │        └──────────────────┘  │ (JSON)   │   │
│                │ Janelas:            │                              └──────────┘   │
│                │  - TUMBLE 5s → Redis│                                             │
│                │  - TUMBLE 1min → PG │                                             │
│                │  - TUMBLE 1h → PG   │                                             │
│                │                     │                                             │
│                │ Watermark: 10s      │                                             │
│                │ Checkpoint: 30s     │                                             │
│                └────────┬────────────┘                                             │
│                         │                                                          │
│           ┌─────────────┼─────────────┐                                            │
│           ▼                           ▼                                             │
│  ┌────────────────┐        ┌─────────────────┐                                     │
│  │ Redis (hot)    │        │ Postgres (hist) │                                     │
│  │                │        │                 │                                      │
│  │ Metricas 5s:   │        │ Tabelas:        │                                     │
│  │  - revenue     │        │  - raw_events   │                                     │
│  │  - order_count │        │  - agg_1min     │                                     │
│  │  - by_region   │        │  - agg_1hour    │                                     │
│  │  - by_product  │        │  - agg_daily    │                                     │
│  │                │        │                 │                                      │
│  │ TTL: 24h       │        │ Indices:        │                                     │
│  │                │        │  - event_date   │                                     │
│  └───────┬────────┘        │  - region       │                                     │
│          │                 └────────┬────────┘                                     │
│          │                          │                                               │
│          ▼                          ▼                                               │
│  ┌──────────────────────────────────────────────────┐                               │
│  │              Next.js Dashboard (App Router)       │                               │
│  │                                                   │                               │
│  │  ┌──────────────┐    ┌────────────────────────┐  │                               │
│  │  │ Middleware    │    │ API Routes             │  │                               │
│  │  │ (Auth check) │    │                        │  │                               │
│  │  └──────┬───────┘    │ GET /api/sse/metrics   │──┼── SSE ← Redis                │
│  │         │            │ GET /api/analytics/*   │──┼── REST ← Postgres            │
│  │         ▼            │ POST /api/auth/*       │  │                               │
│  │  ┌──────────────┐    └────────────────────────┘  │                               │
│  │  │ Pages        │                                 │                               │
│  │  │              │    ┌────────────────────────┐  │                               │
│  │  │ /dashboard   │───→│ Modo Operacional       │  │                               │
│  │  │   (SSE)      │    │ (KPIs real-time,       │  │                               │
│  │  │              │    │  graficos streaming)   │  │                               │
│  │  │ /analytics   │    └────────────────────────┘  │                               │
│  │  │   (API)      │───→┌────────────────────────┐  │                               │
│  │  │              │    │ Modo Analytics          │  │                               │
│  │  │ /login       │    │ (comparacao periodos,  │  │                               │
│  │  └──────────────┘    │  filtros, graficos)    │  │                               │
│  │                      └────────────────────────┘  │                               │
│  └──────────────────────────────────────────────────┘                               │
│                                                                                      │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Componentes

| Componente | Proposito | Tecnologia |
|------------|-----------|------------|
| **Kafka Producer** | Publica eventos de venda no topico `sales-events` com idempotencia | Python, `confluent-kafka`, JSON Schema |
| **Kafka Broker** | Backbone de eventos, desacoplamento producer/consumer | Apache Kafka 4.0 (KRaft), 6 particoes, RF=3 |
| **Schema Registry** | Validacao e evolucao de schema dos eventos | Confluent Schema Registry, JSON Schema |
| **Flink SQL (Processador)** | Agregacoes em janelas de tempo: 5s, 1min, 1h; sink para Redis e Postgres | Apache Flink 2.0, Flink SQL, checkpointing 30s |
| **Redis** | Cache de metricas hot para leitura real-time pelo dashboard (TTL 24h) | Redis 7+, estruturas Hash e Sorted Sets |
| **Postgres** | Armazenamento historico de eventos e agregacoes pre-computadas | PostgreSQL 16+, indices B-tree por data e regiao |
| **Next.js Dashboard** | Interface web: modo operacional (SSE) e modo analytics (API REST) | Next.js 15 (App Router), React 19, TypeScript |
| **Auth (NextAuth.js v5)** | Autenticacao via middleware, protecao de rotas | NextAuth.js v5, JWT, Credentials provider |
| **DLQ** | Fila de mensagens invalidas para reprocessamento | Kafka topic `sales-events-dlq` |
| **Docker Compose** | Orquestracao de todos os servicos em ambiente de desenvolvimento | Docker Compose v2 |

---

## Decisoes Principais

### Decisao 1: Flink SQL como Processador Streaming (em vez de Spark Structured Streaming)

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-03-29 |

**Contexto:** O DEFINE lista Flink e Spark Structured Streaming como opcoes para o processador. A questao Q-002 do DEFINE pede que esta decisao seja feita no Design. O sistema requer latencia de 5-30 segundos e janelas de tempo multiplas (5s, 1min, 1h).

**Escolha:** Apache Flink 2.0 com Flink SQL.

**Justificativa:**
- Latencia nativa em milissegundos vs segundos do Spark Structured Streaming (conforme `streaming/quick-reference.md`: Flink = ms, Spark = seconds)
- Flink SQL suporta janelas TUMBLE, HOP, SESSION e CUMULATE nativamente, o que simplifica as agregacoes multi-janela exigidas
- Checkpointing via Chandy-Lamport garante exactly-once semantics sem coordenacao externa (conforme `streaming/concepts/flink-architecture.md`)
- Flink 2.0 traz ForSt state backend para estado disaggregado, facilitando escalabilidade
- Flink SQL permite definir source (Kafka), transformacoes e sinks (JDBC para Postgres, Redis via connector) declarativamente

**Alternativas Rejeitadas:**
1. **Spark Structured Streaming** -- Rejeitado porque: latencia de micro-batch (minimo ~1s com trigger continuous, tipicamente 5-30s com `processingTime`); a janela de 5s do requisito ficaria no limite; Spark e mais adequado para cenarios de batch+streaming unificado, que nao e o caso aqui
2. **Kafka Streams** -- Rejeitado porque: exigiria implementacao em Java, sem SQL declarativo; acoplamento direto ao Kafka sem abstracoes de janelamento tao ricas quanto Flink SQL
3. **RisingWave** -- Rejeitado porque: embora tenha latencia em ms e suporte SQL nativo, e uma tecnologia mais recente com ecossistema de conectores menor (conforme KB); risco de adocao para MVP

**Consequencias:**
- Trade-off: Flink requer JVM, o que adiciona complexidade operacional (configuracao de JobManager/TaskManager)
- Beneficio: Latencia sub-segundo e SQL declarativo reduzem tempo de desenvolvimento
- Beneficio: Checkpointing incremental com ForSt permite recovery rapido sem perda de estado

---

### Decisao 2: Kafka 4.0 com KRaft (sem ZooKeeper)

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-03-29 |

**Contexto:** O Kafka e a unica fonte de eventos (premissa A-002 do DEFINE). A versao 4.0 removeu completamente o ZooKeeper.

**Escolha:** Apache Kafka 4.0 com coordenacao KRaft.

**Justificativa:**
- ZooKeeper foi completamente removido no Kafka 4.0 (conforme `streaming/concepts/kafka-fundamentals.md`)
- KRaft simplifica deployment: nao precisa de cluster separado para coordenacao
- Novo consumer group protocol (KIP-848) reduz downtime durante rebalanceamento
- Para projeto greenfield, nao ha migracao -- comecar direto com KRaft

**Alternativas Rejeitadas:**
1. **Kafka 3.x + ZooKeeper** -- Rejeitado porque: componente legado, mais infraestrutura para gerenciar
2. **Redpanda** -- Rejeitado porque: embora tenha latencia p99 mais baixa (~2ms vs ~10ms do Kafka), o ecossistema de conectores Flink e mais maduro com Kafka nativo; Redpanda seria viavel mas adiciona risco de compatibilidade

**Consequencias:**
- Beneficio: Arquitetura mais simples, menos componentes para gerenciar
- Trade-off: Kafka 4.0 e relativamente recente (Marco 2025); confirmar compatibilidade com conectores Flink

---

### Decisao 3: Next.js 15 com App Router para Dashboard

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita (restricao do DEFINE) |
| **Data** | 2026-03-29 |

**Contexto:** O DEFINE determina Next.js como framework obrigatorio. A decisao aqui e sobre a versao e padroes de implementacao.

**Escolha:** Next.js 15 com App Router, React 19, TypeScript.

**Justificativa:**
- App Router permite Server Components por padrao, reduzindo bundle JS no cliente (conforme `nextjs/concepts/app-router.md`)
- SSE endpoint implementado como Route Handler (`app/api/sse/metrics/route.ts`) sem necessidade de WebSocket (restricao: 5-30s e suficiente)
- Middleware nativo para autenticacao (conforme `nextjs/concepts/middleware.md`)
- API Routes para endpoints de analytics com validacao Zod (conforme `nextjs/patterns/api-routes.md`)

**Consequencias:**
- Beneficio: Server Components reduzem JS enviado ao cliente (graficos pesados carregados via dynamic import com `ssr: false`)
- Trade-off: SSE nao suporta comunicacao bidirecional; se no futuro o dashboard precisar enviar comandos ao servidor, precisara de API REST separada (que ja existe)

---

### Decisao 4: NextAuth.js v5 para Autenticacao

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-03-29 |

**Contexto:** O DEFINE exige autenticacao (MUST): "usuarios nao autenticados nao acessam dados". Teste AT-004 valida que requisicoes sem token retornam 401.

**Escolha:** NextAuth.js v5 (Auth.js) com Credentials provider e JWT strategy.

**Justificativa:**
- Integracao nativa com Next.js App Router e middleware (conforme `nextjs/patterns/auth-patterns.md`)
- Middleware roda antes de cada request, protegendo `/dashboard/*` e `/analytics/*` sem logica duplicada
- JWT strategy evita dependencia de banco de sessoes adicional
- `auth()` funcao server-side permite verificar sessao em Server Components

**Alternativas Rejeitadas:**
1. **Auth0 / Clerk** -- Rejeitados porque: MVP nao precisa de social login nem SSO corporativo; Credentials provider e suficiente; custo adicional injustificado
2. **Custom JWT** -- Rejeitado porque: reinventar autenticacao e anti-pattern; NextAuth.js resolve com padroes testados

**Consequencias:**
- Beneficio: Autenticacao pronta em horas, nao dias
- Trade-off: Credentials provider requer gerenciamento proprio de usuarios (tabela `users` no Postgres)

---

### Decisao 5: Dois Caminhos de Leitura (Redis Hot + Postgres Historico)

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita (restricao do DEFINE) |
| **Data** | 2026-03-29 |

**Contexto:** O DEFINE determina Redis (hot data) + Postgres (historico) como restricao arquitetural. O design precisa definir como os dados fluem para cada banco e como o dashboard os consome.

**Escolha:** Flink SQL grava simultaneamente em ambos; dashboard le Redis via SSE (operacional) e Postgres via API Routes (analytics).

**Justificativa:**
- Redis atende leituras sub-segundo para metricas real-time com TTL de 24h (evita crescimento ilimitado)
- Postgres armazena historico completo para queries de comparacao de periodos
- Separacao clara: SSE le Redis (latencia < 5ms), API Routes consultam Postgres (latencia < 100ms para queries indexadas)

**Consequencias:**
- Trade-off: Consistencia eventual entre Redis e Postgres (evento pode estar no Redis antes do Postgres)
- Mitigacao: SLA do Postgres e 5 minutos (conforme DEFINE); para o usuario, os dados aparecem imediatamente no modo operacional e dentro de minutos no analytics

---

### Decisao 6: Idempotencia por `event_id` em Todas as Camadas

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-03-29 |

**Contexto:** A premissa A-004 do DEFINE assume at-least-once semantics no processador, o que pode gerar duplicatas. O DEFINE exige "zero event_id duplicados no Postgres".

**Escolha:** Idempotencia em tres camadas: producer idempotente + deduplicacao no Flink + UPSERT no Postgres.

**Justificativa:**
- Producer Kafka com `enable.idempotence=True` e `acks=all` previne duplicatas no Kafka (conforme `streaming/patterns/kafka-producer-consumer.md`)
- Flink SQL com `dropDuplicates` ou `ROW_NUMBER() OVER (PARTITION BY event_id)` elimina duplicatas antes do sink
- Postgres com `ON CONFLICT (event_id) DO NOTHING` garante unicidade no armazenamento final
- Redis com `SET` (idempotente por natureza) sobrescreve metricas agregadas

**Consequencias:**
- Beneficio: Zero duplicatas end-to-end, mesmo com retries e falhas
- Trade-off: Leve overhead de deduplicacao no Flink (estado por event_id com TTL)

---

### Decisao 7: JSON Schema (em vez de Avro/Protobuf) para Serializacao de Eventos

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-03-29 |

**Contexto:** Eventos de venda precisam de schema validado. As opcoes sao Avro, Protobuf ou JSON Schema (conforme `data-quality/patterns/schema-validation.md`).

**Escolha:** JSON Schema com Schema Registry.

**Justificativa:**
- JSON e nativamente legivel pelo dashboard Next.js (sem necessidade de deserializacao binaria)
- Flink SQL suporta `format = 'json'` nativamente (conforme `streaming/patterns/flink-sql-patterns.md`)
- Schema Registry com JSON Schema permite evolucao backward-compatible
- Para volume de ~1.15 evento/segundo, a overhead de JSON vs Avro e negligivel

**Alternativas Rejeitadas:**
1. **Avro** -- Rejeitado porque: requer deserializacao binaria no frontend; adiciona complexidade sem ganho significativo para o volume atual
2. **Protobuf** -- Rejeitado porque: mesma questao do Avro, mais overhead de `.proto` compilation

**Consequencias:**
- Beneficio: Simplicidade end-to-end, debugging facilitado (mensagens legiveis)
- Trade-off: JSON ocupa ~2-3x mais espaco que Avro; com zstd compression no Kafka, a diferenca e minimizada
- Risco: Se o volume crescer 100x (Black Friday, premissa A-006), reconsiderar Avro

---

## Contrato de Schema (Finalizado)

> Schema de eventos validado e finalizado a partir do rascunho do DEFINE.

### Evento de Venda (`SaleEvent`)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["event_id", "event_timestamp", "sale_amount", "product_id", "seller_id", "region", "status"],
  "properties": {
    "event_id": {
      "type": "string",
      "format": "uuid",
      "description": "Identificador unico do evento (PK, idempotency key)"
    },
    "event_timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "Timestamp UTC do evento de venda (event-time para watermarks)"
    },
    "sale_amount": {
      "type": "number",
      "minimum": 0,
      "multipleOf": 0.01,
      "description": "Valor da venda em moeda local"
    },
    "product_id": {
      "type": "string",
      "maxLength": 64,
      "description": "Identificador do produto vendido"
    },
    "seller_id": {
      "type": "string",
      "maxLength": 64,
      "description": "Identificador do vendedor (potencialmente PII -- ver Decisao Q-004)"
    },
    "region": {
      "type": "string",
      "maxLength": 64,
      "description": "Regiao geografica da venda"
    },
    "status": {
      "type": "string",
      "enum": ["completed", "pending", "cancelled"],
      "description": "Status da venda"
    }
  },
  "additionalProperties": false
}
```

### Modelo Pydantic (Validacao no Producer)

```python
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from enum import Enum
from uuid import UUID


class SaleStatus(str, Enum):
    COMPLETED = "completed"
    PENDING = "pending"
    CANCELLED = "cancelled"


class SaleEvent(BaseModel):
    """Schema de evento de venda -- validado no producer antes de publicar no Kafka."""
    event_id: UUID
    event_timestamp: datetime
    sale_amount: float = Field(..., ge=0)
    product_id: str = Field(..., max_length=64)
    seller_id: str = Field(..., max_length=64)
    region: str = Field(..., max_length=64)
    status: SaleStatus

    @field_validator("sale_amount")
    @classmethod
    def validate_amount_precision(cls, v: float) -> float:
        if round(v, 2) != v:
            raise ValueError("sale_amount deve ter no maximo 2 casas decimais")
        return v
```

---

## Manifesto de Arquivos

### Pipeline (`pipeline/`)

| # | Arquivo | Acao | Proposito | Agente | Dependencias |
|---|---------|------|-----------|--------|--------------|
| 1 | `pipeline/docker-compose.yml` | Criar | Orquestracao de todos os servicos (Kafka, Flink, Redis, Postgres, Schema Registry) | (direto) | Nenhuma |
| 2 | `pipeline/producer/requirements.txt` | Criar | Dependencias Python do producer | (direto) | Nenhuma |
| 3 | `pipeline/producer/config.yaml` | Criar | Configuracao do producer (bootstrap servers, topic, batch settings) | (direto) | Nenhuma |
| 4 | `pipeline/producer/schema.py` | Criar | Modelo Pydantic `SaleEvent` para validacao de schema | @python-developer | Nenhuma |
| 5 | `pipeline/producer/producer.py` | Criar | Kafka producer idempotente com validacao Pydantic e DLQ | @streaming-engineer | 3, 4 |
| 6 | `pipeline/producer/simulator.py` | Criar | Gerador de eventos sinteticos para testes de carga | @python-developer | 4 |
| 7 | `pipeline/flink/sql/create_source.sql` | Criar | DDL Flink SQL: tabela source Kafka com watermark | @streaming-engineer | Nenhuma |
| 8 | `pipeline/flink/sql/agg_5s_redis.sql` | Criar | DML Flink SQL: agregacao TUMBLE 5s com sink Redis | @streaming-engineer | 7 |
| 9 | `pipeline/flink/sql/agg_1min_postgres.sql` | Criar | DML Flink SQL: agregacao TUMBLE 1min com sink Postgres | @streaming-engineer | 7 |
| 10 | `pipeline/flink/sql/agg_1hour_postgres.sql` | Criar | DML Flink SQL: agregacao TUMBLE 1h com sink Postgres | @streaming-engineer | 7 |
| 11 | `pipeline/flink/sql/raw_events_postgres.sql` | Criar | DML Flink SQL: sink de eventos brutos para Postgres (dedup) | @streaming-engineer | 7 |
| 12 | `pipeline/flink/flink-conf.yaml` | Criar | Configuracao Flink: checkpointing, state backend, paralelismo | @streaming-engineer | Nenhuma |
| 13 | `pipeline/postgres/init.sql` | Criar | DDL Postgres: tabelas, indices, particoes, funcao de dedup | @sql-optimizer | Nenhuma |
| 14 | `pipeline/postgres/queries/analytics_queries.sql` | Criar | Queries de agregacao e comparacao de periodos para API analytics | @sql-optimizer | 13 |
| 15 | `pipeline/schemas/sale_event.json` | Criar | JSON Schema para registro no Schema Registry | @data-quality-analyst | 4 |
| 16 | `pipeline/tests/test_schema.py` | Criar | Testes unitarios do modelo Pydantic (validos + invalidos) | @test-generator | 4 |
| 17 | `pipeline/tests/test_producer.py` | Criar | Testes do producer com mock Kafka | @test-generator | 5 |
| 18 | `pipeline/tests/test_queries.py` | Criar | Testes das queries SQL de analytics | @test-generator | 14 |
| 19 | `pipeline/quality/data_quality_checks.yaml` | Criar | Checks de qualidade: completude, unicidade, timeliness | @data-quality-analyst | 13 |

### Dashboard (`dashboard/`)

| # | Arquivo | Acao | Proposito | Agente | Dependencias |
|---|---------|------|-----------|--------|--------------|
| 20 | `dashboard/package.json` | Criar | Dependencias do projeto Next.js | (direto) | Nenhuma |
| 21 | `dashboard/tsconfig.json` | Criar | Configuracao TypeScript | (direto) | Nenhuma |
| 22 | `dashboard/next.config.ts` | Criar | Configuracao Next.js (rewrites, env vars) | @frontend-architect | Nenhuma |
| 23 | `dashboard/.env.example` | Criar | Template de variaveis de ambiente | (direto) | Nenhuma |
| 24 | `dashboard/src/middleware.ts` | Criar | Middleware de autenticacao: protege /dashboard e /analytics | @frontend-architect | 30 |
| 25 | `dashboard/src/app/layout.tsx` | Criar | Root layout com providers (SessionProvider, QueryClientProvider) | @react-developer | 20 |
| 26 | `dashboard/src/app/page.tsx` | Criar | Pagina raiz: redirect para /dashboard ou /login | @react-developer | 25 |
| 27 | `dashboard/src/app/login/page.tsx` | Criar | Pagina de login com formulario de credenciais | @react-developer | 30 |
| 28 | `dashboard/src/app/dashboard/page.tsx` | Criar | Modo operacional: KPIs real-time via SSE | @react-developer | 32, 33, 34 |
| 29 | `dashboard/src/app/dashboard/loading.tsx` | Criar | Skeleton de carregamento para o dashboard | @react-developer | Nenhuma |
| 30 | `dashboard/src/lib/auth.ts` | Criar | Configuracao NextAuth.js v5 (providers, callbacks, session) | @frontend-architect | Nenhuma |
| 31 | `dashboard/src/lib/api.ts` | Criar | Fetch wrapper tipado com Zod e tratamento de erros | @frontend-architect | Nenhuma |
| 32 | `dashboard/src/hooks/use-sse.ts` | Criar | Custom hook para consumir SSE endpoint (EventSource API) | @react-developer | Nenhuma |
| 33 | `dashboard/src/hooks/use-sales-metrics.ts` | Criar | Hook que combina SSE com estado local para metricas de vendas | @react-developer | 32 |
| 34 | `dashboard/src/components/dashboard/kpi-card.tsx` | Criar | Componente de KPI card (receita, contagem, ticket medio) | @react-developer | Nenhuma |
| 35 | `dashboard/src/components/dashboard/sales-chart.tsx` | Criar | Grafico de vendas real-time (dynamic import, client-only) | @react-developer | 33 |
| 36 | `dashboard/src/components/dashboard/region-breakdown.tsx` | Criar | Breakdown por regiao (tabela ou grafico de barras) | @react-developer | 33 |
| 37 | `dashboard/src/app/analytics/page.tsx` | Criar | Modo analytics: consultas historicas com filtros e comparacao | @react-developer | 31, 38 |
| 38 | `dashboard/src/app/analytics/loading.tsx` | Criar | Skeleton de carregamento para analytics | @react-developer | Nenhuma |
| 39 | `dashboard/src/components/analytics/period-selector.tsx` | Criar | Seletor de periodo para comparacao (hoje vs ontem, semana vs semana) | @react-developer | Nenhuma |
| 40 | `dashboard/src/components/analytics/comparison-chart.tsx` | Criar | Grafico de comparacao entre periodos | @react-developer | 39 |
| 41 | `dashboard/src/components/analytics/data-table.tsx` | Criar | Tabela de dados historicos com paginacao | @react-developer | Nenhuma |
| 42 | `dashboard/src/components/ui/skeleton.tsx` | Criar | Componente Skeleton reutilizavel | @react-developer | Nenhuma |
| 43 | `dashboard/src/components/ui/error-message.tsx` | Criar | Componente de mensagem de erro reutilizavel | @react-developer | Nenhuma |
| 44 | `dashboard/src/app/api/sse/metrics/route.ts` | Criar | SSE endpoint: le Redis e envia eventos ao cliente | @frontend-architect | Nenhuma |
| 45 | `dashboard/src/app/api/analytics/summary/route.ts` | Criar | API Route: retorna agregacoes por periodo do Postgres | @frontend-architect | 14 |
| 46 | `dashboard/src/app/api/analytics/comparison/route.ts` | Criar | API Route: retorna dados comparativos entre dois periodos | @frontend-architect | 14 |
| 47 | `dashboard/src/app/api/auth/[...nextauth]/route.ts` | Criar | Route Handler do NextAuth.js v5 | @frontend-architect | 30 |
| 48 | `dashboard/src/types/api.ts` | Criar | Tipos TypeScript compartilhados (SaleEvent, Metrics, etc.) | @react-developer | Nenhuma |
| 49 | `dashboard/src/app/error.tsx` | Criar | Error Boundary global do dashboard | @react-developer | 43 |
| 50 | `dashboard/src/app/global-error.tsx` | Criar | Error Boundary global do root layout | @react-developer | Nenhuma |
| 51 | `dashboard/src/app/not-found.tsx` | Criar | Pagina 404 customizada | @react-developer | Nenhuma |

### Testes do Dashboard

| # | Arquivo | Acao | Proposito | Agente | Dependencias |
|---|---------|------|-----------|--------|--------------|
| 52 | `dashboard/src/__tests__/hooks/use-sse.test.ts` | Criar | Teste do hook useSSE com mock EventSource | @test-generator | 32 |
| 53 | `dashboard/src/__tests__/components/kpi-card.test.tsx` | Criar | Teste de renderizacao do KPI card | @test-generator | 34 |
| 54 | `dashboard/src/__tests__/api/analytics.test.ts` | Criar | Teste de integracao das API Routes de analytics | @test-generator | 45, 46 |

**Total de Arquivos:** 54

---

## Justificativa de Atribuicao de Agentes

> Agentes descobertos em `.claude/agents/` -- a fase de Build invoca os especialistas correspondentes.

| Agente | Arquivos Atribuidos | Por Que Este Agente |
|--------|---------------------|---------------------|
| @streaming-engineer | 5, 7, 8, 9, 10, 11, 12 | Especialista em Flink SQL, Kafka producer/consumer, watermarks, checkpointing. KB domains: `streaming`, `spark`, `sql-patterns` |
| @python-developer | 4, 6 | Especialista em Python, Pydantic, dataclasses, type hints. KB domains: `python`, `pydantic`, `testing` |
| @react-developer | 25, 26, 27, 28, 29, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 48, 49, 50, 51 | Especialista em React hooks, Server Components, state management, composicao de componentes. KB domains: `react`, `nextjs` |
| @frontend-architect | 22, 24, 30, 31, 44, 45, 46, 47 | Especialista em arquitetura Next.js, API Routes, middleware, caching, deployment. KB domains: `nextjs`, `frontend-patterns` |
| @sql-optimizer | 13, 14 | Especialista em SQL cross-dialect, window functions, otimizacao de queries, indices. KB domains: `sql-patterns`, `data-modeling` |
| @data-quality-analyst | 15, 19 | Especialista em data quality, schema validation, data contracts. KB domains: `data-quality`, `dbt`, `data-modeling` |
| @test-generator | 16, 17, 18, 52, 53, 54 | Especialista em pytest, testes unitarios, fixtures, mocks. KB domains: `data-quality`, `testing` |
| (direto) | 1, 2, 3, 20, 21, 23 | Arquivos de configuracao padrao que nao requerem especializacao |

**Descoberta de Agentes:**
- Escaneado: `.claude/agents/**/*.md` -- 63 agentes em 8 categorias
- Correspondido por: Tipo de arquivo (.py, .sql, .tsx, .ts, .yaml), palavras-chave de proposito, padroes de caminho, dominios KB

---

## Padroes de Codigo

### Padrao 1: Kafka Producer Idempotente (de `streaming/patterns/kafka-producer-consumer.md`)

```python
from confluent_kafka import Producer
import json

producer_config = {
    "bootstrap.servers": "kafka:9092",
    "enable.idempotence": True,
    "acks": "all",
    "retries": 5,
    "max.in.flight.requests.per.connection": 5,
    "compression.type": "zstd",
    "linger.ms": 10,
    "batch.size": 65536,
}

producer = Producer(producer_config)

def produce_sale_event(event: SaleEvent) -> None:
    """Publica evento validado no Kafka com delivery callback."""
    def on_delivery(err, msg):
        if err:
            logger.error("Delivery failed for %s: %s", event.event_id, err)
        else:
            logger.debug("Delivered %s to [%d] @ %d", event.event_id, msg.partition(), msg.offset())

    producer.produce(
        topic="sales-events",
        key=str(event.event_id).encode("utf-8"),
        value=event.model_dump_json().encode("utf-8"),
        on_delivery=on_delivery,
    )
    producer.poll(0)
```

### Padrao 2: Flink SQL Source com Watermark (de `streaming/patterns/flink-sql-patterns.md`)

```sql
CREATE TABLE raw_sales (
    event_id       STRING,
    event_timestamp TIMESTAMP(3),
    sale_amount    DECIMAL(18, 2),
    product_id     STRING,
    seller_id      STRING,
    region         STRING,
    status         STRING,
    WATERMARK FOR event_timestamp AS event_timestamp - INTERVAL '10' SECOND
) WITH (
    'connector' = 'kafka',
    'topic' = 'sales-events',
    'properties.bootstrap.servers' = 'kafka:9092',
    'properties.group.id' = 'flink-sales-processor',
    'scan.startup.mode' = 'earliest-offset',
    'format' = 'json',
    'json.timestamp-format.standard' = 'ISO-8601'
);
```

### Padrao 3: Agregacao Tumble 5s para Redis (de `streaming/patterns/flink-sql-patterns.md`)

```sql
INSERT INTO redis_metrics_5s
SELECT
    window_start,
    window_end,
    region,
    COUNT(*)                       AS order_count,
    SUM(sale_amount)               AS total_revenue,
    AVG(sale_amount)               AS avg_ticket,
    COUNT(DISTINCT product_id)     AS unique_products
FROM TABLE(
    TUMBLE(TABLE raw_sales, DESCRIPTOR(event_timestamp), INTERVAL '5' SECOND)
)
WHERE status = 'completed'
GROUP BY window_start, window_end, region;
```

### Padrao 4: SSE Route Handler no Next.js (de `nextjs/patterns/api-routes.md` + custom)

```typescript
// app/api/sse/metrics/route.ts
import { NextRequest } from "next/server";
import { auth } from "@/lib/auth";
import Redis from "ioredis";

export const dynamic = "force-dynamic";

export async function GET(request: NextRequest) {
  const session = await auth();
  if (!session) {
    return new Response("Unauthorized", { status: 401 });
  }

  const redis = new Redis(process.env.REDIS_URL!);
  const encoder = new TextEncoder();

  const stream = new ReadableStream({
    async start(controller) {
      const interval = setInterval(async () => {
        try {
          const metrics = await redis.hgetall("sales:metrics:latest");
          const data = `data: ${JSON.stringify(metrics)}\n\n`;
          controller.enqueue(encoder.encode(data));
        } catch (error) {
          controller.error(error);
        }
      }, 5000); // push every 5 seconds

      request.signal.addEventListener("abort", () => {
        clearInterval(interval);
        redis.disconnect();
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

### Padrao 5: Custom Hook useSSE (de `react/concepts/hooks-patterns.md`)

```typescript
// hooks/use-sse.ts
"use client";
import { useState, useEffect, useCallback, useRef } from "react";

interface UseSSEOptions<T> {
  url: string;
  transform?: (data: string) => T;
  reconnectInterval?: number;
}

export function useSSE<T>({ url, transform, reconnectInterval = 3000 }: UseSSEOptions<T>) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);

  const connect = useCallback(() => {
    const es = new EventSource(url);
    eventSourceRef.current = es;

    es.onopen = () => setIsConnected(true);
    es.onmessage = (event) => {
      try {
        const parsed = transform ? transform(event.data) : JSON.parse(event.data);
        setData(parsed);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err : new Error("Parse error"));
      }
    };
    es.onerror = () => {
      setIsConnected(false);
      es.close();
      setTimeout(connect, reconnectInterval);
    };
  }, [url, transform, reconnectInterval]);

  useEffect(() => {
    connect();
    return () => eventSourceRef.current?.close();
  }, [connect]);

  return { data, error, isConnected };
}
```

### Padrao 6: API Analytics com Validacao Zod (de `nextjs/patterns/api-routes.md` + `frontend-patterns/patterns/api-integration.md`)

```typescript
// app/api/analytics/summary/route.ts
import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { auth } from "@/lib/auth";
import { pool } from "@/lib/db";

const SummaryParamsSchema = z.object({
  period: z.enum(["1h", "1d", "7d", "30d"]),
  region: z.string().optional(),
});

export async function GET(request: NextRequest) {
  const session = await auth();
  if (!session) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const { searchParams } = new URL(request.url);
  const parsed = SummaryParamsSchema.safeParse(Object.fromEntries(searchParams));

  if (!parsed.success) {
    return NextResponse.json({ error: parsed.error.flatten() }, { status: 400 });
  }

  const { period, region } = parsed.data;
  const result = await pool.query(
    `SELECT ... FROM agg_1hour WHERE ... ORDER BY window_start DESC`,
    [period, region]
  );

  return NextResponse.json(result.rows);
}
```

### Padrao 7: Deduplicacao no Postgres (de `sql-patterns/patterns/deduplication.md`)

```sql
-- Insert com deduplicacao por event_id
INSERT INTO raw_events (event_id, event_timestamp, sale_amount, product_id, seller_id, region, status)
VALUES ($1, $2, $3, $4, $5, $6, $7)
ON CONFLICT (event_id) DO NOTHING;
```

### Padrao 8: Configuracao YAML

```yaml
# pipeline/producer/config.yaml
kafka:
  bootstrap_servers: "kafka:9092"
  topic: "sales-events"
  dlq_topic: "sales-events-dlq"
  compression: "zstd"
  linger_ms: 10
  batch_size: 65536
  idempotent: true
  acks: "all"

schema:
  registry_url: "http://schema-registry:8081"
  subject: "sales-events-value"

logging:
  level: "INFO"
  format: "json"
```

---

## Fluxo de Dados

```text
1. App/POS gera evento de venda
   │
   ▼
2. Kafka Producer valida com Pydantic (SaleEvent)
   ├─ Valido → Publica no topic `sales-events` (particionado por event_id)
   └─ Invalido → Log + DLQ `sales-events-dlq`
   │
   ▼
3. Flink SQL consome `sales-events` com watermark de 10s
   │
   ├─ TUMBLE 5s → Agrega metricas (revenue, count, avg, by region)
   │              └─ Sink → Redis Hash `sales:metrics:latest` + `sales:metrics:5s:{timestamp}`
   │
   ├─ TUMBLE 1min → Agrega metricas por minuto
   │                └─ Sink → Postgres `agg_1min` (UPSERT por window_start + region)
   │
   ├─ TUMBLE 1h → Agrega metricas por hora
   │              └─ Sink → Postgres `agg_1hour` (UPSERT por window_start + region)
   │
   └─ Raw events → Dedup por event_id
                    └─ Sink → Postgres `raw_events` (INSERT ON CONFLICT DO NOTHING)
   │
   ▼
4. Dashboard Next.js consome dados
   ├─ Modo Operacional (/dashboard):
   │  └─ SSE endpoint le Redis a cada 5s → push para client
   │     └─ Hook useSSE → atualiza KPI cards e graficos em tempo real
   │
   └─ Modo Analytics (/analytics):
      └─ API Routes consultam Postgres (agg_1hour, agg_1min)
         └─ React Query no client → cache + revalidacao
            └─ Comparacao de periodos: hoje vs ontem, semana vs semana
```

---

## Pontos de Integracao

| Sistema Externo | Tipo de Integracao | Autenticacao |
|----------------|-------------------|--------------|
| Kafka Broker | Protocolo Kafka (TCP) | SASL/PLAIN (producao) / sem auth (dev) |
| Schema Registry | REST API (HTTP) | Sem auth (dev) / Basic auth (producao) |
| Redis | Protocolo Redis (TCP) | Password (producao) / sem auth (dev) |
| Postgres | Protocolo Postgres (TCP) | Username/password via connection string |
| NextAuth.js | JWT internal | `NEXTAUTH_SECRET` env var |

---

## Arquitetura de Pipeline

### Diagrama do DAG

```text
                         ┌─────────────────────────────────────────┐
                         │            Kafka Broker (4.0)            │
                         │  Topic: sales-events (6 partitions)     │
                         │  Topic: sales-events-dlq                │
                         └──────────────┬──────────────────────────┘
                                        │
                                        ▼
                         ┌──────────────────────────────┐
                         │     Flink SQL JobManager      │
                         │  (Checkpoint: 30s, ForSt)     │
                         └──────────────┬───────────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    ▼                   ▼                   ▼
          ┌─────────────┐    ┌─────────────────┐   ┌───────────────┐
          │ Job: 5s Agg  │    │ Job: 1min Agg   │   │ Job: 1h Agg   │
          │ (TUMBLE 5s)  │    │ (TUMBLE 1min)   │   │ (TUMBLE 1h)   │
          └──────┬───────┘    └────────┬────────┘   └──────┬────────┘
                 │                     │                    │
                 ▼                     ▼                    ▼
          ┌───────────┐        ┌──────────────┐     ┌──────────────┐
          │   Redis   │        │   Postgres   │     │   Postgres   │
          │ (hot 24h) │        │  agg_1min    │     │  agg_1hour   │
          └───────────┘        └──────────────┘     └──────────────┘
                                       │
                                       ▼
                               ┌──────────────┐
                               │   Postgres   │
                               │  raw_events  │
                               │  (dedup)     │
                               └──────────────┘
```

### Estrategia de Particionamento

| Tabela | Chave de Particao | Granularidade | Justificativa |
|--------|-------------------|---------------|---------------|
| `raw_events` | `event_date` (derivado de `event_timestamp`) | Diaria | Volume alto (100K+/dia), queries sempre filtram por data; particao diaria facilita retencao e pruning |
| `agg_1min` | `window_start::date` | Diaria | Queries de analytics filtram por periodo; ~1440 registros/dia/regiao |
| `agg_1hour` | `window_start::date` | Diaria | ~24 registros/dia/regiao; particao diaria por consistencia |
| `agg_daily` | Nenhuma | N/A | Volume baixo (~1 registro/dia/regiao); sem necessidade de particao |

### Estrategia Incremental

| Modelo | Estrategia | Coluna-Chave | Lookback |
|--------|------------|--------------|----------|
| `raw_events` | Append + dedup | `event_id` | N/A (streaming continuo, dedup por `ON CONFLICT`) |
| `agg_1min` | Upsert por janela | `window_start` + `region` | 0 (cada janela e calculada uma vez pelo Flink) |
| `agg_1hour` | Upsert por janela | `window_start` + `region` | 0 |
| `agg_daily` | Recalculado do `agg_1hour` | `date` + `region` | 1 dia (recalcula o dia atual quando novos dados de 1h chegam) |

### Plano de Evolucao de Schema

| Tipo de Mudanca | Tratamento | Rollback |
|----------------|------------|----------|
| Nova coluna no evento | Adicionar campo opcional ao JSON Schema (backward compatible); Flink ignora campos desconhecidos; ALTER TABLE ADD COLUMN no Postgres com DEFAULT NULL | DROP COLUMN |
| Mudanca de tipo de coluna | Periodo de dual-write: producer envia ambos os formatos; Flink transforma; apos migracao completa, remover campo antigo | Reverter producer, reprocessar do Kafka |
| Remocao de coluna | Marcar como deprecated no JSON Schema; parar de enviar apos 30 dias; DROP COLUMN no Postgres apos confirmacao de nao-uso | Re-adicionar coluna, reprocessar |
| Novo valor de ENUM (status) | Adicionar ao JSON Schema (backward compatible); adicionar ao CHECK constraint do Postgres; Flink nao requer mudanca (string) | Remover do schema, limpar dados invalidos |

### Gates de Qualidade de Dados

| Gate | Ferramenta | Threshold | Acao em Falha |
|------|------------|-----------|---------------|
| Nulls em `event_id` | Validacao Pydantic no producer | 0 nulls | Rejeitar evento, enviar para DLQ |
| Duplicatas em `event_id` | Postgres `ON CONFLICT` + check periodico | 0 duplicatas | Ignorar silenciosamente (idempotencia) |
| Completude de campos obrigatorios | Pydantic `SaleEvent` | 100% dos 7 campos | Rejeitar evento, enviar para DLQ |
| Validade de `status` | Pydantic enum + JSON Schema | 100% em enum valido | Rejeitar evento, enviar para DLQ |
| Validade de `sale_amount` | Pydantic `ge=0` | 0 valores negativos | Rejeitar evento, enviar para DLQ |
| Timeliness Redis | Comparacao `event_timestamp` vs Redis write | 99.9% dentro de 30s | Alertar via log; investigar backpressure no Flink |
| Timeliness Postgres | Comparacao `event_timestamp` vs Postgres insert | 100% dentro de 5min | Alertar; verificar sink JDBC do Flink |
| Volume diario | Check de contagem vs media movel 7 dias | < 0.5x ou > 2.0x = alerta | Alertar; verificar saude do producer |
| Freshness do Redis | `MAX(window_end)` vs `NOW()` | Stale se > 1 minuto | Alertar; verificar Flink job status |

---

## Estrategia de Testes

| Tipo de Teste | Escopo | Arquivos | Ferramentas | Meta de Cobertura |
|---------------|--------|----------|-------------|-------------------|
| Unitario (pipeline) | Modelo Pydantic, funcoes de validacao | `test_schema.py`, `test_producer.py` | pytest, pydantic | 90% |
| Unitario (dashboard) | Hooks, componentes, utils | `use-sse.test.ts`, `kpi-card.test.tsx` | Vitest, React Testing Library | 80% |
| Integracao (pipeline) | Queries SQL contra Postgres real | `test_queries.py` | pytest, testcontainers-postgres | Todos os cenarios AT |
| Integracao (dashboard) | API Routes com mock de banco | `analytics.test.ts` | Vitest, MSW (Mock Service Worker) | Caminhos principais |
| E2E | Fluxo completo: producer → Kafka → Flink → Redis/PG → Dashboard | Manual / script | Docker Compose + curl + playwright | AT-001 a AT-005 |
| Carga | 100K eventos em 24h simulados | `simulator.py` + metricas | Confluent Kafka benchmark + Prometheus | AT-002 (< 2s response) |

### Mapeamento de Testes de Aceitacao

| AT-ID | Cenario | Como Testar | Automatizado? |
|-------|---------|-------------|---------------|
| AT-001 | Evento aparece em < 30s | `simulator.py` envia evento + Playwright verifica aparicao no dashboard | Sim (E2E) |
| AT-002 | 100K eventos sem degradacao | `simulator.py` com 100K eventos + medir latencia p99 do dashboard | Sim (Carga) |
| AT-003 | Comparacao de periodos | Seed Postgres com 7 dias + request para `/api/analytics/comparison` | Sim (Integracao) |
| AT-004 | Acesso nao autenticado bloqueado | Request sem session cookie para `/dashboard` → assert redirect 302 para `/login` | Sim (Integracao) |
| AT-005 | Falha no processador nao perde eventos | Parar Flink, enviar eventos, reiniciar Flink, verificar que todos eventos estao no Postgres | Semi-automatizado |

---

## Tratamento de Erros

| Tipo de Erro | Estrategia de Tratamento | Retry? | Componente |
|-------------|-------------------------|--------|------------|
| Evento invalido (schema) | Pydantic rejeita; evento enviado para DLQ com header `error` | Nao (requer correcao no producer) | Producer |
| Kafka delivery failure | Callback `on_delivery` loga erro; producer retenta ate 5x (config `retries`) | Sim (automatico pelo producer) | Producer |
| Kafka broker indisponivel | Producer usa buffer interno; retenta com backoff exponencial | Sim (automatico) | Producer |
| Flink checkpoint failure | Flink retenta automaticamente; se falhar 3x, alerta via metricas | Sim (automatico) | Flink |
| Flink job crash | Recovery do ultimo checkpoint bem-sucedido; at-least-once semantics | Sim (automatico) | Flink |
| Redis indisponivel | Flink sink retenta com backoff; dashboard SSE retorna erro ao client | Sim (Flink retenta) | Flink + Dashboard |
| Postgres connection lost | Flink JDBC sink retenta; API Routes retornam 503 com `Retry-After` | Sim (ambos) | Flink + Dashboard |
| SSE connection drop | Hook `useSSE` reconecta automaticamente apos `reconnectInterval` (3s) | Sim (client-side) | Dashboard |
| API 4xx (validacao) | Retorna erro estruturado com detalhes Zod; toast no frontend | Nao | Dashboard |
| API 5xx (servidor) | Loga erro; retorna 500 generico; toast com botao retry no frontend | Sim (manual) | Dashboard |
| Auth failure (401) | Middleware redireciona para `/login`; SSE retorna 401 | Nao | Dashboard |
| Render crash | `error.tsx` captura; mostra fallback UI com botao retry | Sim (manual, via `reset()`) | Dashboard |

---

## Configuracao

### Pipeline

| Chave de Config | Tipo | Padrao | Descricao |
|----------------|------|--------|-----------|
| `kafka.bootstrap_servers` | string | `kafka:9092` | Endereco dos brokers Kafka |
| `kafka.topic` | string | `sales-events` | Topico principal de eventos |
| `kafka.dlq_topic` | string | `sales-events-dlq` | Topico DLQ para eventos invalidos |
| `kafka.compression` | string | `zstd` | Algoritmo de compressao |
| `kafka.partitions` | int | `6` | Numero de particoes do topico |
| `kafka.replication_factor` | int | `3` | Fator de replicacao |
| `flink.checkpoint_interval` | string | `30s` | Intervalo de checkpoint |
| `flink.checkpoint_mode` | string | `EXACTLY_ONCE` | Modo de checkpoint |
| `flink.watermark_delay` | string | `10s` | Tolerancia de late data |
| `flink.state_backend` | string | `rocksdb` | Backend de estado (rocksdb para dev, forst para prod) |
| `flink.parallelism` | int | `4` | Paralelismo dos jobs |
| `redis.url` | string | `redis://redis:6379` | URL de conexao Redis |
| `redis.ttl_hours` | int | `24` | TTL das chaves de metricas |
| `postgres.url` | string | `postgresql://user:pass@postgres:5432/sales` | Connection string Postgres |

### Dashboard

| Chave de Config | Tipo | Padrao | Descricao |
|----------------|------|--------|-----------|
| `REDIS_URL` | string | `redis://localhost:6379` | URL de conexao Redis para SSE |
| `DATABASE_URL` | string | `postgresql://...` | Connection string Postgres para analytics |
| `NEXTAUTH_SECRET` | string | (obrigatorio) | Secret para JWT do NextAuth |
| `NEXTAUTH_URL` | string | `http://localhost:3000` | URL base da aplicacao |
| `SSE_INTERVAL_MS` | int | `5000` | Intervalo de push SSE (ms) |

---

## Consideracoes de Seguranca

- **Autenticacao obrigatoria**: Middleware NextAuth.js bloqueia todas as rotas `/dashboard/*`, `/analytics/*` e `/api/*` (exceto `/api/auth/*`) para usuarios nao autenticados (AT-004)
- **Credenciais em variaveis de ambiente**: Nenhuma credencial hardcoded; `.env.example` como template, `.env` no `.gitignore`
- **seller_id como potencial PII**: Questao Q-004 do DEFINE permanece aberta. Se confirmado como PII:
  - Aplicar hashing (SHA-256) ou tokenizacao no producer antes de publicar no Kafka
  - Armazenar mapeamento original em vault separado com acesso restrito
  - Alternativa: excluir `seller_id` das tabelas de agregacao (mantem apenas em `raw_events` com acesso restrito)
- **CORS**: API Routes devem configurar headers CORS restritivos (apenas dominio do dashboard)
- **Rate limiting**: API Routes de analytics devem ter rate limit para prevenir abuse (ex.: 100 req/min por usuario)
- **SQL Injection**: Todas as queries usam parametros preparados (`$1`, `$2`), nunca interpolacao de strings
- **Redis sem auth em dev**: Em producao, habilitar `requirepass` e TLS
- **Kafka sem auth em dev**: Em producao, habilitar SASL/PLAIN ou SASL/SCRAM + TLS
- **JWT rotation**: `NEXTAUTH_SECRET` deve ser rotacionado periodicamente; sessions existentes invalidam na rotacao

---

## Observabilidade

| Aspecto | Implementacao |
|---------|---------------|
| **Logging (Pipeline)** | Logging estruturado em JSON via Python `logging` com campos: `event_id`, `timestamp`, `level`, `component`, `message`. Flink logs via `log4j2` com JSON appender |
| **Logging (Dashboard)** | Console logging em dev; structured JSON em prod via `pino` ou Winston; request ID via middleware header `x-request-id` |
| **Metricas Kafka** | JMX metrics do broker: `UnderReplicatedPartitions`, `BytesInPerSec`, `RequestsPerSec`, consumer lag via `consumer_offset` |
| **Metricas Flink** | Flink Web UI (porta 8081): checkpoint duration, backpressure, records per second, watermark lag |
| **Metricas Redis** | `INFO` command: `connected_clients`, `used_memory`, `keyspace_hits/misses`, `expired_keys` |
| **Metricas Postgres** | `pg_stat_statements`: query duration p50/p95/p99; `pg_stat_user_tables`: sequential vs index scans |
| **Metricas Dashboard** | Next.js built-in analytics: Web Vitals (LCP, FID/INP, CLS); custom: SSE reconnection count, API response time |
| **Health checks** | Docker Compose healthchecks para todos os servicos; Next.js `/api/health` endpoint |
| **Alertas** | Fora do escopo do MVP (YAGNI conforme DEFINE). Monitorar manualmente via dashboards de metricas. Para v2: Prometheus + Grafana + Alertmanager |

### SLA de Observabilidade

| Metrica | Meta | Como Medir |
|---------|------|------------|
| Latencia end-to-end (evento a tela) | < 30s (MUST) | `event_timestamp` vs timestamp de renderizacao no dashboard |
| Latencia Redis write | < 30s (MUST) | `event_timestamp` vs Redis `HSET` timestamp |
| Latencia Postgres write | < 5 min | `event_timestamp` vs `inserted_at` no Postgres |
| Uptime do pipeline | 99% em 30 dias | Monitoramento de health checks + incidentes |
| Consumer lag | < 1000 mensagens | Kafka consumer group offset monitoring |
| Flink checkpoint duration | < 10s | Flink Web UI metricas |

---

## Riscos, Blockers e Restricoes Tecnicas

### Riscos Identificados

| # | Risco | Probabilidade | Impacto | Mitigacao |
|---|-------|--------------|---------|-----------|
| R-001 | Flink 2.0 + Kafka 4.0 compatibilidade de conectores | Media | Alto | Validar com PoC antes do build; fallback para Kafka 3.7 se necessario |
| R-002 | Redis single-instance nao suporta 100+ usuarios concorrentes (premissa A-001) | Baixa | Medio | Redis 7 suporta 10K+ connections; se necessario, adicionar Redis Cluster |
| R-003 | Volume de pico (Black Friday) excede 10x o normal (premissa A-006) | Baixa (fora do MVP) | Alto | Kafka particoes + Flink paralelismo escalam horizontalmente; monitorar consumer lag |
| R-004 | SSE connection limit do browser (6 por dominio em HTTP/1.1) | Media | Medio | Usar HTTP/2 (multiplex); ou single SSE connection com multiplexacao de metricas |
| R-005 | Watermark de 10s pode descartar eventos late > 10s | Baixa | Medio | Monitorar taxa de descarte; aumentar watermark se necessario; late events vao para DLQ |
| R-006 | JSON Schema overhead para alto volume | Baixa (volume atual OK) | Medio | Se volume crescer 100x, migrar para Avro com Schema Registry |
| R-007 | Flink state size cresce com cardinalidade de `region` x `product_id` | Baixa | Medio | State TTL de 24h limita crescimento; monitorar via Flink Web UI |
| R-008 | Next.js SSE route handler pode ter limite de conexoes concorrentes | Media | Alto | Testar com 100+ conexoes em carga; se necessario, mover SSE para servico dedicado (Node.js ou Go) |

### Blockers

| # | Blocker | Resolvido? | Acao |
|---|---------|-----------|------|
| B-001 | Q-001: Provedor de cloud para producao nao definido | Nao | Design feito cloud-agnostic (Docker Compose para dev); decisao de cloud adiada. Para build, usar apenas dev local |
| B-002 | Q-004: `seller_id` e PII? | Nao | Implementar sem mascaramento no MVP; adicionar layer de anonimizacao se confirmado como PII |

### Restricoes Tecnicas (do KB)

| # | Restricao | Origem | Impacto no Design |
|---|-----------|--------|-------------------|
| C-001 | Flink 2.0 removeu DataSet API e Scala API | `streaming/concepts/flink-architecture.md` | Usar apenas Flink SQL (sem DataStream em Scala); Java DataStream API como fallback |
| C-002 | Flink 2.0 Source/Sink V1 removidos | `streaming/concepts/flink-architecture.md` | Garantir que conectores Kafka e JDBC usem Source V2 / Sink V2 |
| C-003 | Kafka 4.0 KRaft-only | `streaming/concepts/kafka-fundamentals.md` | Docker Compose deve configurar KRaft, nao ZooKeeper |
| C-004 | Next.js App Router: layouts sao Server Components por padrao | `nextjs/concepts/app-router.md` | Providers (SessionProvider, QueryClientProvider) devem estar em Client Component wrapper |
| C-005 | Middleware Next.js deve ser leve (apenas cookies/headers) | `nextjs/concepts/middleware.md` | Auth check no middleware apenas verifica cookie; nao fazer fetch externo |
| C-006 | useEffect para data fetching e anti-pattern | `react/concepts/hooks-patterns.md` | Usar Server Components para fetch ou React Query para client |
| C-007 | Dynamic import para componentes pesados (graficos) | `frontend-patterns/concepts/performance.md` | Chart components devem usar `dynamic(() => import(...), { ssr: false })` |
| C-008 | ROW_NUMBER sem ORDER BY e nao-deterministico | `sql-patterns/concepts/window-functions.md` | Toda deduplicacao deve ter `ORDER BY event_timestamp DESC` explicito |
| C-009 | Flink sem watermark em event-time = estado infinito | `streaming/concepts/stream-processing-fundamentals.md` | Watermark obrigatorio em `event_timestamp`; state TTL como segunda barreira |
| C-010 | DLQ obrigatoria para poison messages | `streaming-engineer` agent anti-patterns | Todo consumer deve rotear mensagens invalidas para DLQ, nunca descartar silenciosamente |

---

## Modelo de Dados Postgres

### Tabela `raw_events`

```sql
CREATE TABLE raw_events (
    event_id        UUID PRIMARY KEY,
    event_timestamp TIMESTAMPTZ NOT NULL,
    sale_amount     DECIMAL(18, 2) NOT NULL CHECK (sale_amount >= 0),
    product_id      VARCHAR(64) NOT NULL,
    seller_id       VARCHAR(64) NOT NULL,
    region          VARCHAR(64) NOT NULL,
    status          VARCHAR(16) NOT NULL CHECK (status IN ('completed', 'pending', 'cancelled')),
    inserted_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
) PARTITION BY RANGE (event_timestamp);

-- Particao por dia (criar via cron ou pg_partman)
CREATE TABLE raw_events_2026_03_29 PARTITION OF raw_events
    FOR VALUES FROM ('2026-03-29') TO ('2026-03-30');

CREATE INDEX idx_raw_events_timestamp ON raw_events (event_timestamp);
CREATE INDEX idx_raw_events_region ON raw_events (region);
CREATE INDEX idx_raw_events_product ON raw_events (product_id);
```

### Tabela `agg_1min`

```sql
CREATE TABLE agg_1min (
    window_start    TIMESTAMPTZ NOT NULL,
    window_end      TIMESTAMPTZ NOT NULL,
    region          VARCHAR(64) NOT NULL,
    order_count     BIGINT NOT NULL,
    total_revenue   DECIMAL(18, 2) NOT NULL,
    avg_ticket      DECIMAL(18, 2) NOT NULL,
    unique_products INT NOT NULL,
    PRIMARY KEY (window_start, region)
);

CREATE INDEX idx_agg_1min_date ON agg_1min ((window_start::date));
```

### Tabela `agg_1hour`

```sql
CREATE TABLE agg_1hour (
    window_start    TIMESTAMPTZ NOT NULL,
    window_end      TIMESTAMPTZ NOT NULL,
    region          VARCHAR(64) NOT NULL,
    order_count     BIGINT NOT NULL,
    total_revenue   DECIMAL(18, 2) NOT NULL,
    avg_ticket      DECIMAL(18, 2) NOT NULL,
    unique_products INT NOT NULL,
    PRIMARY KEY (window_start, region)
);

CREATE INDEX idx_agg_1hour_date ON agg_1hour ((window_start::date));
```

### Tabela `users` (para NextAuth.js)

```sql
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(255) UNIQUE NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    name            VARCHAR(255),
    role            VARCHAR(32) DEFAULT 'viewer',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

## Estrutura de Diretorios

```text
sales-dashboard/
├── pipeline/
│   ├── docker-compose.yml          # Kafka, Flink, Redis, Postgres, Schema Registry
│   ├── producer/
│   │   ├── config.yaml             # Configuracao do producer
│   │   ├── requirements.txt        # confluent-kafka, pydantic, pyyaml
│   │   ├── schema.py               # Modelo Pydantic SaleEvent
│   │   ├── producer.py             # Kafka producer idempotente
│   │   └── simulator.py            # Gerador de eventos sinteticos
│   ├── flink/
│   │   ├── flink-conf.yaml         # Configuracao Flink
│   │   └── sql/
│   │       ├── create_source.sql   # DDL: source Kafka com watermark
│   │       ├── agg_5s_redis.sql    # DML: TUMBLE 5s para Redis
│   │       ├── agg_1min_postgres.sql   # DML: TUMBLE 1min para Postgres
│   │       ├── agg_1hour_postgres.sql  # DML: TUMBLE 1h para Postgres
│   │       └── raw_events_postgres.sql # DML: eventos brutos para Postgres (dedup)
│   ├── postgres/
│   │   ├── init.sql                # DDL: tabelas, indices, particoes
│   │   └── queries/
│   │       └── analytics_queries.sql   # Queries de agregacao para API
│   ├── schemas/
│   │   └── sale_event.json         # JSON Schema para Schema Registry
│   ├── quality/
│   │   └── data_quality_checks.yaml    # Checks de qualidade de dados
│   └── tests/
│       ├── test_schema.py          # Testes do modelo Pydantic
│       ├── test_producer.py        # Testes do producer
│       └── test_queries.py         # Testes das queries SQL
│
└── dashboard/
    ├── package.json
    ├── tsconfig.json
    ├── next.config.ts
    ├── .env.example
    └── src/
        ├── middleware.ts           # Auth middleware
        ├── app/
        │   ├── layout.tsx          # Root layout + providers
        │   ├── page.tsx            # Redirect para /dashboard ou /login
        │   ├── error.tsx           # Error boundary
        │   ├── global-error.tsx    # Global error boundary
        │   ├── not-found.tsx       # 404
        │   ├── login/
        │   │   └── page.tsx        # Pagina de login
        │   ├── dashboard/
        │   │   ├── page.tsx        # Modo operacional (SSE real-time)
        │   │   └── loading.tsx     # Skeleton
        │   ├── analytics/
        │   │   ├── page.tsx        # Modo analytics (historico)
        │   │   └── loading.tsx     # Skeleton
        │   └── api/
        │       ├── auth/
        │       │   └── [...nextauth]/
        │       │       └── route.ts    # NextAuth route handler
        │       ├── sse/
        │       │   └── metrics/
        │       │       └── route.ts    # SSE endpoint (Redis para client)
        │       └── analytics/
        │           ├── summary/
        │           │   └── route.ts    # Agregacoes por periodo
        │           └── comparison/
        │               └── route.ts    # Comparacao entre periodos
        ├── lib/
        │   ├── auth.ts             # NextAuth.js v5 config
        │   └── api.ts              # Fetch wrapper tipado + Zod
        ├── hooks/
        │   ├── use-sse.ts          # Hook SSE com reconexao automatica
        │   └── use-sales-metrics.ts    # Hook de metricas de vendas
        ├── components/
        │   ├── ui/
        │   │   ├── skeleton.tsx
        │   │   └── error-message.tsx
        │   ├── dashboard/
        │   │   ├── kpi-card.tsx
        │   │   ├── sales-chart.tsx
        │   │   └── region-breakdown.tsx
        │   └── analytics/
        │       ├── period-selector.tsx
        │       ├── comparison-chart.tsx
        │       └── data-table.tsx
        ├── types/
        │   └── api.ts              # Tipos TypeScript compartilhados
        └── __tests__/
            ├── hooks/
            │   └── use-sse.test.ts
            ├── components/
            │   └── kpi-card.test.tsx
            └── api/
                └── analytics.test.ts
```

---

## Questoes Abertas Herdadas do DEFINE

| # | Questao | Status | Decisao de Design |
|---|---------|--------|-------------------|
| Q-001 | Provedor de cloud para producao? | Aberta | Design cloud-agnostic; Docker Compose para dev. Decisao adiada para pre-producao |
| Q-002 | Flink ou Spark Structured Streaming? | **Resolvida** | Flink SQL (Decisao 1 deste DESIGN) |
| Q-003 | SLA de 99% alinhado com stakeholder? | Aberta | Assumido para design; validar antes do build |
| Q-004 | `seller_id` e PII? | Aberta | Implementar sem mascaramento no MVP; preparar layer de anonimizacao como extensao |

---

## Premissas Validadas pelo Design

| ID | Premissa | Validacao |
|----|----------|-----------|
| A-001 | Redis suporta 100+ usuarios concorrentes | Parcialmente validada: Redis 7 suporta 10K+ connections nativamente. SSE com 100 usuarios = 100 connections ao Redis (via pool no Next.js). Sem risco para MVP |
| A-002 | Kafka e a unica fonte | Confirmada pelo DEFINE. Topico unico `sales-events` |
| A-003 | Browsers modernos com suporte SSE | Confirmada: EventSource API suportada em todos os browsers modernos (Chrome, Firefox, Safari, Edge). Sem necessidade de polyfill |
| A-004 | At-least-once semantics | Mitigada: Deduplicacao em 3 camadas (Decisao 6). Flink + Postgres garantem zero duplicatas na pratica |
| A-005 | Single tenant no MVP | Confirmada. Sem isolamento multi-tenant. Modelo de dados sem coluna `tenant_id` |
| A-006 | Volume estavel (100K/dia) | Assumida para MVP. Kafka 6 particoes + Flink paralelismo 4 = headroom para ~3x sem reconfig |

---

## Historico de Revisoes

| Versao | Data | Autor | Mudancas |
|--------|------|-------|----------|
| 1.0 | 2026-03-29 | design-agent (Pipeline C) | Versao inicial -- draft multi-agent, 7 decisoes arquiteturais, 54 arquivos, 7 agentes matched |

---

## Proximo Passo

**Pronto para:** `/build .claude/sdd/features/DESIGN_SALES_DASHBOARD_PIPELINE_C.md`
