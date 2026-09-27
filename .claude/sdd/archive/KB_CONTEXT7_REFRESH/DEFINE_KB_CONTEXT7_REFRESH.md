# DEFINE: KB_CONTEXT7_REFRESH

> Bancada local e reproduzível que mede, com `grok-4.7`, se consultar o Context7 em tempo de execução (com ou sem uma KB enxuta) resolve tarefas de data engineering tão bem quanto as KBs atuais do AgentSpec, e recomenda manter, enxugar ou aposentar a KB em cada estrato de domínio.

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | KB_CONTEXT7_REFRESH |
| **Data** | 2026-09-23 |
| **Autor** | define-agent |
| **Status** | ✅ Shipped |
| **Clarity Score** | 14/15 |
| **Origem** | `.claude/sdd/features/BRAINSTORM_KB_CONTEXT7_REFRESH.md` |

---

## Declaração do Problema

O AgentSpec distribui 39 domínios de KB (~235 mil palavras, 471 arquivos) com `mcp_validated` entre 2026-02-17 e 2026-04-22, ou seja, 5 a 7 meses de defasagem. Não há registro de refresh (`log.md` inexistente), e o fluxo de refresh está quebrado: o `kb-evolution-agent` não tem ferramenta MCP e os agents apontam para um servidor Context7 que não está configurado. O mantenedor não tem evidência de quanto essas KBs melhoram o resultado em relação a consultar a documentação oficial na hora ou a não usar nada, e por isso não consegue decidir, por tipo de domínio, entre manter, enxugar ou aposentar.

---

## Usuários-Alvo

| Usuário | Papel | Dor |
|---------|-------|-----|
| Mantenedor do AgentSpec (Marco) | Decide o destino das KBs e mantém o plugin | Mantém 39 domínios sem saber se valem o custo; o refresh não acontece; a decisão hoje seria por opinião |
| Usuário do plugin AgentSpec | Recebe agents que consultam a KB antes de agir | Pode receber padrões desatualizados sem perceber |

---

## Objetivos

| Prioridade | Objetivo |
|------------|----------|
| **MUST** | Rodar as mesmas tarefas em 4 braços (A — KB atual; B — sem KB + Context7; C — KB enxuta + Context7; D — nada) com `grok-4.7`, variando **apenas** a fonte de conhecimento |
| **MUST** | Classificar cada execução por eval executável: PASS de primeira, PASS com retry (≤2) ou fila humana |
| **MUST** | Garantir e **provar** o isolamento: B e D não podem ler nenhuma KB (nem a do plugin Grok global); nenhum braço usa busca web |
| **MUST** | Gerar um relatório por braço e estrato que aplique a regra de decisão fixada e recomende uma ação por estrato |
| **MUST** | Não alterar KBs, agents, `_index.yaml`, `build-plugin.sh` nem os bundles gerados |
| **SHOULD** | Registrar custo (tokens) e latência por execução, usados só como desempate |
| **SHOULD** | Fila de revisão humana cega (sem revelar o braço) |
| **SHOULD** | Modo `--dry-run` que valida tarefas, evals e isolamento sem chamar o modelo |
| **COULD** | Reexecutar só um estrato, braço ou tarefa (`--stratum`, `--arm`, `--task`) |

---

## Critérios de Sucesso

- [ ] Smoke test registrado: o MCP `@upstash/context7-mcp` responde a `resolve-library-id` e `query-docs` dentro de uma execução headless do Grok nos braços B e C, com cobertura verificada para cada um dos 6 domínios (registrada como `covered` ou `not_covered`).
- [ ] 18 tarefas (3 por domínio × 6 domínios) versionadas, cada uma com eval executável que **falha** num workspace vazio. A proporção real/sintética alvo é 9/9; na primeira rodada, as sintéticas podem ocupar o lugar das reais ainda não fornecidas, com o fato registrado no relatório.
- [ ] Uma rodada completa gera 72 registros (18 tarefas × 4 braços) em JSONL, cada um com: `run_id`, braço, tarefa, domínio, estrato, desfecho (`pass_first` | `pass_retry` | `human` | `unavailable` | `timeout` | `contaminated`), tentativas (1–3), tokens, latência em segundos e modelo.
- [ ] Zero execuções `contaminated` aceitas: 100% das execuções de B e D passam na checagem de isolamento (nenhum acesso a caminho de KB); qualquer violação é excluída do placar e listada no relatório.
- [ ] O relatório aplica a regra de decisão aos 3 estratos e emite exatamente uma recomendação por estrato (`substituir por B` | `enxugar (C)` | `manter A` | `aposentar KB`), com o placar que a justifica.
- [ ] A rodada completa roda com um comando (`make kb-bench`), e a suíte `pytest` da bancada passa em `make test`.
- [ ] `git status` depois de uma rodada não mostra mudanças fora de `scripts/kb-bench/` e do diretório de resultados.

---

## Testes de Aceitação

| ID | Cenário | Dado | Quando | Então |
|----|---------|------|--------|-------|
| AT-001 | Rodada completa | 18 tarefas válidas, MCP Context7 ativo, Grok logado | `make kb-bench` | 72 registros no JSONL e relatório MD com placar por braço × estrato e uma recomendação por estrato |
| AT-002 | Eval discriminante | Uma tarefa cujo eval passa num workspace vazio | `kb-bench validate` (ou `--dry-run`) | A tarefa é rejeitada com erro nomeando o eval não discriminante; a rodada não começa |
| AT-003 | Retry | A primeira tentativa falha no eval | O runner reexecuta | Até 2 retries, com a saída do eval anexada ao prompt; passou → `pass_retry` com `attempts` = 2 ou 3; não passou → `human` |
| AT-004 | Contaminação | Uma execução de B ou D cujo transcript mostra leitura de caminho que contém `/kb/` ou do diretório do plugin agentspec | Checagem pós-execução | O registro recebe o desfecho `contaminated`, sai do placar e aparece no relatório |
| AT-005 | Context7 indisponível | O MCP falha ou dá timeout num braço B ou C | Durante a execução | Desfecho `unavailable`, que não conta como falha do braço; o relatório mostra a contagem por braço |
| AT-006 | Fila humana cega | Execuções com desfecho `human` | Geração da fila | Cada item recebe um ID opaco, sem nome de braço no conteúdo; o mapeamento ID → braço fica num arquivo separado, lido só pelo relatório |
| AT-007 | Regra de decisão | JSONL fixture em que B resolve ≥ A e não gera mais `human` num estrato | Geração do relatório | Recomendação `substituir por B` nesse estrato; com fixture em que D empata com A → `aposentar KB` |
| AT-008 | Dry-run | Tarefas e config válidas | `make kb-bench ARGS=--dry-run` | Valida tarefas, evals (contra workspace vazio), config dos braços e MCP, sem chamar o modelo, e sai com código 0 |
| AT-009 | Limite por tentativa | Uma execução excede o limite de turnos ou de tempo | Durante a execução | Desfecho `timeout`, registrado e contabilizado no relatório |
| AT-010 | Sem efeito colateral | Rodada completa concluída | `git status --porcelain` | Nenhuma mudança em `.claude/`, `plugin*/`, `.codex/`, `.grok/` ou `build-plugin.sh` |

---

## Desenho do Experimento (normativo)

| Braço | Conhecimento no workspace | MCP | Busca web |
|-------|---------------------------|-----|-----------|
| **A — KB atual** | Cópia de `.claude/kb/{domain}/` + instrução "consulte a KB antes de agir" | Nenhum | Desligada |
| **B — Estilo task-spec** | Nenhuma KB | Context7 (upstash) | Desligada |
| **C — KB enxuta + Context7** | KB enxuta do domínio (ver regra abaixo) | Context7 (upstash) | Desligada |
| **D — Controle** | Nada | Nenhum | Desligada |

**Controles obrigatórios:** mesmo modelo (`grok-4.7`), mesmo prompt de tarefa, mesmos evals, mesmo limite de turnos e tempo, workspace temporário novo por execução, ordem embaralhada com semente registrada, subagents desligados (`--no-subagents`) e ferramentas embutidas restritas ao necessário.

**Regra da KB enxuta (braço C):** ficam anti-patterns, decisões com justificativa e convenções de nomenclatura e estrutura; saem tabelas de API, assinaturas, sintaxe e exemplos de configuração que existem na documentação oficial. A KB enxuta fica em `scripts/kb-bench/` e nunca substitui `.claude/kb/`.

**Amostra estratificada:**

| Estrato | Domínios | Hipótese |
|---------|----------|----------|
| Biblioteca que muda rápido | dbt, airflow | B ou C ≥ A |
| Conceitual/opinativo | medallion, data-modeling | A ou C > B |
| Nicho/proprietário | microsoft-fabric, shadowtraffic | A > B com folga |

**Regra de decisão (fixada antes da primeira rodada):**

1. Num estrato, B substitui a KB se resolver (`pass_first` + `pass_retry`) **pelo menos o mesmo número de tarefas que A** e **não gerar mais `human` que A**.
2. Se B não cumprir o item 1 mas C cumprir, a recomendação é **enxugar (C)**.
3. Se D cumprir o item 1 em relação a A, a recomendação é **aposentar a KB** naquele estrato, com precedência sobre os itens 1 e 2.
4. Caso contrário, **manter A**.
5. Tokens e latência só desempatam quando dois braços cumprem a mesma regra.
6. Execuções `unavailable`, `timeout` e `contaminated` saem do denominador. Se mais de 1/3 das execuções de um braço num estrato cair nesses desfechos, o estrato recebe **inconclusivo** em vez de recomendação.

---

## Fora do Escopo

- Qualquer mudança nos 39 domínios, no `_index.yaml`, no `build-plugin.sh` e nos bundles Codex, Grok e DeepSeek.
- Alterar `kb_domains`, a "KB-first resolution" dos agents ou o agent-router.
- Corrigir o prefixo MCP nos agents de produção e dar MCP ao `kb-evolution-agent` (achado registrado no BRAINSTORM, para feature própria).
- Refresh automático agendado das KBs.
- Contrato `AuthoringEvidence/v1` completo.
- Juiz LLM cruzado e dashboard.
- Rodar a bancada com Claude, Opus ou múltiplos modelos (responsabilidade de `LLM_PHASE_ROUTING`).
- Outros provedores de pesquisa (Exa, Firecrawl, Tavily) e busca web.
- A camada de evals do produto (`POST_BUILD_EVALS`); o loop desta bancada é mínimo e próprio.

---

## Restrições

| Tipo | Restrição | Impacto |
|------|-----------|---------|
| Técnica | Executor: Grok CLI headless (`grok -p … -m grok-4.7 --output-format json`), autenticado pela **assinatura grok.com**, sem API key | O runner chama a CLI `grok`, e não `claude -p` (revisão do BRAINSTORM, que citava `claude -p`) |
| Técnica | O plugin `agentspec` (plugin-grok, com `kb/`) e 115 skills estão instalados globalmente no Grok | O isolamento de B e D precisa bloquear a leitura desses caminhos **e** provar isso pelo transcript (AT-004) |
| Técnica | Context7 via `@upstash/context7-mcp` local (`npx`), configurado no Grok | Precisa estar ativo só em B e C; o mecanismo por execução é decidido no Design |
| Técnica | Busca web desligada em todos os braços (`--disable-web-search`) | O Context7 é a única fonte externa, e só em B e C |
| Técnica | Evals executáveis dependem de ferramentas locais (ex.: `dbt-core` + adapter DuckDB; parse de DAG Airflow) | O Design escolhe entre instalar as ferramentas ou usar asserts estruturais (AST, schema, grep) |
| Recurso | Cota da assinatura Grok: até 18 × 4 × 3 = 216 execuções por rodada completa | Limite de turnos por tentativa e opção de rodar por estrato |
| Método | ~6 tarefas por estrato por braço | Resultado indicativo, não estatístico; o relatório precisa declarar isso |
| Processo | Documentos SDD em pt-BR; código, comandos e identificadores em inglês | — |

---

## Contexto Técnico

| Aspecto | Valor | Notas |
|---------|-------|-------|
| **Localização de Deploy** | `scripts/kb-bench/` (runner, `tasks/`, `kb-lean/`, relatório), `tests/test_kb_bench.py`, alvo `kb-bench` no `Makefile` | Mesmo padrão de `scripts/judge.py` e da suíte `tests/`; resultados em diretório ignorado pelo git (ex.: `.kb-bench/`) |
| **Domínios KB** | dbt, airflow, medallion, data-modeling, microsoft-fabric, shadowtraffic (objetos do teste); testing (padrões pytest para a bancada) | O braço A lê `.claude/kb/{domain}/` só como cópia no workspace temporário |
| **Impacto IaC** | Nenhum | Execução local; só depende de `grok`, `npx` e das ferramentas dos evals |

---

## Premissas

| ID | Premissa | Se Errada, Impacto | Validada? |
|----|----------|-------------------|-----------|
| A-001 | `grok -p --output-format json` (ou `grok usage <sessão>`) expõe tokens por execução | Tokens viram "não medido"; o desempate cai só na latência | [ ] |
| A-002 | Dá para impedir B e D de ler o plugin global (via `--sandbox`, `--cwd` temporário + `--tools` restrito, ou home Grok separado) **sem desinstalar o plugin** do usuário | Seria preciso desabilitar o plugin durante a rodada, o que altera o estado global e exige consentimento explícito | [ ] |
| A-003 | O MCP Context7 pode ser ativado só nas execuções de B e C (config por execução, por projeto ou `grok mcp enable/disable`) | Alternância global com trava contra execuções paralelas | [ ] |
| A-004 | O transcript da execução (`streaming-json` ou `grok export`) registra os caminhos lidos, permitindo detectar contaminação | O AT-004 perde a prova; seria preciso auditar por sandbox com log de acesso | [ ] |
| A-005 | O Context7 cobre dbt e airflow; a cobertura de microsoft-fabric e shadowtraffic é desconhecida | Sem cobertura, B e C nesse estrato medem só a KB enxuta ou nada; o relatório declara isso | [ ] |
| A-006 | A cota da assinatura grok.com suporta uma rodada completa (≤216 execuções) | Rodar por estrato, em dias diferentes | [ ] |
| A-007 | O usuário fornece até 9 tarefas reais durante o `/build` | A primeira rodada usa só sintéticas e declara o risco de viés a favor do KB | [ ] |

**Nota:** A-002, A-003 e A-004 são críticas e devem ser validadas no início do Design, com um spike de 1 execução por braço.

---

## Detalhamento do Clarity Score

| Elemento | Score (0-3) | Notas |
|----------|-------------|-------|
| Problema | 3 | Específico e com evidência (datas, contagens, fluxo de refresh quebrado) |
| Usuários | 2 | O mantenedor está claro; a dor do usuário do plugin é inferida, não medida |
| Objetivos | 3 | MoSCoW com MUSTs verificáveis |
| Sucesso | 3 | Números fixos (18 tarefas, 72 registros, 0 contaminação, 1 recomendação por estrato) e regra de decisão escrita |
| Escopo | 3 | Fora do escopo explícito e alinhado às outras 4 frentes |
| **Total** | **14/15** | |

---

## Questões em Aberto

Nenhuma bloqueia o Design. Para resolver no Design (spike) ou no Build:

1. Mecanismo de isolamento de B e D contra o plugin agentspec global do Grok (A-002) e forma de provar pelo transcript (A-004).
2. Mecanismo para ativar o Context7 só em B e C (A-003).
3. Ferramentas dos evals por domínio: instalar `dbt-core`/Airflow ou usar asserts estruturais.
4. Tarefas reais: o usuário indica repositórios e arquivos durante o `/build` (A-007).

---

## Fronteiras com as Outras Frentes

| Frente | Fronteira |
|--------|-----------|
| `LIVING_MEMORY` | Aqui, só conhecimento externo (como a ferramenta funciona). Conhecimento do projeto fica lá. A KB enxuta não guarda decisões de projeto |
| `POST_BUILD_EVALS` | O loop eval → retry → humano daqui é mínimo e próprio da bancada; pode migrar para a camada de lá depois |
| `LLM_PHASE_ROUTING` | O modelo fica fixo em `grok-4.7` como variável de controle; a escolha de modelo por fase é de lá |
| `JEV_AGENT_SELECTION` | Nada muda no roteamento; o efeito de uma KB menor sobre `kb_domains` e o agent-router é avaliado depois do placar |

---

## Histórico de Revisões

| Versão | Data | Autor | Mudanças |
|--------|------|-------|----------|
| 1.0 | 2026-09-23 | define-agent | Versão inicial a partir do BRAINSTORM. Revisões sobre o BRAINSTORM: executor trocado de `claude -p` para a Grok CLI com `grok-4.7` via assinatura; busca web desligada em todos os braços; desfechos `timeout`, `contaminated` e o estado "inconclusivo" adicionados; confirmado que `generate-dsh-bundle.py` não vendoriza `kb/` |
| 1.1 | 2026-09-27 | ship-agent | Shipped and archived |

---

## Próximo Passo

**Pronto para:** `/design .claude/sdd/features/DEFINE_KB_CONTEXT7_REFRESH.md`
