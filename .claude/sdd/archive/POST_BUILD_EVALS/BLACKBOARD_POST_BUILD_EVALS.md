# BLACKBOARD: Post-Build Evals

> Quadro de coordenação compartilhada — o estado vivo desta feature durante o Build.
> Todos os agentes (orquestrador e especialistas) LEEM este arquivo antes de agir
> e ANEXAM aqui qualquer decisão, interface ou bloqueador que criarem.

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | POST_BUILD_EVALS |
| **Fase** | Build |
| **Atualizado em** | 2026-09-23 |
| **DESIGN** | [DESIGN_POST_BUILD_EVALS.md](DESIGN_POST_BUILD_EVALS.md) |
| **Status** | ✅ Completo |

---

## Interfaces Compartilhadas

| # | Tipo | Nome / Assinatura | Definido por | Consumido por | Notas |
|---|------|-------------------|--------------|---------------|-------|
| I-001 | módulo | `scripts/jev_client.py`: `Question`, `Answer`, `DecisionResult`, `JevError(code)`, `decide(state, questions, *, api_key, model, endpoints, timeout, opener)`, `parse_response(dict, truncated)`, `load_answers(dict)`, `budget_remaining(ledger, budget)`, `append_ledger(ledger, ...)` | @build-agent | eval_runner, testes | `opener` injetável; sem rede nos testes |
| I-002 | CLI | `eval_runner.py {validate,freeze,pre,run,attest,waive,verify,calibrate}`; exit 0 ok, 1 gate/eval falhou, 2 ambiente/uso, 3 erro estrutural | @build-agent | agentes workflow, testes | `--root` define a raiz do repo (padrão: `git rev-parse --show-toplevel` do cwd) |
| I-003 | arquivo | `.claude/sdd/features/DESIGN_{F}.md` (bloco contract), `DEFINE_{F}.md` (tabela AT), `EVALS_EXTRA_{F}.toml` | design-agent / eval-agent | eval_runner | Feature resolvida pelo nome `{F}` relativo a `--root` |
| I-004 | arquivo | `.claude/sdd/reports/EVAL_{F}.json` (schema `agentspec/eval-receipt/v1`), `EVAL_REPORT_{F}.md`, `EVAL_{F}.attestations.json` | eval_runner | ship-agent, /continuar, LIVING_MEMORY | Ver Padrão 5 do DESIGN |
| I-005 | arquivo | `.claude/sdd/evals/JEV_CALIBRATION.json` | eval_runner calibrate | eval_runner run | `approved`, `model`, `thresholds` |
| I-006 | env | `OPENROUTER_API_KEY`, `JEV_MODEL`, `JEV_BUDGET`, `JUDGE_CMD`, `AGENTSPEC_PYTHON` (exportada aos evals) | eval_runner | evals, testes | `JUDGE_CMD` é dividido com `shlex.split` |
| I-007 | função pura | `eval_runner.classify(answers, Thresholds) -> "pass"\|"fail"\|"escalated"` | @build-agent | testes | Padrão 3 do DESIGN |

---

## Log de Decisões

| # | Agente | Decisão | Justificativa | Substitui | Data |
|---|--------|---------|---------------|-----------|------|
| D-001 | @build-agent | Núcleo (`jev_client.py`, `eval_runner.py`) escrito pelo orquestrador; testes e docs delegados | As interfaces I-001..I-007 precisam nascer coerentes antes de especialistas consumirem | — | 2026-09-23 |
| D-002 | @build-agent | Testes rodam com `python3.12` localmente (único interpretador com pytest nesta máquina); CI usa 3.11 | Achado do DESIGN v1.1 | — | 2026-09-23 |
| D-003 | @test-generator | O eval `graded` retroconvertido de `KB_EVOLUTION` (`eval_at003`) referencia `.claude/kb/dbt/deprecated_api_fixture.md`, um arquivo dentro do repo avaliado — não `tests/fixtures/evals/kb_evolution/deprecated_api.md` do AgentSpec | `[eval.state]` roda com `cwd` na raiz do repo avaliado (o repo git temporário do teste), não no repo do AgentSpec; um `state` command apontando para um caminho que só existe aqui geraria `STATE_COMMAND_FAILED` (`error`), quebrando o critério "sem erro de execução" do DEFINE | — | 2026-09-23 |
| D-004 | @test-generator | `test_at005_stale_contract` reedita e re-congela o DESIGN sem commitar a mudança | `worktree_digest` exclui `.claude/sdd/` (Decision 3): só assim dá para mudar o `contract_digest` sem também mudar `commit` (via `git commit`) ou `worktree_digest` (edição não commitada fora do `.claude/sdd`), isolando `STALE_CONTRACT` de `STALE_COMMIT`/`STALE_WORKTREE` | — | 2026-09-23 |
| D-005 | @test-generator | O caso PRE-check "erro de bash" usa um comando inexistente (`nonexistent_command_xyz_12345`), não uma variável não definida sob `set -u` | Confirmado empiricamente: `bash -c 'set -u; echo "$X"'` sai com exit 1 (fora de `{2,126,127}`), então `is_bash_error()` o classificaria como `fail`, não `error`. "command not found" sai com exit 127 e bate no regex `_BASH_ERROR`, exercitando o branch correto | — | 2026-09-23 |
| D-006 | @build-agent | `is_bash_error` casa os diagnósticos do bash (`^bash: (-c: )?line N: …`) em qualquer exit code; 126/127 sozinhos também contam | Resolve D-005 no runner, não no teste: `set -u` sai com exit 1 e o DEFINE exige detectar variável não definida | D-005 (contorno no fixture) | 2026-09-23 |

---

## Perguntas Abertas e Bloqueadores

| # | Levantado por | Pergunta / Bloqueador | Status | Resolução |
|---|---------------|------------------------|--------|-----------|

---

## Status dos Arquivos

| Arquivo | Agente | Status | Verificado | Notas |
|---------|--------|--------|------------|-------|
| `scripts/jev_client.py` | @build-agent | ✅ Completo | ✅ | 36 testes |
| `scripts/eval_runner.py` | @build-agent | ✅ Completo | ✅ | 37 testes; `is_bash_error` corrigido (D-006) |
| `DESIGN_POST_BUILD_EVALS.md` (freeze + pre) | @build-agent | ✅ Completo | ✅ | Digest `sha256:89a9e4ff…`; 17/17 falharam (exit 4), 0 erros |
| `.claude/sdd/templates/EVAL_REPORT_TEMPLATE.md` | @build-agent | ✅ Completo | ✅ | |
| `tests/fixtures/evals/**` | @test-generator | ✅ Completo | Verificado ✅ | `basic/` (3 ATs, evals deterministic que passam), `cases/` (7 cenários de borda + DEFINE correspondentes), `jev/` (4 respostas reais do JEV de 2026-09-23 + 1 sintética + `calibration_cases.toml` com 12 casos), `kb_evolution/` e `frontend_ecosystem/` (retroconversão dos ATs shipados em contratos `## Evals` mistos) |
| `tests/test_jev_client.py` | @test-generator | ✅ Completo | Verificado ✅ | 36 testes (35 passed + 1 skip sem `OPENROUTER_API_KEY`): build_body/truncamento, parse_response nas 4 fixtures reais, load_answers, fallback de endpoint (NOT_FOUND/UNAVAILABLE caem para o próximo; AUTH/BAD_REQUEST propagam), orçamento (`typesafe/` only, só hoje), schema do ledger, `test_live_decide` |
| `tests/test_eval_runner.py` | @test-generator | ✅ Completo | Verificado ✅ | 36 testes: um grupo `test_atNNN_*` por AT (AT-001..AT-017, incl. `test_at004_stale_worktree`, `test_at006_pre_interpreter_error`, `test_at009_complementary_accepted`), `test_retro_kb_evolution`, `test_retro_frontend_ecosystem`, `test_calibrate_approval`, unitários de `classify`/`find_contract`/`canonical_digest` |
| Agentes/comandos/templates/contratos workflow (#11–#23) | @build-agent | ✅ Completo | ✅ | Contrato v2.2.0 (CRLF preservado) |
| `build-plugin.sh` | @build-agent | ✅ Completo | ✅ | 3 runtime scripts em `plugin/scripts/` |
| Docs (#25–#30) | @code-documenter | ✅ Concluído | — | `docs/concepts/post-build-evals.md` (novo); `docs/reference/README.md`, `docs/getting-started/judge-setup.md`, `.claude/agents/README.md`, `CLAUDE.md`, `CHANGELOG.md` (modificados) |
| Gerados (#31) | @build-agent | ✅ Completo | ✅ | Sem drift nos 4 geradores |
