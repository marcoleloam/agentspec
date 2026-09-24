# AgentSpec — Project Memory

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
