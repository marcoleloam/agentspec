# AgentSpec — Project Memory

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
