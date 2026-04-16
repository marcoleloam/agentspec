# DEFINE: Sales Dashboard Real-Time

> Pipeline de dados Kafka + processamento Flink SQL + dashboard Next.js com dois modos de visualizacao (operacional e analytics)

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | SALES_DASHBOARD |
| **Data** | 2026-03-29 |
| **Autor** | define-multiagent |
| **Status** | Pronto para Design |
| **Clarity Score** | 15/15 (14 pre-consulta + 1 pos-consulta) |
| **Modo** | Multi-agent final (Pipeline B do teste comparativo — validado por 4 especialistas) |

---

## Declaracao do Problema

O time de vendas nao tem visibilidade em tempo real sobre metricas de vendas, e a gestao comercial nao consegue analisar tendencias historicas de forma consolidada — resultando em decisoes reativas baseadas em dados com atraso de horas ou tomadas a partir de planilhas manuais.

---

## Usuarios-Alvo

| Usuario | Papel | Dor |
|---------|-------|-----|
| Time de vendas | Operadores do dia a dia | Precisam reagir rapido a quedas de performance ou picos de venda, mas hoje so visualizam dados no fim do dia |
| Gestao comercial | Tomadores de decisao estrategica | Precisam comparar periodos (hoje vs ontem, semana vs semana) e identificar tendencias, mas hoje dependem de planilhas manuais consolidadas manualmente |

---

## Objetivos

O que significa sucesso (priorizado):

| Prioridade | Objetivo |
|------------|----------|
| **MUST** | Construir pipeline end-to-end: Kafka producer + Schema Registry (Avro) + Flink SQL + Redis + Postgres |
| **MUST** | Dashboard operacional (`/ops`) com atualizacao near real-time via SSE (latencia < 30 segundos) |
| **MUST** | Dashboard analytics (`/analytics`) com comparacao historica entre periodos via Server Components + ISR/PPR |
| **MUST** | Dead Letter Queue (DLQ) implementada desde o dia 1 para capturar eventos malformados sem derrubar o pipeline |
| **MUST** | Schema Registry com Avro garantindo compatibilidade backward de eventos desde o dia 1 |
| **MUST** | Autenticacao implementada — dashboard nao e publico |
| **SHOULD** | Watermarks e TTL de estado configurados no Flink SQL para evitar acumulo de estado indefinido |
| **SHOULD** | Hook `useSSEStream` com cleanup correto no `useEffect` e backoff exponencial para evitar memory leaks |
| **SHOULD** | Dynamic imports com `next/dynamic` para bibliotecas de charting (evitar bundle bloat ~300KB) |
| **COULD** | Alertas automaticos (Slack/email) — nao essencial para MVP |
| **COULD** | Export CSV/PDF — nice-to-have, nao bloqueia uso do dashboard |
| **COULD** | Multi-tenancy — comecar com uma empresa, escalar depois |

**Guia de Prioridade:**
- **MUST** = O MVP falha sem isso
- **SHOULD** = Importante, mas existe alternativa
- **COULD** = Nice-to-have, cortar primeiro se necessario

---

## Criterios de Sucesso

Resultados mensuraveis (devem incluir numeros):

- [ ] Dashboard exibe metricas de vendas com latencia < 30 segundos do evento ao display
- [ ] Modo analytics permite comparacao entre periodos (hoje vs ontem, semana vs semana anterior)
- [ ] Sistema suporta 100K+ eventos/dia (~1-2 evt/s media, bursts de 5-10x) sem degradacao de performance
- [ ] DLQ captura 100% dos eventos malformados sem interromper o fluxo principal
- [ ] Schema Registry garante compatibilidade backward — adicao de campos novos nao quebra consumers existentes
- [ ] Autenticacao implementada e funcional antes do deploy em producao
- [ ] Bundle do frontend < 500KB para a rota `/ops` com dynamic imports aplicados
- [ ] Watermarks e TTL de estado configurados no Flink SQL (sem state acumulado apos window expirar)

---

## Testes de Aceitacao

| ID | Cenario | Dado | Quando | Entao |
|----|---------|------|--------|-------|
| AT-001 | Evento de venda aparece no dashboard operacional | Pipeline rodando, Redis com dados hot | Evento publicado no Kafka topic `sales-events` | Metrica atualizada no `/ops` em < 30 segundos |
| AT-002 | Evento malformado e tratado pela DLQ | Pipeline rodando, evento com schema incorreto | Evento sem campo obrigatorio publicado no Kafka | Evento roteado para `sales-events-dlq`, pipeline continua sem interrupcao |
| AT-003 | Campo novo adicionado ao schema Avro | Schema Registry configurado | Novo campo opcional adicionado ao schema | Consumers existentes continuam funcionando sem redeployar (compatibilidade backward) |
| AT-004 | Comparacao historica no modo analytics | Postgres com dados historicos de 7+ dias | Usuario acessa `/analytics` e seleciona comparacao semana atual vs semana passada | Dados corretos exibidos via Server Components com ISR |
| AT-005 | SSE nao causa memory leak no frontend | Pagina `/ops` aberta por 30+ minutos | Usuario navega para outra rota e volta | Sem memory leak; EventSource anterior destruido no cleanup do `useEffect` |
| AT-006 | Dashboard nao acessivel sem autenticacao | Sistema em producao | Usuario nao autenticado tenta acessar `/ops` ou `/analytics` | Redirecionado para pagina de login |

---

## Fora do Escopo

Explicitamente NAO incluido nesta feature:

- Alertas automaticos (Slack/email) — confirmado YAGNI no brainstorm
- Export CSV/PDF — confirmado YAGNI no brainstorm
- Multi-tenancy — comecar com uma empresa, escalar depois (confirmado YAGNI)
- App mobile — nao mencionado como requisito
- Deploy em plataforma serverless (Vercel) — SSE e incompativel com serverless por timeout; deploy obrigatoriamente em Node.js custom server
- Spark Structured Streaming — superdimensionado para 100K eventos/dia (~1-2 evt/s); decisao confirmada por dois especialistas de streaming
- WebSocket — dados sao unidirecionais; SSE e suficiente e mais simples

---

## Restricoes

| Tipo | Restricao | Impacto |
|------|-----------|---------|
| Tecnica | Next.js como stack frontend (decisao do usuario) | Design e build devem usar App Router com dual-mode (`/ops` + `/analytics`) |
| Tecnica | Latencia aceitavel de 5-30 segundos (near real-time, nao real-time absoluto) | SSE e viavel; WebSocket desnecessario |
| Tecnica | Deploy obrigatoriamente em Node.js custom server | SSE incompativel com serverless (Vercel timeout); nao e possivel usar Vercel no modo padrao |
| Tecnica | Flink SQL como processador streaming (nao Spark SS) | Decisao tecnica baseada no volume: 100K/dia e ~1-2 evt/s nao justifica overhead de cluster Spark |
| Tecnica | Schema Registry + Avro obrigatorio desde o dia 1 | Sem schema registry, adicao de campo pela area comercial quebra o deserializador de todos os consumers |
| Tecnica | DLQ obrigatoria desde o dia 1 | Sem DLQ, mensagem malformada derruba o pipeline inteiro |
| Tecnica | Watermarks e TTL de estado no Flink SQL | Sem TTL, estado Flink acumula indefinidamente e causa OOM em producao |
| Tecnica | Kafka topic com minimo 6 particoes, chave por `store_id` | Garantir paralelismo adequado no Flink e ordering por loja |
| Projeto | Projeto end-to-end do zero | Nao existe nenhuma infraestrutura preexistente; escopo inclui producers + Kafka + processamento + dashboard |

---

## Contexto Tecnico

> Contexto essencial para a fase de Design.

| Aspecto | Valor | Notas |
|---------|-------|-------|
| **Localizacao de Deploy** | Monorepo: `pipeline/` + `dashboard/` | Dois modulos separados — pipeline de dados e frontend |
| **Dominios KB** | `streaming`, `nextjs`, `react`, `frontend-patterns`, `sql-patterns` | 5 dominios cross-domain (DE + frontend); confirmados no brainstorm |
| **Impacto IaC** | Novos recursos | Docker Compose para dev local; definir stack cloud para producao na fase de Design |

**Por Que Isso Importa:**

- **Localizacao** → Fase de Design usa a estrutura correta do projeto, evita arquivos mal posicionados
- **Dominios KB** → Fase de Design puxa os padroes corretos de `.claude/kb/`
- **Impacto IaC** → Infraestrutura completa a definir: Kafka cluster, Flink job, Redis, Postgres, Node.js server

---

## Contrato de Dados

### Inventario de Origens

| Origem | Tipo | Volume | Frequencia | Responsavel |
|--------|------|--------|------------|-------------|
| `sales-events` | Kafka topic | 100K+ eventos/dia (~1-2 evt/s media; bursts 5-10x) | Real-time continuo | Time de engenharia |
| `sales-events-dlq` | Kafka topic (DLQ) | Subconjunto de eventos malformados | Eventual (on error) | Time de engenharia |

### Esboco do Fluxo de Dados (Abordagem A — Selecionada)

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
                              [Next.js App Router — Node.js custom server]
                              ├─ /ops      → Client Components + SSE + Zustand
                              └─ /analytics → Server Components + ISR/PPR + Suspense
```

### Contrato de Schema (Rascunho — A Definir no Design)

| Coluna | Tipo | Restricoes | PII? |
|--------|------|------------|------|
| `event_id` | UUID | NOT NULL, UNIQUE | Nao |
| `store_id` | VARCHAR | NOT NULL (chave de particao Kafka) | Nao |
| `product_id` | VARCHAR | NOT NULL | Nao |
| `amount` | DECIMAL(18,2) | NOT NULL, >= 0 | Nao |
| `quantity` | INT | NOT NULL, > 0 | Nao |
| `seller_id` | VARCHAR | NOT NULL | Potencialmente |
| `event_ts` | TIMESTAMP | NOT NULL (usado como watermark Flink) | Nao |
| `status` | ENUM | `completed` \| `cancelled` \| `pending` | Nao |

> Nota: Schema Avro final a ser definido e registrado no Schema Registry na fase de Design. Compatibilidade BACKWARD obrigatoria em todas as evolucoes.

### SLAs de Atualizacao

| Camada | Meta | Medicao |
|--------|------|---------|
| Hot (Redis) | Dentro de 30 segundos apos evento publicado no Kafka | Comparacao de timestamp evento vs timestamp Redis |
| Cold (Postgres) | Janela de 1 hora (TUMBLE 1h Flink SQL) | Tempo de conclusao da janela Flink |
| Frontend `/ops` | Exibicao em < 30 segundos do evento ao display | Timestamp evento vs render no browser |

### Metricas de Completude

- 100% dos eventos malformados capturados na DLQ sem interrupcao do pipeline principal
- Zero eventos perdidos em condicoes normais de operacao (sem DLQ overflow)
- Todos os campos NOT NULL presentes em 100% dos eventos no topico principal

### Requisitos de Lineage

- Rastreabilidade de `event_id` do Kafka producer ao Redis/Postgres
- Eventos na DLQ devem conter motivo do erro para reprocessamento futuro

---

## Premissas

Premissas que, se incorretas, podem invalidar o design:

| ID | Premissa | Se Errada, Impacto |  Validada? |
|----|----------|--------------------|-----------|
| A-001 | Latencia de 5-30 segundos e aceitavel para o time de vendas | Se precisar de < 1s, SSE e o fluxo inteiro precisam ser revistos; WebSocket e streaming dedicado necessarios | [ ] |
| A-002 | Volume pico nao excede 10x a media (bursts de 5-10x sobre ~1-2 evt/s) | Se volume for muito maior, dimensionamento do Kafka, Flink e Redis precisa ser revisado | [ ] |
| A-003 | ETL nao exige joins entre streams nem logica de janela complexa na V1 | Se exigir, Abordagem B (consumer Python) nao seria viavel; Flink SQL confirma como obrigatorio | [ ] |
| A-004 | Node.js custom server e viavel como ambiente de deploy | Se obrigatorio usar plataforma serverless, SSE precisa ser substituido por polling ou WebSocket via solucao alternativa | [ ] |
| A-005 | Time tem ou pode adquirir familiaridade com Flink SQL 2.0 | Se curva de aprendizado for bloqueante, Abordagem B (consumer Python) e fallback valido para ETL simples | [ ] |
| A-006 | Uma unica empresa/tenant na V1 | Se multi-tenancy for exigido antes do launch, escopo aumenta significativamente | [ ] |

**Nota:** Validar A-001, A-004 e A-005 antes da fase de DESIGN. Sao os de maior risco tecnico.

---

## Bloqueios Identificados pelos Especialistas

> Secao adicional capturando bloqueios da consulta multi-agente do brainstorm. Todos os bloqueios ALTO devem ser mitigados antes ou durante a fase de Design.

| Bloqueio | Especialista | Severidade | Mitigacao Obrigatoria |
|----------|-------------|------------|-----------------------|
| SSE incompativel com serverless (timeout Vercel) | `@frontend-architect` | **Alto** | Deploy obrigatorio em Node.js custom server; serverless descartado do escopo |
| Schema evolution sem Schema Registry | `@streaming-engineer` | **Alto** | Avro + Schema Registry configurados no dia 1, antes do primeiro evento em producao |
| DLQ ausente derruba pipeline inteiro | `@streaming-engineer` | **Alto** | DLQ obrigatoria como requisito MUST; nao existe MVP sem DLQ |
| State TTL nao configurado no Flink | `@spark-streaming-architect` | **Alto** | Watermarks + TTL obrigatorios no Flink SQL; configurar como parte do job desde o inicio |
| Memory leak com EventSource no React | `@react-developer` | **Medio** | Cleanup no `useEffect` + backoff exponencial no hook `useSSEStream` |
| Bundle bloat com charting libs (~300KB) | `@react-developer` + `@frontend-architect` | **Medio** | Dynamic imports com `next/dynamic` para todos os componentes de charting |

---

## Decisoes Tecnicas Confirmadas (Do Brainstorm)

> Decisoes tomadas na fase de exploração com justificativa e alternativa rejeitada. Devem ser respeitadas na fase de Design.

| # | Decisao | Justificativa | Alternativa Rejeitada |
|---|---------|---------------|-----------------------|
| 1 | Flink SQL (nao Spark SS) | 100K/dia e ~1-2 evt/s; Spark SS superdimensionado para esse volume | Spark Structured Streaming |
| 2 | Schema Registry + Avro | Schema evolui; campo novo sem registry quebra todos os deserializadores | Schema inline (fragil) |
| 3 | DLQ desde o dia 1 | Mensagem malformada sem DLQ derruba o pipeline inteiro | Sem DLQ (risco critico inaceitavel) |
| 4 | Node.js custom server | SSE incompativel com serverless por timeout | Vercel serverless |
| 5 | Zustand (nao React Context) | Subscricao granular por slice evita re-renders em arvore | React Context (re-render cascade) |
| 6 | Dual-mode App Router (`/ops` + `/analytics`) | Separacao clara de concerns: real-time (Client) vs historico (RSC) | SPA unico (concerns misturados) |
| 7 | Redis + Postgres (nao apenas Postgres) | Hot data (real-time) precisa de latencia de leitura < 5ms; Postgres insuficiente para isso | Postgres unico |
| 8 | SSE (nao WebSocket) | Dados sao unidirecionais; SSE e mais simples e suficiente | WebSocket (bidirecional desnecessario) |

---

## Agentes Recomendados para Design e Build

| Fase | Agentes | Motivo |
|------|---------|--------|
| Design (streaming) | `@streaming-engineer`, `@spark-streaming-architect` | Arquitetura Flink SQL + Kafka + Schema Registry + DLQ |
| Design (frontend) | `@frontend-architect`, `@react-developer` | Next.js dual-mode App Router + SSE + Zustand |
| Design (schema) | `@schema-designer` | Schema Avro de eventos de venda + contrato de dados |
| Build (streaming) | `@streaming-engineer` | Implementacao Flink SQL jobs + Kafka config |
| Build (frontend) | `@react-developer`, `@frontend-architect` | Next.js components + hook `useSSEStream` + dynamic imports |
| Build (data quality) | `@data-quality-analyst` | Validacao de eventos + metricas de completude |

---

## Detalhamento do Clarity Score

| Elemento | Score (0-3) | Notas |
|----------|-------------|-------|
| Problema | 3/3 | Declaracao clara e especifica; dois perfis de usuario com dores distintas identificados |
| Usuarios | 3/3 | Dois usuarios definidos com papeis e dores especificas e mensuravelmente diferentes |
| Objetivos | 3/3 | MoSCoW completo; 6 MUSTs, 3 SHOULDs, 3 COULDs com justificativa tecnica |
| Sucesso | 3/3 | Todos os criterios tem numeros (< 30s, 100K+/dia, 100%, < 500KB) |
| Escopo | 2/3 | Fora do escopo explicito e bem definido; algumas decisoes de infra (cloud vs on-prem) ainda abertas para Design |
| **Total** | **14/15** | |

**Guia de Pontuacao:**
- 0 = Totalmente ausente
- 1 = Vago ou incompleto
- 2 = Claro mas faltam detalhes
- 3 = Cristalino e acionavel

**Minimo para prosseguir: 12/15**

---

## Questoes em Aberto

1. Qual a plataforma de cloud para producao? (AWS / GCP / Azure / on-prem) — impacta escolha do Kafka managed (MSK, Confluent Cloud, etc.) e do runtime Flink
2. Autenticacao: usar solucao existente (Okta, Auth0, NextAuth) ou implementar custom? — impacta escopo do build
3. Schema Avro final: quais campos sao obrigatorios vs opcionais? — a definir e registrar no Schema Registry na fase de Design
4. Flink SQL 2.0 (DataStream API removida): time tem familiaridade ou precisa de capacitacao? — impacta timeline do build

---

## Historico de Revisoes

| Versao | Data | Autor | Mudancas |
|--------|------|-------|----------|
| 1.0 | 2026-03-29 | define-agent | Versao inicial — extraida do BRAINSTORM_SALES_DASHBOARD_MULTIAGENT.md |
| 2.0 | 2026-03-30 | define-multiagent | Validacao por 4 especialistas: 10 requisitos adicionados, 3 criterios ajustados, 8 restricoes descobertas |

---

## Validacao Multi-Agente

### Especialistas Consultados

| Agente | Dominio | Confidence | Contribuicao |
|--------|---------|------------|--------------|
| `@streaming-engineer` | Kafka, Flink, stream processing | 0.88 | 3 MUSTs + 3 SHOULDs + flagou "zero duplicatas" como irrealista |
| `@spark-streaming-architect` | Spark SS, streaming patterns | 0.87 | 3 MUSTs + 2 SHOULDs + gap de latencia janela 5s + watermark 10s = 15s |
| `@frontend-architect` | Next.js, frontend patterns | 0.88 | 3 MUSTs + 3 SHOULDs + 4 restricoes ocultas + flagou "< 30s" como permissivo |
| `@react-developer` | React, hooks, state management | 0.88 | 4 MUSTs + 3 SHOULDs + metricas de re-render e bundle |

### Requisitos Adicionados por Especialistas

| # | Requisito | Prioridade | Especialista | Motivo |
|---|-----------|-----------|-------------|--------|
| R1 | Watermark strategy definida para event-time processing | MUST | `@streaming-engineer` | Sem watermark, janelas nunca fecham e estado cresce infinitamente |
| R2 | Semantica de entrega definida (exactly-once vs at-least-once) | MUST | `@streaming-engineer` + `@spark-streaming-architect` | "Zero duplicatas" implica exactly-once mas nao estava declarado |
| R3 | Partition key strategy por topico Kafka | MUST | `@streaming-engineer` | Sem chave coerente, hotspots ou reordenamento entre particoes |
| R4 | Checkpoint interval e state backend configurados | MUST | `@spark-streaming-architect` | Recovery dentro do SLA de 30s exige checkpoint <= 20s |
| R5 | State retention com TTL configurado | MUST | `@spark-streaming-architect` | Janelas de 1h acumulam estado sem limite sem TTL |
| R6 | Error Boundary no componente SSE | MUST | `@react-developer` + `@frontend-architect` | Sem ele, falha de stream derruba dashboard inteiro |
| R7 | Loading states / Suspense boundaries por widget | MUST | `@react-developer` + `@frontend-architect` | PPR exige Suspense explicito; evita layout shift |
| R8 | Indicador visual de status da conexao SSE | MUST | `@react-developer` | Usuario precisa saber se esta conectado/reconectando/offline |
| R9 | Zustand store com selectors memorizados | MUST | `@react-developer` | Evita re-renders em cascata quando stream atualiza um KPI |
| R10 | Retencao de topico Kafka definida (retention.ms) | SHOULD | `@streaming-engineer` | Sem retencao definida, recovery de checkpoint pode falhar |
| R11 | Schema evolution policy (BACKWARD) | SHOULD | `@streaming-engineer` | Mudanca de schema sem policy quebra consumers |
| R12 | Replication factor + min.insync.replicas | SHOULD | `@streaming-engineer` | Durabilidade dos topicos nao estava capturada |
| R13 | Router Cache strategy para troca de modo | SHOULD | `@frontend-architect` | Dados stale de 30s aparecem na troca ops/analytics |
| R14 | Bundle budget por modo (charts dynamic import) | SHOULD | `@frontend-architect` + `@react-developer` | Bundle < 100-150KB gzipped para first load |
| R15 | RBAC (niveis de acesso por papel) | SHOULD | `@frontend-architect` | "Autenticacao" definida mas sem niveis de acesso |
| R16 | Comportamento offline documentado | SHOULD | `@react-developer` | O que o usuario ve quando SSE cai por mais de X segundos? |
| R17 | Estrategia de reprocessamento em falha de checkpoint | SHOULD | `@spark-streaming-architect` | Sem fallback definido para perda de checkpoint |
| R18 | Comportamento em falha de sink (Redis/Postgres indisponivel) | SHOULD | `@spark-streaming-architect` | Pipeline pausa ou descarta? |

### Restricoes Descobertas por Especialistas

| # | Restricao | Especialista | Impacto |
|---|-----------|-------------|---------|
| C1 | Janela 5s + watermark 10s = 15s de latencia real, nao 5s | `@spark-streaming-architect` | SLA de latencia precisa considerar o gap do watermark |
| C2 | Consumer group rebalance (KIP-848) pode pausar consumo 5-30s em bursts | `@streaming-engineer` | Coincide com o limite de latencia declarado |
| C3 | Middleware Next.js intercepta rota SSE — excluir do matcher | `@frontend-architect` | Middleware pode quebrar conexao de longa duracao |
| C4 | `output: "standalone"` obrigatorio no next.config para custom server | `@frontend-architect` | Afeta Dockerfile e servico de assets estaticos |
| C5 | PPR requer `experimental.ppr = true` — confirmar estabilidade na versao alvo | `@frontend-architect` | Feature experimental pode mudar API |
| C6 | Zustand e client-only — fronteira RSC/Client precisa ser desenhada no layout tree | `@frontend-architect` + `@react-developer` | Bugs de hidratacao silenciosos se misturar |
| C7 | 3 janelas (5s, 1min, 1h) em um unico job compartilham estado — sizing de memoria | `@spark-streaming-architect` | Pressao de memoria nao prevista |
| C8 | Redis sem TTL definido — memoria cresce sem limite | `@streaming-engineer` | OOM em producao |

### Criterios de Sucesso Ajustados

| Criterio Original | Ajuste | Especialista | Motivo |
|-------------------|--------|-------------|--------|
| "Zero duplicatas" | "Zero duplicatas visiveis no dashboard apos deduplicacao" | `@streaming-engineer` | Exactly-once end-to-end tem overhead de 20-30%; dedup no Flink e mais pratico |
| "Latencia < 30s" | Separar: SSE propagacao < 5s; analytics refresh < 5min; P99 janela 5s < 15s | `@frontend-architect` + `@spark-streaming-architect` | 30s e permissivo demais para real-time; cada modo tem SLA diferente |
| "99.9% completude" | "99.9% dos eventos com timestamp dentro do watermark incluidos na agregacao correta" | `@spark-streaming-architect` | Late data alem do watermark e descartada por design — definicao precisa necessaria |

### Criterios de Sucesso Adicionados

| Criterio | Meta | Especialista |
|----------|------|-------------|
| LCP (Largest Contentful Paint) | < 2.5s | `@frontend-architect` |
| INP (Interaction to Next Paint) | < 200ms | `@frontend-architect` |
| CLS (Cumulative Layout Shift) | < 0.1 | `@frontend-architect` |
| Bundle JS inicial (first load) | < 100KB gzipped | `@frontend-architect` + `@react-developer` |
| SSE reconnect time | < 3-5s com backoff exponencial | `@react-developer` + `@frontend-architect` |
| Consumer lag Kafka | < 1000-5000 offsets em operacao normal | `@streaming-engineer` + `@spark-streaming-architect` |
| DLQ rate | < 0.1% do volume total | `@streaming-engineer` |
| Checkpoint interval | <= 20s | `@spark-streaming-architect` |
| Tempo de recuperacao apos falha | < 2x checkpoint interval | `@spark-streaming-architect` |
| Re-renders por atualizacao SSE | Max 1 componente por evento | `@react-developer` |
| Tempo de troca entre modos | < 1s percebido | `@frontend-architect` |

---

## Proximo Passo

**Pronto para:** `/design .claude/sdd/features/DEFINE_SALES_DASHBOARD_PIPELINE_B.md`
