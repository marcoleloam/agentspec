# DESIGN: Post-Build Evals

> Design técnico da fase `/eval`: evals-contrato declarados no DESIGN em TOML, congelados por digest, checados antes do build, reexecutados por um runner determinístico depois do build, com o JEV como juiz calibrado dos critérios subjetivos e um recibo que o `/ship` exige.

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | POST_BUILD_EVALS |
| **Data** | 2026-09-23 |
| **Autor** | design-agent |
| **DEFINE** | [DEFINE_POST_BUILD_EVALS.md](./DEFINE_POST_BUILD_EVALS.md) |
| **Status** | ✅ Shipped |
| **Evals Digest** | `sha256:89a9e4ff6d5f878856ae5466b23b42f6829d9a0c22f962d80738e6c0df8d861b` |

---

## Visão Geral da Arquitetura

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│                         CAMADA DE EVALS PÓS-BUILD                            │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  DEFINE_{F}.md            DESIGN_{F}.md                                      │
│  | AT-001 | ... |  ──►   ## Evals  (bloco TOML "contract")                   │
│  | AT-002 | ... |        **Evals Digest** sha256:…  ◄── eval_runner freeze   │
│        │                        │                                            │
│        └──── validate ──────────┤  (rastreabilidade AT ↔ eval, regras)       │
│                                 │                                            │
│  /build ── build-agent ── eval_runner pre ──► erro de bash? BLOQUEIA         │
│                                 │             já passa?     AVISA            │
│                                 ▼                                            │
│                          (código gerado)                                     │
│                                 │                                            │
│  /eval ── eval-agent (sem Edit) │                                            │
│     │                           ▼                                            │
│     ├─► EVALS_EXTRA_{F}.toml  eval_runner run ───────────────────────────┐   │
│     │   (só acrescenta)         │                                        │   │
│     │                           ├─ deterministic ─► bash -c isolado      │   │
│     │                           ├─ graded ───────► jev_client.decide()   │   │
│     │                           │        │           │ OpenRouter        │   │
│     │                           │        │           ▼ /api/v1/systemone │   │
│     │                           │        └─ escalated ─► judge.py        │   │
│     │                           │                        ou humano       │   │
│     ├─► attest / waive ────────►├─ human ──────────► attestations.json   │   │
│     │   (resposta do usuário)   │                                        │   │
│     │                           ▼                                        │   │
│     │              reports/EVAL_{F}.json  (recibo v1)                    │   │
│     │              reports/EVAL_REPORT_{F}.md  (pt-BR, gerado)           │   │
│     │                           │                                        │   │
│     │              FAIL ──► /continuar (ATs reprovados como gaps)        │   │
│     ▼                           │                                        │   │
│  /ship ── ship-agent ── eval_runner verify ─► recusa: sem recibo, FAIL,  │   │
│                                               commit/worktree/contrato   │   │
│                                               divergentes, legado s/     │   │
│                                               waiver                     │   │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Componentes

| Componente | Propósito | Tecnologia |
|------------|-----------|------------|
| `scripts/eval_runner.py` | CLI determinística: `validate`, `freeze`, `pre`, `run`, `attest`, `waive`, `verify`, `calibrate`. Única fonte do veredito | Python ≥ 3.11 stdlib (`tomllib`, `subprocess`, `hashlib`, `json`) |
| `scripts/jev_client.py` | Cliente do JEV no endpoint de decisões do OpenRouter; tipos `Question`/`Answer`/`DecisionResult`; ledger de custo | Python stdlib (`urllib`) |
| `scripts/judge.py` (existente) | Fallback de escalonamento para evals `graded`, chamado por subprocess | Inalterado |
| Bloco `## Evals` no DESIGN | Contrato de evals em TOML, delimitado por marcador HTML | Markdown + TOML |
| `EVALS_EXTRA_{F}.toml` | Evals complementares do eval-agent, fora do contrato | TOML |
| `eval-agent` | Orquestra o `/eval`: roda o runner, escreve complementares, coleta atestações humanas, resume o resultado | Agente Claude Code (T2) |
| `/eval` | Comando da nova fase entre `/build` e `/ship` | Markdown command |
| `EVAL_{F}.json` | Recibo `agentspec/eval-receipt/v1`, vinculado a commit + worktree + contrato | JSON |
| `EVAL_REPORT_{F}.md` | Relatório pt-BR renderizado pelo runner a partir do template (o agente não escreve o veredito) | Markdown |
| `EVAL_{F}.attestations.json` | Atestações humanas, decisões escalonadas e waivers | JSON |
| `.claude/sdd/evals/JEV_CALIBRATION.json` | Resultado da calibração do JEV no projeto; controla se o JEV pode decidir | JSON |

---

## Decisões Principais

### Decisão 1: Evals declarados em TOML dentro do DESIGN

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-09-23 |

**Contexto:** o runner precisa extrair metadados (id, verifies, check_type, rubrica) e scripts bash multilinha do DESIGN sem dependências externas. O task-spec usa YAML + funções bash e precisa de um extrator awk heredoc-aware.

**Escolha:** um único bloco cercado ` ```toml ` logo após o marcador `<!-- agentspec:evals:contract -->`, com `[[eval]]` por eval e o bash em string literal multilinha (`run = '''…'''`). Parse com `tomllib` (stdlib a partir do Python 3.11).

**Justificativa:** `tomllib` elimina parser caseiro; strings literais TOML carregam bash sem escaping; um só parse fornece metadados e scripts; LLMs escrevem TOML de forma confiável.

**Alternativas Rejeitadas:**
1. YAML + funções `eval_N()` como no task-spec — YAML não está na stdlib; extrator de bash heredoc-aware é frágil.
2. JSON — bash multilinha em JSON exige escaping ilegível.
3. Tabela Markdown — não comporta rubricas nem scripts.

**Consequências:**
- Piso de Python sobe para 3.11 (hoje o `judge.py` já exige ≥ 3.10 por `dataclass(slots=True)`; o CI de testes já usa 3.11). O runner sai com código 2 e mensagem clara em versões menores.
- Formato diferente do task-spec; a ideia (eval = processo com exit code, rastreado a um AT) é a mesma.

---

### Decisão 2: Congelamento por digest canônico gravado nos metadados do DESIGN

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-09-23 |

**Contexto:** os evals-contrato não podem mudar depois do DESIGN sem passar por `/iterate` (DEFINE MUST); espaços e comentários não devem invalidar o contrato.

**Escolha:** `digest = "sha256:" + sha256(json.dumps(tomllib.loads(bloco), sort_keys=True, separators=(",", ":"), ensure_ascii=False))`. O subcomando `freeze` grava o valor na linha `**Evals Digest**` dos metadados. `run` recalcula e recusa com `CONTRACT_TAMPERED` se divergir. Só o design-agent e o iterate-agent rodam `freeze`.

**Justificativa:** digest do conteúdo parseado é estável a formatação e sensível a qualquer mudança semântica; fica visível no próprio documento.

**Alternativas Rejeitadas:**
1. Arquivo `.lock` separado — mais um artefato para arquivar e sincronizar.
2. Exigir o contrato commitado (`git show HEAD:`) — em projetos que ignoram `.claude/sdd/` no git, quebraria.
3. HMAC — fora do escopo (DEFINE).

**Consequências:**
- Um agente que desobedeça a instrução e rode `freeze` consegue reescrever o contrato; aceitamos esse risco no MVP (A-004). O recibo registra o digest, e o `SHIPPED` o exibe.

---

### Decisão 3: Recibo vinculado a commit **e** estado do worktree

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-09-23 |

**Contexto:** "commit == HEAD" não detecta edições não commitadas feitas depois do `/eval`.

**Escolha:** o recibo guarda `commit` (`git rev-parse HEAD`) e `worktree_digest` = sha256 de `git diff HEAD --binary` + lista ordenada `(path, sha256)` dos arquivos não rastreados, excluindo `.claude/sdd/` e `.claude/storage/`. `verify` recalcula os dois.

**Justificativa:** pega qualquer mudança de código entre `/eval` e `/ship`, commitada ou não, sem exigir worktree limpo; exclui os próprios artefatos SDD, que mudam no `/ship`.

**Alternativas Rejeitadas:**
1. Exigir worktree limpo — atrito alto no fluxo real do usuário.
2. Só `commit` — deixa passar edições não commitadas.

**Consequências:**
- Exige git. Fora de um repositório git, o runner sai com código 2 (`NOT_A_GIT_REPO`).

---

### Decisão 4: Gate = todos os evals exigidos em `pass` ou `waived` (sem expressão booleana)

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-09-23 |

**Contexto:** o DEFINE pede um `exit_check` único. O task-spec usa uma expressão bash (`eval_1 && eval_2`).

**Escolha:** `[gate] required = ["eval_1", …]` opcional; padrão = todos os evals do contrato + todos os complementares. Semântica AND. Veredito `PASS` sse todo eval exigido está em `pass` ou `waived` e não há erro estrutural.

**Justificativa:** cobre o caso de uso real (AND) sem parser de expressões; o exit check fica explícito e auditável.

**Alternativas Rejeitadas:**
1. Expressão booleana arbitrária — complexidade sem caso de uso no MVP.

**Consequências:**
- OR entre evals não é suportado (pode vir depois).

---

### Decisão 5: Regra de decisão do JEV em três saídas, com autoridade condicionada à calibração

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-09-23 |

**Contexto:** o teste real de 2026-09-23 (DEFINE, "Evidência do teste do JEV") mostrou Noul 0,70 com confiança 0 para um AT pendente: Noul sozinho aprovaria o caso errado.

**Escolha:** função pura `classify(answers, thresholds) -> "pass" | "fail" | "escalated"`:
- `pass` sse **todas** as Noul ≥ `noul_pass` (0,85) **e** **todas** as Score têm `confidence ≥ score_confidence` (0,75) com a maior probabilidade no nível de topo;
- `fail` sse **alguma** Noul ≤ `noul_fail` (0,15) **e** alguma Score tem `confidence ≥ 0,75` com a maior probabilidade no nível mais baixo;
- caso contrário `escalated`.

O resultado só é autoritativo se `.claude/sdd/evals/JEV_CALIBRATION.json` existir com `approved: true` e o mesmo `model`; senão o eval vira `escalated` e as respostas do JEV entram no recibo como `advisory`. Todo eval `graded` exige ≥ 1 pergunta Score e de 2 a 5 perguntas.

**Justificativa:** segue o padrão documentado pela TypeSafe (decisões pequenas + escalonamento da incerteza) e a evidência empírica; torna impossível um PASS por Noul ambígua.

**Alternativas Rejeitadas:**
1. Limiar só em Noul (proposta original do DEFINE v1.0) — aprovaria o caso pendente.
2. JEV decidindo sem calibração — sem benchmark publicado para julgar código/relatórios.

**Consequências:**
- Até o usuário rodar `calibrate`, todo `graded` escala (para `judge.py` ou humano). É o comportamento seguro esperado.

---

### Decisão 6: Escalonamento executado pelo runner, não pelo agente

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-09-23 |

**Contexto:** se o agente resolver escalonamentos e "registrar" o resultado, o veredito volta a ser palavra de LLM.

**Escolha:** para cada eval `escalated`, se `OPENROUTER_API_KEY` existir e `--escalate` ≠ `human`, o runner chama `judge.py --stdin --json --phase generic` por subprocess com o `state` e as perguntas renderizados; exit 0 → `pass` (`decided_by: judge`), exit 1 → `fail`. Exit 2/3/4 ou sem chave → `pending` (`decided_by: human` exigido). Só o humano entra via `attest`.

**Justificativa:** reduz os pontos de confiança no agente a um só (repassar a resposta humana), que fica registrado como `recorded_via: eval-agent`.

**Alternativas Rejeitadas:**
1. Agente roda `/judge` e registra — veredito não reprodutível.

**Consequências:**
- `judge.py` passa a ser dependência de runtime distribuída no plugin (ver Decisão 9).

---

### Decisão 7: Atestações humanas vinculadas ao mesmo estado do recibo

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-09-23 |

**Contexto:** AT-004 exige que mudança de código invalide o recibo; uma atestação humana antiga não pode ser reaproveitada automaticamente depois de uma mudança.

**Escolha:** `attest` grava `{eval_id, verdict, owner, evidence, attested_at, commit, worktree_digest, contract_digest, recorded_via}`. No `run`, atestações com estado diferente do atual viram `pending` com motivo `STALE_ATTESTATION`. `waive` registra `{eval_id | "*legacy*", supervisor, reason, waived_at, commit, contract_digest}` e segue a mesma regra.

**Justificativa:** consistência com a filosofia de gate; nada verificado em outro estado conta como verificado agora.

**Alternativas Rejeitadas:**
1. Atestação vinculada só ao contrato — reaproveitaria validações humanas de código já alterado.

**Consequências:**
- Mais atrito: após mudar código, o humano reatesta. É deliberado.

---

### Decisão 8: Relatório renderizado pelo runner a partir do template

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-09-23 |

**Contexto:** o `KB_EVOLUTION` saiu com `⏳` porque o relatório é escrito pelo agente.

**Escolha:** `run` grava `EVAL_{F}.json` e renderiza `EVAL_REPORT_{F}.md` com `string.Template` sobre `EVAL_REPORT_TEMPLATE.md`. O agente não escreve o relatório; só resume ao usuário.

**Justificativa:** o documento humano não pode divergir do recibo.

**Alternativas Rejeitadas:**
1. Agente escreve o relatório a partir do JSON — pode divergir.

**Consequências:**
- O runner precisa achar o template no repo (`.claude/sdd/templates/`) e no plugin (`sdd/templates/`): busca relativa a `__file__` nas duas posições.

---

### Decisão 9: `build-plugin.sh` passa a copiar os scripts de runtime

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-09-23 |

**Contexto:** hoje `plugin/scripts/` contém só `init-workspace.sh` e `status-dashboard.py`; `scripts/judge.py` não é distribuído, então `${CLAUDE_PLUGIN_ROOT}/scripts/judge.py` não existe em instalações via plugin.

**Escolha:** lista explícita `RUNTIME_SCRIPTS=(judge.py eval_runner.py jev_client.py)` copiada de `scripts/` para `plugin/scripts/` com `chmod +x`. Geradores e `judge.py` ficam no mesmo diretório do repo.

**Justificativa:** mantém uma única cópia do código (testável em `tests/`) e corrige de passagem a distribuição do `/judge`.

**Alternativas Rejeitadas:**
1. Mover para `plugin-extras/scripts/` — tiraria os scripts do alcance do `conftest.py` e duplicaria o `judge.py`.

**Consequências:**
- O drift check de CI precisa enxergar os três arquivos em `plugin/scripts/`.

---

### Decisão 10: Ledger do JEV na raiz do projeto, no formato do ledger do `judge.py`

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-09-23 |

**Contexto:** o DEFINE pede reaproveitar o ledger do `judge.py`, mas o `LEDGER` dele é relativo ao diretório do script: em instalações via plugin cairia no cache do plugin.

**Escolha:** o `jev_client` grava em `<raiz do git>/.claude/storage/judge-ledger.jsonl`, com o mesmo schema de linha do `judge.py` (`date, ts, model, target, verdict, cost_usd`) e `verdict` = decisão do classify. Orçamento próprio `JEV_BUDGET` (padrão 200 chamadas/dia), contando só linhas com `model` iniciando em `typesafe/`.

**Justificativa:** mesmo arquivo e schema quando o repo é o próprio AgentSpec; caminho correto quando é plugin; o JEV custa ~US$ 0,000016 por chamada e não deve disputar o orçamento de 10 chamadas/dia do `/judge`.

**Alternativas Rejeitadas:**
1. Importar `append_ledger` do `judge.py` — herdaria o caminho errado em modo plugin.
2. Corrigir o caminho do `judge.py` nesta feature — fora do escopo; registrado como follow-up.

**Consequências:**
- `judge.py --ledger` rodado no repo do AgentSpec mostra as linhas do JEV; em projetos de usuário, os dois ledgers ficam em lugares diferentes até o follow-up.

---

### Decisão 11: Bootstrap — esta feature se avalia com o próprio runner

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-09-23 |

**Contexto:** a feature cria o runner que deveria congelar e checar os evals dela mesma.

**Escolha:** a seção `## Evals` deste DESIGN já é o contrato (17 evals determinísticos, um por AT, via `pytest -k atNNN`). A tarefa #3 do build, logo após o runner existir e **antes** de qualquer teste ser escrito, roda `freeze` (grava o digest) e `pre`. Todos devem falhar com exit 4 (arquivo de teste inexistente) e nenhum pode ser `error`. O `/eval` final roda o runner recém-construído.

**Justificativa:** dogfooding verdadeiro com a menor exceção possível.

**Alternativas Rejeitadas:**
1. Aceitar esta feature sem gate — contradiria o propósito.

**Consequências:**
- Quem escreve os testes (`@test-generator`) é o mesmo build que implementa. Mitigação: a tabela "Plano de Testes por AT" abaixo fixa o que cada teste deve afirmar, e o `/eval` roda o eval complementar `eval_selfcheck` que confere que cada teste `atNNN` contém ao menos um `assert`/`pytest.raises`.

---

## Manifesto de Arquivos

| # | Arquivo | Ação | Propósito | Agente | Dependências |
|---|---------|------|-----------|--------|--------------|
| 1 | `scripts/jev_client.py` | Criar | Cliente JEV (OpenRouter decisions), tipos, fallback de endpoint, truncamento de `state`, ledger + orçamento | @python-developer | Nenhuma |
| 2 | `scripts/eval_runner.py` | Criar | CLI `validate/freeze/pre/run/attest/waive/verify/calibrate`, parse TOML, execução isolada, classify, escalonamento, recibo, render do relatório | @python-developer | 1, 4 |
| 3 | `.claude/sdd/features/DESIGN_POST_BUILD_EVALS.md` | Modificar | Bootstrap: `freeze` grava o Evals Digest; `pre` confirma que os 17 evals falham | (direto) | 2 |
| 4 | `.claude/sdd/templates/EVAL_REPORT_TEMPLATE.md` | Criar | Template pt-BR com placeholders `$feature`, `$verdict`, `$results_table`, `$waivers_table`, `$next_step`… | @code-documenter | Nenhuma |
| 5 | `tests/fixtures/evals/basic/` (`DEFINE_BASIC.md`, `DESIGN_BASIC.md`) | Criar | Feature mínima com 3 ATs e evals deterministic que passam | @test-generator | 2 |
| 6 | `tests/fixtures/evals/cases/` (`design_orphan.md`, `design_bash_error.md`, `design_trivial.md`, `design_graded.md`, `design_human.md`, `design_legacy.md`, `design_too_many_graded.md`) | Criar | Um DESIGN por cenário de falha/borda | @test-generator | 2 |
| 7 | `tests/fixtures/evals/jev/` (`pass.json`, `fail.json`, `pending_ambiguous.json`, `calibration_cases.toml`) | Criar | Respostas reais do JEV (teste de 2026-09-23) como fixtures do cliente simulado + casos de calibração | @test-generator | 1 |
| 8 | `tests/fixtures/evals/kb_evolution/` e `tests/fixtures/evals/frontend_ecosystem/` | Criar | Retroconversão dos ATs das 2 features shipadas em blocos `## Evals` (deterministic/graded/human) | @test-generator | 2 |
| 9 | `tests/test_jev_client.py` | Criar | Parse de resposta, fallback de endpoint, erros tipados, truncamento, orçamento — sem rede | @test-generator | 1, 7 |
| 10 | `tests/test_eval_runner.py` | Criar | Testes `test_atNNN_*` (um grupo por AT do DEFINE) em repositórios git temporários | @test-generator | 2, 4, 5, 6, 7, 8 |
| 11 | `.claude/agents/workflow/eval-agent.md` | Criar | Agente da fase `/eval` (sem Edit), protocolo de complementares e de atestação | (direto) | 2 |
| 12 | `.claude/commands/workflow/eval.md` | Criar | Comando `/eval [feature]`, resolve a feature ativa, chama o agente | (direto) | 11 |
| 13 | `.claude/sdd/templates/DESIGN_TEMPLATE.md` | Modificar | Linha `**Evals Digest**` nos metadados + seção `## Evals` com esqueleto TOML | (direto) | 2 |
| 14 | `.claude/agents/workflow/design-agent.md` | Modificar | Passo "Autorar evals a partir dos ATs → `validate` → `freeze`"; doutrina deterministic-first | (direto) | 13 |
| 15 | `.claude/commands/workflow/design.md` | Modificar | Passo equivalente no processo e no quality gate | (direto) | 14 |
| 16 | `.claude/agents/workflow/build-agent.md` | Modificar | PRE-check antes da primeira tarefa; tabela de ATs do relatório vira "autoverificação" | (direto) | 2 |
| 17 | `.claude/commands/workflow/build.md` | Modificar | Passo PRE e próximo passo `/eval` | (direto) | 16 |
| 18 | `.claude/sdd/templates/BUILD_REPORT_TEMPLATE.md` | Modificar | Seção de ATs rotulada "Autoverificação do build (não substitui /eval)"; próximo passo `/eval` | (direto) | 12 |
| 19 | `.claude/agents/workflow/ship-agent.md` | Modificar | `eval_runner verify` como pré-condição bloqueante; arquiva recibo, relatório, atestações e complementares; SHIPPED lista waivers | (direto) | 2 |
| 20 | `.claude/commands/workflow/ship.md` | Modificar | Passo de verificação e mensagens de recusa por código | (direto) | 19 |
| 21 | `.claude/agents/workflow/iterate-agent.md` | Modificar | Ao mudar ATs ou `## Evals`: `validate` + `freeze` e aviso de recibo invalidado | (direto) | 2 |
| 22 | `.claude/commands/workflow/continue.md` | Modificar | Ler `EVAL_{F}.json` e tratar evals `fail`/`pending` como gaps prioritários | (direto) | 2 |
| 23 | `.claude/sdd/architecture/WORKFLOW_CONTRACTS.yaml` | Modificar | Fase `eval` (comando, agente, input, output, gate), `ship.input` exige recibo, `archive_contents`, `pre_ship_checklist`, transições de status | (direto) | 11, 12 |
| 24 | `build-plugin.sh` | Modificar | Copiar `RUNTIME_SCRIPTS` para `plugin/scripts/` com `chmod +x` | @shell-script-specialist | 1, 2 |
| 25 | `.claude/agents/README.md` | Modificar | eval-agent no mapa de roteamento/escalonamento | @code-documenter | 11 |
| 26 | `docs/concepts/post-build-evals.md` | Criar | Conceito, formato TOML, fluxo, JEV + calibração, waivers, limites | @code-documenter | 2, 11 |
| 27 | `docs/reference/README.md` | Modificar | `/eval` no catálogo de comandos e agentes | @code-documenter | 12 |
| 28 | `docs/getting-started/judge-setup.md` | Modificar | Seção JEV: modelo, endpoint, `JEV_BUDGET`, `calibrate`, dica `export OPENROUTER_API_KEY="$(omp token openrouter)"` | @code-documenter | 1 |
| 29 | `CLAUDE.md` | Modificar | Contagens (74 agentes, 43 comandos), tabela de comandos, key files, tarefa ativa | @code-documenter | 11, 12 |
| 30 | `CHANGELOG.md` | Modificar | Entrada `[Unreleased]` | @code-documenter | todos |
| 31 | Gerados: `.claude/skills/agent-router/*`, `.codex/`, `AGENTS.md`, `plugin-grok/`, `.grok/`, bundle DSH, `plugin/` | Regenerar | `make generate`, `make codex`, `make grok`, `make dsh`, `./build-plugin.sh`; `make check` sem drift | (direto) | 11, 12, 24 |

**Total de Arquivos:** 31 itens (19 criados/regenerados em grupo, 16 modificados).

---

## Justificativa de Atribuição de Agentes

| Agente | Arquivos Atribuídos | Por Que Este Agente |
|--------|---------------------|---------------------|
| @python-developer | 1, 2 | Python stdlib, dataclasses, type hints, CLI com argparse — mesmo idioma do `judge.py` |
| @test-generator | 5, 6, 7, 8, 9, 10 | pytest, fixtures, repositórios git temporários, cliente simulado |
| @shell-script-specialist | 24 | Edição segura de script bash de empacotamento |
| @code-documenter | 4, 25–30 | Template pt-BR e documentação de referência |
| (direto) | 3, 11–23, 31 | Arquivos do próprio framework SDD (agentes, comandos, contratos) — o build-agent conhece o formato; nenhum especialista externo agrega |

**Descoberta de Agentes:**
- Escaneado: `.claude/agents/**/*.md`
- Correspondido por: tipo de arquivo (`.py`, `.sh`, `.md`), propósito (testes, docs), domínios KB `python`, `testing`

---

## Padrões de Código

### Padrão 1: Bloco `## Evals` no DESIGN (formato de autoria)

````markdown
## Evals

<!-- agentspec:evals:contract -->
```toml
[gate]
required = ["eval_1", "eval_2", "eval_3"]   # opcional; padrão = todos

[[eval]]
id = "eval_1"
verifies = ["AT-001"]
check_type = "deterministic"
description = "_index.yaml registra mcp_validated com a data do ingest"
timeout_sec = 60
run = '''
grep -A3 '^  dbt:' .claude/kb/_index.yaml | grep -q "mcp_validated: $(date +%Y-%m-%d)"
'''

[[eval]]
id = "eval_2"
verifies = ["AT-003"]
check_type = "graded"
description = "Lint reporta a API deprecada como stale, citando arquivo e linha"

[eval.state]                     # campo -> comando bash cuja stdout vira o valor
report = "cat .claude/kb/dbt/LINT_REPORT.md"
fixture = "cat tests/fixtures/deprecated_api.md"

[[eval.questions]]
id = "lists_stale"
type = "noul"
instructions = "Does `report` list the API deprecated in `fixture` as an issue of type 'stale'?"

[[eval.questions]]
id = "cites_location"
type = "score"
instructions = "How precisely does `report` cite the file and line of that issue?"
criteria = ["no citation", "file only", "file and line"]

[[eval]]
id = "eval_3"
verifies = ["AT-002"]
check_type = "human"
owner = "Marco"
description = "Domínio sem cobertura no Context7 é detectado e nada é alterado"
instructions = "Rode /ingest-kb medallion e confirme a mensagem de fallback e o git status limpo."
```
````

Regras que o `validate` aplica:

| Regra | Severidade |
|-------|------------|
| Exatamente um marcador `<!-- agentspec:evals:contract -->` **fora** de blocos cercados (o scanner acompanha aberturas/fechamentos de ` ``` ` e ` ```` `), seguido do bloco ` ```toml ` | erro (`NO_CONTRACT` / `MULTIPLE_CONTRACTS`) |
| Todo AT da tabela do DEFINE tem ≥ 1 eval em `verifies` | erro (`ORPHAN_AT`) |
| Todo `verifies` aponta para um AT existente | erro (`UNKNOWN_AT`) |
| `id` único; `check_type` ∈ {deterministic, graded, human} | erro |
| deterministic tem `run`; `bash -n` passa | erro |
| graded tem `state` não vazio e 2–5 perguntas, ≥ 1 do tipo `score` com 2–10 `criteria` | erro |
| human tem `owner` e `instructions` | erro |
| > 50% dos evals são graded | aviso |
| Todas as linhas de `run` são testes de existência (`test -[efd]`, `[ -[efd]`) | aviso (`EXISTENCE_ONLY`) |

### Padrão 2: Cliente JEV

```python
DEFAULT_MODEL = "typesafe/jev-1.13"
ENDPOINTS = (
    "https://openrouter.ai/api/v1/systemone",
    "https://openrouter.ai/api/alpha/decisions",
)
MAX_STATE_CHARS = 96_000


@dataclass(frozen=True, slots=True)
class Question:
    id: str
    type: Literal["noul", "score"]
    instructions: str
    criteria: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Answer:
    id: str
    type: str
    noul: float | None = None
    score: float | None = None
    probabilities: dict[str, float] | None = None
    confidence: float | None = None


@dataclass(frozen=True, slots=True)
class DecisionResult:
    model: str
    answers: dict[str, Answer]
    cost_usd: float | None
    request_id: str | None
    truncated: bool


class JevError(RuntimeError):
    def __init__(self, message: str, code: str) -> None:
        super().__init__(message)
        self.code = code


def decide(
    state: dict[str, str],
    questions: Sequence[Question],
    *,
    api_key: str,
    model: str = DEFAULT_MODEL,
    endpoints: Sequence[str] = ENDPOINTS,
    timeout: float = 30.0,
    opener: Callable[..., Any] = urllib.request.urlopen,
) -> DecisionResult:
    body, truncated = _build_body(state, questions, model)
    last_error: JevError | None = None
    for url in endpoints:
        try:
            return _parse(_post(url, body, api_key, timeout, opener), truncated)
        except JevError as err:
            if err.code not in {"NOT_FOUND", "UNAVAILABLE"}:
                raise
            last_error = err
    raise last_error or JevError("no endpoint configured", "CONFIG")
```

`opener` injetável permite testar sem rede. Códigos de erro: `AUTH` (401/403), `BAD_REQUEST` (400), `NOT_FOUND` (404 → tenta o próximo endpoint), `UNAVAILABLE` (5xx, timeout, URLError → tenta o próximo), `BUDGET`, `CONFIG`, `PARSE`.

### Padrão 3: Classificação da resposta do JEV

```python
@dataclass(frozen=True, slots=True)
class Thresholds:
    noul_pass: float = 0.85
    noul_fail: float = 0.15
    score_confidence: float = 0.75


def classify(answers: Mapping[str, Answer], t: Thresholds) -> Literal["pass", "fail", "escalated"]:
    nouls = [a.noul for a in answers.values() if a.type == "noul"]
    scores = [a for a in answers.values() if a.type == "score"]
    confident = [s for s in scores if (s.confidence or 0.0) >= t.score_confidence]
    top = [s for s in confident if _argmax_level(s) == _max_level(s)]
    bottom = [s for s in confident if _argmax_level(s) == 0]

    if nouls and all(n is not None and n >= t.noul_pass for n in nouls) and len(top) == len(scores):
        return "pass"
    if any(n is not None and n <= t.noul_fail for n in nouls) and bottom:
        return "fail"
    return "escalated"
```

Aplicado às fixtures reais: caso positivo (0,94 / conf 0,97, topo) → `pass`; contradição (0,21 / conf 0,65) → `escalated` (a confiança não alcança 0,75, então o runner não reprova sozinho); pendente (0,70 / conf 0) → `escalated`.

### Padrão 4: Execução isolada de um eval deterministic

```python
def run_deterministic(ev: Eval, root: Path) -> EvalResult:
    script = f"set -euo pipefail\n{ev.run}"
    env = {k: v for k, v in os.environ.items() if k != "OPENROUTER_API_KEY"}
    env["AGENTSPEC_PYTHON"] = sys.executable
    started = time.monotonic()
    try:
        proc = subprocess.run(
            ["bash", "-c", script],
            cwd=root,
            env=env,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=ev.timeout_sec,
        )
    except subprocess.TimeoutExpired:
        return EvalResult(ev.id, "error", reason="TIMEOUT", duration=time.monotonic() - started)
    status = "pass" if proc.returncode == 0 else ("error" if _is_bash_error(proc) else "fail")
    return EvalResult(
        ev.id,
        status,
        exit_code=proc.returncode,
        stdout=proc.stdout[-4000:],
        stderr=proc.stderr[-4000:],
        duration=time.monotonic() - started,
    )


_BASH_ERROR = re.compile(r"syntax error|unbound variable|command not found|No such file or directory: bash")
_INTERPRETER_ERROR = re.compile(r"^\S*python[\d.]*: No module named ", re.MULTILINE)


def _is_bash_error(proc: subprocess.CompletedProcess[str]) -> bool:
    if _INTERPRETER_ERROR.search(proc.stderr):
        return True
    return proc.returncode in {2, 126, 127} and bool(_BASH_ERROR.search(proc.stderr))
```

No `run`, `error` conta como falha. No `pre`, `error` bloqueia (exit 1), `pass` gera aviso `ALREADY_PASSING` e `fail` é o esperado.

`AGENTSPEC_PYTHON` expõe aos evals o interpretador que roda o runner (≥ 3.11). Evals que chamam Python devem usar `"$AGENTSPEC_PYTHON"` em vez de `python3`: nesta máquina, `python3` é o 3.14 sem pytest, e `python3.12` tem pytest. `_INTERPRETER_ERROR` pega o caso `python3: No module named pytest` (exit 1), que de outra forma seria classificado como `fail` comum e esconderia um ambiente quebrado. `ModuleNotFoundError` do código da feature, reportado pelo pytest (exit 2 com a mensagem no stdout), continua sendo `fail`, que é o esperado antes do build.

### Padrão 5: Recibo `agentspec/eval-receipt/v1`

```json
{
  "schema": "agentspec/eval-receipt/v1",
  "feature": "KB_EVOLUTION",
  "commit": "3f2c1ab…",
  "worktree_digest": "sha256:…",
  "contract_digest": "sha256:…",
  "evaluated_at": "2026-09-24T14:03:11Z",
  "runner_version": "1.0.0",
  "jev": {"model": "typesafe/jev-1.13", "calibrated": false},
  "results": [
    {"eval_id": "eval_1", "origin": "contract", "verifies": ["AT-001"], "check_type": "deterministic",
     "status": "pass", "exit_code": 0, "duration_sec": 0.12, "evidence": {"stdout": "", "stderr": ""}},
    {"eval_id": "eval_2", "origin": "contract", "verifies": ["AT-003"], "check_type": "graded",
     "status": "pass", "decided_by": "judge",
     "jev": {"role": "advisory", "decision": "escalated", "answers": {"lists_stale": {"noul": 0.7}}, "cost_usd": 0.000016},
     "judge": {"exit_code": 0, "model": "openai/gpt-4o-mini"}},
    {"eval_id": "eval_3", "origin": "contract", "verifies": ["AT-002"], "check_type": "human",
     "status": "waived", "waiver": {"supervisor": "Marco", "reason": "Context7 fora do ar"}}
  ],
  "required": ["eval_1", "eval_2", "eval_3"],
  "structural_errors": [],
  "verdict": "PASS"
}
```

Status possíveis por eval: `pass | fail | error | escalated | pending | waived`. `escalated` só aparece como estado intermediário; no recibo final vira `pass`/`fail` (judge) ou `pending`.

### Padrão 6: Códigos do `verify` (usados pelo `/ship`)

| Exit | Código | Mensagem ao usuário |
|------|--------|---------------------|
| 0 | `OK` / `OK_LEGACY_WAIVED` | Pode shipar |
| 1 | `NO_RECEIPT` | Rode `/eval {F}` antes do `/ship` |
| 1 | `VERDICT_FAIL` | Evals reprovados ou pendentes: rode `/continuar {F}` ou registre waiver |
| 1 | `STALE_COMMIT` / `STALE_WORKTREE` | O código mudou depois do `/eval`: rode `/eval {F}` de novo |
| 1 | `STALE_CONTRACT` | O contrato de evals mudou depois do `/eval`: rode `/eval {F}` de novo |
| 1 | `CONTRACT_TAMPERED` | O bloco `## Evals` não bate com o Evals Digest: use `/iterate` |
| 1 | `LEGACY_NO_EVALS` | DESIGN sem `## Evals`: adicione evals via `/iterate` ou `waive --legacy` |
| 2 | `CONFIG` / `NOT_A_GIT_REPO` / `PYTHON_TOO_OLD` | Erro de ambiente |

---

## Fluxo de Dados

```text
1. /design   design-agent lê ATs do DEFINE → escreve ## Evals (TOML)
             → eval_runner validate DESIGN DEFINE   (exit 3 se erro estrutural)
             → eval_runner freeze DESIGN            (grava Evals Digest)

2. /build    build-agent → eval_runner pre DESIGN
             → erro de bash: BLOQUEIA antes de gerar código
             → eval já passa: AVISA no BUILD_REPORT
             → gera código; tabela de ATs = "autoverificação"

3. /eval     eval-agent → (opcional) escreve EVALS_EXTRA_{F}.toml (deterministic|graded)
             → eval_runner run F
                 a. digest do contrato == Evals Digest?   senão CONTRACT_TAMPERED
                 b. validate (contrato + extras)
                 c. deterministic → bash isolado
                 d. graded → JEV → classify → [não calibrado ou escalated] → judge.py → [erro] pending
                 e. human → attestations.json (estado atual?) senão pending
                 f. waivers aplicados
                 g. grava EVAL_{F}.json + EVAL_REPORT_{F}.md
             → pending human? agente pergunta ao usuário (AskUserQuestion)
               → eval_runner attest … → eval_runner run F (de novo)
             → FAIL: sugere /continuar F

4. /ship     ship-agent → eval_runner verify F → exit ≠ 0: recusa com o código
             → arquiva EVAL_{F}.json, EVAL_REPORT_{F}.md, attestations, EVALS_EXTRA
```

---

## Pontos de Integração

| Sistema Externo | Tipo de Integração | Autenticação |
|----------------|-------------------|--------------|
| OpenRouter — JEV (`typesafe/jev-1.13`) | REST `POST /api/v1/systemone` (fallback `/api/alpha/decisions`), corpo `{model, state, questions}` | `Authorization: Bearer $OPENROUTER_API_KEY` |
| `scripts/judge.py` | Subprocess `--stdin --json --phase generic` | Herda `OPENROUTER_API_KEY` |
| git | Subprocess (`rev-parse`, `diff HEAD --binary`, `ls-files --others --exclude-standard`) | — |
| bash | Subprocess por eval | — |

---

## Estratégia de Testes

| Tipo de Teste | Escopo | Arquivos | Ferramentas | Meta de Cobertura |
|---------------|--------|----------|-------------|-------------------|
| Unitário | `classify`, parse TOML, digest canônico, `_is_bash_error`, truncamento, parse de resposta do JEV | `tests/test_jev_client.py`, `tests/test_eval_runner.py` | pytest | 90% das funções puras |
| Integração | CLI `validate/freeze/pre/run/attest/waive/verify/calibrate` em repositórios git temporários (`tmp_path` + `git init`) | `tests/test_eval_runner.py` | pytest + subprocess | Todos os ATs |
| Fixtures reais | Retroconversão de `KB_EVOLUTION` e `FRONTEND_ECOSYSTEM`; respostas reais do JEV | `tests/fixtures/evals/` | pytest | 2 features |
| Live (opcional) | Uma chamada real ao JEV; pula sem `OPENROUTER_API_KEY` | `tests/test_jev_client.py::test_live_decide` | pytest skipif | — |
| E2E manual | `/design → /build → /eval → /ship` numa feature de exemplo | — | Manual | Caminho feliz |

Toda a suíte roda offline: o JEV é simulado por `opener` injetado e o `judge.py` por um executável falso no `PATH` do teste (`JUDGE_CMD` configurável).

### Plano de Testes por AT

| AT | Teste(s) `test_atNNN_*` | O que deve afirmar |
|----|------------------------|--------------------|
| AT-001 | `test_at001_happy_path` | `run` → exit 0, recibo `PASS` com `commit`, `worktree_digest`, `contract_digest` corretos; `verify` → exit 0; relatório renderizado contém a tabela de resultados |
| AT-002 | `test_at002_eval_fails` | eval com `exit 1` → recibo `FAIL`, stdout/stderr na evidência, relatório menciona `/continuar`; `verify` → `VERDICT_FAIL` |
| AT-003 | `test_at003_ship_without_receipt` | `verify` sem recibo → exit 1, `NO_RECEIPT` |
| AT-004 | `test_at004_stale_commit`, `test_at004_stale_worktree` | commit novo → `STALE_COMMIT`; edição não commitada → `STALE_WORKTREE`; edição só em `.claude/sdd/` → continua `OK` |
| AT-005 | `test_at005_stale_contract` | mudar o bloco + `freeze` → `verify` → `STALE_CONTRACT` |
| AT-006 | `test_at006_pre_bash_error`, `test_at006_pre_interpreter_error` | `pre` com erro de sintaxe e com comando inexistente → exit 1, saída aponta o eval; `python: No module named pytest` → `error` (`ENVIRONMENT`), não `fail` |
| AT-007 | `test_at007_pre_already_passing` | `pre` com eval que passa → exit 0 com aviso `ALREADY_PASSING` |
| AT-008 | `test_at008_orphan_at` | `validate` → exit 3, lista `ORPHAN_AT: AT-004`; `UNKNOWN_AT` para `verifies` inválido |
| AT-009 | `test_at009_contract_tampered`, `test_at009_complementary_accepted` | bloco editado sem `freeze` → `run` → `FAIL` com `CONTRACT_TAMPERED`; eval em `EVALS_EXTRA` → aceito com `origin: complementary` e exigido no gate |
| AT-010 | `test_at010_human_pending` | eval human sem atestação → `pending`, `FAIL`; atestação de outro commit → `pending` com `STALE_ATTESTATION` |
| AT-011 | `test_at011_waiver` | `waive` → `waived`, `PASS`, `waivers[]` preenchido; `verify` → exit 0 |
| AT-012 | `test_at012_graded_confident_calibrated` | calibração aprovada + fixture `pass.json` → `pass`, `decided_by: jev`, respostas e custo no recibo |
| AT-013 | `test_at013_graded_low_confidence` | fixture `pending_ambiguous.json` → escala; judge falso exit 0 → `pass` com `decided_by: judge` e JEV `advisory`; judge falso exit 1 → `fail` |
| AT-014 | `test_at014_jev_unavailable` | `opener` levanta 5xx/timeout nos 2 endpoints; orçamento esgotado → nunca `pass` pelo JEV; `escalated`/`pending` com motivo |
| AT-015 | `test_at015_uncalibrated` | sem `JEV_CALIBRATION.json` (ou com outro `model`) → JEV `advisory`, decisão via judge/humano |
| AT-016 | `test_at016_legacy` | DESIGN sem `## Evals` → `verify` → `LEGACY_NO_EVALS`; `waive --legacy` → recibo com `legacy_waiver`, `verify` → `OK_LEGACY_WAIVED` |
| AT-017 | `test_at017_too_many_graded` | 3 de 4 graded → `validate` exit 0 com aviso de > 50% graded |

Testes adicionais obrigatórios: `test_retro_kb_evolution` e `test_retro_frontend_ecosystem` (runner executa as retroconversões sem erro de execução, critério de sucesso do DEFINE) e `test_calibrate_approval` (10 casos, concordância ≥ 80% e cobertura ≥ 50% → `approved: true`).

---

## Tratamento de Erros

| Tipo de Erro | Estratégia de Tratamento | Retry? |
|-------------|-------------------------|--------|
| JEV 404 ou 5xx/timeout no endpoint primário | Tenta `/api/alpha/decisions` | Sim, 1 fallback |
| JEV 401/403/400 | `JevError(AUTH/BAD_REQUEST)`; eval `escalated` com motivo | Não |
| Orçamento `JEV_BUDGET` esgotado | Não chama; eval `escalated` com `BUDGET` | Não |
| `judge.py` exit 2/3/4 ou sem chave | Eval `pending` (exige humano) | Não |
| Timeout de eval deterministic | `error` com `TIMEOUT` | Não |
| Erro de bash no `pre` | Bloqueia o build (exit 1) | Não |
| TOML inválido / regra estrutural | `validate`/`run` exit 3 com lista de erros | Não |
| Python < 3.11 | Exit 2 `PYTHON_TOO_OLD` com instrução | Não |
| Fora de repositório git | Exit 2 `NOT_A_GIT_REPO` | Não |
| `state` > `MAX_STATE_CHARS` | Trunca cada campo proporcionalmente com marcador `…[truncated]`, `truncated: true` no recibo | Não |

Princípio: nenhuma falha de infraestrutura produz `pass`.

---

## Configuração

| Chave de Config | Tipo | Padrão | Descrição |
|----------------|------|--------|-----------|
| `OPENROUTER_API_KEY` | env string | — | Chave usada pelo JEV e pelo `judge.py` |
| `JEV_MODEL` | env string | `typesafe/jev-1.13` | Modelo do JEV |
| `JEV_BUDGET` | env int | `200` | Máximo de chamadas ao JEV por dia (UTC) |
| `JUDGE_CMD` | env string | `<sys.executable> <scripts>/judge.py` | Comando de escalonamento (sobrescrito nos testes) |
| `AGENTSPEC_PYTHON` | env string (exportada pelo runner) | `sys.executable` | Interpretador disponível para os evals; usar em vez de `python3` |
| `--escalate` | flag | `auto` | `auto` (judge se houver chave, senão humano) \| `judge` \| `human` |
| `timeout_sec` (por eval) | TOML int | `120` | Timeout de cada eval deterministic |
| `thresholds` em `JEV_CALIBRATION.json` | JSON | `noul_pass 0.85`, `noul_fail 0.15`, `score_confidence 0.75` | Sobrescreve os limiares padrão |

---

## Considerações de Segurança

- Evals executam bash arbitrário do DESIGN com os privilégios do usuário, como qualquer teste do projeto: o DESIGN é código e deve ser revisado como tal. O runner não expõe `OPENROUTER_API_KEY` aos evals (`env` do subprocess remove a variável).
- A chave nunca é gravada em recibo, relatório, ledger ou log; mensagens de erro HTTP são truncadas e não ecoam headers.
- `state` enviado ao JEV sai da máquina: o `validate` avisa quando um campo de `state` lê arquivos que batem com `.env*`, `*.pem`, `*secret*` ou `*credential*`.
- O recibo e o digest são proteção contra drift acidental, não contra adulteração deliberada (sem HMAC, decisão do DEFINE).

---

## Observabilidade

| Aspecto | Implementação |
|---------|---------------|
| Logging | Saída humana no terminal por eval (`✓/✗/⚠/⏳`), `--json` para máquina |
| Métricas | Recibo por execução (duração por eval, custo do JEV, decided_by) — formato estável para `LIVING_MEMORY` consumir |
| Custo | Ledger `<projeto>/.claude/storage/judge-ledger.jsonl` com `cost_usd` por chamada do JEV |

---

## Evals

Contrato desta própria feature (Decisão 11). Todos deterministic: cada um roda o grupo de testes do AT correspondente. Antes do build, o pytest sai com exit 4 (arquivo de teste inexistente) ou 5 (nenhum teste coletado). Ambos são `fail`, não `error`, então o `pre` deixa o build seguir. Conferido em 2026-09-23 com `python3.12 -m pytest`.

<!-- agentspec:evals:contract -->
```toml
[[eval]]
id = "eval_at001"
verifies = ["AT-001"]
check_type = "deterministic"
description = "Caminho feliz: run PASS e verify OK"
run = '''
"$AGENTSPEC_PYTHON" -m pytest tests/test_eval_runner.py -q -k at001
'''

[[eval]]
id = "eval_at002"
verifies = ["AT-002"]
check_type = "deterministic"
description = "Eval reprovado gera FAIL e aponta /continuar"
run = '''
"$AGENTSPEC_PYTHON" -m pytest tests/test_eval_runner.py -q -k at002
'''

[[eval]]
id = "eval_at003"
verifies = ["AT-003"]
check_type = "deterministic"
description = "Ship sem recibo é recusado"
run = '''
"$AGENTSPEC_PYTHON" -m pytest tests/test_eval_runner.py -q -k at003
'''

[[eval]]
id = "eval_at004"
verifies = ["AT-004"]
check_type = "deterministic"
description = "Recibo obsoleto por commit ou worktree"
run = '''
"$AGENTSPEC_PYTHON" -m pytest tests/test_eval_runner.py -q -k at004
'''

[[eval]]
id = "eval_at005"
verifies = ["AT-005"]
check_type = "deterministic"
description = "Recibo obsoleto por contrato"
run = '''
"$AGENTSPEC_PYTHON" -m pytest tests/test_eval_runner.py -q -k at005
'''

[[eval]]
id = "eval_at006"
verifies = ["AT-006"]
check_type = "deterministic"
description = "PRE bloqueia erro de bash"
run = '''
"$AGENTSPEC_PYTHON" -m pytest tests/test_eval_runner.py -q -k at006
'''

[[eval]]
id = "eval_at007"
verifies = ["AT-007"]
check_type = "deterministic"
description = "PRE avisa eval que já passa"
run = '''
"$AGENTSPEC_PYTHON" -m pytest tests/test_eval_runner.py -q -k at007
'''

[[eval]]
id = "eval_at008"
verifies = ["AT-008"]
check_type = "deterministic"
description = "AT órfão é detectado"
run = '''
"$AGENTSPEC_PYTHON" -m pytest tests/test_eval_runner.py -q -k at008
'''

[[eval]]
id = "eval_at009"
verifies = ["AT-009"]
check_type = "deterministic"
description = "Contrato adulterado reprova; complementares são aceitos"
run = '''
"$AGENTSPEC_PYTHON" -m pytest tests/test_eval_runner.py -q -k at009
'''

[[eval]]
id = "eval_at010"
verifies = ["AT-010"]
check_type = "deterministic"
description = "Eval human sem atestação fica pendente e reprova"
run = '''
"$AGENTSPEC_PYTHON" -m pytest tests/test_eval_runner.py -q -k at010
'''

[[eval]]
id = "eval_at011"
verifies = ["AT-011"]
check_type = "deterministic"
description = "Waiver nomeado libera o gate e aparece no recibo"
run = '''
"$AGENTSPEC_PYTHON" -m pytest tests/test_eval_runner.py -q -k at011
'''

[[eval]]
id = "eval_at012"
verifies = ["AT-012"]
check_type = "deterministic"
description = "Graded confiante com calibração aprovada passa pelo JEV"
run = '''
"$AGENTSPEC_PYTHON" -m pytest tests/test_eval_runner.py tests/test_jev_client.py -q -k at012
'''

[[eval]]
id = "eval_at013"
verifies = ["AT-013"]
check_type = "deterministic"
description = "Graded de baixa confiança escala para judge ou humano"
run = '''
"$AGENTSPEC_PYTHON" -m pytest tests/test_eval_runner.py -q -k at013
'''

[[eval]]
id = "eval_at014"
verifies = ["AT-014"]
check_type = "deterministic"
description = "JEV indisponível nunca gera PASS"
run = '''
"$AGENTSPEC_PYTHON" -m pytest tests/test_eval_runner.py tests/test_jev_client.py -q -k at014
'''

[[eval]]
id = "eval_at015"
verifies = ["AT-015"]
check_type = "deterministic"
description = "JEV sem calibração é apenas consultivo"
run = '''
"$AGENTSPEC_PYTHON" -m pytest tests/test_eval_runner.py -q -k at015
'''

[[eval]]
id = "eval_at016"
verifies = ["AT-016"]
check_type = "deterministic"
description = "Feature legada exige waiver global"
run = '''
"$AGENTSPEC_PYTHON" -m pytest tests/test_eval_runner.py -q -k at016
'''

[[eval]]
id = "eval_at017"
verifies = ["AT-017"]
check_type = "deterministic"
description = "Excesso de graded gera aviso"
run = '''
"$AGENTSPEC_PYTHON" -m pytest tests/test_eval_runner.py -q -k at017
'''
```

Evals complementares previstos para o `/eval` desta feature (em `EVALS_EXTRA_POST_BUILD_EVALS.toml`, fora do contrato): `eval_selfcheck` (cada teste `test_atNNN_*` contém `assert` ou `pytest.raises`), `eval_retro` (`pytest -k retro`), `eval_plugin_scripts` (`"$AGENTSPEC_PYTHON" plugin/scripts/eval_runner.py --help`) e `eval_no_drift` (`make check`).

---

## Riscos e Limitações Conhecidas

| Risco | Mitigação |
|-------|-----------|
| Agente desobedece e roda `freeze` ou edita código durante o `/eval` | Premissa A-004 aceita no MVP; o recibo registra digest e estado, e o `SHIPPED` exibe waivers e digest |
| Endpoint do JEV é alpha e pode mudar | Cliente isolado, fallback entre dois paths, nenhuma falha vira PASS |
| Calibração com poucos casos | `calibrate` exige n ≥ 10 e cobertura ≥ 50% para aprovar |
| Evals de projetos de usuário dependem de ferramentas locais (dbt, npm) | Mesmo requisito do `build.verification` atual; `error` distingue ambiente quebrado de falha |
| Autoria de evals deixa o `/design` mais longo | Esqueleto no template; um eval por AT como mínimo |

**Follow-ups fora do escopo:** corrigir o caminho do ledger no `judge.py` em modo plugin; `/status` exibir o estado do gate (COULD do DEFINE); checagem de escopo do diff; gold-sanity.

---

## Histórico de Revisões

| Versão | Data | Autor | Mudanças |
| 1.2 | 2026-09-24 | ship-agent | Entregue e arquivado (recibo `/eval` PASS, 17/17) |
|--------|------|-------|----------|
| 1.0 | 2026-09-23 | design-agent | Versão inicial a partir de `DEFINE_POST_BUILD_EVALS.md` v1.1 |
| 1.1 | 2026-09-23 | design-agent | Autoverificação: marcador do contrato só conta fora de blocos cercados; `AGENTSPEC_PYTHON` e detecção de erro de interpretador; exit codes reais do pytest (4/5) no bootstrap |

---

## Próximo Passo

**Pronto para:** `/eval POST_BUILD_EVALS`
