# DESIGN: Living Memory (Segundo Cérebro entre Fases)

> O Blackboard passa a cobrir o ciclo todo; um script stdlib (`memory-index.py`) lê Blackboards, `archive/` e `MEMORY.md` para gerar o resumo de entrada de fase, o gate de perguntas abertas, o tail do SessionStart e o `MEMORY_INDEX.md`.

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | LIVING_MEMORY |
| **Data** | 2026-09-23 |
| **Autor** | design-agent |
| **DEFINE** | [DEFINE_LIVING_MEMORY.md](./DEFINE_LIVING_MEMORY.md) (v1.1) |
| **Status** | ✅ Shipped |

---

## Visão Geral da Arquitetura

```text
                ┌──────────────────────── ESCRITA (prompts dos agentes) ─────────────────────────┐
                │                                                                                │
 /brainstorm ──►│ cria BLACKBOARD ─► D/Q (fase brainstorm)                                       │
 /define ──────►│ cria se faltar  ─► A/Q/D (fase define)                                         │
 /design ──────►│ ─► D por ADR inline (ponteiro p/ DESIGN), 🟡→🟢                                │
 /build,/continuar ─► Interfaces + Status + D de DESVIO ("Substitui D-00X")                     │
 /iterate,/work►│ ─► D com "Substitui" / M                                                       │
 /ship ────────►│ ─► L no MEMORY.md + arquiva BLACKBOARD                                         │
                └──────────────────────────────┬─────────────────────────────────────────────────┘
                                               ▼
   .claude/sdd/features/BLACKBOARD_*.md   .claude/sdd/archive/*/{BLACKBOARD,DESIGN,SHIPPED}*.md   .claude/sdd/MEMORY.md
                                               │   (+ DEFINE_*.md e kb/_index.yaml p/ domínios)
                                               ▼
                     ┌──────────────── plugin-extras/scripts/memory-index.py (stdlib) ────────────────┐
                     │ collect() → [Entry] ── parse tolerante (header-driven, sem acento, legado)      │
                     │                                                                                 │
                     │  brief FEATURE --phase P  → ≤15 linhas (stdout)   ◄── agente ao ENTRAR na fase  │
                     │  gate  FEATURE --to design|build → exit 0/1       ◄── design/build ao ENTRAR    │
                     │  tail  [FEATURE] --n 5    → últimas entradas      ◄── init-workspace.sh (Start) │
                     │  build                    → .claude/sdd/MEMORY_INDEX.md (gitignored)            │
                     └─────────────────────────────────────────────────────────────────────────────────┘
```

**Princípio:** os agentes só **escrevem** Markdown no Blackboard (o que já sabem fazer). Toda **leitura** agregada, ranqueamento e checagem é determinística, no script. Isso ataca a premissa de maior risco (A-001): a entrada de fase não depende do modelo lembrar de ler histórico — ele recebe o resumo pronto.

---

## Componentes

| Componente | Propósito | Tecnologia |
|------------|-----------|------------|
| `BLACKBOARD_TEMPLATE.md` (estendido) | Estado vivo da feature do Brainstorm ao Ship; coluna `Fase` + tabela de Premissas | Markdown pt-BR |
| `memory-index.py` | Coleta entradas, gera resumo, gate, tail e índice | Python 3.10+ stdlib (`re`, `unicodedata`, `argparse`, `dataclasses`, `pathlib`) |
| Protocolo de Memória de Fase | Bloco ENTRADA/SAÍDA em cada agente e comando de workflow | Markdown (prompts em inglês) |
| `WORKFLOW_CONTRACTS.yaml` → `living_memory` | Fonte da verdade do ciclo de vida, IDs, status e gates | YAML |
| `init-workspace.sh` → `surface_memory` | Anexa o tail da feature `.active` ao SessionStart | Bash |
| `tests/test_memory_index.py` + fixtures | Cobertura dos parsers, ranking, gate, determinismo, compatibilidade | pytest |

---

## Decisões Principais

### Decisão 1: Coluna `Fase` nas tabelas existentes, não uma seção "Diário" separada

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-09-23 |

**Contexto:** DEFINE delegou o formato do Diário (Questão 1). O Blackboard já tem Log de Decisões, Perguntas e Melhorias; `status-dashboard.py` lê essas seções por nome.

**Escolha:** manter uma tabela por **tipo** de entrada e adicionar a coluna `Fase` (e `Alternativa Rejeitada`, `Onde Ler` no Log de Decisões). Nova seção `## Premissas`. Nomes de seção inalterados.

**Justificativa:** um tipo = uma tabela deixa o parser simples e o "Substitui" resolvível dentro da mesma tabela; o dashboard continua funcionando sem mudança; a visão por fase sai do filtro `Fase`.

**Alternativas Rejeitadas:**
1. Seção única `## Diário por Fase` com blocos `### define` — rejeitada porque mistura tipos, duplica o Log de Decisões e exige parser por bloco livre
2. Arquivo `JOURNAL_{FEATURE}.md` — rejeitado no BRAINSTORM (duplicação)

**Consequências:**
- Tabela de decisões fica larga (9 colunas); aceitável em Markdown
- Blackboards antigos (sem `Fase`) são lidos como fase `build` (AT-010)

---

### Decisão 2: Parser dirigido pelo cabeçalho da tabela, normalizado sem acento

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-09-23 |

**Contexto:** formatos variam entre versões (colunas novas × antigas) e entre documentos (`Decisao`/`Decisão`, `Licoes`/`Lições`) — A-003 observada.

**Escolha:** cada tabela é lida pela linha de cabeçalho; nomes de coluna e de heading passam por `fold()` (NFKD, remove marcas, minúsculas). Colunas desconhecidas são ignoradas; ausentes viram vazio.

**Justificativa:** um único parser serve formato antigo e novo, e não quebra com colunas acrescentadas por outras frentes (ex.: "modelo" de `LLM_PHASE_ROUTING`).

**Alternativas Rejeitadas:**
1. Posição fixa de coluna (como `file_status_counts` do dashboard) — rejeitada porque quebra na primeira coluna nova
2. Frontmatter YAML por entrada — rejeitado: sem parser YAML na stdlib e ilegível para humanos

**Consequências:**
- Linhas-modelo do template (`{...}`) precisam ser descartadas explicitamente
- Tolerância maior = menos erros ruidosos; entradas malformadas são puladas em silêncio (contadas em `build --verbose`)

---

### Decisão 3: Um script com subcomandos em `plugin-extras/scripts/`

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-09-23 |

**Contexto:** DEFINE Questão 2. `scripts/` guarda ferramentas de build do repo (`generate-*.py`) e `judge.py`; `plugin-extras/scripts/` guarda o que roda **no projeto do usuário** (`init-workspace.sh`, `status-dashboard.py`).

**Escolha:** `plugin-extras/scripts/memory-index.py` com `brief | gate | tail | build`. Chamado como `${CLAUDE_PLUGIN_ROOT:-.}/scripts/memory-index.py`, com fallback para `plugin-extras/scripts/` ao desenvolver no próprio repo.

**Justificativa:** é runtime do usuário, igual ao dashboard. `build-plugin.sh` (Step 2b) e `generate-grok-plugin.py` (`EXTRAS_SCRIPTS`) já copiam **todo** arquivo dessa pasta — zero mudança nos geradores (SC-9). Codex/DSH não empacotam scripts; só precisam ser regenerados pelos agentes/comandos alterados.

**Alternativas Rejeitadas:**
1. `scripts/memory-index.py` — rejeitada: exigiria cópia explícita no build e no Grok, como é feito com `judge.py`
2. Quatro scripts separados — rejeitada: parser e coleta seriam duplicados

**Consequências:**
- Nome com hífen → testes importam via `importlib.util.spec_from_file_location`
- `tests/conftest.py` não muda

---

### Decisão 4: Gate por script + instrução de prompt; status 🟡 "Delegada" não bloqueia

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-09-23 |

**Contexto:** DEFINE Questão 5 e G6. Um hook não sabe em que fase o usuário está; um prompt sozinho pode "esquecer".

**Escolha:** `/design` e `/build` rodam `memory-index.py gate FEATURE --to design|build` no Step 1. Exit 1 → o agente para, lista as 🔴 e pede resolução (resposta direta ou `/iterate`). Sem Python disponível, o agente lê a seção `Perguntas Abertas e Bloqueadores` e aplica a mesma regra. Novo status **🟡 Delegada** para decisões que o Define passa explicitamente ao Design — não bloqueia, e o Design deve fechá-la como 🟢 com referência a um `D`.

**Justificativa:** checagem determinística onde existe Python; mesma regra escrita no prompt como fallback. 🟡 resolve o caso real deste próprio DEFINE ("delegadas ao Design, não são 🔴").

**Alternativas Rejeitadas:**
1. Só instrução no prompt — rejeitada: é exatamente a disciplina que A-001 põe em dúvida
2. Hook `PreToolUse` bloqueando `Write(DESIGN_*.md)` — rejeitada: frágil, acoplado a nomes de arquivo, e bloquearia `/iterate` legítimo

**Consequências:**
- Gate só dispara com 🔴 explícito — Blackboard ausente ou override local que ignora o Blackboard **não** bloqueia (restrição do DEFINE)
- `Brainstorm→Define` e `Build→Ship` não chamam o gate

---

### Decisão 5: Ranqueamento do resumo em faixas fixas, dentro de 15 linhas

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-09-23 |

**Contexto:** DEFINE Questão 3, G5, SC-5, AT-012.

**Escolha:** orçamento total = `--max` (padrão 15), incluindo cabeçalho e rodapé. Faixas, em ordem, cada uma ordenada por data desc e depois ID:

| Faixa | Conteúdo | Teto |
|-------|----------|------|
| 0 | Cabeçalho `▶ Memória de {F} — entrando em {fase}` | 1 |
| 1 | 🔴 perguntas abertas da feature | sem teto próprio |
| 2 | 🟡 delegadas à fase que está entrando | sem teto próprio |
| 3 | ⚠ fases anteriores sem nenhuma entrada (aviso de cobertura) | 1 |
| 4 | Decisões vigentes da feature (substituídas excluídas) | 6 |
| 5 | Premissas ⏳ não validadas | 3 |
| 6 | Decisões/lições de **outras** features com domínio KB em comum | 4 |
| 7 | Rodapé `… N omitidas — ver BLACKBOARD_{F}.md / MEMORY_INDEX.md` | 1 (só se houver omissão) |

Faixas são preenchidas em ordem até o orçamento; o rodapé é reservado antes.

**Justificativa:** o que bloqueia ou foi delegado vem primeiro (é o que a fase precisa agir); a faixa 3 torna visível quando uma fase anterior não registrou nada — mitigação barata de A-001 sem subcomando novo.

**Alternativas Rejeitadas:**
1. Pontuação por relevância (TF-IDF) — rejeitada: não determinística o bastante para teste e explicação
2. Só recência — rejeitada: esconderia 🔴 antigas

**Consequências:**
- Com muitas 🔴 a faixa 4+ pode sumir; aceitável, pois a fase está bloqueada de qualquer forma

---

### Decisão 6: Domínios KB por cascata de fontes

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-09-23 |

**Contexto:** DEFINE Questão 4 e A-004 (DEFINE arquivado cita domínios só em texto).

**Escolha:** para cada feature, a primeira fonte não vazia vence: (1) linha `Domínios KB` nos Metadados do Blackboard; (2) linha `Domínios KB` da tabela "Contexto Técnico" do DEFINE; (3) varredura, em palavra inteira, dos nomes de domínio de `.claude/kb/_index.yaml` (chaves sob `domains:`) no texto do DEFINE. `Relacionada a:` (G11) cria ligação direta independente de domínio.

**Justificativa:** usa dado estruturado quando existe e ainda cobre as features arquivadas sem migração (fora do escopo).

**Alternativas Rejeitadas:**
1. Exigir domínio declarado — rejeitada: excluiria todo o `archive/` atual
2. Parser YAML de `_index.yaml` — rejeitada: sem dependência; as chaves de domínio são reconhecíveis por regex (`^  ([a-z0-9-]+):$` dentro do bloco `domains:`)

**Consequências:**
- Varredura (3) pode gerar falsos positivos para nomes genéricos (`python`, `testing`); limitado à faixa 6 com teto 4

---

### Decisão 7: `MEMORY_INDEX.md` é artefato derivado e fica fora do git

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-09-23 |

**Contexto:** G4 e AT-009. O usuário trabalha em várias worktrees em paralelo.

**Escolha:** `brief`, `gate` e `tail` calculam a partir das fontes a cada chamada; `build` escreve `.claude/sdd/MEMORY_INDEX.md` só para leitura humana/grep. O arquivo entra no `.gitignore`. Saída sem timestamp (ordem estável) → determinística.

**Justificativa:** arquivo derivado versionado gera conflito de merge a cada feature paralela; as fontes (Blackboards, archive, MEMORY.md) já estão no git.

**Alternativas Rejeitadas:**
1. Versionar o índice — rejeitada pelos conflitos entre worktrees
2. Ler sempre o índice em disco — rejeitada: poderia estar desatualizado

**Consequências:**
- Um clone novo não tem o índice até a primeira fase rodar `build` (ou o usuário rodar manualmente)

---

### Decisão 8: Protocolo único no contrato, bloco curto em cada agente

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-09-23 |

**Contexto:** 9 agentes de workflow e 10 comandos precisam do mesmo comportamento. O skill `component-model` recomenda evitar lógica duplicada fora da camada certa.

**Escolha:** regras completas em `WORKFLOW_CONTRACTS.yaml` → `living_memory` (fonte da verdade). Cada agente recebe uma seção `## Phase Memory` de ~15 linhas com só o que muda por fase (o que registrar e se chama o gate). Comandos ganham 2 passos: "Memory brief" no Step 1 e "Record to blackboard" antes do Quality Gate.

**Justificativa:** o agente precisa da instrução no próprio prompt (é o que ele lê); o detalhe comum vive num só lugar.

**Alternativas Rejeitadas:**
1. Skill novo `living-memory` — rejeitada: skill é carregado por descrição, não garantido em toda fase; e aumenta o número de skills distribuídos (hoje 10)
2. Duplicar o protocolo completo em cada agente — rejeitada: 9 cópias divergindo

**Consequências:**
- Overrides locais antigos não terão a seção; continuam funcionando (sem entradas → brief vazio, gate não bloqueia)

---

### Decisão 9: Build cria o Blackboard só se ele não existir

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-09-23 |

**Contexto:** hoje `build-agent.md` diz "Copy BLACKBOARD_TEMPLATE.md → BLACKBOARD_{FEATURE}.md" — com o Blackboard nascendo no Brainstorm/Define isso **apagaria** a trajetória.

**Escolha:** "create from template **only if missing**; otherwise extend: fill Interfaces Compartilhadas and Status dos Arquivos, keep every existing entry". Desvios do DESIGN viram `D` de fase `build` com `Substitui`.

**Justificativa:** é o ponto de maior risco de perda de dados da feature.

**Alternativas Rejeitadas:**
1. Blackboard de Build separado — rejeitada: volta ao problema original

**Consequências:**
- Teste manual no Build: rodar `/build` numa feature com Blackboard existente e verificar que as entradas anteriores permanecem

---

### Decisão 10: Hooks do plugin garantem as chamadas ao script

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita (revisão pós-E2E, substitui parte da Decisão 4) |
| **Data** | 2026-09-24 |

**Contexto:** o teste E2E da Q-009 mostrou que, com o prompt reforçado, os agentes gravam o Blackboard (4 de 4 fases), mas pulam `brief`, `gate` e `build`, e um design relatou um gate que não rodou.

**Escolha:** `scripts/memory-hook.py`, ligado em `hooks/hooks.json`: `UserPromptSubmit` injeta o `brief` quando o prompt é um comando de fase com feature; `PreToolUse(Write)` roda `gate --to design` antes de **criar** `features/DESIGN_{F}.md` e bloqueia com 🔴 ou com linhas ilegíveis; `PostToolUse(Write|Edit)` em `BLACKBOARD_*.md` roda `build` e devolve linhas ilegíveis ao agente. O prompt segue descrevendo as mesmas chamadas (fallback para Codex, Grok, dsh e o repo fonte).

**Justificativa:** o que depende de disciplina do agente virou chamada determinística onde o harness permite.

**Alternativas Rejeitadas:**
1. Manter só o prompt — rejeitada: o E2E derrubou A-001 para as chamadas ao script
2. Hook também em edições do DESIGN — rejeitada: bloquearia o `/iterate` que resolve a 🔴 (a objeção original da Decisão 4 vale só para edição, não para criação)

**Consequências:**
- O gate Design→Build segue só no prompt: o Build não escreve um arquivo único em que o hook possa se apoiar
- Todo hook sai com 0 em erro inesperado; memória quebrada nunca derruba a sessão

---

### Decisão 11: Parser aceita coluna `ID` e avisa sobre linhas ilegíveis

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita (revisão pós-E2E) |
| **Data** | 2026-09-24 |

**Contexto:** no E2E um agente escreveu `| ID |` no lugar de `| # |`; as 8 entradas foram descartadas em silêncio, o `brief` disse "sem memória" e o `gate` passaria mesmo com uma 🔴.

**Escolha:** o ID vem da coluna `#` ou `ID` e, na falta de ambas, de qualquer célula no formato `D-/A-/Q-/M-###`. Linhas com cara de entrada que não viram entrada entram em `unreadable`: `gate` e `build` saem com **2**, `brief` e `tail` mostram uma linha ⚠.

**Justificativa:** perda silenciosa de memória é o pior modo de falha desta feature.

**Alternativas Rejeitadas:**
1. Aceitar só `#` e confiar no template — rejeitada: o agente não abriu o template no E2E

**Consequências:**
- Um Blackboard fora do template agora trava o design até ser corrigido, em vez de passar vazio

---

### Decisão 12: Caminho do script em três níveis

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita (revisão pós-E2E) |
| **Data** | 2026-09-24 |

**Contexto:** o Claude Code só substitui a forma exata `${CLAUDE_PLUGIN_ROOT}` ao carregar um comando de plugin, e o Bash do agente não recebe a variável. `${CLAUDE_PLUGIN_ROOT:-.}` virava `./scripts/…` num projeto de usuário.

**Escolha:** `MI="${CLAUDE_PLUGIN_ROOT}/scripts/memory-index.py"` → `$AGENTSPEC_MEMORY_INDEX` (o SessionStart grava em `$CLAUDE_ENV_FILE`) → `plugin-extras/scripts/memory-index.py` (repo fonte).

**Justificativa:** cobre comando de plugin, agente de plugin e repo fonte sem depender de o agente descobrir o caminho sozinho.

**Alternativas Rejeitadas:**
1. Procurar o script em `~/.claude/plugins/cache` — rejeitada: acopla a um layout interno do Claude Code

**Consequências:**
- Validado no E2E: a variável chega ao Bash do agente apontando para o script do plugin

---

### Decisão 13: 🔴 só fecha com resposta do usuário; só Status/Resolução mudam na linha

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita (revisão pós-E2E) |
| **Data** | 2026-09-24 |

**Contexto:** no E2E um design viu o gate bloqueado e fechou a 🔴 sozinho, com uma premissa, antes de escrever. E o contrato dizia ao mesmo tempo "nunca edite uma entrada" e "feche a 🟡 como 🟢".

**Escolha:** uma 🔴 fecha só com a resposta do usuário ou via `/iterate`, nunca por premissa do agente, nem em execução não interativa: sem poder perguntar, o agente para e reporta. Append-only vale para o conteúdo; apenas as células `Status` e `Resolução` de Q e A mudam na própria linha.

**Justificativa:** o gate só protege se quem o destrava for o humano; e o parser já lê o status atual da linha.

**Alternativas Rejeitadas:**
1. Hook bloqueando edição 🔴→🟢 — rejeitada: bloquearia também o fechamento legítimo depois da resposta do usuário

**Consequências:**
- Regra de prompt, não verificável pelo script; revalidada no E2E (o agente parou e pediu a resposta)

---

## Manifesto de Arquivos

| # | Arquivo | Ação | Propósito | Agente | Dependências |
|---|---------|------|-----------|--------|--------------|
| 1 | `.claude/sdd/templates/BLACKBOARD_TEMPLATE.md` | Modificar | Coluna `Fase`, colunas novas no Log de Decisões, seção `## Premissas`, metadados `Domínios KB` / `Relacionada a`, status 🟡, texto "do Brainstorm ao Ship" | (direto) | Nenhuma |
| 2 | `.claude/sdd/architecture/WORKFLOW_CONTRACTS.yaml` | Modificar | Seção `living_memory` (IDs, status, fases, gate, brief, index); `blackboard.lifecycle` com seed no brainstorm/define e regra "only if missing" | (direto) | 1 |
| 3 | `plugin-extras/scripts/memory-index.py` | Criar | `collect` + `brief` / `gate` / `tail` / `build` | @python-developer | 1, 2 |
| 4 | `tests/fixtures/memory/` (árvore `sdd/` mínima: blackboard novo, legado, com 🔴, com substituição, archive com DESIGN/SHIPPED com e sem acento, `MEMORY.md`, `kb/_index.yaml` reduzido) | Criar | Fixtures determinísticas | @test-generator | 1 |
| 5 | `tests/test_memory_index.py` | Criar | Unit + CLI + teste contra o `archive/` real (SC-4) | @test-generator | 3, 4 |
| 6 | `plugin-extras/scripts/init-workspace.sh` | Modificar | `surface_memory` anexa `memory-index.py tail --n 5` quando há `.active` e `python3` | @shell-script-specialist | 3 |
| 7 | `.gitignore` | Modificar | Ignorar `.claude/sdd/MEMORY_INDEX.md` | (direto) | 3 |
| 8 | `.claude/agents/workflow/brainstorm-agent.md` | Modificar | `## Phase Memory`: criar Blackboard; registrar Q 🟢, D (escolhida + rejeitadas), cortes YAGNI | (direto) | 1, 2 |
| 9 | `.claude/agents/workflow/brainstorm-multiagent.md` | Modificar | Idem 8 + contribuições de especialistas como D com `@agente` | (direto) | 8 |
| 10 | `.claude/agents/workflow/define-agent.md` | Modificar | Brief na entrada; criar Blackboard se faltar (importar BRAINSTORM); registrar A, Q (🔴/🟡/🟢), D de mudança de escopo | (direto) | 1, 2 |
| 11 | `.claude/agents/workflow/define-multiagent.md` | Modificar | Idem 10 | (direto) | 10 |
| 12 | `.claude/agents/workflow/design-agent.md` | Modificar | Brief + gate `--to design`; D por decisão inline com `Onde Ler`; fechar 🟡; premissas ✅/❌ | (direto) | 1, 2 |
| 13 | `.claude/agents/workflow/design-multiagent.md` | Modificar | Idem 12 | (direto) | 12 |
| 14 | `.claude/agents/workflow/build-agent.md` | Modificar | Gate `--to build`; seed "only if missing" (Decisão 9); D de desvio com `Substitui`; prompt de delegação cita a coluna `Fase` | (direto) | 1, 2 |
| 15 | `.claude/agents/workflow/iterate-agent.md` | Modificar | Toda mudança aceita → D com `Substitui` (fase `iterate`) além do Histórico de Revisões | (direto) | 1, 2 |
| 16 | `.claude/agents/workflow/ship-agent.md` | Modificar | Checar entradas por fase; consolidar L no `MEMORY.md`; `build` do índice; arquivar Blackboard | (direto) | 1, 2, 3 |
| 17 | `.claude/commands/workflow/brainstorm.md` | Modificar | Step 1 brief (tema) + passo "Record to blackboard" + Quality Gate | (direto) | 8 |
| 18 | `.claude/commands/workflow/define.md` | Modificar | Idem para Define | (direto) | 10 |
| 19 | `.claude/commands/workflow/define-m.md` | Modificar | Idem | (direto) | 11 |
| 20 | `.claude/commands/workflow/design.md` | Modificar | Step 1 brief + gate; passo de registro | (direto) | 12 |
| 21 | `.claude/commands/workflow/design-m.md` | Modificar | Idem | (direto) | 13 |
| 22 | `.claude/commands/workflow/build.md` | Modificar | Gate + seed only-if-missing + desvios | (direto) | 14 |
| 23 | `.claude/commands/workflow/continue.md` | Modificar | Gap fix que diverge do DESIGN → D de desvio | (direto) | 14 |
| 24 | `.claude/commands/workflow/iterate.md` | Modificar | Registro D com `Substitui` | (direto) | 15 |
| 25 | `.claude/commands/workflow/ship.md` | Modificar | Step 8 reforçado + `memory-index.py build` + verificação de cobertura por fase | (direto) | 16 |
| 26 | `.claude/commands/workflow/work.md` | Modificar | Step 2 usa `brief --phase <fase atual>` para a orientação compacta | (direto) | 3 |
| 27 | `.claude/commands/core/memory.md` | Modificar | Referências: índice, brief e tail; relação com o Blackboard | (direto) | 3 |
| 28 | `docs/concepts/living-memory.md` | Criar | Conceito, tipos de entrada, fluxo, comandos, limites | @code-documenter | 1–3 |
| 29 | `CHANGELOG.md` | Modificar | Entrada em `[Unreleased] → Added/Changed` | (direto) | todos |
| 30 | `plugin/`, `.codex/` + `AGENTS.md`, `plugin-grok/`, `.grok/`, `plugin-dsh/assets/` | Regenerar | Via `make build` / geradores — **nunca** editar à mão | (direto) | 1–27 |

**Total de arquivos:** 29 editados/criados + bundles regenerados

---

## Justificativa de Atribuição de Agentes

| Agente | Arquivos Atribuídos | Por Que Este Agente |
|--------|---------------------|---------------------|
| @python-developer | 3 | Script stdlib com dataclasses, type hints e parsing de texto |
| @test-generator | 4, 5 | Fixtures pytest e testes de CLI |
| @shell-script-specialist | 6 | Alteração em script Bash com `set -euo pipefail` num hook |
| @code-documenter | 28 | Documento conceitual para `docs/concepts/` |
| (direto) | 1, 2, 7–27, 29, 30 | Prompts e contratos do próprio framework: o build-agent conhece o formato e não há especialista em "prompts de workflow AgentSpec" |

---

## Padrões de Código

### Padrão 1: Template do Blackboard (trechos novos/alterados)

```markdown
## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | {FEATURE_NAME} |
| **Fase** | Brainstorm / Define / Design / Build / Ship |
| **Atualizado em** | {YYYY-MM-DD} |
| **Domínios KB** | {domínio-1, domínio-2} |
| **Relacionada a** | {OUTRA_FEATURE, …} ou — |
| **DESIGN** | [DESIGN_{FEATURE}.md](DESIGN_{FEATURE}.md) |
| **Status** | 🔄 Em Andamento / ✅ Completo / ❌ Bloqueado |

## Log de Decisões

> Append-only, do Brainstorm ao Ship. Nunca edite uma decisão: registre uma nova com
> "Substitui". Guarde ponteiro + uma frase de porquê — o conteúdo vive no documento da fase.

| # | Fase | Agente | Decisão | Justificativa | Alternativa Rejeitada | Substitui | Onde Ler | Data |
|---|------|--------|---------|---------------|-----------------------|-----------|----------|------|
| D-001 | {brainstorm/define/design/build/iterate} | @{agente} | {decisão} | {1 frase} | {o que não foi feito} | — | {DESIGN_X.md#decisão-1-…} | {YYYY-MM-DD} |

## Premissas

| # | Fase | Premissa | Se Errada | Status | Onde Ler |
|---|------|----------|-----------|--------|----------|
| A-001 | define | {premissa} | {impacto} | ⏳ Não validada / ✅ Validada / ❌ Derrubada | {DEFINE_X.md#premissas} |

## Perguntas Abertas e Bloqueadores

| # | Fase | Levantado por | Pergunta / Bloqueador | Status | Resolução |
|---|------|---------------|------------------------|--------|-----------|
| Q-001 | {fase} | @{agente} | {pergunta} | 🔴 Aberto / 🟡 Delegada ao {fase} / 🟢 Resolvido | {resposta ou D-###} |
```

### Padrão 2: Núcleo do `memory-index.py`

```python
#!/usr/bin/env python3
"""AgentSpec Living Memory — phase brief, open-question gate, session tail and
a derived MEMORY_INDEX.md, computed from BLACKBOARD / archive / MEMORY.md.
Zero dependencies. Deterministic output (no timestamps, stable ordering)."""
from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path

PHASES = ("brainstorm", "define", "design", "build", "iterate", "ship")
GATED = {"design", "build"}


@dataclass(frozen=True)
class Entry:
    feature: str
    phase: str      # one of PHASES; legacy rows default to "build"
    kind: str       # D | Q | A | L | M
    id: str
    text: str
    status: str     # "open" | "delegated" | "resolved" | "pending" | "" …
    supersedes: str
    where: str      # relative path + anchor, e.g. "features/DESIGN_X.md#decisão-2-…"
    date: str       # YYYY-MM-DD or ""


def fold(s: str) -> str:
    """Lowercase, strip accents — 'Decisão' == 'Decisao', 'Lições' == 'Licoes'."""
    return "".join(c for c in unicodedata.normalize("NFKD", s)
                   if not unicodedata.combining(c)).lower().strip()


def slug(heading: str) -> str:
    """GitHub-style anchor: lowercase, keep word chars/space/hyphen, spaces → '-'."""
    return re.sub(r"[^\w\- ]", "", heading.strip().lower()).replace(" ", "-")


def parse_table(body: str) -> list[dict[str, str]]:
    """Header-driven: map folded column names → cell text. Skips separator and
    template placeholder rows ('{...}'). Unknown columns are kept but unused."""
    rows = [l for l in body.splitlines() if l.lstrip().startswith("|")]
    if len(rows) < 2:
        return []
    header = [fold(c) for c in rows[0].strip().strip("|").split("|")]
    out = []
    for line in rows[2:]:
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if not cells or cells[0].startswith("{"):
            continue
        out.append(dict(zip(header, cells + [""] * (len(header) - len(cells)))))
    return out


def question_status(cell: str) -> str:
    if "🔴" in cell:
        return "open"
    if "🟡" in cell:
        return "delegated"
    if "🟢" in cell:
        return "resolved"
    return ""


def current(entries: list[Entry]) -> list[Entry]:
    """Drop decisions superseded by a later entry of the same feature."""
    dead = {(e.feature, s.strip()) for e in entries
            for s in e.supersedes.split(",") if s.strip() not in ("", "—", "-")}
    return [e for e in entries if (e.feature, e.id) not in dead]


def gate(entries: list[Entry], feature: str) -> list[Entry]:
    return [e for e in entries if e.feature == feature and e.kind == "Q" and e.status == "open"]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="memory-index.py")
    ap.add_argument("--root", default=".claude/sdd", type=Path)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("brief"); b.add_argument("feature"); b.add_argument("--phase", required=True, choices=PHASES); b.add_argument("--max", type=int, default=15)
    g = sub.add_parser("gate"); g.add_argument("feature"); g.add_argument("--to", required=True, choices=sorted(GATED))
    t = sub.add_parser("tail"); t.add_argument("feature", nargs="?"); t.add_argument("--n", type=int, default=5)
    sub.add_parser("build")
    args = ap.parse_args(argv)
    ...  # dispatch; gate returns 1 when blocked, 0 otherwise; missing files → 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

**Fontes lidas por `collect(root)`:**

| Fonte | O que vira entrada | Fase |
|-------|--------------------|------|
| `features/BLACKBOARD_*.md`, `archive/*/BLACKBOARD_*.md` | Tabelas `Log de Decisões` (D), `Perguntas…` (Q), `Premissas` (A), `Melhorias…` (M) | coluna `Fase`; ausente → `build` |
| `archive/*/DESIGN_*.md` **sem** Blackboard | `### Decis[aã]o N: título` → D; `Onde Ler` = arquivo + `slug(título)`; data da tabela `**Data**` | `design` |
| `archive/*/SHIPPED_*.md` | bullets sob `## Li[cç][oõ]es Aprendidas` (até o próximo `## `) → L; data do nome do arquivo | `ship` |
| `MEMORY.md` | headings `## {data} — {resumo}` → L (feature `—`) | `ship` |

### Padrão 3: Bloco `## Phase Memory` (exemplo: design-agent)

```markdown
## Phase Memory

> Full rules: `WORKFLOW_CONTRACTS.yaml` → `living_memory`. Blackboard content in pt-BR.

```bash
MI="${CLAUDE_PLUGIN_ROOT:-.}/scripts/memory-index.py"
[ -f "$MI" ] || MI="plugin-extras/scripts/memory-index.py"
```

ON ENTRY
1. `python3 "$MI" gate {FEATURE} --to design` → exit 1: STOP. List the 🔴 questions and ask
   the user to resolve them (answer now or `/iterate`). Do not write DESIGN.
2. `python3 "$MI" brief {FEATURE} --phase design` → read the brief; open a pointer only when
   the topic is relevant. No Python → read the Blackboard sections directly.

ON EXIT (before the Quality Gate)
1. One `D-###` per inline decision: fase `design`, one-sentence why, rejected alternative,
   `Onde Ler` = `DESIGN_{FEATURE}.md#<anchor>`. Never copy the decision body.
2. Close every 🟡 "Delegada ao design" as 🟢 with the `D-###` that answers it.
3. Mark premissas ✅ Validada / ❌ Derrubada when the design settles them.
4. Update Metadados (`Fase`, `Atualizado em`). Run `python3 "$MI" build`.

RULES: append-only; supersede, never edit; 3–8 entries per phase; pointer + one sentence.
```

### Padrão 4: Tail no SessionStart (`init-workspace.sh`)

```bash
surface_active_feature() {
    local here mi
    here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    mi="${here}/memory-index.py"
    [[ -f ".claude/sdd/.active" && -f "$mi" ]] || return 0
    command -v python3 >/dev/null 2>&1 || return 0
    python3 "$mi" tail --n 5 2>/dev/null || true
}
```

Chamado ao final de `surface_memory` (antes do marcador `=== end memory index`), respeitando `AGENTSPEC_MEMORY_SILENT=1`. Nunca falha o hook.

### Padrão 5: Teste (importando script com hífen)

```python
import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "memory_index", REPO / "plugin-extras" / "scripts" / "memory-index.py")
mi = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mi)
FIX = Path(__file__).parent / "fixtures" / "memory" / "sdd"


def test_superseded_decision_is_not_in_brief(capsys):
    assert mi.main(["--root", str(FIX), "brief", "DEMO", "--phase", "build"]) == 0
    out = capsys.readouterr().out
    assert "D-002" not in out          # superseded by D-004
    assert len(out.splitlines()) <= 15
```

---

## Fluxo de Dados

```text
1. /brainstorm X  → BRAINSTORM_X.md + BLACKBOARD_X.md (Q🟢, D, Fase=brainstorm)
2. /define X      → brief(define) ─► DEFINE_X.md ─► +A, +Q(🔴/🟡/🟢), +D(escopo) ─► build
3. /design X      → gate(→design) ─[🔴? PARA]─► brief(design) ─► DESIGN_X.md ─► +D(Onde Ler), 🟡→🟢 ─► build
4. /build X       → gate(→build) ─► Blackboard existente é ESTENDIDO (Interfaces, Status) ─► +D desvio (Substitui)
5. /iterate, /work, /continuar → +D (Substitui) / +M
6. /ship X        → +L em MEMORY.md ─► build ─► archive/X/ (inclui BLACKBOARD_X.md)
7. Nova sessão    → SessionStart: índice MEMORY.md + tail(.active, 5)
8. Nova feature Y → brief(define) inclui D/L de X se domínios KB em comum
```

---

## Pontos de Integração

| Sistema | Tipo de Integração | Autenticação |
|---------|-------------------|--------------|
| `status-dashboard.py` | Lê as mesmas seções do Blackboard por nome — nomes preservados, sem mudança | — |
| `build-plugin.sh` (Step 2b) | Copia `plugin-extras/scripts/*` automaticamente | — |
| `generate-grok-plugin.py` | Copia `EXTRAS_SCRIPTS/*` automaticamente | — |
| `generate-codex-plugin.py`, `generate-dsh-bundle.py` | Regenerar pelos agentes/comandos alterados; `--check` na CI detecta drift | — |
| `.claude/kb/_index.yaml` | Leitura das chaves sob `domains:` (regex) | — |
| Frentes paralelas | `POST_BUILD_EVALS` pode acrescentar linha `E-###`; `LLM_PHASE_ROUTING` pode acrescentar coluna `Modelo` — o parser dirigido por cabeçalho tolera ambos | — |

---

## Estratégia de Testes

| Tipo de Teste | Escopo | Arquivos | Ferramentas | Meta de Cobertura |
|---------------|--------|----------|-------------|-------------------|
| Unitário | `fold`, `slug`, `parse_table`, `question_status`, `current`, cascata de domínios, ranking por faixas | `tests/test_memory_index.py` | pytest | ≥ 80% de linhas (SC-6) |
| CLI | `brief`/`gate`/`tail`/`build` via `main([...])`, exit codes | idem + `tests/fixtures/memory/` | pytest + `capsys` | Todos os subcomandos |
| Dados reais | `collect` sobre `.claude/sdd/archive/` | idem | pytest | SC-4 (10 D + lições dos 2 SHIPPED) |
| Regressão de geradores | Bundles incluem o script; drift | testes existentes + `make check` | pytest | Verdes (SC-9) |
| Manual (Build) | Fluxo `/brainstorm`→`/design` numa feature de teste; `/build` com Blackboard pré-existente preserva entradas | — | — | Caminho feliz + Decisão 9 |

**Ambiente:** a CI (`.github/workflows/quality-checks.yml`) roda Python 3.11 e instala só `pytest` — `sys.stdlib_module_names` (3.10+) está disponível. Cobertura (SC-6) é medida localmente com `pytest-cov` como ferramenta de dev, sem entrar na CI nem no runtime (não conta para SC-8).

**Mapa AT → teste:**

| AT | Como é verificado |
|----|-------------------|
| AT-001, AT-002, AT-003 | Manual no Build (comportamento de prompt) + fixture do resultado esperado lida pelo script |
| AT-004 | Fixture com `D-002` substituída por `D-004` → brief exclui `D-002` |
| AT-005 | Fixture com `Q-003 🔴` → `gate --to design` retorna 1 e lista Q-003 |
| AT-006 | `gate` não é chamado em `--to define` (choices não aceitam `define`) → erro de uso; brief lista a 🔴 |
| AT-007 | Brief de feature fixture com domínio `kb` inclui D do KB_EVOLUTION real; `Onde Ler` aponta arquivo existente e âncora = `slug` de heading existente |
| AT-008 | Fixture `.active` + 8 entradas → `tail --n 5` imprime as 5 mais recentes |
| AT-009 | `build` duas vezes → bytes idênticos; apagar e recriar |
| AT-010 | Fixture de Blackboard legado (colunas antigas) → sem exceção, fase `build`; `status-dashboard.py` roda na mesma fixture |
| AT-011 | Manual no Build (prompt do ship) + `collect` lê o `MEMORY.md` gerado |
| AT-012 | Fixture com 40 D vigentes → ≤ 15 linhas e rodapé "N omitidas" |
| SC-7 | `build` sobre o repo real < 2 s (`time.perf_counter`) |
| SC-8 | Teste varre `import` do script e falha se algum módulo não estiver em `sys.stdlib_module_names` |

---

## Tratamento de Erros

| Tipo de Erro | Estratégia de Tratamento | Retry? |
|-------------|-------------------------|--------|
| Blackboard/feature inexistente | `brief` imprime "sem memória registrada para {F}"; `gate` retorna 0; `tail` não imprime nada | Não |
| Arquivo ilegível (encoding/OSError) | Ignorado (mesmo padrão `read()` do dashboard); contado em `build --verbose` | Não |
| Linha de tabela malformada / placeholder `{…}` | Pulada | Não |
| `_index.yaml` ausente | Cascata de domínios pula a fonte (3) | Não |
| Argumentos inválidos | `argparse` → exit 2 | Não |
| `python3` ausente | Agentes usam o fallback de leitura manual; hook do SessionStart pula o tail | Não |

---

## Configuração

| Chave de Config | Tipo | Padrão | Descrição |
|----------------|------|--------|-----------|
| `--max` (brief) | int | `15` | Orçamento de linhas do resumo de entrada |
| `--n` (tail) | int | `5` | Entradas mostradas no SessionStart |
| `--root` | path | `.claude/sdd` | Raiz SDD (testes usam fixtures) |
| `AGENTSPEC_MEMORY_SILENT` | env | `0` | Já existente; `1` também desliga o tail |

Tetos por faixa (Decisão 5) ficam como constantes no script — YAGNI para torná-los configuráveis.

---

## Considerações de Segurança

- Script só lê dentro de `--root` e de `.claude/kb/_index.yaml`; escreve apenas `MEMORY_INDEX.md` — sem rede, sem subprocess, sem `eval`
- Conteúdo do Blackboard entra no contexto do modelo como texto: mesma superfície que os MDs de fase já têm hoje; nada de segredos deve ir para o Blackboard (regra já vale para os MDs)
- Hook do SessionStart continua não-fatal (`|| true`)

---

## Observabilidade

| Aspecto | Implementação |
|---------|---------------|
| Logging | `build --verbose` imprime contagem por fonte e linhas puladas (stderr) |
| Métricas | Faixa 3 do brief ("⚠ fase X sem entradas") expõe falhas de captura (A-001) |
| Tracing | N/A |

---

## Revisão das Premissas do DEFINE

| ID | Status após o Design | Como |
|----|----------------------|------|
| A-001 | ⏳ Mitigada, não validada | Leitura saiu do prompt para o script; faixa 3 torna visível a fase sem registro. Validação real no Build (teste manual) |
| A-002 | ⏳ Não validada | Teto 4 na faixa 6 limita ruído; `Relacionada a:` como ligação direta |
| A-003 | ✅ Validada | `fold()` + regex `Decis[aã]o` / `Li[cç][oõ]es`; teste contra o archive real |
| A-004 | ✅ Tratada | Cascata de 3 fontes (Decisão 6) |
| A-005 | ⏳ Não validada | `MEMORY_INDEX.md` é só para humanos; brief calcula direto das fontes |

**Questões delegadas pelo DEFINE:** 1 → Decisão 1 · 2 → Decisão 3 · 3 → Decisão 5 · 4 → Decisão 6 · 5 → Decisão 4. Nenhuma aberta.

---

## Histórico de Revisões

| Versão | Data | Autor | Mudanças |
|--------|------|-------|----------|
| 1.0 | 2026-09-23 | design-agent | Versão inicial; responde as 5 questões delegadas pelo DEFINE; corrige evidência do problema no DEFINE (v1.1) |
| 1.1 | 2026-09-24 | iterate (pós-E2E) | Decisões 10–13 a partir do teste E2E da Q-009: hooks do plugin, parser tolerante e ruidoso, caminho do script em três níveis, 🔴 só fecha com o usuário |
| 1.2 | 2026-09-25 | ship-agent | Shipped e archived — implementação completa, 93/93 testes passando, E2E validada. |

---

## Próximo Passo

**Pronto para:** `/build .claude/sdd/features/DESIGN_LIVING_MEMORY.md`
