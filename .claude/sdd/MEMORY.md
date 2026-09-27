# AgentSpec — Project Memory

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

## 2026-09-26 — Shipped JEV_AGENT_SELECTION

### Decisions
| Decision | Rationale |
| -------- | --------- |
| LLM da fase aplica `AGENT_SELECTION_RUBRIC.md`; JEV é segunda opinião opcional | No corpus retrospectivo, LLM superou JEV e regra por domínios; a decisão e os motivos ficam no documento. |
| `/define-m` e `/design-m` preservam `multiagent` explícito | A escolha do usuário não pode ser revertida pela rubrica nem pela segunda opinião. |

### Gotchas
- O contrato de sete evals foi escrito após o build v1.3: registrar essa cronologia; PASS não significa TDD histórico.
- Os 46 rótulos são do build-agent Claude e o corpus não é versionado: não apresentar 0,8913 de acurácia como validação humana ou estimativa de produção.
- `memory-index.py brief` apontou ausência de trajetória no Blackboard para define, design e build: acrescentar entradas ao longo das fases, não só no `/iterate`.

### Reusable
- Usar a mesma rubrica nos comandos e no benchmark, com teste de sincronismo, reduz divergência entre comportamento entregue e medição.

## 2026-09-25 — Shipped LIVING_MEMORY

### Decisions
| Decision | Rationale |
| -------- | --------- |
| Hooks do plugin (`memory-hook.py`) garantem chamadas determinísticas ao script | A-001 caiu no E2E: agentes gravam o Blackboard mas pulam `brief`/`gate`/`build`. Hooks em UserPromptSubmit, PreToolUse(Write de DESIGN novo) e PostToolUse(Write\|Edit do Blackboard). |
| Parser header-driven, tolerante a `| ID |` e colunas fora de ordem | E2E: 8 entradas sumiram em silêncio quando agente escreveu `| ID |` em vez de `| # |`. D-025 adiciona validação com exit 2 e aviso ⚠. |
| Caminho do script em 3 níveis: `${CLAUDE_PLUGIN_ROOT}` → `$AGENTSPEC_MEMORY_INDEX` → `plugin-extras/scripts/` | O Claude Code só substitui a forma exata `${CLAUDE_PLUGIN_ROOT}` ao carregar o comando, e o Bash do agente não recebe a variável. SessionStart grava o caminho em `$CLAUDE_ENV_FILE`. |
| 🔴 só fecha com resposta do usuário; só Status/Resolução de Q e A mudam na linha | No E2E um design fechou a 🔴 por premissa para passar no gate (D-027). Hook bloqueia criar DESIGN com 🔴; o gate Design→Build segue só no prompt. |
| `brief --domains` + cascata (Blackboard → DEFINE → varredura KB) cobre features arquivadas sem migração | AT-007 memória cruzada validado: decision boundaries entre features por domínio KB comum, sem reescrever `archive/`. |

### Gotchas
- Teste de prompt só vale com E2E real: `claude -p` num projeto de exemplo com o plugin via `--plugin-dir` e o `agentspec` instalado desligado (`--settings '{"enabledPlugins":{"agentspec@agentspec":false}}'`), stdin em `/dev/null`. Numa cópia em `/tmp` do próprio repo, os comandos locais não carregam (workspace não confiável) e roda o plugin antigo.
- `eval_runner.py`, `judge.py` e `status-dashboard.py` ainda são chamados como `${CLAUDE_PLUGIN_ROOT:-.}/scripts/…`, forma que nunca é substituída. No E2E do `/eval` o agente se recuperou deduzindo a pasta do plugin pelo loader de skills (2/2), mas isso não é determinístico — follow-up aberto.

### Reusable
- `regex` header-driven + stateless parser resolve compatibilidade retroativa: teste contra archive com/sem acento, coluna `ID` acidental, formatos legados. Padrão para parsing robusto de Markdown.
- Protocolo em contrato (`WORKFLOW_CONTRACTS.yaml` → `living_memory`) + blocos `## Phase Memory` curtos em agentes = rule uniqueness + code readability. Evita skill novo + duplicação entre 9 agentes.

## 2026-09-24 — Shipped LLM_PHASE_ROUTING

### Decisions
| Decision | Rationale |
| -------- | --------- |
| Manifesto em TOML (`PHASE_MODEL_ROLES.toml`); papéis OMP via `task.agentModelOverrides`, sem IDs concretos no repo | O mesmo plugin vale no Claude Code e no OMP; o modelo concreto fica no `config.yml` do usuário |
| `/design` e `/ship` delegam por instrução no corpo do comando; fases interativas ficam na sessão | Frontmatter `agent:`/`context: fork` é ignorada no OMP; subagent não pode perguntar ao usuário |
| `plugin/agents/` achatado no `build-plugin.sh` | O OMP não lê subpastas; sem isso nem roteamento nem especialistas aparecem |

### Gotchas
- Delegação no OMP é prompt-instructed, não enforced: sessão `@plan` (`gpt-6-astra`) pode rodar `/ship` inline (fallback). 1 de 2 runs delegou
- Config OMP é `~/.omp/agent/config.yml`; `config.yml.lock` é lock de 0 bytes
- Marketplace Claude Code não puxa layout novo se a versão do plugin (3.4.1) não subir — `claude plugin update` diz "already latest"
- Slash commands de plugin incluem a pasta: `/agentspec:workflow:design`, não `/agentspec:design`
- Commitar depois do `/eval` → `STALE_COMMIT`; manter o recibo uncommitted até o ship, ou rerodar `/eval`
- Modelo default da sessão (`deepseek`) deu 402 Insufficient Balance; testes precisaram de `--model` explícito

### Reusable
- `make omp-roles` imprime o trecho de overrides; o usuário cola — o repo nunca lê/escreve `~/.omp`

## 2026-09-24 — Shipped POST_BUILD_EVALS

### Decisions
| Decision | Rationale |
| -------- | --------- |
| `/ship` exige recibo `/eval` PASS (`eval_runner.py verify`), sem flag de bypass | A aceitação é a prova reexecutada, não a autoverificação do build |
| Contrato `## Evals` congelado por digest; só design-agent/iterate-agent rodam `freeze` | Qualquer mudança semântica vira `CONTRACT_TAMPERED` / `STALE_CONTRACT` |

### Gotchas
- O runner exporta o próprio interpretador aos evals: rode `/eval` com `AGENTSPEC_PYTHON=.venv/bin/python` (`make venv`), senão o `python3` sem pytest dá `error (ENVIRONMENT)` em tudo
- O recibo é vinculado a commit + worktree: qualquer edição de código depois do `/eval` exige novo `/eval` antes do `/ship`
- `WORKFLOW_CONTRACTS.yaml` usa CRLF — preserve o fim de linha ao editar

### Reusable
- Rodar `eval_runner.py pre` logo após o `freeze` e antes de escrever testes: todo eval deve falhar (não `error`), o que prova que discrimina
