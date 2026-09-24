# AgentSpec — Project Memory

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
