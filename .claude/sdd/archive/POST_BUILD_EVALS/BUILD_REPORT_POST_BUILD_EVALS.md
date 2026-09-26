# BUILD REPORT: Post-Build Evals

> Relatório de implementação da camada de evals pós-build (`/eval` + `eval_runner.py` + JEV)

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | POST_BUILD_EVALS |
| **Data** | 2026-09-23 |
| **Autor** | build-agent |
| **DEFINE** | [DEFINE_POST_BUILD_EVALS.md](../features/DEFINE_POST_BUILD_EVALS.md) |
| **DESIGN** | [DESIGN_POST_BUILD_EVALS.md](../features/DESIGN_POST_BUILD_EVALS.md) |
| **Status** | ✅ Completo |

---

## Resumo

| Métrica | Valor |
|---------|-------|
| **Tarefas Concluídas** | 31/31 itens do manifesto |
| **Arquivos Criados** | 33 (inclui 26 fixtures) |
| **Arquivos Modificados** | 22 fontes + artefatos gerados (plugin/, plugin-grok/, plugin-dsh/, .grok/, .codex/, AGENTS.md, agent-router) |
| **Linhas de Código** | `eval_runner.py` 1311 · `jev_client.py` 280 · testes 1139 |
| **Testes Passando** | 113/113 (+1 skip: teste live do JEV sem `OPENROUTER_API_KEY`) |
| **Agentes Utilizados** | 3 (build-agent direto, @test-generator, @code-documenter) |

---

## Execução de Tarefas com Atribuição de Agentes

| # | Tarefa | Agente | Status | Notas |
|---|--------|--------|--------|-------|
| 1 | `scripts/jev_client.py` | (direto) | ✅ Completo | Núcleo escrito pelo orquestrador (Blackboard D-001) |
| 2 | `scripts/eval_runner.py` | (direto) | ✅ Completo | 8 subcomandos; smoke test completo antes de delegar |
| 3 | Bootstrap: `freeze` + `pre` no próprio DESIGN | (direto) | ✅ Completo | Digest `sha256:89a9e4ff…861b`; 17/17 evals falharam com exit 4, 0 erros |
| 4 | `EVAL_REPORT_TEMPLATE.md` | (direto) | ✅ Completo | Planejado para @code-documenter; feito direto por ser pré-requisito do runner |
| 5–8 | Fixtures (`basic/`, `cases/`, `jev/`, retroconversões) | @test-generator | ✅ Completo | Respostas reais do JEV de 2026-09-23 como fixtures |
| 9 | `tests/test_jev_client.py` | @test-generator | ✅ Completo | 36 testes, sem rede |
| 10 | `tests/test_eval_runner.py` | @test-generator + (direto) | ✅ Completo | 37 testes; `test_at006_pre_syntax_error` e o caso `set -u` acrescentados pelo orquestrador |
| 11–12 | `eval-agent.md`, `/eval` | (direto) | ✅ Completo | |
| 13–15 | DESIGN template, design-agent, `/design` | (direto) | ✅ Completo | Capability 5: autoria do contrato + validate + freeze |
| 16–18 | build-agent, `/build`, BUILD_REPORT template | (direto) | ✅ Completo | PRE-check bloqueante; tabela de ATs virou "autoverificação" |
| 19–20 | ship-agent, `/ship` | (direto) | ✅ Completo | `verify` como Step 0, sem flag de bypass |
| 21 | iterate-agent | (direto) | ✅ Completo | Cascata do contrato; ganhou a ferramenta Bash |
| 22 | `/continuar` | (direto) | ✅ Completo | Lê `EVAL_{F}.json` como fonte primária de gaps |
| 23 | `WORKFLOW_CONTRACTS.yaml` | (direto) | ✅ Completo | Fase 3.5, versão 2.2.0 |
| 24 | `build-plugin.sh` | (direto) | ✅ Completo | Planejado para @shell-script-specialist; mudança de 16 linhas feita direto |
| 25–30 | Docs, CLAUDE.md, CHANGELOG | @code-documenter | ✅ Completo | |
| 31 | Artefatos gerados | (direto) | ✅ Completo | Sem drift nos 4 geradores |

**Legenda:** ✅ Completo | 🔄 Em Andamento | ⏳ Pendente | ❌ Bloqueado

---

## Contribuições dos Agentes

| Agente | Arquivos | Especialização Aplicada |
|--------|----------|------------------------|
| @test-generator | 28 | pytest com repositórios git temporários, cliente JEV simulado por monkeypatch, juiz falso via `JUDGE_CMD` |
| @code-documenter | 6 | Conceito, referência, setup do JEV, contagens e CHANGELOG, conferidos contra o código e o `--help` |
| (direto) | 20 | Padrões do DESIGN (Padrões 1–6) |

---

## Arquivos Criados

| Arquivo | Linhas | Agente | Verificado | Notas |
|---------|--------|--------|------------|-------|
| `scripts/eval_runner.py` | 1311 | (direto) | ✅ | stdlib, Python ≥ 3.11 |
| `scripts/jev_client.py` | 280 | (direto) | ✅ | `opener` injetável |
| `.claude/sdd/templates/EVAL_REPORT_TEMPLATE.md` | 55 | (direto) | ✅ | `string.Template` |
| `.claude/agents/workflow/eval-agent.md` | 175 | (direto) | ✅ | Roteado pelo agent-router (74 agentes) |
| `.claude/commands/workflow/eval.md` | 143 | (direto) | ✅ | Espelhado em Codex, Grok e DSH |
| `docs/concepts/post-build-evals.md` | 335 | @code-documenter | ✅ | |
| `tests/test_eval_runner.py` | 789 | @test-generator | ✅ | |
| `tests/test_jev_client.py` | 350 | @test-generator | ✅ | |
| `tests/fixtures/evals/**` | 26 arquivos | @test-generator | ✅ | |

---

## Resultados de Verificação

### Verificação de Lint

| Verificação | Resultado |
|-------------|-----------|
| `ruff` / `pyflakes` | ⚠️ Não instalados nesta máquina — não executados |
| `python3.12 -m py_compile` (runner + cliente) | ✅ |
| `bash -n build-plugin.sh` | ✅ |
| `shellcheck build-plugin.sh` | ✅ Só avisos SC2016 que já existiam (linhas 160–163) |
| CI "stale paths" replicado localmente | ✅ Passa |

### Verificação de Tipos

Sem type checker configurado no projeto.

### Testes

```text
python3.12 -m pytest tests/ -q
113 passed, 1 skipped in 6.31s
```

| Suíte | Resultado |
|-------|-----------|
| Suíte anterior (41) | ✅ Passa |
| `test_eval_runner.py` (37) | ✅ Passa |
| `test_jev_client.py` (36, 1 skip) | ✅ Passa |

### Drift dos Geradores

| Gerador | Resultado |
|---------|-----------|
| `generate-agent-router.py --check` | ✅ Sem drift |
| `generate-codex-plugin.py --check` | ✅ Sem drift |
| `generate-dsh-bundle.py --check` | ✅ Sem drift |
| `generate-grok-plugin.py --check` | ✅ Sem drift |

`make check` não roda nesta máquina porque usa `python3` (3.14, sem pytest). As etapas foram rodadas individualmente com `python3.12`. O CI usa 3.11.

---

## Problemas Encontrados

| # | Problema | Resolução |
|---|----------|-----------|
| 1 | `set -u` com variável não definida sai com exit 1, então o runner classificava como `fail`, não `error`. O DEFINE exige detectar "variável não definida" (achado do @test-generator, D-005) | `is_bash_error` passou a casar os diagnósticos do próprio bash (`bash: line N: …`) em qualquer exit code. Teste `set -u` acrescentado, junto com `test_at006_pre_syntax_error` |
| 2 | A edição do `WORKFLOW_CONTRACTS.yaml` converteu CRLF → LF e gerou um diff de 2104 linhas | CRLF restaurado; o diff real é +137/−3 |
| 3 | 3 testes dos geradores fixavam contagens (39 comandos, 73 agentes) | Atualizados para 40 / 74 e passaram a checar `eval.md` e `eval-agent.md` |
| 4 | Drift no DSH por ordem de execução (o gerador DSH rodou antes das skills do Codex) | Regenerado depois do `build-plugin.sh` |
| 5 | Um recibo `EVAL_POST_BUILD_EVALS.json` foi gerado durante o build por um run de teste do especialista | Removido: aceitação é papel do `/eval`, não do build |

---

## Desvios do Design

| Desvio | Motivo | Impacto |
|--------|--------|---------|
| `is_bash_error` (Padrão 4) casa `^bash: (-c: )?line N: …` em qualquer exit code, e 126/127 sozinhos | Cobrir `set -u` (problema 1) sem confundir falhas de pytest | Positivo; coberto por teste |
| `classify` (Padrão 3): `pass` não exige pergunta Noul; `fail` também quando não há Noul e o Score confiante está no nível mais baixo | O validador exige ≥ 1 Score; Noul é opcional | Nenhum caso real muda de decisão |
| Waivers vinculados a commit + worktree + contrato (o DESIGN citava commit + contrato) | Decisão 7 diz "segue a mesma regra" das atestações | Mais estrito, e consistente |
| iterate-agent ganhou a ferramenta `Bash` | Precisa rodar `validate` e `freeze` | Nenhum |
| Template (#4) e `build-plugin.sh` (#24) feitos direto, não por @code-documenter e @shell-script-specialist | O template era pré-requisito do runner; a mudança no script era de 16 linhas | Nenhum |

---

## Bloqueadores (se houver)

Nenhum.

---

## Autoverificação dos Testes de Aceitação

> Checagem feita pelo próprio build. **Não substitui o `/eval`**, que reexecuta os evals-contrato
> do DESIGN de forma independente e gera o recibo exigido pelo `/ship`.

**Pre-check de evals (`eval_runner.py pre`):** rodado no bootstrap, antes de qualquer teste existir. 17/17 evals falharam como esperado (exit 4, arquivo de teste inexistente), com 0 erros e nenhum aviso `ALREADY_PASSING`.

| ID | Cenário | Status | Evidência |
|----|---------|--------|-----------|
| AT-001 | Caminho feliz | ✅ | `test_at001_happy_path` |
| AT-002 | Eval reprovado | ✅ | `test_at002_eval_fails` |
| AT-003 | Ship sem recibo | ✅ | `test_at003_ship_without_receipt` |
| AT-004 | Recibo obsoleto por código | ✅ | `test_at004_stale_commit`, `test_at004_stale_worktree` |
| AT-005 | Recibo obsoleto por contrato | ✅ | `test_at005_stale_contract` |
| AT-006 | PRE-check com erro de bash | ✅ | `test_at006_pre_bash_error` (comando inexistente + `set -u`), `_syntax_error`, `_interpreter_error` |
| AT-007 | PRE-check com eval trivial | ✅ | `test_at007_pre_already_passing` |
| AT-008 | AT órfão | ✅ | `test_at008_orphan_at` |
| AT-009 | Tentativa de alterar contrato | ✅ | `test_at009_contract_tampered`, `test_at009_complementary_accepted` |
| AT-010 | AT pendente sem waiver | ✅ | `test_at010_human_pending` |
| AT-011 | AT pendente com waiver | ✅ | `test_at011_waiver` |
| AT-012 | Graded confiante (calibrado) | ✅ | `test_at012_*` (runner + cliente) |
| AT-013 | Graded com confiança baixa | ✅ | `test_at013_graded_low_confidence` |
| AT-014 | JEV indisponível | ✅ | `test_at014_*` (runner + cliente) |
| AT-015 | JEV sem calibração | ✅ | `test_at015_uncalibrated` |
| AT-016 | Feature legada | ✅ | `test_at016_legacy` |
| AT-017 | Excesso de graded | ✅ | `test_at017_too_many_graded` |

Critérios de sucesso adicionais: retroconversões de `KB_EVOLUTION` e `FRONTEND_ECOSYSTEM` rodam sem `error` (`test_retro_*`), e a calibração aprova com n ≥ 10 (`test_calibrate_approval`).

---

## Notas de Performance

A suíte nova roda em ~6 s, offline. Uma chamada real ao JEV levou ~0,6 s e custou ~US$ 0,000016 (teste de 2026-09-23).

---

## Pendências Fora do Escopo (registradas)

- `docs/reference/README.md` e `.claude/agents/README.md` já tinham contagens defasadas (58/63 agentes contra 73 reais). O @code-documenter somou +1 sobre essa base; corrigir a base é outra tarefa.
- O ledger do `judge.py` continua relativo ao diretório do script (Decisão 10, follow-up).
- `make check` depende de `python3` ter pytest.

---

## Status Final

### Geral: ✅ COMPLETO

**Checklist de Conclusão:**

- [x] Todas as tarefas do manifesto concluídas
- [x] Todas as verificações passaram
- [x] Todos os testes passam
- [x] Sem bloqueadores
- [x] Pre-check de evals executado antes da primeira tarefa
- [x] Pronto para /eval

---

## Próximo Passo

**Se Completo:** `/eval POST_BUILD_EVALS` (aceitação independente; o `/ship` exige recibo PASS)
