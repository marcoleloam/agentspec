# BUILD REPORT: Seleção de Agentes via JEV

> Relatório de implementação de JEV_AGENT_SELECTION

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | JEV_AGENT_SELECTION |
| **Data** | 2026-09-23 |
| **Autor** | build-agent |
| **DEFINE** | [DEFINE_JEV_AGENT_SELECTION.md](../features/DEFINE_JEV_AGENT_SELECTION.md) |
| **DESIGN** | [DESIGN_JEV_AGENT_SELECTION.md](../features/DESIGN_JEV_AGENT_SELECTION.md) |
| **Status** | Completo (código) — **critérios de sucesso NÃO atingidos** no eval real (ver Avaliação Completa) |

---

## Resumo

| Métrica | Valor |
|---------|-------|
| **Tarefas Concluídas** | 16/17 (a #17, rotulagem das 20 specs, é do maintainer) |
| **Arquivos Criados** | 11 na fonte (script, 2 testes, 7 fixtures, 1 doc) + 2 cópias geradas (`plugin/scripts/`, `plugin-grok/scripts/`) |
| **Arquivos Modificados (fonte)** | 15 |
| **Arquivos Regenerados** | 57 (`plugin/`, `plugin-grok/`, `plugin-dsh/`, `.codex/`, `.grok/`) |
| **Linhas de Código** | `jev_select.py` 646; `test_jev_select.py` 434; `test_plugin_scripts_sync.py` 24 |
| **Testes Passando** | 104/104 (41 pré-existentes + 63 novos) |
| **Agentes Utilizados** | 0 delegações — tudo executado diretamente (ver Desvios) |

---

## Execução de Tarefas com Atribuição de Agentes

| # | Tarefa | Agente (DESIGN) | Executado por | Status | Notas |
|---|--------|-----------------|---------------|--------|-------|
| 1 | `scripts/jev_select.py` | @python-developer | (direto) | ✅ Completo | Núcleo, transporte, portão, CLI `select`/`--eval` |
| 2 | `tests/fixtures/jev/*.json` (6) | @test-generator | (direto) | ✅ Completo | Feliz multi/single, sem confidence, baixa confiança, abaixo do limiar, Noul inválido |
| 3 | `tests/fixtures/agent_selection/labels_sample.json` | (direto) | (direto) | ✅ Completo | 2 casos; **rótulos provisórios**, marcados para revisão do maintainer |
| 4 | `tests/test_jev_select.py` | @test-generator | (direto) | ✅ Completo | 61 testes, com servidor HTTP local para transporte/timeout |
| 5 | `tests/test_plugin_scripts_sync.py` | @test-generator | (direto) | ✅ Completo | Drift gate para `plugin/` e `plugin-grok/` |
| 6 | Templates DEFINE/DESIGN | (direto) | (direto) | ✅ Completo | Seção "Seleção de Agentes" |
| 7 | `build-plugin.sh` | @shell-script-specialist | (direto) | ✅ Completo | Step 2b' copia o script + `chmod +x` |
| 8 | `scripts/generate-grok-plugin.py` | @python-developer | (direto) | ✅ Completo | Copia `jev_select.py` junto do `judge.py` |
| 9 | `define.md`, `design.md` | (direto) | (direto) | ✅ Completo | Step 1b: Agent Selection + item no Quality Gate |
| 10 | `define-m.md`, `design-m.md` | (direto) | (direto) | ✅ Completo | "Detect Domains → fall back" trocado por Specialist Selection com `variant_locked` |
| 11 | `define-multiagent.md`, `design-multiagent.md` | (direto) | (direto) | ✅ Completo | Consomem `specialists.value`; overlap só quando o script está indisponível |
| 12 | `define-agent.md`, `design-agent.md` | (direto) | (direto) | ✅ Completo | Item de Quality Gate para a seção |
| 13 | `WORKFLOW_CONTRACTS.yaml` | (direto) | (direto) | ✅ Completo | Bloco `agent_selection`; CRLF original preservado |
| 14 | `docs/concepts/jev-agent-selection.md` | @code-documenter | (direto) | ✅ Completo | Setup, dados enviados, `JEV_DISABLE`, `--eval`, limites |
| 15 | `.gitignore` | (direto) | (direto) | ✅ Completo | Ignora o conjunto completo de rótulos |
| 16 | `CHANGELOG.md` | (direto) | (direto) | ✅ Completo | Added + Changed (mudança de comportamento do `-m`) |
| 17 | `.claude/sdd/evals/agent_selection_labels.json` (20 specs) | (maintainer) | — | ⏳ Pendente | Rotulagem humana decidida no DEFINE |

**Legenda:** ✅ Completo | 🔄 Em Andamento | ⏳ Pendente | ❌ Bloqueado

---

## Contribuições dos Agentes

| Agente | Arquivos | Especialização Aplicada |
|--------|----------|------------------------|
| (direto) | 26 | Padrões do DESIGN; estilo de `judge.py` (dataclasses frozen/slots, erros tipados) e de `tests/test_judge.py` (import por caminho) |

---

## Arquivos Criados

| Arquivo | Linhas | Agente | Verificado | Notas |
|---------|--------|--------|------------|-------|
| `scripts/jev_select.py` | 646 | (direto) | ✅ ruff + pytest | Stdlib only; exit 0 sempre em `select` |
| `tests/test_jev_select.py` | 434 | (direto) | ✅ | 61 testes |
| `tests/test_plugin_scripts_sync.py` | 24 | (direto) | ✅ | 2 testes (plugin, plugin-grok) |
| `tests/fixtures/jev/*.json` | 6 arquivos | (direto) | ✅ JSON válido | Respostas no formato documentado (`answers`, `usage`) |
| `tests/fixtures/agent_selection/labels_sample.json` | 1 arquivo | (direto) | ✅ | Carregado por `load_labels` |
| `docs/concepts/jev-agent-selection.md` | 97 | (direto) | ✅ | — |
| `plugin/scripts/jev_select.py`, `plugin-grok/scripts/jev_select.py` | gerados | build | ✅ idênticos à fonte | Cobertos pelo drift gate |

---

## Resultados de Verificação

### Verificação de Lint

```text
$ ruff check scripts/jev_select.py tests/test_jev_select.py tests/test_plugin_scripts_sync.py
All checks passed!
```

**Status:** ✅ Passou (ruff 0.x instalado num `.venv` local via `uv`; o repo não tem config de ruff própria)

### Verificação de Tipos

```text
N/A - mypy não configurado no repo
```

**Status:** ⏭️ Ignorado

### Testes

```text
$ make check        # pytest + --check de router, codex, dsh, grok
104 passed in 2.64s
[OK] agent-router is up to date (73 agents, hash ace6165378f2)
OK - .codex/ + AGENTS.md up to date (73 agents, 39 command skills)
OK - plugin-grok/ + .grok/{agents,commands} up to date
make check exit=0
```

`test_jev_select.py` rodou 3 vezes seguidas sem falha intermitente (61/61 em cada).

| Grupo de testes | Qtde | Resultado |
|-----------------|------|-----------|
| `TestSettings` (defaults, precedência de chave, float inválido, disable) | 4 | ✅ |
| `TestPrefilterAndHeuristic` (inclui `routing.json` real) | 6 | ✅ |
| `TestBuildRequest` (state só com dados, variante travada, truncamento) | 3 | ✅ |
| `TestNormalization` (confidence ausente, Noul fora do intervalo/bool/string) | 9 | ✅ |
| `TestSelect` (AT-001 a AT-010, AT-013, respostas inválidas, sem candidatos/routing) | 20 | ✅ |
| `TestPostDecisions` (servidor local: Bearer, timeout total, HTTP 500, não-JSON, host inacessível) | 5 | ✅ |
| `TestEval` (F1, eval na amostra, rótulo inválido) | 7 | ✅ |
| `TestCli` (entrada inválida → exit 0, sem chave ponta a ponta, eval com rótulos ruins → exit 2) | 7 | ✅ |
| `test_plugin_scripts_sync` | 2 | ✅ |

**Status:** ✅ 104/104 Passou

**Execução real do script empacotado (layout do plugin, sem chave):**

```text
$ python3 plugin/scripts/jev_select.py <<<'{"phase":"design","summary":"dbt marts from Postgres","kb_domains":["dbt","sql-patterns"]}'
[jev_select] source=fallback reason=missing_key latency_ms=None
→ variant=single, specialists=[code-reviewer, dbt-specialist, sql-optimizer, airflow-specialist], 12 candidatos
```

Isso confirma que `routing.json` é encontrado em `plugin/skills/agent-router/`.

---

## Problemas Encontrados

| # | Problema | Resolução |
|---|----------|-----------|
| 1 | Timeout de socket do `urllib` disparava antes do `join()` e era classificado como `network` (teste AT-004 falhou) | `TimeoutError` e `URLError(reason=TimeoutError)` passam a virar `timeout` |
| 2 | `WORKFLOW_CONTRACTS.yaml` usa CRLF; reescrevê-lo com `read_text`/`write_text` converteu 2004 linhas para LF | Arquivo restaurado para CRLF e artefatos regenerados; diff final de +34 linhas por cópia |
| 3 | Python do sistema (3.14) sem pytest/ruff | `.venv` local (já ignorado) com `uv pip install pytest ruff pyyaml`; nada instalado globalmente |
| 4 | Ruff apontou TRY004/ISC004/RUF012 | Erros de tipo agora usam `TypeError` (capturado na CLI); strings concatenadas entre parênteses; `ClassVar` no handler de teste |
| 5 | No bundle Grok, `${CLAUDE_PLUGIN_ROOT:-.}` **não** é reescrito para `${GROK_PLUGIN_ROOT}` (o gerador só troca a forma exata `${CLAUDE_PLUGIN_ROOT}`) | **Não corrigido.** É pré-existente: o `judge.py` tem o mesmo problema no Grok. No Grok o comando cai em `fallback (script_unavailable)` pela regra manual |

---

## Desvios do Design

| Desvio | Motivo | Impacto |
|--------|--------|---------|
| Nenhuma delegação a @python-developer / @test-generator / @shell-script-specialist / @code-documenter | Execução direta mantém o contexto de decisões num lugar só, numa feature pequena e coesa | A atribuição de agentes do manifesto não foi exercitada neste build |
| Limiares lidos por `Settings.from_env()` em vez de constantes de módulo | Testabilidade: os testes injetam o ambiente sem `monkeypatch` global | Nenhum no comportamento |
| `specialists` é sempre calculado, com o campo `applies` (true só se a variante final for multiagent); o DESIGN previa `source: "none"` para single | O `--eval` precisa da escolha de especialistas mesmo quando a variante prevista erra | Os comandos só usam `specialists.value` quando `applies`/multiagent |
| `invalid_json` do DESIGN foi unificado em `invalid_response` | Um motivo só para qualquer resposta inutilizável | Nenhum para o usuário |
| Teste de drift cobre `plugin-grok/` além de `plugin/` | O Grok também empacota o script (Decisão 7) | Cobertura maior |
| O cabeçalho `HTTP-Referer` aponta para `marcoleloam/agentspec` (o `judge.py` usa o upstream) | O fork é o marketplace de instalação | Nenhum funcional |

---

## Bloqueadores (se houver)

| Bloqueador | Ação Necessária | Responsável |
|------------|-----------------|-------------|
| **Critérios de acurácia não atingidos** (variante 0.64 = heurística; F1 +0.09) | Decidir o `/iterate` do DESIGN (ver Avaliação Completa → Recomendação) | Maintainer |
| Rótulos feitos pelo build-agent, não pelo maintainer (como previa o DEFINE) | Revisar os 22 rótulos em `.claude/sdd/evals/agent_selection_labels.json` | Maintainer |
| Os 2 rótulos da amostra são provisórios, escritos pelo build-agent | Revisar, especialmente KB_EVOLUTION = `single` (o JEV real respondeu `multiagent`) | Maintainer |
| A confiança da variante saturou (0.97–1.0) nas 3 chamadas reais em que foi observada (o `--eval` não imprime a confiança); com isso o portão de 0.7 quase nunca dispara | Observar no `--eval` com os 20 rótulos; se continuar saturada, o portão da variante não protege contra erro e deve ser revisto via `/iterate` | Maintainer |

---

## Verificação dos Testes de Aceitação

| ID | Cenário | Status | Evidência |
|----|---------|--------|-----------|
| AT-001 | Caminho feliz: subir para multiagent | 🟡 Parcial | Lógica ✅ (`test_at001_multiagent_happy_path`); o fluxo `/define` → `define-multiagent` com JEV real não foi executado |
| AT-002 | Caminho feliz: manter single | 🟡 Parcial | Lógica ✅ (`test_at002_single_happy_path`); E2E não executado |
| AT-003 | Chave ausente | ✅ Passou | `test_at003_*`, `test_missing_key_end_to_end`, execução real do script empacotado |
| AT-004 | Timeout ≤ 5 s | ✅ Passou | `test_at004_total_timeout_is_enforced`: servidor dorme 3 s, timeout 0,5 s, retorno < 1,5 s |
| AT-005 | Erro HTTP | ✅ Passou | `test_at005_http_error_code` (500 real) + parametrizado 404/500 |
| AT-006 | Baixa confiança | ✅ Passou | `test_at006_low_confidence_keeps_probabilities` |
| AT-007 | Choice sem `confidence` | ✅ Passou | `test_at007_missing_confidence_is_normalized` |
| AT-008 | Nenhum especialista acima do limiar | ✅ Passou | `test_at008_no_fit_above_threshold` |
| AT-009 | `-m` explícito | 🟡 Parcial | Lógica ✅ (`test_at009_locked_variant`, sem pergunta de variante no payload); fluxo `/define-m` não executado |
| AT-010 | Máximo de 4 | ✅ Passou | `test_at010_at_most_four_specialists` |
| AT-011 | Avaliação offline | ✅ Passou | `--eval` real sobre 22 specs rotuladas, 2 rodadas (2026-09-24); o **mecanismo** funciona, mas o **resultado** reprova (ver Avaliação Completa) |
| AT-012 | Empacotamento | ✅ Passou | `test_plugin_scripts_sync` (plugin + plugin-grok), após `./build-plugin.sh` |
| AT-013 | Kill switch | ✅ Passou | `test_at013_disabled_never_calls`, execução real com `JEV_DISABLE=1` |

---

## Notas de Performance

| Métrica | Esperado | Real | Status |
|---------|----------|------|--------|
| Pior caso adicionado à fase | ≤ 5 s | Timeout total garantido por thread daemon; medido < 1,5 s com timeout de 0,5 s | ✅ (teto = `JEV_TIMEOUT_MS` + ~0,1 s) |
| Latência típica do JEV | ≪ 4 s (A-003) | 404–966 ms em 5 chamadas reais (a primeira foi a mais lenta) | ✅ |
| Custo por chamada | desprezível | ~US$ 0,00006 (1.526 tokens de entrada, 252 de saída; `usage.cost` do OpenRouter) | ✅ |
| Acurácia de variante | ≥ 85% e ≥ heurística + 10 p.p. | JEV 0.64 = heurística 0.64 (22 casos, 2 rodadas idênticas) | ❌ |
| F1 de especialistas | ≥ heurística + 0.10 | JEV 0.44 × heurística 0.35 (+0.09; 14 casos multiagent) | ❌ (por 0.01) |

---

## Status Final

### Geral: ✅ COMPLETO (implementação) — ❌ critérios de sucesso não atingidos; não recomendado para /ship

**Checklist de Conclusão:**

- [x] Todas as tarefas do manifesto concluídas (exceto #17, do maintainer)
- [x] Todas as verificações passaram (`make check` exit 0, ruff limpo)
- [x] Todos os testes passam (104/104)
- [ ] Sem bloqueadores — A-001/A-002 ✅; acurácia medida e **reprovada**
- [ ] Testes de aceitação verificados — 10 ✅, 3 parciais (AT-001/002/009 dependem de rodar `/define`/`/design` de verdade)
- [ ] Pronto para /ship — **não**: a pergunta de variante precisa ser refeita (`/iterate`) e revalidada

---

## Validação com o JEV Real (2026-09-24)

Chave: credencial `openrouter` do OMP (`~/.omp/agent/agent.db`, a mais recente), passada só pelo ambiente do processo e nunca impressa.

**A-001 ✅** — a conta tem acesso a `https://openrouter.ai/api/alpha/decisions` com `typesafe/jev-1.13`.
**A-002 ✅** — o corpo e a resposta seguem o formato da API nativa (`answers`, `usage`). O OpenRouter acrescenta `usage.cost` e devolve `confidence` no Choice, então a normalização não foi necessária.
**A-003 ✅** — latência de 404–966 ms.

| # | Caso | Variante JEV (conf) | Especialistas JEV (p) | Heurística | Leitura |
|---|------|---------------------|-----------------------|------------|---------|
| 1 | ETL Postgres→Snowflake, dbt + Airflow (`dbt`, `sql-patterns`, `airflow`) | multiagent (1.0) | dbt-specialist .82, pipeline-architect .75, airflow-specialist .70, data-quality-analyst .69 | multiagent; airflow, **code-reviewer**, dbt, pipeline | ✅ Melhor: trocou `code-reviewer` (.49) por `data-quality-analyst` |
| 2 | Esta feature (`genai`, `prompt-engineering`, `python`, `testing`) | multiagent (0.97) | ai-prompt-specialist .75, llm-specialist .73, genai-architect .65, prompt-crafter .64 | multiagent; ai-prompt, **ai-prompt-gcp**, genai-architect, **kb-evolution** | 🟡 Melhor que a heurística (derrubou GCP .23 e kb-evolution .12), mas ainda deixou de fora `test-generator` (.49) e `python-developer` (.40). Os domínios `genai`/`prompt-engineering` puxaram a escolha |
| 3 | Teste dbt numa coluna (`dbt`) | single (1.0) | dbt-specialist .60 | single; code-reviewer, data-quality-analyst, dbt, pipeline | ✅ Correto e enxuto |
| 4 | `--eval` FRONTEND_ECOSYSTEM | multiagent (conf. não impressa) | F1 0.75 | multiagent, F1 0.75 | Empate |
| 5 | `--eval` KB_EVOLUTION (rótulo provisório `single`) | multiagent (conf. não impressa) | — | multiagent | Os dois erram contra o rótulo provisório; o rótulo pode estar errado |

**Achados:**

1. **A integração funciona de ponta a ponta.** Nenhum fallback nas 5 chamadas reais.
2. **A escolha de especialistas muda de fato.** Em 2 de 3 casos a lista ficou mais coerente com a spec que o overlap. A escolha continua sensível aos domínios de KB informados, que é a mesma fonte do pré-filtro.
3. **A confiança da variante saturou** (0.97–1.0 nas 3 chamadas observadas), então o portão de 0.7 não segura erro da variante. Registrado como bloqueador a observar no `--eval` completo.
4. **A amostra de 2 casos não mede nada:** empate com a heurística. Os critérios de sucesso continuam dependendo dos 20 rótulos.

---

## Avaliação Completa (2026-09-24)

**Conjunto:** 22 specs de design (20 de projetos de clientes, anonimizadas aqui como C01–C20, + 2 arquivadas neste repo), com 8 single e 14 multiagent. Está em `.claude/sdd/evals/agent_selection_labels.json`, fora do git.

**Quem rotulou:** o build-agent (Claude), **às cegas** em relação às respostas do JEV. O DEFINE previa rótulos do maintainer, e o maintainer autorizou esta substituição na sessão. Rubrica usada:

- **multiagent:** o risco central atravessa 2 ou mais áreas técnicas distintas (frontend, backend, dados, IA, infra), cada uma com implementação real.
- **single:** uma área domina. Exemplos: protótipo só de frontend com dados simulados, entregável que é só documento de uma plataforma, troca de configuração.
- **Especialistas:** até 4 agentes do `routing.json` que um revisor chamaria.

**Montagem do input:** o resumo tem problema + objetivos MUST/SHOULD (≤ 3500 caracteres). A linha "Domínios KB" foi mapeada para nomes reais de KB (`tailwind`→`tailwind-css`, `a11y`→`accessibility`, `sql/postgres`→`sql-patterns`...), descartando o que não existe (`golang`, `security`, `azure`). **Achado:** nas specs reais essa linha é texto livre, então o passo 1b dos comandos depende do agente fazer esse mapeamento, e o DESIGN não previa isso.

### Resultado (2 rodadas, métricas idênticas)

| Métrica | JEV | Heurística | Meta | Status |
|---------|-----|------------|------|--------|
| Acurácia de variante | **0.64** | 0.64 | ≥ 0.85 e ≥ heur. + 0.10 | ❌ |
| F1 médio de especialistas (14 multiagent) | **0.44** | 0.35 | ≥ heur. + 0.10 | ❌ (+0.09) |
| Fallbacks | 1 `low_confidence`, 1 `no_fit_above_threshold` | — | — | — |
| Tempo | 22 chamadas em 9,2 s (~420 ms/chamada) | — | — | ✅ |

**Variante:** o JEV respondeu `multiagent` em **22 de 22** casos, com confiança de 0.84 a 1.0; a única exceção foi C14 (0.69 → fallback). Errou os 8 single, todos protótipos de frontend ou trocas de configuração. A acurácia de 0.64 é só a proporção de multiagent no conjunto. **A pergunta de variante atual não discrimina, e o portão de 0.7 não protege** porque a confiança satura.

**Especialistas:** houve ganho real mas pequeno. O JEV foi claramente melhor em C06 — RAG jurídico (0.86 × 0.57), C10 — runtime SDD hospedado (0.57 × 0.00), C16 — widget + workflow n8n (0.57 × 0.29) e FRONTEND_ECOSYSTEM (0.75 × 0.50). Foi pior em C08 — UI + PDF + prompt (0.29 × 0.57) e C12 — migração de infra (0.33 × 0.50). Padrão observado: com `genai`/`prompt-engineering` nos domínios, ele concentra a escolha em agentes de prompt/LLM e deixa de fora os implementadores gerais (`react-developer`, `python-developer`).

**Estabilidade:** entre as 2 rodadas, 7 casos mudaram só na ordem de empates ou num especialista na fronteira do limiar (C12, C18), sem efeito nas métricas.

### Diagnóstico: formulações alternativas da pergunta de variante (não aplicadas ao código)

| Formulação | Acurácia | Single certos | Multi certos |
|------------|----------|---------------|--------------|
| Atual | 0.64 | 0/8 | 14/14 |
| A — mesma pergunta, sem `kb_domains` no state | 0.64 | 0/8 | 14/14 |
| B — Noul "o trabalho fica numa área técnica só?" | 0.73 | 3/8 | 13/14 |
| C — Choice com contraexemplos explícitos | 0.77 | 3/8 | 14/14 |

⚠️ **B e C estão contaminadas.** Foram escritas depois de ver os erros, e os exemplos de C lembram casos do próprio conjunto (C09, C14, C01, C12). Elas mostram que o JEV **consegue** separar melhor com outra pergunta. Não provam que alguma formulação atinge a meta.

### Recomendação

1. **Não fazer `/ship` com a pergunta de variante atual.** Hoje, `/define` e `/design` subiriam para multiagent em praticamente toda spec, o que aumenta o custo sem ganho.
2. **`/iterate` no DESIGN:** trocar a pergunta de variante por uma formulação do tipo B/C, tirar os domínios de KB do state da pergunta de variante, e substituir o portão de confiança (inútil com saturação) por um limiar sobre `p(single)`.
3. **Revalidar num conjunto novo** (specs que nenhuma formulação viu), rotulado pelo maintainer, antes de ajustar limiares.
4. **Especialistas:** manter o JEV (ganho de +0.09), mas avaliar incluir os implementadores gerais sempre como candidatos e uma instrução que não favoreça só os agentes especializados.

---

## Próximo Passo

1. ~~Validar A-001/A-002~~ ✅ feito em 2026-09-24 (ver Validação com o JEV Real).
2. ~~Rotular e rodar `--eval`~~ ✅ feito em 2026-09-24: **reprovado** (ver Avaliação Completa).
3. Decidir o `/iterate` da pergunta de variante (Recomendação acima).
4. Rodar `/define` e `/design` numa spec real para fechar AT-001, AT-002 e AT-009 (depois do `/iterate`).
5. `/ship JEV_AGENT_SELECTION` só quando os critérios forem atingidos num conjunto novo.
