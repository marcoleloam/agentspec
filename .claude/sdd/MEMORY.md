# MEMORY: Lições Aprendidas do AgentSpec

> Consolidação de insights do projeto entre fases (cross-feature index). Leia com `python3 memory-index.py brief`.

---

## 2026-09-27 — Shipped KB_CONTEXT7_REFRESH

### Decisões

| Decisão | Contexto | Resultado |
|---------|----------|-----------|
| Sandbox SO com deny-list em vez de config de plugin | Plugin agentspec não consegue desabilitar via `[plugins] disabled`; alternativas de HOME separado eram frágeis | Isolamento imposto pelo SO, com prova por transcript; transportável entre rodadas |
| Contrato de evals retroativo sem dependência de conta Grok | Assinatura descontinuada 2026-09-27; rodada completa já havia rodado em 2026-09-24/25 | Criado fake CLI em tests/fixtures para AT-008 (dry-run); rodada real prova AT-001. Evals agora não dependem de serviços externos |
| Dual-vendor blind human judgment + official doc tiebreak | Fila de 2 itens; ambas com veredito humano | Claude + GPT divergiram em 1 (fabric-03); Microsoft Learn resolveu. Padrão reutilizável para calibração de evals estruturais |
| Resume-able runs com orçamento em JSONL append-only | Rodada parou em par 60 (budget_usd=30, custo real $30.57) | `--resume` com idempotência (run_id + seed + pares já registrados); sem repetição. Aplicável a qualquer benchmark em nuvem |

### Gotchas

| Gotcha | Sintoma | Resolução |
|--------|---------|-----------|
| Context7 MCP não sobe dentro do sandbox | `handshake closed during initialize` em preflight | Sandbox profile precisa de `read_write = [npm-cache]`; preflight deve rodar `--sandbox` também |
| Agents specialistas violam Decisão 10 (sem ler KB) | KB-FIRST RESOLUTION mandatory no prompt | Usado agents general-purpose em vez dos especialistas; menos viés, mesma cobertura |
| Overhead de 38k tokens no spike vs 105–130k real | Métricas de custo isentas sem contexto | Overhead é constante entre braços (features globais, não knowledge); mascara diferenças menores, não enviesa |
| Efeito teto: B, C, D a 100% em todos estratos | Tarefas sintéticas abaixo da capacidade de grok-4.7 | 2ª rodada precisa de tarefas reais (A-007) para separar C de D; bench não separa B/C/D em si |

### Reutilizável

| Padrão | Aplicação | Próximas Rodadas |
|--------|-----------|------------------|
| Isolamento OS-level com camada de app prova | Quando config de plugin falha, use sandbox + transcript como árbitro | Replicável em benchmark de modelos, KB, ou agents |
| Fake CLI para evals sem conta externa | AT-008 (dry-run) roда contra grok falso; rodada real fica provada por registros | Preflight nunca deve depender de serviços descontinuáveis |
| Resume-able JSONL com seed fixa | Checkpoints por linha com idempotência (run_id, seed, pares registrados) | Escalável para 1000s de execuções em cloud; pause/resume sem retry |
| Python 3.11+ stdlib é suficiente para benchmark | `pathlib`, `subprocess`, `json`, `dataclasses`; só `sqlglot` como dep externo | Benchmark transportável, sem vendor SDK lock-in |

---

## Índice por Fase

| Fase | Feature | Status | Memória |
|------|---------|--------|---------|
| Ship | KB_CONTEXT7_REFRESH | ✅ Shipped | Acima; sem registro entre Define/Design/Build |

