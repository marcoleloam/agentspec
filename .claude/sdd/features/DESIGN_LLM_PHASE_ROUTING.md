# DESIGN: LLM Phase Routing

> Design técnico para implementar o roteamento de modelo por fase do SDD, com o OMP como harness principal

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | LLM_PHASE_ROUTING |
| **Data** | 2026-09-23 |
| **Autor** | design-agent |
| **DEFINE** | [DEFINE_LLM_PHASE_ROUTING.md](./DEFINE_LLM_PHASE_ROUTING.md) |
| **Status** | Pronto para Build |
| **Evals Digest** | `sha256:b030f8940483c9ab339160ac6b83f94fab8cf09332f4410d910cb0ef0933067a` |
| **Gerado por** | Claude Code — sessão principal, `claude-opus-5-5` (`/design` ainda roda inline; esta feature muda isso) |

---

## Resultado do Spike (A-001, A-002, A-004, A-005)

Executado em 2026-09-23 com `omp` v18.2.11, em diretório temporário (`/tmp/omp-probe`, já removido). O config do usuário não foi alterado: overrides aplicados só por `--config <overlay>` naquela execução. Modelos usados: `@smol` (sessão) e `@plan` (um subagent).

| # | Teste | Resultado | Premissa |
|---|-------|-----------|----------|
| 1 | Pedir ao OMP a lista de agents da ferramenta `task`, com o plugin `agentspec` 3.4.1 instalado | Só nativos: `scout`, `reviewer`, `security-reviewer`, `task`, `sonic`. **Nenhum agent do AgentSpec** | A-004 ❌ na prática |
| 2 | `.omp/agents/flat-probe.md` × `.omp/agents/sub/nested-probe.md` | `flat-probe` aparece; `nested-probe` **não**. O OMP não lê subpastas, e o plugin guarda os agents em `agents/<categoria>/` | Causa de A-004 |
| 3 | `flat-probe` com `model: "@smol"` + overlay `task.agentModelOverrides.flat-probe: "@plan"` | Sessão em `xai-oauth/grok-4.6`; subagent com `resolvedModel` = `openai-codex/gpt-6-astra:high` | A-001 ✅ (chave = `name:`; o override vence a frontmatter). A-005 ✅ (a sessão grava `resolvedModel`; o subagent informou o próprio modelo) |
| 4 | Cópia real de `ship-agent.md` (`model: sonnet`, `tools: [Read, Write, Edit, Glob, Bash]`) + override `@smol` | Rodou em `grok-4.6:xhigh`; ferramentas mapeadas para `read, write, edit, glob, bash` | Nomes de ferramenta do Claude funcionam no OMP |
| 5 | Comando `.omp/commands/probe-cmd.md` com `context: fork` + `agent: flat-probe` | Ignorado: rodou inline no modelo da sessão | A-002 ❌ por frontmatter |
| 6 | Comando com `model: "@plan"` | Ignorado: rodou em `grok-4.6` | Comando não troca modelo no OMP |
| 3′ | Instrução em prosa ("use your task tool to run agent X") | O modelo delegou corretamente | A-002 ✅ por instrução no corpo |

**Consequências para o desenho:**

1. Os agents precisam chegar ao OMP numa pasta única, sem subpastas. Sem isso, nem o roteamento nem o `/build` (que delega a especialistas) funcionam no OMP.
2. A delegação da fase vai como **instrução no corpo do comando**, não por frontmatter.
3. O papel do OMP entra por `task.agentModelOverrides`. A frontmatter dos agents continua com aliases Claude, válidos nos dois harnesses.

---

## Atualização 1.1 — base `9de8ce4` (gate `/eval`, fase 3.5)

Antes do build, a branch avançou por fast-forward até `main@9de8ce4` (ship de `POST_BUILD_EVALS`). O que muda neste DESIGN:

| # | Mudança na base | Ajuste aqui |
|---|-----------------|-------------|
| 1 | Novo agent `eval-agent` (`model: sonnet`, com `AskUserQuestion`) | Entra no manifesto: `omp_role = "default"`, `claude_model = "sonnet"`, `codex_effort = "medium"`. São 10 agents de workflow |
| 2 | Novo comando `/eval` (`eval.md`) | Entra no manifesto como **session** (`recommended_role = "default"`). O `eval-agent` pergunta ao usuário (atestações), e um subagent não consegue fazer isso. A independência do aceite vem do `eval_runner.py` e do JEV, não do modelo da sessão |
| 3 | `/ship` tem o Step 0 bloqueante (`eval_runner.py verify`) | O Step 0 roda na sessão principal; só depois do OK o comando delega os Steps 1–8 ao `ship-agent` |
| 4 | O contrato ganhou `eval.jev.model: "typesafe/jev-1.13"` (documentação do juiz do `/eval`) | A Regra 6 do `--check` só proíbe `model:` com **alias Claude** no contrato; o `jev.model` fica |
| 5 | `Makefile` usa `$(PYTHON)` (`.venv` quando existe) | Os alvos novos usam `$(PYTHON)` |
| 6 | O `DESIGN_TEMPLATE` exige `## Evals` + linha **Evals Digest**; o `/ship` exige recibo PASS | Este DESIGN ganha o contrato `## Evals` (ao final), congelado por `freeze` |

**Observação para `POST_BUILD_EVALS`, fora do escopo:** o `eval.md` diz "Delegate to the **eval-agent**", mas o agent usa `AskUserQuestion`, o que não funciona dentro de um subagent do Claude Code. Não alteramos o texto dessa frente.

---

## Visão Geral da Arquitetura

```text
                         FONTE ÚNICA
        .claude/sdd/architecture/PHASE_MODEL_ROLES.toml
        (agent → papel OMP · alias Claude · effort Codex;
         comando → modo session|delegated)
                               │
            scripts/phase_routing.py  (stdlib: tomllib)
     ┌──────────────┬──────────┴────────┬───────────────────┐
     │ --apply      │ --check           │ --print-omp-      │ lib (import)
     │              │ (make check)      │   overrides       │
     ▼              ▼                   ▼                   ▼
 .claude/agents/  falha se: frontmatter  stdout: trecho    generate-codex-
 workflow/*.md    ≠ manifesto; marcador  task.agent-       plugin.py lê
 (model:)         de comando ≠ modo;     ModelOverrides    codex_effort
 .claude/commands/ ID concreto; contrato  (usuário cola no
 workflow/*.md    com model:; plugin/    ~/.omp/agent/
 (marcador)       agents com subpasta    config.yml)
     │
     ▼
 build-plugin.sh ──► plugin/agents/*.md  (ACHATADO: sem subpastas,
                                           sem README/_template)
     │                         │
     ▼                         ▼
 Claude Code                 OMP (instala o mesmo plugin)
 /design → Task(design-agent)  /design → task(design-agent)
   model: opus                   override "@slow" → config.yml
                                 → modelo concreto do usuário

Fases session (brainstorm, define, define-m, iterate, design-m, build,
continuar, work): rodam inline; o marcador recomenda o papel ao abrir a
sessão (omp --model @plan / @slow / default).
```

---

## Componentes

| Componente | Propósito | Tecnologia |
|------------|-----------|------------|
| `PHASE_MODEL_ROLES.toml` | Fonte única do roteamento fase → papel | TOML (stdlib `tomllib`, Python ≥ 3.11) |
| `scripts/phase_routing.py` | Carregar, validar, aplicar (`--apply`), checar divergências (`--check`) e imprimir o trecho OMP (`--print-omp-overrides`) | Python stdlib |
| Blocos de roteamento nos comandos | `/design` e `/ship` delegam ao agent; os demais declaram modo session + papel recomendado | Markdown + marcador `<!-- phase-routing: … -->` |
| Linha `Gerado por` | Proveniência (harness, papel, modelo) em 5 templates | Markdown |
| Achatamento de `plugin/agents` | Tornar os 73 agents visíveis ao OMP | Bash (`build-plugin.sh`) |
| Integração Codex (S3) | Effort dos agents de workflow vem do manifesto | Python (`generate-codex-plugin.py`) |
| Documentação | Tabela, receita do OMP, aviso de família | Markdown |

---

## Decisões Principais

### Decisão 1: Manifesto em TOML, não YAML

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-09-23 |

**Contexto:** o DEFINE nomeou o arquivo `.yaml`, mas os scripts do repositório só usam a stdlib (os geradores fazem parse de frontmatter com regex), e o CI raiz instala só `pytest`. `PyYAML` não está disponível.

**Escolha:** `.claude/sdd/architecture/PHASE_MODEL_ROLES.toml`, lido com `tomllib` (stdlib desde o 3.11; o CI usa 3.11 e 3.12).

**Justificativa:** parse robusto sem dependência nova, com comentários e legível.

**Alternativas Rejeitadas:**

1. YAML + PyYAML: nova dependência no CI e no `make check`.
2. YAML com parser mínimo próprio: frágil.
3. JSON: sem comentários, e o manifesto precisa explicar papéis.

**Consequências:**

- Desvio de nome em relação ao DEFINE M1 (a extensão muda; o conteúdo é o mesmo).
- Contribuidores editam TOML num repositório majoritariamente YAML/Markdown.

---

### Decisão 2: Achatar `plugin/agents/` no build (entrega para o OMP)

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita (⚠️ mudança visível no Claude Code, ver consequências) |
| **Data** | 2026-09-23 |

**Contexto:** o spike (testes 1 e 2) mostrou que o OMP não descobre agents em subpastas, e o plugin guarda os 73 em `agents/<categoria>/`. É o plano B previsto no DEFINE ("bundle OMP dedicado se a premissa falhar"), aqui sem criar um segundo pacote.

**Escolha:** o `build-plugin.sh` passa a gerar `plugin/agents/*.md` numa pasta única (os nomes de arquivo e os `name:` são únicos, verificado: 73 sem duplicata e sem colisão com `task`, `reviewer`, `scout`, `designer`, `librarian`, `sonic`, `security-reviewer`). `README.md` e `_template.md` deixam de ir para `plugin/agents/`. Referências `${CLAUDE_PLUGIN_ROOT}/agents/<categoria>/` são reescritas para `${CLAUDE_PLUGIN_ROOT}/agents/`. A fonte `.claude/agents/<categoria>/` continua como está.

**Justificativa:** um único artefato atende Claude Code e OMP; o caminho do KB (`${CLAUDE_PLUGIN_ROOT}/kb`) não muda; o `/build` no OMP passa a enxergar os especialistas. O gerador do Grok já achata pelo mesmo motivo (`scripts/generate-grok-plugin.py`, docstring item 2).

**Alternativas Rejeitadas:**

1. Segundo plugin `agentspec-omp` com agents achatados: duplica 73 agents, exige vendorizar `kb/` (3,0 MB) ou quebrar os caminhos de KB, e os usuários instalariam dois plugins.
2. Gerar `.omp/agents/` por projeto: o OMP descobre (teste 2), mas volta ao padrão "copiar por projeto" que o `CLAUDE.md` quer abandonar.
3. Symlinks para o diretório de agents do usuário no OMP: caminho não verificado e escreve fora do repositório.

**Consequências:**

- **Nomes no Claude Code mudam:** `agentspec:workflow:design-agent` passa a `agentspec:design-agent` (e o mesmo para todas as categorias). No repositório, só os dois documentos desta feature citam o nome antigo. Entra no CHANGELOG como breaking para quem referencia o nome qualificado.
- Some o agent-lixo `agentspec:[object Object]` / `agentspec:README`, que hoje aparece no Claude Code por causa do `_template.md` e do `README.md`.
- `docs/concepts/agent-overrides.md` precisa trocar `$CLAUDE_PLUGIN_ROOT/agents/workflow/…` por `$CLAUDE_PLUGIN_ROOT/agents/…`.
- A descoberta de agents em pasta única **dentro de um plugin do marketplace** no OMP não foi testada (só em `.omp/agents`). A validação fica no Build (V-1), com fallback definido.

---

### Decisão 3: Papel do OMP via `task.agentModelOverrides`; frontmatter com alias Claude

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-09-23 |

**Contexto:** o mesmo `plugin/` roda no Claude Code e no OMP. `model: "@slow"` é válido no OMP e inválido no Claude Code.

**Escolha:** a frontmatter mantém `opus`/`sonnet`/`haiku`/`inherit`. O `phase_routing.py --print-omp-overrides` imprime o trecho `task.agentModelOverrides` (`design-agent: "@slow"`, `ship-agent: "@smol"`, …), que o usuário mescla no `~/.omp/agent/config.yml`.

**Justificativa:** o spike (teste 3) provou que o override vence a frontmatter e que a chave é o `name:` do agent. O modelo concreto continua só no config do usuário.

**Alternativas Rejeitadas:**

1. Lista `model: ["@slow", "opus"]`: inválida no Claude Code.
2. Gerar frontmatter diferente por harness: exigiria o segundo plugin (rejeitado na Decisão 2).

**Consequências:**

- Sem o trecho aplicado, o OMP usa `opus`/`haiku` por fuzzy match (AT-003) ou o modelo da sessão. Nada quebra.
- O gerador **nunca lê nem escreve** `~/.omp`; o usuário mescla o trecho manualmente sob o `agentModelOverrides` que já existe (hoje com `task`, `reviewer`, `security-reviewer`, `scout`, `sonic`).

---

### Decisão 4: Delegação por instrução no corpo do comando; só `/design` e `/ship`

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita (desvio no `/design-m`) |
| **Data** | 2026-09-23 |

**Contexto:** no OMP, `context: fork`, `agent:` e `model:` em comando são ignorados (testes 5 e 6), mas o modelo segue a instrução em prosa para usar a ferramenta task (teste 3′). No Claude Code, subagents não criam outros subagents.

**Escolha:**

- **Delegated:** `/design` → `design-agent`; `/ship` → `ship-agent`. O comando instrui a delegar uma vez, passa o caminho de entrada e o nome da feature, e roda o `--judge` na sessão principal depois do retorno.
- **Session:** `/brainstorm`, `/define`, `/define-m`, `/iterate`, `/build`, `/continuar`, `/work` e **`/design-m`**. Rodam inline; o marcador recomenda o papel.

**Justificativa:** `design-agent` e `ship-agent` não têm `AskUserQuestion` nem `Agent`/`Task` nas ferramentas, então rodam sozinhos num subagent. `/design-m` consulta 3 a 4 especialistas via `Agent`: dentro de um subagent do Claude Code isso não funciona, e no OMP exigiria o campo `spawns`, que não foi testado.

**Alternativas Rejeitadas:**

1. `context: fork` + `agent:`: ignorado no OMP (teste 5).
2. Delegar `/design-m` a `design-multiagent`: cria subagent dentro de subagent.
3. Delegar `/build`: o orquestrador delega a especialistas, o mesmo problema.

**Consequências:**

- Desvio do DEFINE M2, que listava `/design-m`. Ele passa a session com `recommended_role = "slow"`.
- A-006 (contexto limpo): o subagent recebe caminhos, não o histórico da conversa. Mitigação: `design-agent.md` já instrui a ler DEFINE, template e `CLAUDE.md`.
- Se a delegação não estiver disponível (agent não encontrado), o comando avisa e roda inline como fallback, registrando o modelo da sessão em **Gerado por**.

---

### Decisão 5: Remover `model:` do `WORKFLOW_CONTRACTS.yaml`

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-09-23 |

**Contexto:** o contrato diverge da frontmatter em 4 de 6 entradas (`brainstorm` opus × sonnet, `define` opus × sonnet, `build` sonnet × opus, `ship` haiku × sonnet). Nenhum código lê esse campo (grep: `spec-linter`, `generate-dsh-bundle.py` e `plugin-dsh/lib` não usam `model`).

**Escolha:** apagar as linhas `model:` com alias Claude do contrato (fases, `cross_phase` e blocos `agent:`) e colocar um comentário: `# Model routing: see PHASE_MODEL_ROLES.toml`. O `--check` falha se alguma dessas linhas voltar. O `eval.jev.model` (juiz do `/eval`) não é roteamento de fase e fica (Atualização 1.1, item 4).

**Justificativa:** elimina uma classe inteira de divergência em vez de sincronizar três fontes.

**Alternativa Rejeitada:** sincronizar o contrato pelo `--apply`. Manteria a duplicação e exigiria parse do YAML por regex, sensível à indentação.

**Consequências:** atende AT-005 de forma mais forte (não existe mais o que divergir). Leitores do contrato são direcionados ao manifesto.

---

### Decisão 6: Checagem de IDs concretos limitada ao manifesto e à frontmatter

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita (ajuste do critério do DEFINE) |
| **Data** | 2026-09-23 |

**Contexto:** a regex do DEFINE aplicada aos **corpos** dos comandos de workflow acusaria exemplos legítimos do `--judge` (`openai/gpt-4o`, `anthropic/claude-opus-4` em `define.md` e `design.md`).

**Escolha:** a regex `(gpt-|grok-|claude-|gemini-|deepseek)[0-9a-z.-]+` roda no `PHASE_MODEL_ROLES.toml`, na **frontmatter** de `.claude/agents/workflow/*.md` e no bloco `phase-routing` dos comandos.

**Consequências:** o objetivo (roteamento sem ID versionado) fica garantido sem falsos positivos. Os slugs do Judge ficam para o C1.

---

### Decisão 7: Mapeamento final

| Agent | `omp_role` | `claude_model` (hoje → novo) | `codex_effort` |
|-------|-----------|------------------------------|----------------|
| `brainstorm-agent` | `plan` | sonnet → **opus** | high |
| `brainstorm-multiagent` | `plan` | opus | high |
| `define-agent` | `plan` | sonnet → **opus** | high |
| `define-multiagent` | `plan` | opus | high |
| `design-agent` | `slow` | opus | high |
| `design-multiagent` | `slow` | opus | high |
| `build-agent` | `default` | opus → **inherit** | high |
| `iterate-agent` | `plan` | sonnet → **opus** | high |
| `ship-agent` | `smol` | sonnet → **haiku** | low |
| `eval-agent` | `default` | sonnet | medium |

| Comando (arquivo) | Modo | Agent / papel recomendado |
|-------------------|------|---------------------------|
| `brainstorm` | session | `plan` |
| `define`, `define-m`, `iterate` | session | `plan` |
| `design` | delegated | `design-agent` |
| `design-m` | session | `slow` |
| `build`, `continue` (`/continuar`), `work` | session | `default` |
| `ship` | delegated | `ship-agent` (Step 0 `verify` na sessão) |
| `eval` | session | `default` |
| `create-pr` | fora do manifesto (não é fase) | — |

**Justificativa das mudanças de alias:**

- Os agents interativos só rodam como subagent quando invocados explicitamente. `opus` alinha com o papel `plan` do DEFINE.
- `build-agent: inherit` porque o orquestrador segue a sessão.
- `ship-agent: haiku` fecha a questão 3 do DEFINE: arquivar é tarefa barata, e o OMP usa `@smol` de qualquer forma.

---

## Manifesto de Arquivos

| # | Arquivo | Ação | Propósito | Agent | Dependências |
|---|---------|------|-----------|-------|--------------|
| 1 | `.claude/sdd/architecture/PHASE_MODEL_ROLES.toml` | Criar | Fonte única (Decisão 7) | @python-developer | Nenhuma |
| 2 | `scripts/phase_routing.py` | Criar | load/validate/apply/check/print-omp-overrides | @python-developer | 1 |
| 3 | `tests/test_phase_routing.py` | Criar | Testes unitários e de divergência (ver Estratégia) | @test-generator | 2 |
| 4 | `.claude/agents/workflow/*.md` (10) | Modificar | `model:` via `--apply`; parágrafo de proveniência | (geral) | 1, 2 |
| 5 | `.claude/commands/workflow/{design,ship}.md` | Modificar | Bloco "Phase Routing (delegated)" + marcador | (geral) | 1 |
| 6 | `.claude/commands/workflow/{brainstorm,define,define-m,design-m,iterate,build,continue,work,eval}.md` | Modificar | Marcador session + linha de recomendação | (geral) | 1 |
| 7 | `.claude/sdd/templates/{BRAINSTORM,DEFINE,DESIGN,BUILD_REPORT,SHIPPED}_TEMPLATE.md` | Modificar | Linha `Gerado por` | (geral) | Nenhuma |
| 8 | `.claude/sdd/architecture/WORKFLOW_CONTRACTS.yaml` | Modificar | Remover `model:`; comentário para o manifesto (Decisão 5) | (geral) | 1 |
| 9 | `build-plugin.sh` | Modificar | Achatar `plugin/agents`; excluir README/_template; reescrever `agents/<cat>/` | @shell-script-specialist | Nenhuma |
| 10 | `scripts/generate-codex-plugin.py` | Modificar | Effort dos agents de workflow vem do manifesto (S3) | @python-developer | 2 |
| 11 | `tests/test_generate_codex_plugin.py` | Modificar | Cobrir effort via manifesto | @test-generator | 10 |
| 12 | `Makefile` | Modificar | `check` + `phase_routing.py --check`; alvos `omp-roles` e `phase-routing-apply` | @shell-script-specialist | 2 |
| 13 | `docs/concepts/phase-model-routing.md` | Criar | Tabela, modos, receita do OMP, aviso de família (S2), fallback | @code-documenter | 1 |
| 14 | `docs/concepts/agent-overrides.md` | Modificar | Caminhos achatados; nota "OMP não lê `.claude/agents`" | @code-documenter | 9 |
| 15 | `CLAUDE.md` | Modificar | Linha na tabela de tarefas + Key Files (manifesto) | @code-documenter | 1 |
| 16 | `CHANGELOG.md` | Modificar | Entrada: feature + breaking (nomes achatados no Claude Code) | @code-documenter | 9 |
| 17 | `plugin/**`, `plugin-grok/**`, `.grok/**`, `.codex/**`, `plugin-dsh/assets/**`, `AGENTS.md` | Regenerar | Via `make build` e geradores (não editar à mão) | (geral) | 4–10 |

**Total:** 3 criados, 12 modificados, artefatos gerados regenerados.

---

## Justificativa de Atribuição de Agentes

| Agent | Arquivos | Por quê |
|-------|----------|---------|
| @python-developer | 1, 2, 10 | Script stdlib com dataclasses e tipagem; mesmo estilo dos geradores existentes |
| @test-generator | 3, 11 | Suíte pytest com fixtures em `tmp_path`; padrão de `tests/test_generate_*` |
| @shell-script-specialist | 9, 12 | `build-plugin.sh` é bash com `sed_i` portável (macOS/Linux) |
| @code-documenter | 13–16 | Documentação em inglês (framework) com tabelas |
| (geral) | 4–8, 17 | Edições de Markdown curtas e mecânicas |

---

## Padrões de Código

### Padrão 1: `PHASE_MODEL_ROLES.toml`

```toml
# PHASE_MODEL_ROLES.toml — single source of truth for per-phase model routing.
#
# omp_role     : an OMP modelRoles name (plan, slow, smol, task, default, or a
#                custom role). The concrete model lives ONLY in the user's
#                ~/.omp/agent/config.yml. NEVER put concrete model IDs here.
# claude_model : Claude Code alias written to the agent frontmatter
#                (opus | sonnet | haiku | fable | inherit).
# codex_effort : Codex model_reasoning_effort (low | medium | high); omit to inherit.
#
# Commands:
#   mode = "delegated" -> the command body delegates the phase to `agent`
#                         (the only way the role applies automatically).
#   mode = "session"   -> runs inline; `recommended_role` is what the user
#                         should start the session with (omp --model @<role>).
#
# Apply:  python3 scripts/phase_routing.py --apply
# Check:  python3 scripts/phase_routing.py --check      (part of `make check`)
# OMP:    python3 scripts/phase_routing.py --print-omp-overrides

schema_version = 1

[agents.brainstorm-agent]
omp_role = "plan"
claude_model = "opus"
codex_effort = "high"

[agents.brainstorm-multiagent]
omp_role = "plan"
claude_model = "opus"
codex_effort = "high"

[agents.define-agent]
omp_role = "plan"
claude_model = "opus"
codex_effort = "high"

[agents.define-multiagent]
omp_role = "plan"
claude_model = "opus"
codex_effort = "high"

[agents.design-agent]
omp_role = "slow"
claude_model = "opus"
codex_effort = "high"

[agents.design-multiagent]
omp_role = "slow"
claude_model = "opus"
codex_effort = "high"

[agents.build-agent]
omp_role = "default"
claude_model = "inherit"
codex_effort = "high"

[agents.iterate-agent]
omp_role = "plan"
claude_model = "opus"
codex_effort = "high"

[agents.ship-agent]
omp_role = "smol"
claude_model = "haiku"
codex_effort = "low"

# eval-agent asks the user for attestations (AskUserQuestion), so /eval runs
# in the session; independence comes from eval_runner.py + JEV, not the model.
[agents.eval-agent]
omp_role = "default"
claude_model = "sonnet"
codex_effort = "medium"

# Keys are command file stems under .claude/commands/workflow/.
[commands.brainstorm]
mode = "session"
recommended_role = "plan"

[commands.define]
mode = "session"
recommended_role = "plan"

[commands.define-m]
mode = "session"
recommended_role = "plan"

[commands.iterate]
mode = "session"
recommended_role = "plan"

[commands.design]
mode = "delegated"
agent = "design-agent"

# design-m consults specialists via the Agent tool; a subagent cannot spawn
# subagents in Claude Code, so it stays in the session.
[commands.design-m]
mode = "session"
recommended_role = "slow"

[commands.build]
mode = "session"
recommended_role = "default"

[commands.continue]
mode = "session"
recommended_role = "default"

[commands.work]
mode = "session"
recommended_role = "default"

[commands.ship]
mode = "delegated"
agent = "ship-agent"

[commands.eval]
mode = "session"
recommended_role = "default"

# Cross-model review. judge.py still resolves its model via OpenRouter
# (PHASE_MODEL_DEFAULTS / --model / JUDGE_MODEL). REVIEWER is an optional
# custom OMP role; keep it on a different model family than plan/slow.
[judge]
omp_role = "REVIEWER"
```

### Padrão 2: `scripts/phase_routing.py` (esqueleto)

```python
#!/usr/bin/env python3
"""Per-phase model routing: load, validate, apply, and check PHASE_MODEL_ROLES.toml.

Stdlib only (tomllib, Python >= 3.11) so `make check` needs no extra deps.

  python3 scripts/phase_routing.py --check                # fail on drift (CI)
  python3 scripts/phase_routing.py --apply                # sync sources from manifest
  python3 scripts/phase_routing.py --print-omp-overrides  # stdout only, never touches ~/.omp
"""
from __future__ import annotations

import argparse
import re
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST = REPO_ROOT / ".claude" / "sdd" / "architecture" / "PHASE_MODEL_ROLES.toml"
AGENTS_DIR = REPO_ROOT / ".claude" / "agents" / "workflow"
COMMANDS_DIR = REPO_ROOT / ".claude" / "commands" / "workflow"
CONTRACTS = REPO_ROOT / ".claude" / "sdd" / "architecture" / "WORKFLOW_CONTRACTS.yaml"
PLUGIN_AGENTS = REPO_ROOT / "plugin" / "agents"

CLAUDE_MODELS = frozenset({"opus", "sonnet", "haiku", "fable", "inherit"})
CODEX_EFFORTS = frozenset({"low", "medium", "high"})
MODES = frozenset({"session", "delegated"})
NON_PHASE_COMMANDS = frozenset({"create-pr"})
ROLE_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")
CONCRETE_ID_RE = re.compile(r"(gpt-|grok-|claude-|gemini-|deepseek)[0-9a-z.-]+", re.I)
MARKER_RE = re.compile(r"<!-- phase-routing: (?P<body>[^>]*?) -->")
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.S)
MODEL_LINE_RE = re.compile(r"^model:[ \t]*(\S+).*$", re.M)


@dataclass(frozen=True)
class AgentRoute:
    name: str
    omp_role: str
    claude_model: str
    codex_effort: str | None


@dataclass(frozen=True)
class CommandRoute:
    stem: str
    mode: str
    agent: str | None
    recommended_role: str | None

    def marker(self) -> str:
        if self.mode == "delegated":
            return f"<!-- phase-routing: mode=delegated agent={self.agent} -->"
        return f"<!-- phase-routing: mode=session role={self.recommended_role} -->"


def load(path: Path = MANIFEST) -> tuple[dict[str, AgentRoute], dict[str, CommandRoute]]:
    """Parse and validate the manifest; raise ValueError listing every problem."""
    ...


def check(repo: Path = REPO_ROOT) -> list[str]:
    """Return human-readable drift errors: '<file>: <field> expected <x>, found <y>'."""
    ...


def apply(repo: Path = REPO_ROOT) -> list[Path]:
    """Rewrite frontmatter `model:` and command markers from the manifest; return changed files."""
    ...


def omp_overrides(agents: dict[str, AgentRoute]) -> str:
    lines = [
        "# Merge under the EXISTING `task.agentModelOverrides` key in",
        "# ~/.omp/agent/config.yml. Roles resolve through your modelRoles.",
        "task:",
        "  agentModelOverrides:",
    ]
    lines += [f'    {a.name}: "@{a.omp_role}"' for a in sorted(agents.values(), key=lambda a: a.name)]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--apply", action="store_true")
    group.add_argument("--print-omp-overrides", action="store_true")
    args = parser.parse_args(argv)
    ...
```

**Regras do `check()`** (cada violação vira uma linha de erro, e o exit code é 1 se houver qualquer uma):

1. O manifesto é válido: enums, `ROLE_RE`, `delegated` exige `agent` existente em `[agents]`, `session` exige `recommended_role`, sem ID concreto.
2. Conjunto de `[agents]` = conjunto de `.claude/agents/workflow/*.md` (sem `README.md`/`_*.md`), nos dois sentidos.
3. Conjunto de `[commands]` = stems de `.claude/commands/workflow/*.md` menos `NON_PHASE_COMMANDS`, nos dois sentidos.
4. `model:` da frontmatter de cada agent de workflow == `claude_model`; frontmatter sem ID concreto.
5. Cada comando do manifesto contém **exatamente um** marcador, igual a `CommandRoute.marker()`.
6. O `WORKFLOW_CONTRACTS.yaml` não tem linha `model:` cujo valor seja alias Claude (`opus`, `sonnet`, `haiku`, `fable`, `inherit`). O `eval.jev.model` não é afetado.
7. `plugin/agents/` (se existir) não tem subpastas nem `README.md`/`_template.md`.

### Padrão 3: bloco delegated (`design.md`; `ship.md` análogo)

Inserido logo antes de `## Process`:

```markdown
## Phase Routing (delegated)

<!-- phase-routing: mode=delegated agent=design-agent -->

This phase runs in the **`design-agent` subagent**, so it uses the model routed to the
design phase (OMP: `task.agentModelOverrides` → `@slow`; Claude Code: `model: opus`).
Do not do the design work in the main session.

1. Delegate exactly once — Claude Code: Task tool, `subagent_type: design-agent`
   (plugin name `agentspec:design-agent`); OMP: `task` tool, agent `design-agent`.
2. Pass: the DEFINE path, the FEATURE name, and this instruction: "Fill the
   **Gerado por** metadata row with your harness, the routed role, and your model id
   (or `desconhecido`)."
3. When the subagent returns the DESIGN path, run Step 8 (`--judge`) here in the main
   session if the flag was given.

> `ship.md` is analogous, with one difference: **Step 0 (`eval_runner.py verify`) runs
> here in the main session first**; delegate Steps 1–8 to `ship-agent` only after it
> returns OK.
4. If the subagent is unavailable, say so, run Steps 1–7 inline as a fallback, and
   record the session model in **Gerado por**.
```

### Padrão 4: marcador session (`brainstorm.md` e similares)

Inserido logo abaixo do título:

```markdown
<!-- phase-routing: mode=session role=plan -->
> **Model routing:** this phase runs in the main session (it asks you questions).
> Recommended: start OMP with `omp --model @plan` (Claude Code: `/model opus`).
> Record the session model in the **Gerado por** metadata row.
```

### Padrão 5: linha de proveniência nos templates e nos agents

```markdown
| **Gerado por** | {harness} · papel `{omp_role ou "sessão"}` · `{modelo ou desconhecido}` |
```

Parágrafo acrescentado a cada agent de workflow (inglês, junto das regras de saída):

```markdown
**Provenance:** fill the **Gerado por** metadata row with the harness (OMP, Claude Code,
Codex…), the routed role (or "sessão"), and your exact model id if you know it; otherwise
write `desconhecido`. Never leave it blank.
```

### Padrão 6: achatamento no `build-plugin.sh`

Logo após o loop que copia `agents commands skills kb`:

```bash
# Flatten plugin/agents: OMP (and Grok) only discover agents/*.md, not
# agents/<category>/*.md. Names are unique across categories (checked below).
flatten_agents() {
    local dir="${PLUGIN_DIR}/agents" f base
    rm -f "${dir}/README.md" "${dir}/_template.md"
    while IFS= read -r -d '' f; do
        base="$(basename "$f")"
        if [ -e "${dir}/${base}" ]; then
            echo -e "${RED}Duplicate agent filename after flatten: ${base}${NC}" >&2
            exit 1
        fi
        mv "$f" "${dir}/${base}"
    done < <(find "${dir}" -mindepth 2 -name '*.md' ! -name 'README.md' ! -name '_*' -print0)
    find "${dir}" -mindepth 1 -type d -exec rm -rf {} + 2>/dev/null || true
}
flatten_agents
echo "  Flattened agents/ (OMP/Grok discovery)"
```

No passo de reescrita de caminhos (depois do sed atual), acrescentar:

```bash
sed_i -E 's|\$\{CLAUDE_PLUGIN_ROOT\}/agents/[a-z-]+/|${CLAUDE_PLUGIN_ROOT}/agents/|g' "$file"
```

Isso preserva `${CLAUDE_PLUGIN_ROOT}/agents/**/*.md`, que continua casando com a pasta única.

### Padrão 7: `Makefile`

```makefile
check: ## Drift check — tests + generators in --check mode (fails on drift)
	@$(PYTHON) -m pytest tests/ -q
	@$(PYTHON) scripts/phase_routing.py --check
	@python3 scripts/generate-agent-router.py --check
	@python3 scripts/generate-codex-plugin.py --check
	@python3 scripts/generate-dsh-bundle.py --check
	@python3 scripts/generate-grok-plugin.py --check

omp-roles: ## Print task.agentModelOverrides for ~/.omp/agent/config.yml (stdout only)
	@$(PYTHON) scripts/phase_routing.py --print-omp-overrides

phase-routing-apply: ## Sync agent frontmatter + command markers from PHASE_MODEL_ROLES.toml
	@$(PYTHON) scripts/phase_routing.py --apply
```

(Acrescentar `omp-roles phase-routing-apply` ao `.PHONY`.)

### Padrão 8: effort do Codex a partir do manifesto (S3)

```python
# scripts/generate-codex-plugin.py
import importlib.util

def _load_phase_routes() -> dict[str, str]:
    spec = importlib.util.spec_from_file_location("phase_routing", REPO_ROOT / "scripts" / "phase_routing.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    agents, _ = module.load()
    return {name: route.codex_effort for name, route in agents.items() if route.codex_effort}

PHASE_EFFORT = _load_phase_routes()
# ...
effort = PHASE_EFFORT.get(fm.get("name", "")) or EFFORT_BY_MODEL.get((fm.get("model") or "").strip())
```

---

## Fluxo de Dados

```text
1. Contribuidor edita PHASE_MODEL_ROLES.toml
   │
   ▼
2. make phase-routing-apply ─► reescreve model: (10 agents) + marcadores (11 comandos)
   │
   ▼
3. make build ─► plugin/ (agents achatados) + codex/grok/dsh regenerados
   │
   ▼
4. make check ─► pytest + phase_routing --check + geradores --check  (CI)
   │
   ▼
5. Usuário: omp plugin update  (marketplace local → novo plugin/)
            make omp-roles ─► cola o trecho em ~/.omp/agent/config.yml
   │
   ▼
6. /design no OMP ─► comando instrui task(design-agent) ─► override "@slow"
   ─► modelRoles.slow ─► modelo concreto ─► DESIGN com "Gerado por" preenchido
```

---

## Pontos de Integração

| Sistema | Tipo | Observação |
|---------|------|------------|
| OMP `task.agentModelOverrides` | Config do usuário (manual) | Chave = `name:` do agent (teste 3). O gerador só imprime |
| OMP `modelRoles` | Config do usuário | `plan`, `slow`, `smol`, `default` e `REVIEWER` (opcional) precisam existir. Se faltar, vale a precedência normal do OMP |
| OMP descoberta de plugins | Plugin do marketplace | Pasta única de agents: validar em V-1 |
| Claude Code Task tool | Subagent | `subagent_type` = `design-agent` / `agentspec:design-agent` |
| Geradores Codex/Grok/DSH | Build | Codex lê o effort do manifesto; Grok remove `model:`; DSH copia sem alteração |
| `scripts/judge.py` | OpenRouter | Inalterado no MVP (C1 adiado) |

---

## Estratégia de Testes

| Tipo | Escopo | Arquivos | Ferramentas | Meta |
|------|--------|----------|-------------|------|
| Unitário | `load()`: enums, papel, `delegated` sem agent, `session` sem papel, ID concreto no manifesto | `tests/test_phase_routing.py` | pytest | Todos os ramos de validação |
| Divergência | Cópia do repositório mínimo em `tmp_path`; mutar frontmatter, marcador, contrato (`model:`), agent extra ou faltando, subpasta em `plugin/agents` → `check()` retorna erro com arquivo, campo e esperado | idem | pytest | AT-004, AT-005, AT-006 |
| Idempotência | `apply()` duas vezes: a segunda não muda nada; depois de `apply()`, `check()` retorna vazio | idem | pytest | — |
| Isolamento | `--print-omp-overrides` com `HOME` apontando para `tmp_path` com `.omp/agent/config.yml`: hash igual antes e depois; nada criado | idem | pytest + monkeypatch | AT-008 |
| Formato OMP | A saída contém `task:` / `agentModelOverrides:` e uma linha `name: "@role"` por agent | idem | pytest | M3 |
| Codex | Effort dos agents de workflow vem do manifesto (`build-agent` → high com `inherit`) | `tests/test_generate_codex_plugin.py` | pytest | S3 |
| Repositório real | `phase_routing.py --check` verde no repositório depois do Build | `make check` | CI | M5 |
| Aceite manual no OMP | AT-001, AT-002, AT-003, AT-007 com o plugin atualizado e o trecho aplicado; conferir `resolvedModel` na sessão salva e **Gerado por** no documento | — | `omp` + `--session-dir` | Critérios de sucesso 3 e 7 |
| Aceite manual no Claude Code | AT-009: `/design` roda em subagent | — | Claude Code | S1 |

### Validação V-1 (primeira tarefa do Build, antes de editar comandos)

Depois do `make build` com o achatamento, confirmar que o OMP descobre agents em pasta única **dentro de um plugin do marketplace**. Como isso exige atualizar o plugin no OMP do usuário (estado fora do repositório), o Build **pede ao usuário** para rodar o `update` do plugin e repetir o teste 1 do spike (listar agents). Custo estimado: um prompt em `@smol`.

- **Passa:** segue o plano.
- **Falha:** fallback documentado. `make omp-project-agents DEST=<projeto>` copia `plugin/agents/*.md` para `<projeto>/.omp/agents/` (caminho verificado no teste 2). A documentação registra a limitação, e as Decisões 2 e 4 continuam válidas para o Claude Code.

---

## Tratamento de Erros

| Tipo de Erro | Estratégia | Retry? |
|--------------|------------|--------|
| Manifesto inválido (TOML ou enum) | `ValueError` com todas as violações; exit 2 no CLI | Não |
| Divergência (`--check`) | Lista `arquivo: campo esperado X, encontrado Y`; exit 1 | Não |
| Nome de arquivo duplicado ao achatar | `build-plugin.sh` aborta com o nome duplicado | Não |
| Subagent indisponível no `/design`/`/ship` | O comando avisa e roda inline (fallback), registrando o modelo da sessão | Não |
| Papel inexistente no `modelRoles` do usuário | Comportamento do OMP (override não resolve → precedência normal). A documentação lista os papéis exigidos | Não |
| Modelo desconhecido para o agent | `Gerado por` = `desconhecido` (nunca vazio) | Não |

---

## Configuração

| Chave | Tipo | Default | Descrição |
|-------|------|---------|-----------|
| `agents.<name>.omp_role` | string | — | Papel do OMP (sem `@`; o gerador acrescenta) |
| `agents.<name>.claude_model` | enum | — | Escrito na frontmatter pelo `--apply` |
| `agents.<name>.codex_effort` | enum \| ausente | ausente → `EFFORT_BY_MODEL` | Lido pelo gerador Codex |
| `commands.<stem>.mode` | `session` \| `delegated` | — | Decide o marcador e o bloco do comando |
| `commands.<stem>.agent` | string | — | Obrigatório se `delegated` |
| `commands.<stem>.recommended_role` | string | — | Obrigatório se `session` |
| `judge.omp_role` | string | `REVIEWER` | Só documentação no MVP |

---

## Considerações de Segurança

- O gerador nunca lê nem escreve `~/.omp` nem outro arquivo fora do repositório (testado em AT-008).
- Nenhum ID de modelo, chave ou `config.yml` versionado.
- O `--apply` só reescreve a linha `model:` da frontmatter e a linha do marcador; nada além disso nos arquivos.

---

## Observabilidade

| Aspecto | Implementação |
|---------|---------------|
| Proveniência por documento | Linha `Gerado por` (harness · papel · modelo) nos 5 artefatos SDD |
| Evidência de roteamento no OMP | `resolvedModel` nas sessões salvas (`--session-dir`), usado nos aceites manuais |
| Divergência | `make check` / CI |

---

## Fronteiras com as Outras Frentes

| Frente | Contato neste Design |
|--------|----------------------|
| `JEV_AGENT_SELECTION` | O achatamento torna os 73 agents visíveis no OMP, pré-requisito para qualquer seleção de agentes lá. A seleção em si não entra aqui |
| `POST_BUILD_EVALS` | Consome `Gerado por` e o papel `REVIEWER`; nada de eval aqui |
| `LIVING_MEMORY` | Pode indexar `Gerado por`; nada de memória aqui |
| `KB_CONTEXT7_REFRESH` | Não verificado se o OMP expande `${CLAUDE_PLUGIN_ROOT}` nos corpos dos agents (leitura de KB pelos especialistas). Risco registrado para aquela frente; esta feature não muda os caminhos de KB |

---

## Riscos

| Risco | Probabilidade | Mitigação |
|-------|---------------|-----------|
| O OMP não descobrir agents em pasta única dentro de plugins | Média | V-1 no início do Build; fallback `.omp/agents` por projeto |
| Quebra de referências a `agentspec:<categoria>:<agent>` em projetos de usuários | Baixa | CHANGELOG (breaking); só os docs desta feature usam o nome antigo no repositório |
| DESIGN pior por contexto limpo no subagent (A-006) | Baixa | O subagent recebe caminhos e lê DEFINE, template e `CLAUDE.md`; revisar no aceite AT-001 |
| O OMP não expandir `${CLAUDE_PLUGIN_ROOT}` nos agents | Desconhecida | Fora do escopo; registrado para `KB_CONTEXT7_REFRESH` |

---

## Evals

> Contrato de aceitação executável: pelo menos um eval por AT do DEFINE. Escrito antes do código,
> congelado por `eval_runner.py freeze` (linha **Evals Digest**), checado pelo `/build` (`pre`)
> e reexecutado pelo `/eval`. Mude este bloco só via `/iterate`.
>
> ATs que exigem rodar o OMP ou o Claude Code de verdade (AT-001, AT-002, AT-003, AT-007, AT-009) são `human`.

<!-- agentspec:evals:contract -->
```toml
[[eval]]
id = "drift_detected"
verifies = ["AT-004"]
check_type = "deterministic"
description = "phase_routing.check() reports file, field and expected value when an agent frontmatter model diverges from the manifest"
run = '''
"$AGENTSPEC_PYTHON" -m pytest tests/test_phase_routing.py -q -k "frontmatter_drift"
'''

[[eval]]
id = "repo_in_sync"
verifies = ["AT-005", "AT-004"]
check_type = "deterministic"
description = "The real repo passes phase_routing --check and the contract has no Claude-alias model lines left"
run = '''
set -e
"$AGENTSPEC_PYTHON" scripts/phase_routing.py --check
if grep -nE '^\s+model:\s*"?(opus|sonnet|haiku|fable|inherit)"?\s*$' .claude/sdd/architecture/WORKFLOW_CONTRACTS.yaml; then
  exit 1
fi
'''

[[eval]]
id = "no_concrete_ids"
verifies = ["AT-006"]
check_type = "deterministic"
description = "No concrete model IDs in the manifest or in the workflow agents' frontmatter"
run = '''
set -e
test -s .claude/sdd/architecture/PHASE_MODEL_ROLES.toml
ids='(gpt-|grok-|claude-|gemini-|deepseek)[0-9a-z.-]+'
if grep -niE "$ids" .claude/sdd/architecture/PHASE_MODEL_ROLES.toml; then exit 1; fi
for f in .claude/agents/workflow/*.md; do
  if awk '/^---$/{c++; next} c==1' "$f" | grep -niE "$ids"; then exit 1; fi
done
exit 0
'''

[[eval]]
id = "overrides_stdout_only"
verifies = ["AT-008"]
check_type = "deterministic"
description = "--print-omp-overrides prints the routed roles and never touches $HOME/.omp"
run = '''
set -e
home="$(mktemp -d)"
mkdir -p "$home/.omp/agent"
printf 'modelRoles:\n  slow: x/y\n' > "$home/.omp/agent/config.yml"
before="$(shasum "$home/.omp/agent/config.yml")"
out="$(HOME="$home" "$AGENTSPEC_PYTHON" scripts/phase_routing.py --print-omp-overrides)"
after="$(shasum "$home/.omp/agent/config.yml")"
test "$before" = "$after"
test "$(find "$home" -type f | wc -l | tr -d ' ')" = "1"
printf '%s\n' "$out" | grep -q 'agentModelOverrides:'
printf '%s\n' "$out" | grep -q 'design-agent: "@slow"'
printf '%s\n' "$out" | grep -q 'ship-agent: "@smol"'
'''

[[eval]]
id = "delegation_blocks"
verifies = ["AT-001", "AT-002", "AT-009"]
check_type = "deterministic"
description = "/design and /ship carry the delegated routing block; interactive phases carry the session marker"
run = '''
set -e
grep -q '<!-- phase-routing: mode=delegated agent=design-agent -->' .claude/commands/workflow/design.md
grep -q '<!-- phase-routing: mode=delegated agent=ship-agent -->' .claude/commands/workflow/ship.md
grep -q '<!-- phase-routing: mode=session role=plan -->' .claude/commands/workflow/brainstorm.md
grep -q '<!-- phase-routing: mode=session role=plan -->' .claude/commands/workflow/define.md
grep -q '<!-- phase-routing: mode=session role=slow -->' .claude/commands/workflow/design-m.md
'''

[[eval]]
id = "plugin_agents_flat"
verifies = ["AT-001", "AT-003"]
check_type = "deterministic"
description = "plugin/agents is flat (OMP discovery), with no README/_template and every agent present"
run = '''
set -e
test -z "$(find plugin/agents -mindepth 1 -type d)"
test ! -e plugin/agents/README.md
test ! -e plugin/agents/_template.md
src="$(find .claude/agents -name '*.md' ! -name README.md ! -name '_*' | wc -l | tr -d ' ')"
dst="$(find plugin/agents -maxdepth 1 -name '*.md' | wc -l | tr -d ' ')"
test "$src" = "$dst"
grep -q '^model: opus' plugin/agents/design-agent.md
'''

[[eval]]
id = "provenance_rows"
verifies = ["AT-007"]
check_type = "deterministic"
description = "All five SDD templates carry the Gerado por row and every workflow agent instructs filling it"
run = '''
set -e
for t in BRAINSTORM DEFINE DESIGN BUILD_REPORT SHIPPED; do
  grep -q '^| \*\*Gerado por\*\* |' ".claude/sdd/templates/${t}_TEMPLATE.md"
done
for f in .claude/agents/workflow/*.md; do
  grep -q 'Gerado por' "$f"
done
'''

[[eval]]
id = "full_suite"
verifies = ["AT-004", "AT-006", "AT-008"]
check_type = "deterministic"
description = "Whole pytest suite plus every generator --check stays green"
run = '''
make check
'''

[[eval]]
id = "omp_design_routed"
verifies = ["AT-001"]
check_type = "human"
owner = "usuário (dono do AgentSpec)"
description = "In OMP, /design runs in the design-agent subagent on the @slow model"
instructions = "After updating the plugin in OMP and pasting `make omp-roles` into ~/.omp/agent/config.yml, run `/design` on a small DEFINE with `omp --session-dir /tmp/lpr-s`. Confirm: (1) a task call to design-agent appears; (2) `grep -r resolvedModel /tmp/lpr-s` shows your modelRoles.slow model; (3) the DESIGN 'Gerado por' row names that model."

[[eval]]
id = "omp_ship_routed"
verifies = ["AT-002"]
check_type = "human"
owner = "usuário (dono do AgentSpec)"
description = "In OMP, /ship runs verify in the session and then ship-agent on the @smol model"
instructions = "Run `/ship` on a feature with a PASS eval receipt, with --session-dir. Confirm the verify step ran first, a task call to ship-agent follows, resolvedModel equals modelRoles.smol, and the SHIPPED 'Gerado por' row names it."

[[eval]]
id = "omp_without_override"
verifies = ["AT-003"]
check_type = "human"
owner = "usuário (dono do AgentSpec)"
description = "Without the overrides snippet, /design still completes and records the real model"
instructions = "Run OMP without the agentspec overrides (remove them or use a clean profile config), run `/design`, and confirm it finishes and the 'Gerado por' row names the model actually used."

[[eval]]
id = "omp_interactive_session"
verifies = ["AT-007"]
check_type = "human"
owner = "usuário (dono do AgentSpec)"
description = "Interactive phases stay inline and keep asking questions"
instructions = "Start `omp --model @plan`, run `/brainstorm \"ideia de teste\"`; confirm it asks questions in the main session (no task call) and the BRAINSTORM 'Gerado por' row names the session model."

[[eval]]
id = "claude_code_design_subagent"
verifies = ["AT-009"]
check_type = "human"
owner = "usuário (dono do AgentSpec)"
description = "In Claude Code, /design delegates to the design-agent subagent with model opus"
instructions = "With the rebuilt plugin in Claude Code, run `/design` on a small DEFINE; confirm a Task call with subagent_type design-agent (or agentspec:design-agent) and that the DESIGN 'Gerado por' row names an Opus model."
```

---

## Histórico de Revisões

| Versão | Data | Autor | Mudanças |
|--------|------|-------|----------|
| 1.0 | 2026-09-23 | design-agent | Versão inicial com o resultado do spike no OMP (6 testes); desvios do DEFINE: TOML (D1), achatamento (D2), `/design-m` session (D4), `model:` removido do contrato (D5), escopo da regex (D6) |
| 1.1 | 2026-09-24 | iterate (no início do /build) | Base avançada até `main@9de8ce4`: `eval-agent` e `/eval` no manifesto (session), Step 0 do `/ship` na sessão, Regra 6 restrita a aliases Claude, `$(PYTHON)` no Makefile, contrato `## Evals` adicionado e congelado |

---

## Próximo Passo

**Pronto para:** `/build .claude/sdd/features/DESIGN_LLM_PHASE_ROUTING.md`
