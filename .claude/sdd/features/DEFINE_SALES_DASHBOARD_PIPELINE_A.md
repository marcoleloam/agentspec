# DEFINE: Sales Dashboard Real-Time

> Pipeline de dados e dashboard web para monitoramento operacional e análise histórica de vendas, com latência de até 30 segundos do evento à tela.

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | SALES_DASHBOARD |
| **Data** | 2026-03-29 |
| **Autor** | define-agent |
| **Status** | Pronto para Design |
| **Clarity Score** | 13/15 |
| **Modo** | Single-agent (Pipeline A do teste comparativo) |
| **Brainstorm de Origem** | `.claude/sdd/features/BRAINSTORM_SALES_DASHBOARD.md` |

---

## Declaração do Problema

O time de vendas não tem visibilidade em tempo real sobre métricas de venda, e a gestão comercial não consegue analisar tendências históricas de forma consolidada — hoje ambos dependem de dados disponíveis apenas no fim do dia ou em planilhas manuais, o que impede reação rápida a variações de performance.

---

## Usuários-Alvo

| Usuário | Papel | Dor |
|---------|-------|-----|
| Time de vendas | Operacional — acompanha vendas em andamento | Só visualiza dados no fim do dia; não consegue reagir a quedas ou picos em tempo real |
| Gestão comercial | Estratégico — avalia performance e tendências | Depende de planilhas manuais para comparar períodos; análise histórica não está consolidada |

---

## Objetivos

O que significa sucesso (priorizado):

| Prioridade | Objetivo |
|------------|----------|
| **MUST** | Construir pipeline Kafka end-to-end: producers → topic `sales-events` → processador streaming → Redis (hot) + Postgres (histórico) |
| **MUST** | Implementar dashboard Next.js com modo operacional (métricas real-time via SSE) e modo analytics (consultas históricas via API routes) |
| **MUST** | Garantir latência máxima de 30 segundos do evento de venda até exibição no dashboard |
| **MUST** | Suportar volume de 100K+ eventos/dia sem degradação de performance |
| **MUST** | Implementar autenticação — dashboard não é público |
| **SHOULD** | Agregações por janelas de tempo: 5 segundos (real-time), 1 minuto, 1 hora (analytics) |
| **SHOULD** | Comparação entre períodos no modo analytics (hoje vs ontem, semana vs semana anterior) |
| **COULD** | Alertas automáticos via Slack/email quando métricas ultrapassam limiares |
| **COULD** | Export de relatórios em CSV ou PDF |
| **COULD** | Suporte a múltiplos tenants (multi-tenancy) |

**Guia de Prioridade:**
- **MUST** = O MVP falha sem isso
- **SHOULD** = Importante, mas existe alternativa
- **COULD** = Nice-to-have, cortar primeiro se necessário

---

## Critérios de Sucesso

Resultados mensuráveis:

- [ ] Dashboard exibe métricas de vendas com latência < 30 segundos do evento à tela (medido end-to-end)
- [ ] Pipeline processa 100K+ eventos/dia sem aumento de latência ou perda de mensagens
- [ ] Modo analytics permite comparação entre ao menos dois períodos (ex.: hoje vs ontem, semana atual vs semana anterior)
- [ ] Autenticação implementada: usuários não autenticados não acessam dados
- [ ] Agregações pré-computadas: dashboard não executa queries direto no raw Kafka
- [ ] Disponibilidade do pipeline: 99% de uptime em janela de 30 dias (SLA de observabilidade)

---

## Testes de Aceitação

| ID | Cenário | Dado | Quando | Então |
|----|---------|------|--------|-------|
| AT-001 | Evento aparece no dashboard em tempo real | Pipeline rodando, dashboard aberto | Um evento de venda é publicado no Kafka | O dashboard exibe a atualização em até 30 segundos, sem refresh manual |
| AT-002 | Volume alto não degrada performance | 100K eventos foram processados no dia | O dashboard é consultado no modo operacional | O tempo de resposta do painel é < 2 segundos |
| AT-003 | Comparação de períodos no modo analytics | Histórico de ao menos 7 dias em Postgres | Usuário seleciona "hoje vs ontem" | O dashboard retorna os dados comparativos corretamente |
| AT-004 | Acesso não autenticado bloqueado | Dashboard em produção | Requisição sem token válido para qualquer rota | Retorna 401 ou redireciona para login |
| AT-005 | Falha no processador não perde eventos | Processador reinicia após falha | Eventos chegam ao Kafka durante downtime do processador | Após recuperação, eventos são processados sem lacuna (at-least-once) |

---

## Fora do Escopo

Explicitamente NÃO incluído nesta feature:

- Alertas automáticos (Slack, email, push notification) — YAGNI para MVP
- Export de relatórios em CSV ou PDF — nice-to-have, pode ser adicionado depois
- Multi-tenancy — começar com uma única empresa, escalar depois
- Aplicativo mobile — apenas web (Next.js)
- Integração com ferramentas de BI externas (Metabase, Looker, Power BI)
- Ingestão de fontes além do Kafka (ex.: REST API, bancos legados) — fora do escopo inicial

---

## Restrições

| Tipo | Restrição | Impacto |
|------|-----------|---------|
| Técnica | Frontend obrigatoriamente em Next.js | Design e build devem usar App Router; sem liberdade para escolher outro framework |
| Técnica | Latência aceitável: near real-time (5-30s), não real-time absoluto (< 1s) | SSE é suficiente; WebSocket não é necessário |
| Técnica | Projeto do zero — nenhum código ou infraestrutura pré-existente | Escopo end-to-end: producers, Kafka, processador, bancos, dashboard |
| Arquitetural | Dois bancos obrigatórios: Redis (hot data) + Postgres (histórico) | Design deve contemplar dois caminhos de leitura e estratégia de cache |
| Arquitetural | Agregação pré-computada é requisito de performance | Processador streaming (Flink ou Spark Structured Streaming) é parte do escopo |

---

## Contexto Técnico

| Aspecto | Valor | Notas |
|---------|-------|-------|
| **Localização de Deploy** | Monorepo: `pipeline/` (Kafka + processador + bancos) e `dashboard/` (Next.js) | Dois módulos separados com responsabilidades distintas |
| **Domínios KB** | `streaming`, `react`, `nextjs`, `frontend-patterns`, `data-quality`, `sql-patterns` | Ver detalhamento abaixo |
| **Impacto IaC** | Novos recursos a definir | Docker Compose para dev local; decisão de cloud (AWS/GCP) para prod adiada para Design |

**Detalhamento dos Domínios KB:**

| Domínio KB | Por Que Usar |
|------------|--------------|
| `streaming` | Padrões Kafka producer/consumer, Flink/Spark Structured Streaming, janelas de tempo, semântica at-least-once |
| `react` | Hooks e composição de componentes para o dashboard (state de SSE, gráficos, filtros) |
| `nextjs` | App Router, API routes para analytics, SSE endpoint, middleware de autenticação, caching |
| `frontend-patterns` | Estrutura do projeto Next.js, autenticação, performance de renderização |
| `data-quality` | Validação de schema do evento de venda, métricas de completude, observabilidade do pipeline |
| `sql-patterns` | Queries de agregação e comparação de períodos no Postgres |

**Por Que Isso Importa:**

- **Localização** → Fase de Design usa a estrutura correta do monorepo, evita arquivos mal posicionados
- **Domínios KB** → Fase de Design puxa os padrões corretos de `.claude/kb/`
- **Impacto IaC** → Aciona o planejamento de infraestrutura, evita falhas do tipo "funciona local"

---

## Contexto de Data Engineering

### Inventário de Origens

| Origem | Tipo | Volume | Frequência | Responsável |
|--------|------|--------|------------|-------------|
| `sales-events` | Kafka topic | 100K+ eventos/dia (~1,15 evento/seg em média) | Real-time contínuo | Time de engenharia |

### Esboço do Fluxo de Dados

```text
[App/POS] → [Kafka Producer] → [Kafka Topic: sales-events]
                                         │
                                         ▼
                               [Processador Streaming]
                               (Flink ou Spark SS)
                               Janelas: 5s / 1min / 1h
                                    │         │
                                    ▼         ▼
                              [Redis]      [Postgres]
                           (métricas hot)  (histórico)
                                    │         │
                                    ▼         ▼
                            [Next.js Dashboard]
                        SSE (operacional) + API (analytics)
```

### Contrato de Schema

> Schema de eventos a ser validado e finalizado na fase de Design. Rascunho inicial:

| Coluna | Tipo | Restrições | PII? |
|--------|------|------------|------|
| `event_id` | UUID | NOT NULL, UNIQUE | Não |
| `event_timestamp` | TIMESTAMP (UTC) | NOT NULL | Não |
| `sale_amount` | DECIMAL(18,2) | NOT NULL, >= 0 | Não |
| `product_id` | VARCHAR(64) | NOT NULL | Não |
| `seller_id` | VARCHAR(64) | NOT NULL | Possivelmente — validar |
| `region` | VARCHAR(64) | NOT NULL | Não |
| `status` | ENUM(`completed`, `pending`, `cancelled`) | NOT NULL | Não |

### SLAs de Atualização

| Camada | Meta | Medição |
|--------|------|---------|
| Redis (hot data) | Dentro de 30 segundos após publicação no Kafka | Comparação de `event_timestamp` vs timestamp de escrita no Redis |
| Postgres (histórico) | Dentro de 5 minutos após evento | Comparação de `event_timestamp` vs timestamp de inserção |
| Dashboard (visualização) | Atualização visível em até 30 segundos | Timestamp de renderização vs `event_timestamp` |

### Métricas de Completude

- 99,9% dos eventos publicados no Kafka presentes no Redis dentro do SLA (30s)
- 100% dos eventos presentes no Postgres dentro de 5 minutos
- Zero `event_id` duplicados no Postgres
- Zero `event_id` nulos em qualquer camada

### Requisitos de Lineage

- Rastreabilidade de cada evento desde o Kafka topic até a exibição no dashboard
- Identificação de eventos processados vs descartados pelo processador streaming

---

## Premissas

| ID | Premissa | Se Errada, Impacto |  Validada? |
|----|----------|-------------------|-----------|
| A-001 | Redis suporta a carga de leituras simultâneas do dashboard (100+ usuários concorrentes) | Precisaria de cache adicional ou ajuste de topologia Redis Cluster | [ ] |
| A-002 | Kafka é o único sistema de origem (nenhuma integração com ERP, CRM ou outros bancos) | Escopo de ingestão expandiria significativamente | [ ] |
| A-003 | Os usuários usam browsers modernos com suporte nativo a SSE (EventSource API) | Precisaria de polyfill ou fallback para polling | [ ] |
| A-004 | O processador streaming (Flink/Spark SS) processa eventos com semântica at-least-once | Deduplicação no consumidor (Postgres) seria obrigatória; idempotência por `event_id` | [ ] |
| A-005 | Um único tenant/empresa no MVP — sem isolamento de dados entre organizações | Se multi-tenant for necessário antes do ship, redesign do modelo de dados | [ ] |
| A-006 | Volume de 100K eventos/dia é estável — sem picos sazonais extremos (ex.: 10x em Black Friday) | Processador e Redis precisariam de auto-scaling configurado desde o início | [ ] |

**Nota:** Validar A-001, A-002 e A-006 antes da fase de DESIGN. São as premissas de maior impacto arquitetural.

---

## Detalhamento do Clarity Score

| Elemento | Score (0-3) | Notas |
|----------|-------------|-------|
| Problema | 3/3 | Declaração específica, identifica dois públicos e descreve o impacto operacional atual |
| Usuários | 3/3 | Dois perfis com papéis distintos e dores concretas extraídas do brainstorm |
| Objetivos | 3/3 | MoSCoW completo com 5 MUSTs, 2 SHOULDs, 3 COULDs — todos mensuráveis |
| Sucesso | 2/3 | 6 critérios mensuráveis; SLA de disponibilidade (99%) assumido — precisa validação com stakeholder |
| Escopo | 2/3 | Fora do escopo bem definido (6 itens), mas stack de cloud para produção ainda indefinida |
| **Total** | **13/15** | Acima do mínimo (12/15) — pronto para Design |

**Guia de Pontuação:**
- 0 = Totalmente ausente
- 1 = Vago ou incompleto
- 2 = Claro mas faltam detalhes
- 3 = Cristalino e acionável

**Mínimo para prosseguir: 12/15**

---

## Questões em Aberto

| # | Questão | Impacto | Urgência |
|---|---------|---------|---------|
| Q-001 | Qual o provedor de cloud para produção? (AWS, GCP, Azure) | Define qual serviço gerenciado usar para Kafka (MSK, Confluent Cloud, Pub/Sub) e onde hospedar o processador | Alta — resolver antes do Design |
| Q-002 | Flink ou Spark Structured Streaming como processador? | Escolha afeta KB domains prioritários e padrões de janelamento | Média — pode ser decidido no Design |
| Q-003 | O SLA de disponibilidade de 99% está alinhado com o stakeholder? | Afeta custo de infraestrutura e estratégia de redundância | Média |
| Q-004 | `seller_id` é considerado PII e precisa de mascaramento ou tokenização? | Se sim, pipeline precisa de camada de anonimização antes de Postgres | Alta — impacto em design de dados |

---

## Histórico de Revisões

| Versão | Data | Autor | Mudanças |
|--------|------|-------|----------|
| 1.0 | 2026-03-29 | define-agent (Pipeline A) | Versão inicial — extraído de BRAINSTORM_SALES_DASHBOARD.md |

---

## Próximo Passo

**Pronto para:** `/design .claude/sdd/features/DEFINE_SALES_DASHBOARD_PIPELINE_A.md`
