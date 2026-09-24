# BUILD REPORT: LLM Phase Routing

> Relatório de implementação do roteamento de modelo por fase do SDD (OMP como harness principal)

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | LLM_PHASE_ROUTING |
| **Data** | 2026-09-24 |
| **Autor** | build-agent |
| **DEFINE** | [DEFINE_LLM_PHASE_ROUTING.md](../features/DEFINE_LLM_PHASE_ROUTING.md) |
| **DESIGN** | [DESIGN_LLM_PHASE_ROUTING.md](../features/DESIGN_LLM_PHASE_ROUTING.md) |
| **Status** | Completo (aceite humano no OMP pendente) |
| **Gerado por** | Claude Code · papel `sessão` · `claude-opus-5-5` |

---

## Resumo

| Métrica | Valor |
|---------|-------|
| **Tarefas Concluídas** | 17/17 do manifesto de arquivos + 1 correção extra (`init-workspace.sh`) |
| **Arquivos Criados** | 4 fontes (`PHASE_MODEL_ROLES.toml`, `scripts/phase_routing.py`, `tests/test_phase_routing.py`, `docs/concepts/phase-model-routing.md`) |
| **Linhas de Código** | 851 nos 4 arquivos novos; 37 arquivos-fonte alterados (+1367/−1143, sem contar artefatos gerados) |
| **Testes Passando** | 140/141 (1 skip já existente); 27 testes novos (25 em `test_phase_routing.py`, 2 em `test_generate_codex_plugin.py`) |
| **Agentes Utilizados** | 0 especialistas: tudo feito direto pela sessão (ver nota) |

**Nota sobre delegação:** o `/build` rodou inline na sessão principal (modo `session`, papel `default`). Os arquivos foram escritos diretamente, seguindo os padrões do DESIGN; nenhum especialista foi chamado.

---

## Execução de Tarefas com Atribuição de Agentes

| # | Tarefa | Agente | Status | Notas |
|---|--------|--------|--------|-------|
| 0 | Avançar a branch até `main@9de8ce4` (fast-forward) e atualizar o DESIGN (rev. 1.1, com contrato `## Evals`) | (direto) | ✅ Completo | O `main` tinha o gate `/eval`, que muda agents, comandos, templates, contrato, `Makefile` e `build-plugin.sh` |
| 1 | `PHASE_MODEL_ROLES.toml` | (direto) | ✅ Completo | 10 agents, 11 comandos, `[judge]` |
| 2 | `scripts/phase_routing.py` (`--check`/`--apply`/`--print-omp-overrides`) | (direto) | ✅ Completo | Só stdlib (`tomllib`) |
| 3 | `tests/test_phase_routing.py` | (direto) | ✅ Completo | 25 testes |
| 4 | Agents de workflow: `model:` via `--apply` + parágrafo **Provenance** | (direto) | ✅ Completo | 5 modelos mudaram; 10 parágrafos |
| 5 | Bloco delegated em `design.md` e `ship.md` | (direto) | ✅ Completo | No `/ship`, o Step 0 fica na sessão |
| 6 | Marcador session em 9 comandos | (direto) | ✅ Completo | Inclui `eval.md` |
| 7 | Linha `Gerado por` nos 5 templates | (direto) | ✅ Completo | — |
| 8 | `WORKFLOW_CONTRACTS.yaml`: remover 15 `model:` com alias + comentário | (direto) | ✅ Completo | `eval.jev.model` preservado |
| 9 | `build-plugin.sh`: achatar `plugin/agents` + reescrever caminhos de categoria | (direto) | ✅ Completo | Aborta se houver nome de arquivo duplicado |
| 10 | `generate-codex-plugin.py`: effort vindo do manifesto | (direto) | ✅ Completo | — |
| 11 | Testes do gerador Codex | (direto) | ✅ Completo | 2 testes |
| 12 | `Makefile`: `check` + `omp-roles` + `phase-routing-apply` | (direto) | ✅ Completo | Usa `$(PYTHON)` |
| 13 | `docs/concepts/phase-model-routing.md` | (direto) | ✅ Completo | — |
| 14 | `docs/concepts/agent-overrides.md` | (direto) | ✅ Completo | Caminho achatado + nota do OMP |
| 15 | `CLAUDE.md` + `README.md` | (direto) | ✅ Completo | Tarefa, Key Files, caminho do `cp`, linha na tabela de docs |
| 16 | `CHANGELOG.md` | (direto) | ✅ Completo | Added + Changed (breaking) |
| 17 | Regenerar `plugin/`, `.codex/`, `plugin-grok/`, `.grok/`, `plugin-dsh/`, `agent-router` | (direto) | ✅ Completo | `make build` + 4 geradores |
| 18 | **Extra:** excluir `plugin/scripts/init-workspace.sh` da reescrita `.claude/` → `${CLAUDE_PLUGIN_ROOT}/` | (direto) | ✅ Completo | Ver Problemas Encontrados #2 |

---

## Arquivos Criados

| Arquivo | Linhas | Verificado | Notas |
|---------|--------|------------|-------|
| `.claude/sdd/architecture/PHASE_MODEL_ROLES.toml` | 128 | ✅ | `load()` válido; sem ID concreto |
| `scripts/phase_routing.py` | 319 | ✅ | `--check` verde no repositório |
| `tests/test_phase_routing.py` | 286 | ✅ | 25/25 |
| `docs/concepts/phase-model-routing.md` | 118 | ✅ | — |

---

## Resultados de Verificação

### Lint

```text
shellcheck -S warning build-plugin.sh   → sem avisos
ruff                                   → indisponível no ambiente (nem no .venv nem no sistema); sintaxe validada com ast.parse
```

**Status:** ✅ Passou (com a ressalva do `ruff`)

### Testes e checagens de divergência

```text
make check
  140 passed, 1 skipped
  phase routing: in sync with PHASE_MODEL_ROLES.toml
  [OK] agent-router is up to date (74 agents)
  OK - .codex/ + AGENTS.md up to date (74 agents, 40 command skills)
  OK - plugin-grok/ + .grok/{agents,commands} up to date
exit 0
```

### Evals determinísticos do contrato (conferência local, sem recibo)

Rodei os comandos `run` dos 8 evals `deterministic` com `AGENTSPEC_PYTHON=.venv/bin/python`. Todos passaram: `drift_detected`, `repo_in_sync`, `no_concrete_ids`, `overrides_stdout_only`, `delegation_blocks`, `plugin_agents_flat`, `provenance_rows`, `full_suite`. Não rodei `eval_runner.py run`: o recibo pertence ao `/eval`, que é independente do build.

### V-1b — descoberta no OMP (sem tocar no config do usuário)

Copiei os 74 `plugin/agents/*.md` achatados para `/tmp/lpr/v1/.omp/agents/` e pedi ao `omp` (`@smol`, um prompt) a lista de agents da ferramenta task. **Os 74 apareceram, com 0 faltando**, junto com os nativos (`reviewer`, `scout`, `security-reviewer`, `sonic`, `task`). Diretório removido depois. A **V-1 completa**, com os agents vindos de dentro do plugin do marketplace, continua pendente: depende de atualizar o plugin no OMP do usuário.

---

## Problemas Encontrados

| # | Problema | Resolução |
|---|----------|-----------|
| 1 | O `make build` quebrou: o `generate-codex-plugin.py` carregava `phase_routing` via `importlib` sem registrar o módulo em `sys.modules`, e o `@dataclass` falha nesse caso. O pytest não pegou porque, lá, o módulo já estava importado | Troquei por import normal, com o diretório `scripts/` no `sys.path` (mesmo padrão do `eval_runner.py`) |
| 2 | **Bug anterior à feature:** a reescrita `.claude/agents/` → `${CLAUDE_PLUGIN_ROOT}/agents/` do build também alterava o `plugin/scripts/init-workspace.sh` (hook SessionStart). Com isso, o hook criava `agents/workflow/`, `agents/custom/` e `README.md` **dentro do plugin instalado**, em vez de no projeto do usuário. Com o achatamento, isso recolocaria o pseudo-agent `README` e subpastas no plugin a cada sessão | O script foi excluído da reescrita; ele volta a usar `.claude/agents/...` do workspace. Verificado no `plugin/scripts/init-workspace.sh` gerado |
| 3 | O pré-check do `/build` bloqueou 2 evals por ambiente: o `python3` do sistema não tem `pytest` | `make venv` (novo no `main`) e pré-check com `AGENTSPEC_PYTHON=.venv/bin/python` → `OK — build may proceed` |

---

## Desvios do Design

| Desvio | Motivo | Impacto |
|--------|--------|---------|
| DESIGN rev. 1.1 antes do código: `eval-agent`/`/eval` no manifesto (session), Step 0 do `/ship` na sessão, Regra 6 restrita a alias Claude, `$(PYTHON)`, contrato `## Evals` | A base avançou para `main@9de8ce4` | Registrado no histórico do DESIGN; digest `sha256:b030f894…` |
| O `--apply` insere só a **linha do marcador**; o texto de recomendação dos comandos session e os blocos delegated foram escritos à mão | Manter o `--apply` mínimo (Segurança: "só a linha `model:` e a linha do marcador") | `--check` garante marcador ↔ manifesto; a prosa não é checada |
| Correção extra no `build-plugin.sh` (`init-workspace.sh`) | Bug anterior que interage com o achatamento (Problemas #2) | Uma linha de exclusão no `find` da reescrita |
| `docs/concepts/README.md` não foi alterado; o link novo entrou no `README.md` raiz, junto do de Agent Overrides | O índice de conceitos não lista os docs individuais | — |

---

## Bloqueadores

Nenhum no código. Os aceites humanos dependem de ações fora do repositório (tabela abaixo).

---

## Autoverificação dos Testes de Aceitação

> Checagem feita pelo próprio build. **Não substitui o `/eval`**, que reexecuta os evals-contrato
> do DESIGN de forma independente e gera o recibo exigido pelo `/ship`.

**Pre-check de evals (`eval_runner.py pre`):** 7 evals determinísticos falharam como esperado; aviso ALREADY_PASSING: `full_suite` (esperado: é guarda de regressão da suíte existente); 5 evals `human` pulados antes do build.

| ID | Cenário | Status | Evidência |
|----|---------|--------|-----------|
| AT-001 | Design no papel `slow` (OMP) | ⏳ Humano | Pré-requisitos verificados: bloco delegated (`delegation_blocks`), agents achatados e descobertos pelo OMP (V-1b), override por nome comprovado no spike. Falta rodar `/design` no OMP com o plugin atualizado |
| AT-002 | Ship no papel `smol` (OMP) | ⏳ Humano | Idem; `ship-agent` rodou via override `@smol` no spike (teste 4) |
| AT-003 | Sem override aplicado | ⏳ Humano | `plugin/agents/design-agent.md` mantém `model: opus` (`plugin_agents_flat`) |
| AT-004 | Divergência detectada | ✅ Passou | `test_check_reports_frontmatter_drift`: mensagem com arquivo, campo e esperado |
| AT-005 | Contrato alinhado | ✅ Passou | 15 `model:` com alias removidos; `repo_in_sync` verde |
| AT-006 | Sem IDs no repositório | ✅ Passou | `no_concrete_ids` + regra no `--check` |
| AT-007 | Fase interativa preservada | ⏳ Humano | Marcadores session presentes; `/brainstorm` segue inline (nenhum bloco de delegação) |
| AT-008 | Gerador não toca no usuário | ✅ Passou | `overrides_stdout_only` + `test_print_overrides_never_touches_home` (hash igual, nenhum arquivo novo) |
| AT-009 | Paridade Claude Code | ⏳ Humano | Bloco com `subagent_type: design-agent` / `agentspec:design-agent`; `model: opus` no agent |

---

## Status Final

### Geral: ✅ COMPLETO (código e checagens); aceites humanos pendentes

**O que falta, fora deste build:**

1. `/eval LLM_PHASE_ROUTING`: roda o contrato de forma independente e registra as 5 atestações humanas.
2. Para os aceites no OMP: o marketplace `agentspec` do seu OMP aponta para `/Users/marcoleloam/projetos/framework/agentspec` (checkout principal), não para este worktree. O plugin atualizado só chega ao OMP depois do merge (ou apontando o marketplace para cá), seguido do update do plugin e de `make omp-roles` colado no `~/.omp/agent/config.yml`.
3. Nada foi commitado; nenhum push.

**Observação para `POST_BUILD_EVALS`:** o `eval.md` diz "Delegate to the **eval-agent**", mas o agent usa `AskUserQuestion`, que não funciona dentro de um subagent.

**Pendência para `KB_CONTEXT7_REFRESH`:** não foi verificado se o OMP expande `${CLAUDE_PLUGIN_ROOT}` nos corpos dos agents (leitura de KB pelos especialistas). O `WORKFLOW_CONTRACTS.yaml` distribuído também tem textos de "agent resolution" alterados pela mesma reescrita `.claude/` (linhas sobre override local); é um problema anterior, fora do escopo.

---

## Próximo Passo

**Pronto para:** `/eval LLM_PHASE_ROUTING` (depois, `/ship`)
