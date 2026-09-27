# DESIGN: KB_CONTEXT7_REFRESH

> Design técnico da bancada `kb_bench`: executa as mesmas tarefas de data engineering com `grok-4.7` em 4 braços de conhecimento (KB atual, Context7, KB enxuta + Context7, nada), com isolamento imposto pelo sandbox do sistema operacional e provado pelo transcript, e recomenda o destino da KB por estrato.

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | KB_CONTEXT7_REFRESH |
| **Data** | 2026-09-23 |
| **Autor** | design-agent |
| **DEFINE** | [DEFINE_KB_CONTEXT7_REFRESH.md](./DEFINE_KB_CONTEXT7_REFRESH.md) |
| **Status** | ✅ Shipped |
| **Evals Digest** | `sha256:5dd9c7f7f6a3a159a2cf5350516eb53cb2aadc3821626d38ec1e7bfe05ffd634` |
| **Gerado por** | Claude Code · papel `sessão` · `claude-opus-5-5` (seção Evals, 2026-09-27) |

---

## Histórico de Revisões

| Versão | Data | Mudanças |
|--------|------|----------|
| 1.0 | 2026-09-23 | Versão inicial com design técnico completo |
| 1.1 | 2026-09-27 | Shipped and archived |

---

## Resultado do Spike (premissas críticas do DEFINE)

Executado em 2026-09-23 com Grok CLI 1.0.41 e `grok-4.7`, em diretório descartável (`/tmp/kbbench-spike.xhYv`), com 3 execuções headless ao todo (custo total ≈ US$ 0,10).

| Premissa | Resultado | Evidência |
|----------|-----------|-----------|
| **A-001** Tokens por execução | ✅ Validada | O evento final `{"type":"end"}` do `--output-format streaming-json` traz `usage.total_tokens`, `total_cost_usd`, `num_turns`, `stopReason` e `modelUsage`. O modelo efetivo reportado é `grok-4.7-build` |
| **A-002** Bloquear a KB do plugin sem desinstalá-lo | ✅ Validada, **via sandbox** | Perfil customizado `extends = "workspace"` + `deny = [<plugin>/kb]` fez o `read_file` voltar `PermissionDenied`; a leitura no workspace funcionou. **`[plugins] disabled` no config de projeto não funciona**: testados 4 formatos de ID, e o plugin continua ativo |
| **A-003** Context7 só em B e C | ✅ Validada, **com condição** | `.grok/config.toml` no cwd adiciona o `context7` e desliga `wiki-sysmanager`, `azure-devops-oauth` e `azure-devops-sebrae` (estes vêm de `~/.claude.json`). **Porém**, MCP definido por projeto só inicia se a pasta estiver em `~/.grok/trusted_folders.toml`. Com a pasta confiável: handshake OK, 2 ferramentas, chamadas `context7__resolve-library-id` e `context7__query-docs` funcionando sob sandbox. A entrada de trust do spike foi removida depois (`diff` idêntico ao backup) |
| **A-004** Transcript registra caminhos lidos | ✅ Validada | `tool_call.rawInput.target_file`, `tool_call_update.locations[].path`, `status` (`completed`/`failed`) e `rawOutput.PermissionDenied`. As chamadas MCP aparecem como `use_tool` com `tool_name = "context7__…"` |
| **A-005** Cobertura do Context7 | ✅ Medida — **muda a hipótese do estrato nicho** | Ver tabela abaixo |
| Memória entre sessões | ✅ Desligada | Experimental e desligada por padrão; nenhuma pasta nova em `~/.grok/memory-v2/workspaces`. A bancada força `GROK_MEMORY=0` |

**Cobertura Context7 por domínio (resolve-library-id):**

| Domínio | Estrato | Library ID encontrado | Cobertura |
|---------|---------|----------------------|-----------|
| dbt | Biblioteca | `/dbt-labs/docs.getdbt.com` (13.810 snippets), `/dbt-labs/dbt-core` | `covered` |
| airflow | Biblioteca | `/apache/airflow` (6.695 snippets; versões até 3.1.6) | `covered` |
| medallion | Conceitual | Só genéricos (`/microsoftdocs/architecture-center`) | `not_covered` |
| data-modeling | Conceitual | Nada de Kimball (`/microsoft/cdm` é irrelevante) | `not_covered` |
| microsoft-fabric | Nicho | `/websites/learn_microsoft_en-us_fabric` (33.565 snippets) | `covered` |
| shadowtraffic | Nicho | `/websites/shadowtraffic_io` (1.123 snippets) | `covered` |

> **Consequência:** a hipótese do DEFINE "nicho = pouca cobertura externa" está errada para estes dois domínios. O estrato continua (mede produtos de fornecedor único), mas a hipótese passa a ser "B pode competir com A". O relatório registra a cobertura por domínio junto do placar.

**Achados que viram requisitos de design:**

1. O prompt de base custa ~38 mil tokens de entrada **em todos os braços**: 115 skills, 77 agents (incluindo os do plugin agentspec) e 23 hooks globais. É constante entre braços e não enviesa a comparação, mas o relatório precisa declarar o overhead.
2. As descrições dos agents do plugin continuam no prompt em B e D. O modelo pode **tentar** ler a KB; o sandbox nega. Tentativa negada ≠ contaminação: vira a métrica `kb_access_denied`.
3. Qualquer diretório dentro de um repositório git herda `.grok/`, `AGENTS.md` e `CLAUDE.md` do repositório. **Os workspaces precisam ficar fora de qualquer repositório git.**

---

## Visão Geral da Arquitetura

```text
┌───────────────────────────────────────────────────────────────────────────────┐
│                         kb_bench (scripts/kb_bench/)                           │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│  tasks/*.toml ──► [tasks] valida + discrimina (evals falham no workspace vazio) │
│                        │                                                       │
│  bench.toml ──► [config]    plano embaralhado (seed) de tarefa × braço           │
│                        │                                                       │
│                        ▼                                                       │
│  ┌──────────────── [loop] por (tarefa, braço) ─────────────────┐                │
│  │  [workspace] reset ~/.kb-bench/arms/{a,b,c,d}/              │                │
│  │     ├─ fixtures da tarefa                                   │                │
│  │     ├─ kb/ (A: .claude/kb/{d}; C: kb_lean/{d}; B,D: nada)    │                │
│  │     └─ .grok/config.toml (MCP) + .grok/sandbox.toml (deny)   │                │
│  │  [preflight] B,C: grok mcp doctor context7 → senão unavailable│               │
│  │  [grok_runner] grok -p … --sandbox kbbench --streaming-json  │──► grok-4.7    │
│  │  [transcript] NDJSON → tool calls, usage, texto              │   (assinatura) │
│  │  [isolation] contaminated? kb_access_denied? context7 usado? │                │
│  │  [evals] roda checks fora do workspace do agente             │                │
│  │     pass → pass_first/pass_retry │ fail → retry ≤2 → human   │                │
│  └───────────────────────────────┬─────────────────────────────┘                │
│                                  ▼                                             │
│  ~/.kb-bench/results/<run_id>/ runs.jsonl · transcripts/ · human/ (cego)        │
│                                  ▼                                             │
│  [report] placar braço × estrato → regra de decisão → REPORT.md                 │
└───────────────────────────────────────────────────────────────────────────────┘
```

---

## Componentes

| Componente | Propósito | Tecnologia |
|------------|-----------|------------|
| `config` | Carrega `bench.toml`, resolve caminhos (`KB_BENCH_HOME`, default `~/.kb-bench`) e monta a lista de `deny` | Python 3.11+ stdlib (`tomllib`, `pathlib`) |
| `tasks` | Carrega e valida tarefas TOML; checa se os evals discriminam | stdlib |
| `workspace` | Reseta a pasta fixa do braço, copia fixtures e KB, escreve `.grok/config.toml` e `.grok/sandbox.toml` | stdlib (`shutil`) |
| `grok_runner` | Monta o argv, roda `grok` com timeout e devolve o NDJSON bruto | stdlib (`subprocess`) |
| `transcript` | Parser do NDJSON → `Transcript` (tool calls, usage, custo, modelo, texto final) | stdlib (`json`, `dataclasses`) |
| `isolation` | Classifica cada execução: `contaminated`, `kb_access_denied`, `context7_calls`, `context7_failed` | stdlib |
| `evals` | Roda os checks da tarefa numa cópia do workspace com o venv de eval no PATH | stdlib + `.venv` de eval |
| `loop` | Máquina de estados eval → retry → human, mais preflight, timeout e orçamento | stdlib |
| `store` | JSONL append-only por rodada, `run_id`, semente e metadados do ambiente | stdlib |
| `human_queue` | Fila cega com IDs opacos e mapeamento separado; registra o veredito humano | stdlib (`secrets`) |
| `report` | Agrega, aplica a regra de decisão e renderiza `REPORT.md` | stdlib |
| `cli` | Subcomandos `setup`, `teardown`, `validate`, `smoke`, `run`, `report`, `human` | stdlib (`argparse`) |
| `checks/` | Verificadores reutilizáveis chamados pelos evals (AST de DAG, JSON, SQL, regex) | stdlib + `sqlglot` no venv |
| `kb_lean/` | KB enxuta dos 6 domínios (braço C) | Markdown |
| `tasks/` + `fixtures/` | 18 tarefas (3 por domínio) e arquivos de partida | TOML + arquivos |

---

## Decisões Principais

### Decisão 1: Isolamento pelo sandbox do SO, com prova pelo transcript

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-09-23 |

**Contexto:** o plugin agentspec (com `kb/`) está instalado globalmente no Grok, e o config de projeto não consegue desabilitá-lo (spike A-002).

**Escolha:** todo braço roda com `--sandbox kbbench`, definido em `.grok/sandbox.toml` do workspace: `extends = "workspace"` + `deny` para todas as cópias de KB e repositórios do AgentSpec conhecidos na máquina. A lista é resolvida no `setup`, porque o sandbox não aceita glob:

- `~/.grok/installed-plugins/*/kb`
- `~/.claude/plugins/cache/agentspec`
- `~/projetos/framework/agentspec` (checkout principal)
- `~/.superconductor/worktrees/agentspec` e `~/.super.engineering/worktrees/agentspec` (resolvidos por `realpath`)
- a raiz do repositório atual (`git rev-parse --show-toplevel`), o que também esconde as tarefas, os evals e a KB enxuta do agente

**Justificativa:** o sandbox é aplicado ao processo inteiro no startup, de forma irreversível (Seatbelt), e cobre `read_file`, `grep` e `bash`. O transcript prova execução a execução.

**Alternativas Rejeitadas:**
1. `[plugins] disabled` no config de projeto — não funciona (spike).
2. Desabilitar o plugin em `~/.grok/config.toml` durante a rodada — altera o estado global do usuário e quebra se a rodada for interrompida.
3. `HOME` separado — exige copiar `auth.json` (credenciais) e é frágil.

**Consequências:**
- As descrições dos agents do plugin continuam no prompt de todos os braços (constante); tentativas de ler a KB em B e D aparecem como `kb_access_denied`.
- Se o sandbox não for aplicado (a CLI "loga warning e continua"), a proteção cai. Mitigação: **canário** no `smoke` e no início de cada `run` (Decisão 7).

---

### Decisão 2: Pastas fixas por braço fora do git, com trust só em B e C

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita (consentimento do usuário registrado em 2026-09-23) |
| **Data** | 2026-09-23 |

**Contexto:** MCP de projeto só sobe em pasta confiável (spike A-003). A Grok CLI lê `.grok/config.toml` do cwd até a raiz git, e dentro de um repositório herdaria `AGENTS.md`/`CLAUDE.md`.

**Escolha:** 4 pastas fixas `~/.kb-bench/arms/{a,b,c,d}/` (fora de qualquer repositório). O `cwd` de cada execução é a própria pasta do braço, esvaziada antes de cada tentativa (preservando só `.grok/`). `kb-bench setup` adiciona **somente** `arms/b` e `arms/c` a `~/.grok/trusted_folders.toml`, depois de backup e confirmação explícita (`--yes` ou prompt interativo). `kb-bench teardown` remove exatamente essas entradas e restaura a partir do backup.

**Justificativa:** 2 entradas de trust estáveis e reversíveis, em vez de uma por execução; o `.grok/config.toml` de cada braço define o conjunto exato de MCPs.

**Alternativas Rejeitadas:**
1. Workspace temporário por execução — exigiria uma entrada de trust nova a cada execução (216 entradas).
2. Context7 no escopo user alternando `enabled` — muda a configuração global a cada execução e cria corrida entre braços.

**Consequências:**
- As execuções de um mesmo braço são sequenciais (uma pasta por braço). Braços diferentes poderiam rodar em paralelo, mas o MVP roda tudo sequencialmente.
- O `setup` falha com mensagem clara se `~/.kb-bench` estiver dentro de um repositório git.

---

### Decisão 3: Executor Grok CLI headless e retry com sessão nova

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-09-23 |

**Contexto:** o modelo fixo é `grok-4.7` via assinatura (DEFINE), e o DEFINE pede até 2 retries com a saída do eval anexada.

**Escolha:** cada tentativa é uma **sessão nova**: `grok -p <prompt> -m grok-4.7 --sandbox kbbench --output-format streaming-json --disable-web-search --no-subagents --max-turns N --always-approve`, com `GROK_MEMORY=0`. No retry, o workspace é **mantido** (o agente continua o próprio trabalho) e o prompt passa a ser o original mais um bloco "a tentativa anterior falhou nestes checks: …" com a saída dos evals truncada em 4 KB.

**Justificativa:** sessões novas deixam os tokens por tentativa independentes e evitam depender da semântica de `--resume` em modo `-p`; manter o workspace reproduz um retry real.

**Alternativas Rejeitadas:**
1. `--resume <session>` — não validado no spike e acopla o retry ao armazenamento de sessões da CLI.
2. Workspace limpo no retry — deixaria de ser retry e viraria uma nova tentativa às cegas.

**Consequências:**
- Tokens e custo do registro = soma das tentativas; a latência é a soma dos tempos de parede.
- O modelo efetivo (`modelUsage`, ex.: `grok-4.7-build`) é gravado em cada registro.

---

### Decisão 4: Evals escondidos do agente, executáveis onde der e estruturais onde não der

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-09-23 |

**Contexto:** não há `dbt`, `airflow`, `duckdb` nem `pyyaml` instalados; o Fabric não tem runtime local. Se o agente vir os evals, pode otimizar para eles.

**Escolha:**
- Cada eval é um comando (`argv`) que precisa sair com código 0. Os evals rodam **depois** do agente, numa **cópia** do workspace (`<results>/evalws/`), com `PATH` = venv de eval + sistema. Os arquivos de eval ficam no repositório, que é `deny` para o agente (Decisão 1).
- Venv dedicado `scripts/kb_bench/.venv` (ignorado pelo git), criado por `kb-bench setup` com `dbt-core` + `dbt-duckdb` e `sqlglot`, versões fixadas em `scripts/kb_bench/requirements-evals.txt`.
- Por domínio:

| Domínio | Tipo de eval | Exemplos de check |
|---------|--------------|-------------------|
| dbt | Executável | `dbt parse` com `profiles.yml` DuckDB da fixture; asserts sobre `target/manifest.json` (materialização, `unique_key`, testes declarados) |
| airflow | Estrutural (AST) | `checks/airflow_ast.py`: importa `airflow.sdk` ou `airflow.decorators`, usa `schedule=` (não `schedule_interval`), `@dag`/`@task`, sem `days_ago` |
| medallion | Estrutural | Arquivos por camada (`bronze/`, `silver/`, `gold/`), SQL válido (`sqlglot`), dedupe na silver, sem `SELECT *` na gold |
| data-modeling | Estrutural | DDL válido (`sqlglot`), fato com FKs para as dimensões, surrogate key, colunas SCD2 (`valid_from`/`valid_to`/`is_current`) quando pedido |
| microsoft-fabric | Estrutural | Notebook PySpark (AST), escrita Delta com `saveAsTable`, JSON de pipeline com as atividades exigidas |
| shadowtraffic | Estrutural | JSON válido, `generators` com `topic`/`table`, funções `_gen` exigidas, `connections` coerente |

- **Discriminação (AT-002):** `validate` roda os evals sobre o workspace só com as fixtures. Se todos passarem, a tarefa é rejeitada.

**Justificativa:** prova executável onde é barata (dbt); onde não é, checks estruturais determinísticos que capturam exatamente o que muda entre versões (ex.: `schedule_interval` → `schedule` no Airflow 3).

**Alternativas Rejeitadas:**
1. Instalar Apache Airflow — pesado, com restrições de dependência, e o parse de DAG não pega mais que o AST para o que queremos medir.
2. Juiz LLM — fora do escopo (DEFINE).

**Consequências:**
- Checks estruturais podem reprovar soluções corretas escritas de outro jeito; esses casos vão para `human`, e o veredito humano calibra o eval (Decisão 8).

---

### Decisão 5: Detecção de contaminação, indisponibilidade e timeout

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-09-23 |

**Contexto:** AT-004, AT-005 e AT-009.

**Escolha:** regras sobre o `Transcript`, avaliadas nesta ordem:

| Desfecho / métrica | Regra |
|--------------------|-------|
| `contaminated` | (a) Uma tool call **completed** cujo caminho (`rawInput`, `locations[].path` ou string de comando bash) esteja sob um `deny`; **ou** (b) em A ou D, qualquer chamada `use_tool` com `context7__*`; **ou** (c) em qualquer braço, ferramenta de busca ou fetch web |
| `kb_access_denied` (métrica) | Tool call **failed** com `PermissionDenied` sob um `deny` — sem contaminação, apenas contada |
| `unavailable` | B ou C: `grok mcp doctor --json context7` falha no preflight (a execução nem começa); **ou** todas as chamadas `context7__*` da tentativa falharam por erro de transporte |
| `timeout` | O subprocess passou de `attempt_timeout_s` (processo morto); **ou** `stopReason` indica limite de turnos |
| `context7_calls` (métrica) | Número de chamadas `context7__*` completed (B e C) |

**Justificativa:** o sandbox garante; o transcript prova e também detecta falha do próprio sandbox (uma leitura completed num caminho negado só acontece se o sandbox não foi aplicado).

**Alternativas Rejeitadas:**
1. Confiar em `~/.grok/sandbox-events.jsonl` — o arquivo não foi criado no spike, apesar da documentação.

**Consequências:**
- B ou C que simplesmente não chamou o Context7 **não** é `unavailable`: é escolha do modelo e fica visível em `context7_calls = 0`.

---

### Decisão 6: Regra de decisão com taxas e precedência fixa

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-09-23 |

**Contexto:** a regra 6 do DEFINE remove `unavailable`, `timeout` e `contaminated` do denominador, então os braços podem ter denominadores diferentes.

**Escolha:** por estrato e braço, `valid = total − excluídos`, `resolved_rate = (pass_first + pass_retry) / valid` e `human_rate = human / valid`. Um braço X "cumpre" contra A se `resolved_rate(X) ≥ resolved_rate(A)` **e** `human_rate(X) ≤ human_rate(A)`. Precedência:

1. Estrato **inconclusivo** se, em qualquer braço, excluídos > 1/3 do total.
2. D cumpre → `aposentar KB`.
3. B cumpre → `substituir por B`.
4. C cumpre → `enxugar (C)`.
5. Senão → `manter A`.

Quando B e C cumprem juntos, vale B (item 3), e o relatório anota "B e C empatam; tokens: …" para cumprir a regra 5 do DEFINE sem inventar limiar.

**Justificativa:** sem exclusões, é idêntico à regra de contagem do DEFINE; com exclusões, continua justa.

**Consequências:**
- Com cerca de 6 tarefas por estrato, uma tarefa muda a taxa em ~17 pp. O relatório imprime o aviso "indicativo, não estatístico" junto do placar.

---

### Decisão 7: Preflight e canário antes de gastar cota

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-09-23 |

**Escolha:** `kb-bench smoke` (e o início de cada `run`, salvo `--skip-smoke`):
1. `grok --version`, `grok models` contém `grok-4.7`, login ativo.
2. As pastas dos braços estão fora do git; as pastas B e C estão confiáveis; `grok mcp doctor context7` está saudável em B e C e o servidor está ausente em A e D (`grok inspect --json`).
3. **Canário de sandbox**: um arquivo `canary.txt` numa pasta sob `deny`; uma execução curta em D pede para lê-lo. Tem que voltar `PermissionDenied`, senão o `run` aborta.
4. Cobertura do Context7 nos 6 domínios (`resolve-library-id`), gravada em `coverage.json` e levada ao relatório.

**Justificativa:** um sandbox que falha em silêncio invalidaria a rodada inteira; o canário custa cerca de US$ 0,03.

---

### Decisão 8: Fila humana cega e veredito como calibração

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-09-23 |

**Escolha:** cada desfecho `human` gera `human/<id-opaco>.md` com o prompt da tarefa, os arquivos finais do workspace e as falhas de eval, sem nome de braço e sem transcript. O mapeamento `id → (braço, tarefa)` fica em `human/.mapping.json`, lido só pelo `report`. `kb-bench human <run_id>` lista os pendentes e grava `approve` ou `reject` em `human/verdicts.jsonl`.

**Consequências:**
- A regra de decisão usa só `human_rate` (DEFINE). O veredito entra no relatório como **calibração do eval**: muitos `approve` numa tarefa indicam eval rígido demais, a ser corrigido antes da rodada seguinte.

---

### Decisão 9: Nome do pacote e local dos resultados

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-09-23 |

**Escolha:** o pacote é `scripts/kb_bench/`, com sublinhado, para poder ser importado pelos testes (o `tests/conftest.py` já coloca `scripts/` no `sys.path`). O DEFINE dizia `scripts/kb-bench/`; o nome com hífen não é importável. Os resultados ficam em `~/.kb-bench/results/<run_id>/`, fora do repositório, o que cumpre o AT-010 sem tocar no `.gitignore` para eles. Só `scripts/kb_bench/.venv/` entra no `.gitignore`.

---

### Decisão 10: Autoria das tarefas sem ler a KB

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-09-23 |

**Contexto:** se as tarefas sintéticas forem escritas a partir do conteúdo da KB, o braço A é favorecido.

**Escolha:** tarefas sintéticas são escritas a partir de intenção de negócio e da documentação oficial atual, **sem abrir `.claude/kb/`**. Cada tarefa declara `origin = "real" | "synthetic"` e `authored_from` (ex.: "docs Airflow 3.1", "projeto X"). As tarefas reais vêm do usuário durante o build (A-007). O relatório mostra o placar separado por origem quando as duas existirem.

---

## Manifesto de Arquivos

| # | Arquivo | Ação | Propósito | Agente | Dependências |
|---|---------|------|-----------|--------|--------------|
| 1 | `scripts/kb_bench/__init__.py` | Criar | Pacote e versão | @python-developer | Nenhuma |
| 2 | `scripts/kb_bench/bench.toml` | Criar | Configuração padrão (modelo, limites, caminhos, deny, Context7) | @python-developer | Nenhuma |
| 3 | `scripts/kb_bench/config.py` | Criar | Carrega `bench.toml`, resolve caminhos e lista de deny | @python-developer | 2 |
| 4 | `scripts/kb_bench/tasks.py` | Criar | Modelo `Task`, loader TOML, validação de schema | @python-developer | 3 |
| 5 | `scripts/kb_bench/workspace.py` | Criar | Reset das pastas dos braços; fixtures; KB; `.grok/config.toml` e `sandbox.toml` | @python-developer | 3, 4 |
| 6 | `scripts/kb_bench/transcript.py` | Criar | Parser NDJSON → `Transcript` | @python-developer | Nenhuma |
| 7 | `scripts/kb_bench/grok_runner.py` | Criar | argv, subprocess com timeout, `GROK_MEMORY=0` | @python-developer | 3, 6 |
| 8 | `scripts/kb_bench/isolation.py` | Criar | Regras da Decisão 5 | @python-developer | 3, 6 |
| 9 | `scripts/kb_bench/evals.py` | Criar | Roda os evals numa cópia do workspace; discriminação | @python-developer | 3, 4 |
| 10 | `scripts/kb_bench/store.py` | Criar | `run_id`, JSONL, metadados do ambiente | @python-developer | 3 |
| 11 | `scripts/kb_bench/human_queue.py` | Criar | Fila cega, mapeamento e vereditos | @python-developer | 10 |
| 12 | `scripts/kb_bench/loop.py` | Criar | Máquina de estados por (tarefa, braço), preflight, orçamento | @python-developer | 5, 7, 8, 9, 10, 11 |
| 13 | `scripts/kb_bench/report.py` | Criar | Agregação, regra de decisão (função pura) e `REPORT.md` | @python-developer | 10, 11 |
| 14 | `scripts/kb_bench/setup_env.py` | Criar | `setup`/`teardown`: pastas, trust com backup, venv de eval, canário | @shell-script-specialist | 3 |
| 15 | `scripts/kb_bench/cli.py` + `__main__.py` | Criar | `argparse`: setup, teardown, validate, smoke, run, report, human | @python-developer | 12, 13, 14 |
| 16 | `scripts/kb_bench/requirements-evals.txt` | Criar | `dbt-core`, `dbt-duckdb` e `sqlglot` com versões fixadas | @dbt-specialist | Nenhuma |
| 17 | `scripts/kb_bench/checks/{__init__,airflow_ast,sql_check,json_check,regex_check,dbt_manifest}.py` | Criar | Verificadores chamados pelos evals | @python-developer | 16 |
| 18 | `scripts/kb_bench/tasks/dbt/*.toml` + `fixtures/dbt/*` | Criar | 3 tarefas dbt (projeto DuckDB mínimo) | @dbt-specialist | 4, 17 |
| 19 | `scripts/kb_bench/tasks/airflow/*.toml` + fixtures | Criar | 3 tarefas Airflow 3 | @airflow-specialist | 4, 17 |
| 20 | `scripts/kb_bench/tasks/medallion/*.toml` + fixtures | Criar | 3 tarefas medallion | @medallion-architect | 4, 17 |
| 21 | `scripts/kb_bench/tasks/data-modeling/*.toml` + fixtures | Criar | 3 tarefas de modelagem dimensional | @schema-designer | 4, 17 |
| 22 | `scripts/kb_bench/tasks/microsoft-fabric/*.toml` + fixtures | Criar | 3 tarefas Fabric | @fabric-pipeline-developer | 4, 17 |
| 23 | `scripts/kb_bench/tasks/shadowtraffic/*.toml` + fixtures | Criar | 3 tarefas ShadowTraffic | @shopagent-builder | 4, 17 |
| 24 | `scripts/kb_bench/kb_lean/{6 domínios}/*.md` | Criar | KB enxuta do braço C, conforme a regra do DEFINE | @kb-architect | Nenhuma |
| 25 | `scripts/kb_bench/README.md` | Criar | Uso, pré-requisitos, setup/teardown e interpretação do relatório (inglês) | @code-documenter | 15 |
| 26 | `tests/test_kb_bench.py` | Criar | Testes unitários e de integração com `grok` falso | @test-generator | 1–15 |
| 27 | `tests/fixtures/kb_bench/*.ndjson`, `*.jsonl` | Criar | Transcripts reais anonimizados do spike e JSONL fixture da regra de decisão | @test-generator | 26 |
| 28 | `Makefile` | Modificar | Alvos `kb-bench-setup`, `kb-bench`, `kb-bench-report`, `kb-bench-teardown` | @shell-script-specialist | 15 |
| 29 | `.gitignore` | Modificar | `scripts/kb_bench/.venv/` | (direto) | Nenhuma |

**Total de Arquivos:** 29 entradas (~60 arquivos físicos contando tarefas, fixtures e KB enxuta).

> **Guardrail do Build:** os agents 18–23 escrevem tarefas **sem ler `.claude/kb/`** (Decisão 10). O agent 24 lê `.claude/kb/{domínio}` só para derivar a versão enxuta.

---

## Justificativa de Atribuição de Agentes

| Agente | Arquivos Atribuídos | Por Que Este Agente |
|--------|---------------------|---------------------|
| @python-developer | 1–13, 15, 17 | Pacote Python stdlib, dataclasses, type hints; padrão do `scripts/judge.py` |
| @shell-script-specialist | 14, 28 | Setup com backup e restauração de estado global, alvos de Makefile idempotentes |
| @test-generator | 26, 27 | pytest com fixtures e `grok` falso |
| @dbt-specialist | 16, 18 | Projeto dbt + DuckDB mínimo e asserts sobre o manifest |
| @airflow-specialist | 19 | Diferenças Airflow 2 → 3 (`schedule`, `airflow.sdk`) |
| @medallion-architect | 20 | Bronze/Silver/Gold |
| @schema-designer | 21 | Star schema e SCD2 |
| @fabric-pipeline-developer | 22 | Notebooks e pipelines do Fabric |
| @shopagent-builder | 23 | Único agent com ShadowTraffic no escopo |
| @kb-architect | 24 | Curadoria de KB (estrutura e corte do conteúdo) |
| @code-documenter | 25 | README |

**Descoberta de Agentes:** `.claude/agents/**/*.md`, correspondidos por domínio (`kb_domains`), tipo de arquivo e propósito.

---

## Padrões de Código

### Padrão 1: Tarefa (TOML)

```toml
# scripts/kb_bench/tasks/airflow/airflow-01-daily-orders.toml
id = "airflow-01-daily-orders"
domain = "airflow"
stratum = "library"            # library | conceptual | niche
origin = "synthetic"           # synthetic | real
authored_from = "Airflow 3.1 docs (TaskFlow), sem consultar .claude/kb"
fixtures = "fixtures/airflow/airflow-01"   # relativo a scripts/kb_bench/; opcional
prompt = """
Create dags/daily_orders.py: a daily Airflow DAG named daily_orders that extracts
orders from the file data/orders.csv, drops rows with null order_id, and writes
data/orders_clean.parquet. Target Apache Airflow 3. Do not run Airflow.
"""

[[evals]]
name = "dag file exists"
cmd = ["test", "-f", "dags/daily_orders.py"]

[[evals]]
name = "airflow 3 idioms"
cmd = ["python", "-m", "kb_bench.checks.airflow_ast", "dags/daily_orders.py",
       "--require-schedule-kw", "--forbid", "schedule_interval", "--forbid", "days_ago",
       "--dag-id", "daily_orders"]
```

### Padrão 2: Configuração de workspace por braço

```python
# scripts/kb_bench/workspace.py
from __future__ import annotations

import shutil
from pathlib import Path

from kb_bench.config import BenchConfig, Arm

_DISABLED_GLOBAL_MCPS = ("wiki-sysmanager", "azure-devops-oauth", "azure-devops-sebrae")


def reset_arm_dir(arm_dir: Path) -> None:
    """Empty the fixed arm folder, keeping only .grok/ (trust is keyed on the folder)."""
    arm_dir.mkdir(parents=True, exist_ok=True)
    for child in arm_dir.iterdir():
        if child.name == ".grok":
            continue
        shutil.rmtree(child) if child.is_dir() else child.unlink()


def write_grok_config(arm: Arm, arm_dir: Path, cfg: BenchConfig) -> None:
    grok_dir = arm_dir / ".grok"
    grok_dir.mkdir(exist_ok=True)
    lines: list[str] = []
    if arm.uses_context7:
        lines += [
            "[mcp_servers.context7]",
            'command = "npx"',
            f'args = ["-y", "{cfg.context7_package}"]',
            f'env = {{ npm_config_cache = "{cfg.npm_cache_dir}" }}',
            f"startup_timeout_sec = {cfg.context7_startup_timeout_s}",
            "",
        ]
    for name in cfg.disabled_global_mcps or _DISABLED_GLOBAL_MCPS:
        # Project entry replaces the global one entirely (Grok docs) — disable it.
        lines += [f"[mcp_servers.{name}]", 'command = "true"', "enabled = false", ""]
    (grok_dir / "config.toml").write_text("\n".join(lines), encoding="utf-8")

    deny = ", ".join(f'"{p}"' for p in cfg.deny_paths)
    (grok_dir / "sandbox.toml").write_text(
        f'[profiles.{cfg.sandbox_profile}]\nextends = "workspace"\ndeny = [{deny}]\n',
        encoding="utf-8",
    )
```

### Padrão 3: Parser do transcript e regras de isolamento

```python
# scripts/kb_bench/transcript.py
from __future__ import annotations

import json
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ToolCall:
    call_id: str
    tool: str                 # read_file | bash | use_tool | search_tool | ...
    mcp_tool: str | None      # e.g. "context7__query-docs" when tool == "use_tool"
    paths: tuple[str, ...]
    command: str | None
    status: str               # completed | failed | pending
    permission_denied: bool


@dataclass
class Transcript:
    tool_calls: list[ToolCall] = field(default_factory=list)
    text: str = ""
    stop_reason: str | None = None
    total_tokens: int | None = None
    cost_usd: float | None = None
    num_turns: int | None = None
    model: str | None = None


def parse_ndjson(raw: str) -> Transcript:
    t = Transcript()
    pending: dict[str, dict] = {}
    finals: dict[str, dict] = {}
    for line in raw.splitlines():
        if not line.strip():
            continue
        ev = json.loads(line)
        kind = ev.get("type")
        if kind == "text":
            t.text += ev.get("data", "")
        elif kind == "tool_call":
            pending[ev["toolCallId"]] = ev
        elif kind == "tool_call_update":
            cur = finals.setdefault(ev["toolCallId"], {"locations": []})
            cur["locations"] += [loc["path"] for loc in ev.get("locations") or []]
            if ev.get("status"):
                cur["status"], cur["rawOutput"] = ev["status"], ev.get("rawOutput") or {}
        elif kind == "end":
            usage = ev.get("usage") or {}
            t.stop_reason, t.num_turns = ev.get("stopReason"), ev.get("num_turns")
            t.total_tokens, t.cost_usd = usage.get("total_tokens"), ev.get("total_cost_usd")
            t.model = next(iter(ev.get("modelUsage") or {}), None)
    for cid, call in pending.items():
        fin = finals.get(cid, {})
        raw_in = call.get("rawInput") or {}
        paths = {p for p in (raw_in.get("target_file"), raw_in.get("path")) if p}
        paths.update(fin.get("locations", []))
        t.tool_calls.append(ToolCall(
            call_id=cid,
            tool=call.get("toolName", ""),
            mcp_tool=raw_in.get("tool_name") if call.get("toolName") == "use_tool" else None,
            paths=tuple(sorted(paths)),
            command=raw_in.get("command"),
            status=fin.get("status", "pending"),
            permission_denied="PermissionDenied" in (fin.get("rawOutput") or {}),
        ))
    return t
```

```python
# scripts/kb_bench/isolation.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from kb_bench.transcript import Transcript

_WEB_TOOLS = frozenset({"web_search", "web_fetch", "fetch_url"})


@dataclass(frozen=True)
class IsolationVerdict:
    contaminated: bool
    reasons: tuple[str, ...]
    kb_access_denied: int
    context7_calls: int
    context7_failed: int


def _under(path: str, roots: tuple[Path, ...]) -> bool:
    p = Path(path).expanduser()
    return any(p == r or r in p.parents for r in roots)


def check(t: Transcript, *, uses_context7: bool, deny: tuple[Path, ...]) -> IsolationVerdict:
    reasons: list[str] = []
    denied = c7_ok = c7_fail = 0
    for call in t.tool_calls:
        hits = [p for p in call.paths if _under(p, deny)]
        if call.command and any(str(r) in call.command for r in deny):
            hits.append(call.command)
        if hits and call.status == "completed":
            reasons.append(f"{call.tool} read denied path: {hits[0]}")
        elif hits and call.permission_denied:
            denied += 1
        if call.mcp_tool and call.mcp_tool.startswith("context7__"):
            if not uses_context7:
                reasons.append(f"context7 used in non-MCP arm: {call.mcp_tool}")
            c7_ok += call.status == "completed"
            c7_fail += call.status == "failed"
        if call.tool in _WEB_TOOLS:
            reasons.append(f"web tool used: {call.tool}")
    return IsolationVerdict(bool(reasons), tuple(reasons), denied, c7_ok, c7_fail)
```

### Padrão 4: Regra de decisão (função pura, testada pelo AT-007)

```python
# scripts/kb_bench/report.py (trecho)
from __future__ import annotations

from dataclasses import dataclass

EXCLUDED = frozenset({"unavailable", "timeout", "contaminated"})


@dataclass(frozen=True)
class ArmScore:
    total: int
    excluded: int
    resolved: int   # pass_first + pass_retry
    human: int

    @property
    def valid(self) -> int:
        return self.total - self.excluded

    def rate(self, n: int) -> float:
        return n / self.valid if self.valid else 0.0


def satisfies(x: ArmScore, a: ArmScore) -> bool:
    return x.rate(x.resolved) >= a.rate(a.resolved) and x.rate(x.human) <= a.rate(a.human)


def recommend(scores: dict[str, ArmScore]) -> str:
    """scores keyed by arm letter 'A'..'D' for ONE stratum."""
    if any(s.total == 0 or s.excluded * 3 > s.total for s in scores.values()):
        return "inconclusivo"
    a = scores["A"]
    if satisfies(scores["D"], a):
        return "aposentar KB"
    if satisfies(scores["B"], a):
        return "substituir por B"
    if satisfies(scores["C"], a):
        return "enxugar (C)"
    return "manter A"
```

### Padrão 5: Configuração (`bench.toml`)

```toml
# scripts/kb_bench/bench.toml
[run]
model = "grok-4.7"
max_turns = 30
attempt_timeout_s = 600
max_retries = 2
seed = 20260923
budget_usd = 30.0          # aborta a rodada se o custo acumulado passar disto
retry_feedback_bytes = 4096

[paths]
home = "~/.kb-bench"       # sobrescrito por KB_BENCH_HOME; precisa ficar fora de repositório git
repo_kb = ".claude/kb"

[sandbox]
profile = "kbbench"
# Caminhos resolvidos no setup (sem glob no sandbox). A raiz do repo atual é sempre incluída.
deny_globs = [
  "~/.grok/installed-plugins/*/kb",
  "~/.claude/plugins/cache/agentspec",
  "~/projetos/framework/agentspec",
  "~/.superconductor/worktrees/agentspec",
  "~/.super.engineering/worktrees/agentspec",
]

[context7]
package = "@upstash/context7-mcp"
startup_timeout_s = 90
disabled_global_mcps = ["wiki-sysmanager", "azure-devops-oauth", "azure-devops-sebrae"]

[arms.A]
kb = "repo"      # copia .claude/kb/{domain} para ./kb
context7 = false
[arms.B]
kb = "none"
context7 = true
[arms.C]
kb = "lean"      # copia scripts/kb_bench/kb_lean/{domain} para ./kb
context7 = true
[arms.D]
kb = "none"
context7 = false
```

### Padrão 6: Prompt por braço (única diferença entre braços, além de KB e MCP)

```python
# scripts/kb_bench/loop.py (trecho)
ARM_PREAMBLE = {
    "A": "Reference material for this domain is in ./kb/. Consult it before acting.",
    "C": "Reference material for this domain is in ./kb/. Consult it before acting. "
         "You may also use the context7 MCP tools for current official documentation.",
    "B": "You may use the context7 MCP tools for current official documentation.",
    "D": "",
}
COMMON_RULES = (
    "Work only inside the current directory. Do not run network installs. "
    "When done, stop; the result will be checked automatically."
)
```

### Padrão 7: Alvos do Makefile

```makefile
kb-bench-setup: ## KB bench — create arm folders, eval venv, trust arms B/C (asks first)
	@python3 -m kb_bench setup $(ARGS)

kb-bench: ## KB bench — full run (ARGS="--dry-run" | "--stratum library" | "--arm B")
	@python3 -m kb_bench run $(ARGS)

kb-bench-report: ## KB bench — rebuild REPORT.md for the latest (or RUN=<id>) run
	@python3 -m kb_bench report $(if $(RUN),--run $(RUN),--latest)

kb-bench-teardown: ## KB bench — remove trust entries added by setup (restores backup)
	@python3 -m kb_bench teardown $(ARGS)
```

> Os alvos rodam com `PYTHONPATH=scripts` (exportado no Makefile), para `python3 -m kb_bench` achar o pacote.

---

## Fluxo de Dados

```text
1. setup (uma vez): pastas ~/.kb-bench/arms/{a..d}, venv de eval, trust B/C (backup + consentimento)
   │
2. validate: tasks/*.toml → schema OK? evals falham no workspace só com fixtures? (AT-002)
   │
3. smoke: grok/login/modelo · MCP presente só em B e C · canário do sandbox · coverage.json
   │
4. run: plano = shuffle(seed, tarefas × braços)
   │   para cada (tarefa, braço):
   │     tentativa 1..3:
   │       reset da pasta → fixtures + kb (A/C) → .grok/{config,sandbox}.toml
   │       [B/C] preflight mcp doctor → falhou? desfecho = unavailable
   │       grok -p … → NDJSON salvo em transcripts/<task>__<arm>__<n>.ndjson
   │       isolation.check → contaminated? → desfecho = contaminated (para)
   │       timeout/max_turns? → desfecho = timeout (para)
   │       evals na cópia do workspace → passou? pass_first | pass_retry (para)
   │       falhou e ainda há retry → feedback dos evals no próximo prompt
   │     esgotou → human (fila cega)
   │     append em runs.jsonl · custo acumulado > budget? → aborta com relatório parcial
   │
5. human: o usuário aprova/rejeita os itens cegos → verdicts.jsonl
   │
6. report: runs.jsonl + coverage.json + verdicts → placar braço × estrato → recommend() → REPORT.md
```

**Registro JSONL (uma linha por tarefa × braço):**

```json
{"run_id": "20260923T201500Z-3f9a", "task": "airflow-01-daily-orders", "domain": "airflow",
 "stratum": "library", "origin": "synthetic", "arm": "B", "outcome": "pass_retry",
 "attempts": 2, "tokens": 187340, "cost_usd": 0.41, "latency_s": 212.7,
 "model": "grok-4.7-build", "context7_calls": 3, "kb_access_denied": 0,
 "contamination_reasons": [], "eval_failures_last": ["airflow 3 idioms"],
 "seed": 20260923, "grok_version": "1.0.41"}
```

---

## Pontos de Integração

| Sistema Externo | Tipo de Integração | Autenticação |
|----------------|-------------------|--------------|
| Grok CLI (`grok` 1.0.41+) | Subprocess headless (`-p`, `streaming-json`) | Login da assinatura grok.com já existente (`grok login`); a bancada nunca lê `auth.json` |
| Context7 (`@upstash/context7-mcp`) | MCP stdio via `npx`, só em B e C | Sem chave (tier gratuito); falhas de rate limit viram `unavailable` |
| `~/.grok/trusted_folders.toml` | Edição com backup, só pelo `setup`/`teardown` | Consentimento do usuário (2026-09-23) + confirmação a cada setup |
| Venv de eval (`dbt-core`, `dbt-duckdb`, `sqlglot`) | Subprocess nos evals | N/A |

---

## Estratégia de Testes

| Tipo de Teste | Escopo | Arquivos | Ferramentas | Meta de Cobertura |
|---------------|--------|----------|-------------|-------------------|
| Unitário | `transcript.parse_ndjson` com transcripts reais do spike (read negado, read ok, chamadas context7) | `tests/test_kb_bench.py`, `tests/fixtures/kb_bench/*.ndjson` | pytest | 100% das regras de parse usadas |
| Unitário | `isolation.check`: completed em deny → contaminated; failed + PermissionDenied → kb_access_denied; context7 em A/D → contaminated; web → contaminated | idem | pytest | Todas as linhas da tabela da Decisão 5 |
| Unitário | `report.recommend`: fixtures para as 5 saídas (inconclusivo, aposentar, substituir, enxugar, manter) e empate B/C | idem | pytest | AT-007 |
| Unitário | `tasks` + `evals.discriminates`: tarefa cujo eval passa vazio é rejeitada | idem + `tmp_path` | pytest | AT-002 |
| Unitário | `workspace.write_grok_config`: TOML gerado por braço (context7 só em B/C; MCPs globais desligados; deny) | idem | pytest + `tomllib` | 100% |
| Integração | `loop` com **grok falso** (script em `tmp_path` no PATH que emite NDJSON fixo por cenário): pass_first, pass_retry, human, timeout, contaminated, unavailable | idem | pytest + `monkeypatch` | AT-003, AT-004, AT-005, AT-009 |
| Integração | `human_queue`: itens sem nome de braço; mapeamento separado | idem | pytest | AT-006 |
| Integração | `run --dry-run` com grok falso: sem chamada de modelo e exit 0 | idem | pytest | AT-008 |
| E2E | `make kb-bench-setup` → `smoke` → `kb-bench ARGS="--stratum library"` real, depois a rodada completa | Manual | Grok real | AT-001 |
| E2E | `git status --porcelain` após a rodada | Manual / check no fim do `run` | git | AT-010 |

`make test` roda os testes unitários e de integração **sem** Grok, sem rede e sem o venv de eval (os evals reais dos domínios são exercitados no `validate`, fora do `pytest`).

---

## Tratamento de Erros

| Tipo de Erro | Estratégia de Tratamento | Retry? |
|-------------|-------------------------|--------|
| `grok` ausente ou deslogado | `smoke` falha com o comando de correção (`grok login`) | Não |
| MCP Context7 não sobe (B/C) | Preflight → desfecho `unavailable`; conta para a regra "inconclusivo" | Não (não gasta tentativa) |
| Canário lido com sucesso (sandbox inativo) | Aborta o `run` antes de qualquer tarefa | Não |
| Timeout ou limite de turnos | Mata o subprocess; desfecho `timeout` | Não |
| Contaminação detectada | Desfecho `contaminated`; transcript preservado; listado no relatório | Não |
| Eval falhou | Feedback no próximo prompt | Sim (até 2) |
| Eval com erro de infraestrutura (ex.: venv ausente) | Aborta o `run` com mensagem; não conta contra o braço | Não |
| Orçamento estourado | Para a rodada, grava o estado e gera relatório parcial marcado "incompleto" | Não |
| Interrupção (Ctrl-C) | Registro JSONL consistente (append por linha); `run --resume <run_id>` pula pares já registrados | — |
| NDJSON malformado | Registra `outcome = "timeout"` com motivo `parse_error` e salva o bruto | Não |

---

## Configuração

| Chave de Config | Tipo | Padrão | Descrição |
|----------------|------|--------|-----------|
| `run.model` | string | `grok-4.7` | Modelo fixo de todos os braços |
| `run.max_turns` | int | `30` | `--max-turns` por tentativa |
| `run.attempt_timeout_s` | int | `600` | Tempo de parede por tentativa |
| `run.max_retries` | int | `2` | Retries após a 1ª tentativa |
| `run.seed` | int | `20260923` | Semente do embaralhamento |
| `run.budget_usd` | float | `30.0` | Teto de custo acumulado (valor reportado pela CLI) |
| `paths.home` | string | `~/.kb-bench` | Raiz das pastas dos braços e dos resultados (`KB_BENCH_HOME`) |
| `sandbox.deny_globs` | list | ver Padrão 5 | Cópias de KB e repos do AgentSpec negados ao agente |
| `context7.package` | string | `@upstash/context7-mcp` | Pacote npm do MCP |
| `arms.<X>.kb` | enum | `repo`/`none`/`lean`/`none` | Fonte de KB do braço |
| `arms.<X>.context7` | bool | `false`/`true`/`true`/`false` | MCP ativo no braço |

---

## Considerações de Segurança

- **Estado global do usuário:** só `setup`/`teardown` tocam `~/.grok/trusted_folders.toml`, sempre com backup datado em `~/.kb-bench/backups/`, confirmação explícita e remoção apenas das entradas criadas. Nenhuma outra configuração global é alterada (plugin, MCPs e config do usuário ficam intactos).
- **Credenciais:** a bancada nunca lê `~/.grok/auth.json`; o login é o da CLI. `rawOutput` e transcripts podem conter caminhos locais; os fixtures de teste são anonimizados (`$HOME` → `~`).
- **`--always-approve` + sandbox:** a aprovação automática só é aceitável porque o sandbox limita escrita a CWD, `/tmp` e `~/.grok` e nega os caminhos sensíveis. Os prompts proíbem instalações de rede.
- **Evals executam código gerado:** `dbt parse` e os checks rodam numa cópia do workspace, com timeout de 120 s por eval; os checks estruturais nunca importam nem executam o código do agente (só AST, parse e leitura).
- **Isolamento de dados:** tarefas reais do usuário podem conter nomes internos; os arquivos ficam em `scripts/kb_bench/tasks/` apenas se o usuário aprovar versioná-los. O alternativo é `~/.kb-bench/private-tasks/`, carregado por `--tasks-dir`.

---

## Observabilidade

| Aspecto | Implementação |
|---------|---------------|
| Logging | Uma linha por tentativa no stderr (`[B] airflow-01 attempt 2/3 → eval fail (1/2)`); `--verbose` mostra os comandos |
| Métricas | `runs.jsonl` (desfecho, tentativas, tokens, custo, latência, `context7_calls`, `kb_access_denied`) + `coverage.json` + `env.json` (versão do grok, modelo efetivo, seed, commit git) |
| Tracing | Transcript NDJSON bruto por tentativa em `transcripts/`, base de toda afirmação do relatório |

---

## Estrutura do Relatório (`REPORT.md`)

1. Cabeçalho: `run_id`, data, commit, versão do grok, modelo efetivo, seed e aviso "indicativo, não estatístico (≈6 tarefas por estrato)".
2. **Recomendação por estrato**: tabela de estrato → recomendação → justificativa em uma linha.
3. Placar braço × estrato: total, válidos, `pass_first`, `pass_retry`, `human`, excluídos (por tipo), `resolved_rate`, `human_rate`, tokens (mediana), latência (mediana), `context7_calls`, `kb_access_denied`.
4. Cobertura do Context7 por domínio (de `coverage.json`).
5. Isolamento: contaminações (com motivo) e tentativas negadas por braço.
6. Calibração: vereditos humanos por tarefa (`approve` indica eval rígido).
7. Origem das tarefas: real × sintética, e o placar separado quando houver as duas.
8. Overhead constante do prompt de base (tokens de entrada da 1ª chamada) e o tamanho da KB (A) vs. da KB enxuta (C) em palavras.

---

## Fronteiras com as Outras Frentes

| Frente | Como o Design respeita |
|--------|------------------------|
| `LIVING_MEMORY` | `GROK_MEMORY=0`; a KB enxuta não guarda decisões de projeto |
| `POST_BUILD_EVALS` | O loop e os `checks/` ficam isolados em `scripts/kb_bench/`, sem API pública; podem ser absorvidos depois |
| `LLM_PHASE_ROUTING` | Modelo único configurável em `bench.toml`, sem lógica de roteamento |
| `JEV_AGENT_SELECTION` | Nenhum agent, `kb_domains` ou router é tocado |

---

## Riscos Remanescentes

| Risco | Probabilidade | Mitigação |
|-------|---------------|-----------|
| O sandbox falha em silêncio numa atualização da CLI | Baixa | Canário em todo `run`; transcript detecta leitura completed em deny |
| Checks estruturais rígidos punem soluções válidas | Média | Veredito humano como calibração; ajustar o eval antes da 2ª rodada |
| Rate limit do Context7 gratuito | Média | Desfecho `unavailable` + regra "inconclusivo"; `--arm B`/`--stratum` para reexecutar |
| Cota da assinatura Grok | Média | `budget_usd`, execução por estrato e `run --resume` |
| O overhead de ~38 mil tokens de base mascara diferenças de custo | Alta | Tokens são só desempate; o relatório mostra o overhead separado |

---

## Evals

> Contrato de aceitação executável: um eval por AT do DEFINE. **Retroativo:** este DESIGN é anterior à
> camada de evals; o contrato foi adicionado via `/iterate` em 2026-09-27, depois do build e da rodada
> completa, e reexecuta as provas que o BUILD_REPORT cita. Todos são `deterministic` (comandos locais,
> sem chamada a modelo). AT-001 lê a rodada real em `${KB_BENCH_HOME:-~/.kb-bench}`, fora do repositório.
> O contrato não depende de conta Grok (descontinuada em 2026-09-27): o preflight do AT-008 roda contra o
> `grok` falso de `tests/fixtures/kb_bench/fake_grok.py`; a rodada real fica provada pelo registro do AT-001.
> Mude este bloco só via `/iterate`.

<!-- agentspec:evals:contract -->
```toml
[[eval]]
id = "eval_1"
verifies = ["AT-001"]
check_type = "deterministic"
description = "A rodada completa tem 72 registros e o REPORT.md traz placar braço × estrato e uma recomendação por estrato"
run = '''
set -e
"$AGENTSPEC_PYTHON" -m pytest -q tests/test_kb_bench.py -k "test_report_renders_recommendation_and_caveat"
"$AGENTSPEC_PYTHON" - <<'EOF'
import json, os, re
root = os.path.join(os.path.expanduser(os.environ.get("KB_BENCH_HOME", "~/.kb-bench")), "results", "20260924T130130Z-66e2")
recs = [json.loads(l) for l in open(os.path.join(root, "runs.jsonl"), encoding="utf-8") if l.strip()]
plan = json.load(open(os.path.join(root, "plan.json"), encoding="utf-8"))
rep = open(os.path.join(root, "REPORT.md"), encoding="utf-8").read()
assert len(plan["pairs"]) == 72 and len(recs) == 72, (len(plan["pairs"]), len(recs))
assert len({(r["task"], r["arm"]) for r in recs}) == 72, "duplicate pairs"
assert "## Placar braço × estrato" in rep
sec = rep.split("## Recomendação por estrato")[1].split("\n## ")[0]
rows = [l for l in sec.splitlines() if re.match(r"\| (Biblioteca|Conceitual|Nicho) \|", l)]
ok = ("substituir por B", "enxugar (C)", "manter A", "aposentar KB")
assert len(rows) == 3 and all(any(o in r for o in ok) for r in rows), rows
print("AT-001 ok:", len(recs), "records;", [r.split("|")[2].strip() for r in rows])
EOF
'''

[[eval]]
id = "eval_2"
verifies = ["AT-002"]
check_type = "deterministic"
description = "Tarefa não discriminante é rejeitada, e as 18 tarefas do benchmark discriminam (falham nas fixtures, passam na solução)"
run = '''
set -e
"$AGENTSPEC_PYTHON" -m pytest -q tests/test_kb_bench.py -k "test_non_discriminating_task_is_rejected or test_discriminating_task_with_solution"
PYTHONPATH=scripts "$AGENTSPEC_PYTHON" -m kb_bench validate | tee /tmp/kbbench-eval-validate.log
grep -q "18/18 tasks valid" /tmp/kbbench-eval-validate.log
'''

[[eval]]
id = "eval_3"
verifies = ["AT-003"]
check_type = "deterministic"
description = "Retry: até 2 retries com a saída do eval no prompt; pass_retry acumula tentativas e custo; esgotado vira human"
run = '''
"$AGENTSPEC_PYTHON" -m pytest -q tests/test_kb_bench.py -k "test_pass_first or test_pass_retry_accumulates_cost or test_exhausted_retries_go_to_blind_human_queue or test_feedback_hides_evaluator_paths"
'''

[[eval]]
id = "eval_4"
verifies = ["AT-004"]
check_type = "deterministic"
description = "Leitura de KB/plugin, Context7 fora de B/C ou web marcam contaminated; leituras negadas pelo sandbox não"
run = '''
"$AGENTSPEC_PYTHON" -m pytest -q tests/test_kb_bench.py -k "TestIsolation or test_completed_read_of_deny_path_is_contaminated"
'''

[[eval]]
id = "eval_5"
verifies = ["AT-005"]
check_type = "deterministic"
description = "Falha de preflight, de transporte ou ausência do MCP Context7 em B/C resulta em unavailable"
run = '''
"$AGENTSPEC_PYTHON" -m pytest -q tests/test_kb_bench.py -k "test_context7_preflight_failure_is_unavailable or test_context7_transport_failure_is_unavailable or test_context7_missing_in_session_is_unavailable"
'''

[[eval]]
id = "eval_6"
verifies = ["AT-006"]
check_type = "deterministic"
description = "Fila humana cega: ID opaco, sem braço no conteúdo, mapeamento em arquivo separado"
run = '''
"$AGENTSPEC_PYTHON" -m pytest -q tests/test_kb_bench.py -k "test_exhausted_retries_go_to_blind_human_queue"
'''

[[eval]]
id = "eval_7"
verifies = ["AT-007"]
check_type = "deterministic"
description = "Regra de decisão: B ≥ A → substituir por B; D empata com A → aposentar KB; demais saídas e inconclusivo"
run = '''
"$AGENTSPEC_PYTHON" -m pytest -q tests/test_kb_bench.py -k "TestDecisionRule"
'''

[[eval]]
id = "eval_8"
verifies = ["AT-008"]
check_type = "deterministic"
description = "Dry-run: tarefas e evals validados e preflight de braços, trust e MCP aprovado sem conta Grok e sem chamada ao modelo"
run = '''
set -e
"$AGENTSPEC_PYTHON" -m pytest -q tests/test_kb_bench.py -k "TestDryRun"
PYTHONPATH=scripts "$AGENTSPEC_PYTHON" -m kb_bench validate | tee /tmp/kbbench-eval-dryrun.log
grep -q "18/18 tasks valid" /tmp/kbbench-eval-dryrun.log
'''

[[eval]]
id = "eval_9"
verifies = ["AT-009"]
check_type = "deterministic"
description = "Execução sem evento de fim (limite de turnos/tempo) resulta em timeout"
run = '''
"$AGENTSPEC_PYTHON" -m pytest -q tests/test_kb_bench.py -k "test_no_end_event_is_timeout"
'''

[[eval]]
id = "eval_10"
verifies = ["AT-010"]
check_type = "deterministic"
description = "Sem efeito colateral: nenhuma mudança em .claude/ (fora de .claude/sdd/), plugin*/, .codex/, .grok/ ou build-plugin.sh"
run = '''
bad=$(git status --porcelain --untracked-files=all | cut -c4- | grep -E '^(\.claude/|plugin|\.codex/|\.grok/|build-plugin\.sh)' | grep -v '^\.claude/sdd/' || true)
if [ -n "$bad" ]; then echo "unexpected changes:"; echo "$bad"; exit 1; fi
echo "AT-010 ok"
'''
```

---

## Próximo Passo

**Pronto para:** `/build .claude/sdd/features/DESIGN_KB_CONTEXT7_REFRESH.md`
