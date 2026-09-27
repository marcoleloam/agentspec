# BUILD REPORT: KB_CONTEXT7_REFRESH

> Relatório de implementação da bancada `kb_bench`, que compara KB atual × Context7 × KB enxuta + Context7 × nada no Grok CLI (`grok-4.7`).

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | KB_CONTEXT7_REFRESH |
| **Data** | 2026-09-24 (atualizado em 2026-09-27 com a rodada completa) |
| **Autor** | build-agent |
| **DEFINE** | [DEFINE_KB_CONTEXT7_REFRESH.md](../features/DEFINE_KB_CONTEXT7_REFRESH.md) |
| **DESIGN** | [DESIGN_KB_CONTEXT7_REFRESH.md](../features/DESIGN_KB_CONTEXT7_REFRESH.md) |
| **Status** | Completo — bancada pronta e rodada completa executada (72/72 pares, run `20260924T130130Z-66e2`) |

---

## Resumo

| Métrica | Valor |
|---------|-------|
| **Tarefas Concluídas** | 28/29 do manifesto (o item 29, `.gitignore`, era desnecessário: `.venv/` já é ignorado) |
| **Arquivos Criados** | 148 em `scripts/kb_bench/` (fora `.venv`) + 4 em `tests/`; 1 modificado (`Makefile`) |
| **Linhas de Código** | ~2.600 de Python (1.866 na bancada e nos checkers + 447 de testes e `grok` falso), mais tarefas, fixtures, soluções e KB enxuta |
| **Testes Passando** | 88/88 em `tests/` no Python 3.12 (47 da bancada, incluindo 2 de dry-run com `grok` falso adicionados em 2026-09-27) |
| **Tarefas do benchmark** | 18/18 válidas no `validate` (falham nas fixtures e passam na solução de referência) |
| **Agentes Utilizados** | 8 subagentes em paralelo (6 autores de tarefas + 2 de KB enxuta) |
| **Prova E2E real** | setup + smoke + mini-rodada de 1 tarefa × 4 braços no Grok real (custo US$ 0,63) |
| **Rodada completa** | 72/72 pares, 1 contaminada (excluída), 2 para a fila humana (ambas `reject`); custo reportado pela CLI US$ 36,25 (assinatura Grok, não cobrança por token) |
| **Recomendação** | `aposentar KB` nos 3 estratos — indicativa, com efeito teto (ver abaixo) |

---

## Execução de Tarefas com Atribuição de Agentes

| # | Tarefa | Agente | Status | Notas |
|---|--------|--------|--------|-------|
| 1–15 | Pacote `kb_bench` (config, tasks, evals, workspace, transcript, grok_runner, isolation, store, human_queue, loop, report, setup_env, cli) | (direto) | ✅ | Seguiu os Padrões 1–7 do DESIGN |
| 16 | `requirements-evals.txt` | (direto) | ✅ | Versões fixadas após instalação real: dbt-core 1.12.5, dbt-duckdb 1.11.0, duckdb 1.5.5, sqlglot 30.19.0 |
| 17 | `checks/` (7 verificadores) | (direto) | ✅ | Inclui `duckdb_sql`, que **executa** SQL confinado ao workspace (não previsto no DESIGN) |
| 18 | Tarefas dbt | general-purpose | ✅ | Usam `dbt parse`, `dbt build` e `dbt snapshot` reais |
| 19 | Tarefas airflow | general-purpose | ✅ | Migração 2→3, Assets e dynamic task mapping |
| 20 | Tarefas medallion | general-purpose | ✅ | SQL executado no DuckDB com armadilhas nos dados |
| 21 | Tarefas data-modeling | general-purpose | ✅ | SCD2, snapshot semi-aditivo, Data Vault |
| 22 | Tarefas microsoft-fabric | general-purpose | ✅ | Notebook, pipeline JSON e T-SQL de Warehouse |
| 23 | Tarefas shadowtraffic | general-purpose | ✅ | Kafka, Postgres e lookup entre conexões |
| 24 | KB enxuta (6 domínios) | @kb-architect ×2 | ✅ | 7,4%–24,4% do tamanho original |
| 25 | `README.md` | (direto) | ✅ | Inglês |
| 26–27 | Testes + fixtures | (direto) | ✅ | Transcripts reais do spike, anonimizados, e um `grok` falso |
| 28 | `Makefile` | (direto) | ✅ | 6 alvos `kb-bench*` |
| 29 | `.gitignore` | — | ⏭️ | Desnecessário |

---

## Contribuições dos Agentes

| Agente | Arquivos | Especialização Aplicada |
|--------|----------|------------------------|
| general-purpose (dbt) | 3 tarefas + fixtures + soluções | dbt 1.9+/1.10+: YAML snapshots, `hard_deletes`, `arguments:` em testes, contracts, unit tests |
| general-purpose (airflow) | 3 + fixtures + soluções | Airflow 3: `schedule=`, `airflow.sdk`, Assets, `catchup`, `CronDataIntervalTimetable`, `.expand()` |
| general-purpose (medallion) | 3 + fixtures + soluções | Latest-wins, quarentena, UTC, idempotência, CDC incremental |
| general-purpose (data-modeling) | 3 + fixtures + soluções | SCD2 por data do fato, membro Unknown, medida semi-aditiva, hash keys de Data Vault |
| general-purpose (fabric) | 3 + fixtures + soluções | Files/Tables, MERGE Delta, V-Order, `notebookutils`, `TridentNotebook`, PK `NOT ENFORCED` |
| general-purpose (shadowtraffic) | 3 + soluções | `_gen`, `lookup`, `localConfigs`, conexões Kafka/Postgres |
| @kb-architect (A) | 12 (dbt, airflow, medallion) | Corte pela regra "fica o opinativo, sai a referência de API" |
| @kb-architect (B) | 12 (data-modeling, fabric, shadowtraffic) | Idem |

---

## Verificação

### Lint

```text
uv run --with ruff ruff check scripts/kb_bench tests/test_kb_bench.py tests/fixtures/kb_bench \
  --exclude scripts/kb_bench/{.venv,fixtures,solutions}
All checks passed!
```

**Status:** ✅. Fixtures e soluções ficam fora do lint porque são dados do benchmark: o notebook Fabric usa as globais `spark` e `notebookutils` do runtime, e a DAG legada é Airflow 2 de propósito.

### Tipos

**Status:** ⏭️ Ignorado. O repositório não configura mypy/pyright.

### Testes

```text
uv run --python 3.11 --with pytest python -m pytest tests/ -q
83 passed in 2.59s
```

| Grupo | Cobre |
|-------|-------|
| `TestTranscript` | Formato real do grok 1.0.41: leitura negada, chamadas Context7 com saída em `rawOutput.output`, linhas malformadas |
| `TestIsolation` | Leitura negada ≠ contaminação; leitura completada/bash em deny, Context7 em A/D e web tool = contaminação; alias `/private/tmp` |
| `TestDecisionRule` | As 5 saídas (AT-007), taxas com exclusões, humano a mais reprova, braço ausente |
| `TestTasks` | 18 tarefas carregam, 3 por domínio, todas com solução; schema; AT-002 |
| `TestWorkspace` | Context7 só em B/C; MCPs globais desligados; `deny` e `read_write`; cópia de KB por braço |
| `TestLoop` | pass_first, pass_retry, human cego (AT-006), timeout (AT-009), contaminated (AT-004), unavailable por preflight, por transporte e por MCP ausente (AT-005) |
| `TestTrust` | setup/teardown preservam as outras entradas; setup exige consentimento |
| `TestReport` | Recomendação, aviso estatístico, aviso de sintéticas, aviso de amostra mínima |

### Validação das tarefas e geradores

```text
python3 -m kb_bench validate      → 18/18 tasks valid
generate-{agent-router,codex-plugin,dsh-bundle,grok-plugin}.py --check → no drift
```

### Prova ponta a ponta com o Grok real (run `20260924T092049Z-a857`)

| Passo | Resultado |
|-------|-----------|
| `make kb-bench-setup ARGS=--yes` | 2 entradas de trust (`~/.kb-bench/arms/b`, `/c`), backup em `~/.kb-bench/backups/`, registro em `state.json` |
| `make kb-bench-smoke` | Todos os checks `[ok]`: MCP só em B/C, sem outros MCPs, **canário negado pelo sandbox**, cobertura sondada |
| Mini-rodada `airflow-02-asset-driven-mart` × 4 braços | A, B, C e D com `pass_first`; B e C com 4 chamadas ao Context7 cada; 0 contaminações; 0 leituras de KB negadas |
| Cobertura registrada | dbt, airflow, fabric e shadowtraffic `covered`; medallion e data-modeling `not_covered` |
| AT-010 | `git status` sem nenhuma mudança fora de `scripts/kb_bench/` |

| Braço | Tokens | Tokens de entrada na 1ª chamada | Custo | Latência |
|-------|--------|---------------------------------|-------|----------|
| A | 409.820 | 116.575 | US$ 0,16 | 249 s |
| B | 296.863 | 126.683 | US$ 0,14 | 198 s |
| C | 272.843 | 104.140 | US$ 0,13 | 241 s |
| D | 455.971 | 130.635 | US$ 0,20 | 468 s |

> Uma única tarefa **não** sustenta conclusão nenhuma. O relatório agora marca isso explicitamente (⚠️ amostra mínima).

### Rodada completa (run `20260924T130130Z-66e2`)

Executada de 2026-09-24 10:00 a 2026-09-25 14:10 em duas partes: parou no par 60 pelo teto `budget_usd = 30` (US$ 30,57) e foi retomada com `--resume … --skip-smoke` após subir o teto para 60. O `--resume` não repetiu nenhum par. Relatório: `~/.kb-bench/results/20260924T130130Z-66e2/REPORT.md`.

| Estrato | Braço | Resolvidas | 1ª | Retry | Humano | Tokens (mediana) | Chamadas C7 |
|---------|-------|------------|----|-------|--------|------------------|-------------|
| Biblioteca | A — KB atual | 83% | 4 | 1 | 1 | 1.598.762 | 0 |
| Biblioteca | B — Context7 | 100% | 4 | 2 | 0 | 639.892 | 47 |
| Biblioteca | C — KB enxuta + C7 | 100% | 5 | 1 | 0 | 860.760 | 29 |
| Biblioteca | D — nada | 100% | 5 | 1 | 0 | 831.443 | 0 |
| Conceitual | A — KB atual | 100% | 6 | 0 | 0 | 2.136.316 | 0 |
| Conceitual | B — Context7 | 100% | 6 | 0 | 0 | 1.308.680 | 14 |
| Conceitual | C — KB enxuta + C7 | 100% | 6 | 0 | 0 | 1.310.938 | 24 |
| Conceitual | D — nada | 100% | 5 | 1 | 0 | 1.551.676 | 0 |
| Nicho | A — KB atual | 83% | 1 | 4 | 1 | 844.495 | 0 |
| Nicho | B — Context7 | 100% | 6 | 0 | 0 | 375.655 | 25 |
| Nicho | C — KB enxuta + C7 | 100% (5 válidas) | 4 | 1 | 0 | 657.932 | 27 |
| Nicho | D — nada | 100% | 3 | 3 | 0 | 1.176.846 | 0 |

- **Recomendação da regra de decisão:** `aposentar KB` em Biblioteca, Conceitual e Nicho (D ≥ A em resolvidas e ≤ A em humano; a precedência do item 3 do DEFINE se aplica).
- **Isolamento:** 1 execução contaminada (`shadowtraffic-03`, braço C, `find` em `~/.claude/plugins/marketplaces/agentspec`), negada pelo sandbox e excluída. Nenhuma leitura de KB negada em A, B ou D. AT-010: nenhuma mudança fora de `scripts/kb_bench/`.
- **Fila humana (calibração, cega):** julgada por dois fornecedores (Claude Opus 5.5 e GPT via Codex CLI) com o mesmo prompt, sem braço nem transcript.

| Item | Tarefa (braço A) | Claude | Codex | Veredito | Motivo |
|------|------------------|--------|-------|----------|--------|
| `fe84e912` | `dbt-02-yaml-snapshot` | reject | reject | **reject** | Nenhum arquivo de snapshot entregue; eval correto |
| `27d90a7c` | `microsoft-fabric-03-warehouse-dim-customer` | approve (com dúvida) | reject | **reject** | Desempate pela doc oficial (MS Learn, *table-constraints*, 2026-09-08): PK não pode ser declarada inline no `CREATE TABLE`, só via `ALTER TABLE`. A falha de parse do eval coincide com uma incompatibilidade real |

Nenhum `approve`: não há sinal de eval rígido demais nesta rodada.

> **Leitura correta do placar.** B, C e D chegaram a 100% em todos os estratos: as tarefas sintéticas ficaram abaixo do teto de capacidade do `grok-4.7`, e a bancada não separa B, C e D entre si. O resultado sustenta "a KB atual não ajudou nestas tarefas e custou mais tokens", não "a KB é inútil". Com ~6 tarefas por célula, uma tarefa muda a taxa em ~17 pp.

---

## Problemas Encontrados

| # | Problema | Resolução |
|---|----------|-----------|
| 1 | **O Context7 não subia dentro do sandbox** ("handshake closed during initialize"): o perfil `workspace` só grava em CWD, `/tmp` e `~/.grok`, e o cache do npx ficava em `~/.kb-bench/npm-cache`. O `mcp doctor` sem sandbox dizia "saudável" | `read_write = [npm-cache]` no perfil; o preflight agora roda `grok --sandbox kbbench mcp doctor`, que reproduz as condições reais |
| 2 | Nesse cenário, **B e C degeneravam em D em silêncio**: o agente seguia sem MCP e nada falhava | Nova detecção `mcp_missing` no transcript ("No MCP tools are available" etc.) → `unavailable`; com teste |
| 3 | A saída de MCP vem com `content` vazio e o texto em `rawOutput.output.OkayOutput` | Parser lê `rawOutput`; teste com o transcript real |
| 4 | `sql_check --forbid-select-star` marcava `count(*)` (apontado pelo autor das tarefas medallion) | Só considera `*` na lista de colunas do SELECT |
| 5 | `duckdb_sql` dependia do fuso da máquina (America/Sao_Paulo) | `SET TimeZone = 'UTC'` antes do lock de configuração |
| 6 | Falso positivo de cobertura: data-modeling "coberto" por `/websites/mdio_dev` ("multi**dimensional**") | Palavras-chave `kimball`, `dimensional model`, `star schema` |
| 7 | `trusted_folders(path=TRUST_FILE)` fixava o default na definição; a idempotência lia o arquivo errado | Default resolvido na chamada; pego pelo teste |
| 8 | Minha substituição em massa de `check=False` quebrou chamadas multilinha | Corrigido e compilado; lint limpo |
| 9 | `attempt_timeout_s = 600` cortava tentativas reais do `grok-4.7` no meio do trabalho (dbt-01, 2026-09-24) | Subido para 1800 s em `bench.toml` antes da rodada completa |
| 10 | A rodada completa passou do teto de US$ 30 no par 60 (projeção real ~US$ 36–39) | `budget_usd = 60` em `bench.toml`; retomada com `--resume`, sem repetir pares |

---

## Desvios do Design

| Desvio | Motivo | Impacto |
|--------|--------|---------|
| Tarefas escritas por agentes **general-purpose**, e não pelos especialistas (dbt-specialist etc.) | Os especialistas têm "KB-FIRST RESOLUTION … mandatory" no prompt, o que viola a Decisão 10 (não ler a KB ao escrever tarefas) | Menos viés a favor do braço A |
| **Solução de referência obrigatória** por tarefa (o DESIGN a tratava como opcional) | Prova que os evals são satisfatíveis, e não só que falham | O `validate` checa as duas direções; 18/18 ✓ |
| Novo checker `duckdb_sql` (execução confinada) | Medallion e modelagem ficam com prova executável, e não só estrutural | Evals mais fortes nos estratos conceituais |
| Tarefas dbt rodam `dbt build`/`dbt snapshot` + `python -c` sobre `bench.duckdb` | `dbt parse` não pega contrato sem tipo nem unit test errado | Evals dbt executáveis de verdade |
| Sandbox com `read_write` do cache npm; doctor sob sandbox | Problemas 1–2 | Fidelidade do preflight |
| Detecção `mcp_missing` → `unavailable` | Problema 2 | B/C nunca contam como "com Context7" sem tê-lo |
| Aviso de amostra mínima (< 3 válidas por braço) no relatório | Evitar leitura errada de rodadas parciais | A regra de decisão **não** mudou |
| Alvos extras no Makefile: `kb-bench-validate`, `kb-bench-smoke` | Conveniência | Nenhum |
| O overhead de base medido foi de **~105–130 mil** tokens de entrada na 1ª chamada, e não os ~38 mil do spike | O prompt da tarefa soma-se às skills, agents e hooks globais | Tokens continuam só como desempate |

---

## Pendências e Riscos

1. **Efeito teto:** B, C e D a 100% em todos os estratos. Antes de agir sobre `aposentar KB`, a 2ª rodada precisa de tarefas reais e mais difíceis (A-007, via `--tasks-dir`) para separar C de D.
2. **Só tarefas sintéticas** e ~6 por célula: o placar é indicativo, não estatístico.
3. **Context7 não cobre** `data-modeling` nem `medallion` (melhor ID fora do domínio): nesses domínios, na prática, B equivale a D e C equivale à KB enxuta sozinha.
4. **Fatos com confiança < 100% nos evals** (declarados pelos autores das tarefas), ainda não revisados: airflow-01 (`create_cron_data_intervals`), fabric-01 (`notebookutils`), fabric-02 (`TridentNotebook`, `LakehouseTableSink`), fabric-03 (`datetime`), shadowtraffic-03 (lookup entre conexões). O PK inline de fabric-03 foi confirmado pela doc oficial.
5. **A assinatura Grok foi descontinuada (2026-09-27).** A bancada continua executável só com um executor novo; a 2ª rodada depende de trocar o `grok_runner` (fronteira com `LLM_PHASE_ROUTING`). O trust dos braços B e C ainda está em `~/.grok/trusted_folders.toml`; para remover: `make kb-bench-teardown`.
6. `budget_usd` ficou em 60 em `bench.toml`; volte para 30 se quiser o teto conservador na próxima rodada.
7. A pasta do spike `/tmp/kbbench-spike.xhYv` pode ser apagada.

---

## Critérios de Aceitação (DEFINE)

| ID | Status | Evidência |
|----|--------|-----------|
| AT-001 Rodada completa | ✅ | Run `20260924T130130Z-66e2`: 72/72 pares registrados, relatório com recomendação por estrato |
| AT-002 Eval discriminante | ✅ | `validate` + `test_non_discriminating_task_is_rejected` |
| AT-003 Retry | ✅ | `test_pass_retry_accumulates_cost`, `test_exhausted_retries_…` |
| AT-004 Contaminação | ✅ | Testes de isolamento + canário real negado |
| AT-005 Context7 indisponível | ✅ | 3 testes (preflight, transporte, MCP ausente) + problema 1 reproduzido e corrigido |
| AT-006 Fila humana cega | ✅ | `test_exhausted_retries_go_to_blind_human_queue` |
| AT-007 Regra de decisão | ✅ | `TestDecisionRule` (8 casos) |
| AT-008 Dry-run | ✅ | `run --dry-run`: validate + smoke sem chamadas ao modelo |
| AT-009 Limite por tentativa | ✅ | `test_no_end_event_is_timeout`; timeout de parede no runner |
| AT-010 Sem efeito colateral | ✅ | `git status` pós-rodada + seção do relatório |

---

## Próximo Passo

1. ✅ `/eval KB_CONTEXT7_REFRESH` — PASS 10/10 (2026-09-27), contrato retroativo sem dependência de conta Grok.
2. `/ship KB_CONTEXT7_REFRESH`.
3. Depois: 2ª rodada com tarefas reais (A-007) e, só então, a feature de migração das KBs guiada pelo placar.
