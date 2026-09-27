# BRAINSTORM: Post-Build Evals

> Sessão exploratória para clarificar intenção e abordagem antes da captura de requisitos

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | POST_BUILD_EVALS |
| **Data** | 2026-09-23 |
| **Autor** | brainstorm-agent |
| **Status** | ✅ Complete (Defined) |

---

## Ideia Inicial

**Entrada Bruta:** "Não temos uma camada de evals após o build. Acredito que o projeto task-spec pode dar ideias de como fazer. Novamente aqui cabe o JEV."

**Contexto Coletado:**

- O DEFINE já exige `Critérios de Sucesso` e `Testes de Aceitação` (AT-001… em Dado/Quando/Então) — `WORKFLOW_CONTRACTS.yaml` (`define.required_sections`), `DEFINE_TEMPLATE.md:50-66`.
- O BUILD_REPORT tem a tabela "Verificação dos Testes de Aceitação" (`BUILD_REPORT_TEMPLATE.md:127-133`), mas quem preenche é o próprio build-agent, em prosa, sem reexecução independente.
- O `/ship` tem `pre_ship_checklist: [build_report_complete, all_tests_passing, no_blocking_issues, acceptance_tests_verified]` (`WORKFLOW_CONTRACTS.yaml:615-619`), mas nada reexecuta a prova — o ship-agent (haiku) confia no relatório.
- **Evidência do problema:** `archive/KB_EVOLUTION/BUILD_REPORT_KB_EVOLUTION.md` foi shipado com os 6 ATs marcados `⏳ Runtime — Validar executando…` (nenhum verificado). `archive/FRONTEND_ECOSYSTEM/BUILD_REPORT_…` nem preenche a tabela de ATs.
- Ferramentas de avaliação existentes avaliam **documentos/componentes**, não o resultado de uma feature: `scripts/judge.py` (segunda opinião cross-model, chat-completions via OpenRouter, ledger diário de orçamento), `tools/spec-linter` (L1–L4 determinístico) e `tools/spec-judge` (painel adversarial sobre agent.md/contratos). Todos compartilham o veredito `PASS | WARN | FAIL`.
- O Build já tem verificação por arquivo e completa (`build.verification`), mas ela é auto-verificação do executor.

**Referência: como o task-spec faz** (`/Users/marcoleloam/projetos/framework/task-spec`, leitura):

- Eval = função bash `eval_N()` dentro do Task-Spec, exit 0 = passa; card YAML (`id`, `check_type`, `verifies: [B-N]`, `terminal`) e um único `Exit Check` (`src/templates/task-spec.md.tpl:75-162`). Rastreabilidade bidirecional comportamento ↔ eval (`spec/task-spec-v3.md:191-201`).
- Escrito pelo autor **antes** do código (EDD — `docs/concepts/eval-driven-development.md:9`); o executor nunca escreve evals.
- **PRE-gate** (`taskspec gate`): valida forma, bloqueia evals só de existência, roda os evals e bloqueia apenas erro de bash — falha de assertion é esperada (`src/gate/safe-to-delegate.sh:149-216`).
- **POST-gate** (`taskspec accept`): reexecuta os evals por conta própria, nunca lê o relatório do executor; confere escopo do diff, handoff e selo; fail-closed com `ACCEPTANCE_FAILURE=<CODE>` (`src/accept/accept-task.sh`).
- Registro auditável `AcceptanceRecord/v1` em `.taskspec/acceptance/<task>/<attempt>.json` + digest gravado no frontmatter (`src/accept/finalize.py:86-153`).
- **Juiz LLM:** "se pode ser checado em bash, DEVE ser"; `llm_judge` exige `judge_prompt` e >50% gera warning; o task-spec **nunca executa** um juiz — só aceita recibos graduados externos (`docs/patterns/validation-card-yaml.md:189-191`, `src/gate/validate-task-spec.sh:399-428`).
- Limites admitidos: independência não é imposta pela ferramenta; HMAC é "tamper-evident, não tamper-proof".

**Referência: o que o JEV é (somente fontes documentadas)**:

- Modelo "System One" da TypeSafe: **não gera texto**; responde perguntas tipadas — Choice, Score (rubrica de 2–10 níveis) e Noul (sim/não) — com probabilidades e confiança, várias perguntas em paralelo sobre o mesmo "estado" ([docs.typesafe.ai/api](https://docs.typesafe.ai/api), [system-one](https://docs.typesafe.ai/concepts/system-one)).
- Sem justificativa, sem tool calling, sem conversa. Fraco em raciocínio multi-passo, contagem/datas, leitura literal de instruções e conteúdo adversarial ([model-jaggedness/jev-1.13](https://docs.typesafe.ai/model-jaggedness/jev-1.13)).
- Contexto 64k (TypeSafe) / 32k (OpenRouter); ~US$ 0,042 por milhão de tokens de entrada, saída gratuita ([models](https://docs.typesafe.ai/models)).
- OpenRouter: `typesafe/jev-1.13` / `~typesafe/jev-latest`, modalidade `text->decisions`; **não** é chat-completions — endpoint de decisões em alpha ([blog OpenRouter](https://openrouter.ai/blog/insights/what-is-jev/)).
- Uso mais próximo de "juiz" documentado: decompor o julgamento em perguntas pequenas e escalar incerteza para modelo de raciocínio ou humano (cookbooks `sde_cascade`, `citation_check`).
- `jev-gateway` (vinilana, não oficial) usa o Jev para **roteamento de tool calls**, não para julgar; benchmark de 120 sessões com resultados mistos e amostra pequena.
- "OMP" = CLI `omp` (oh-my-pi) — confirmado pelo usuário. Tem `judge()` apoiado no Jev e a regra "Judge output is evidence, not truth".

**Contexto Técnico Observado (para o Define):**

| Aspecto | Observação | Implicação |
|---------|------------|------------|
| Localização Provável | `.claude/commands/workflow/`, `.claude/agents/workflow/`, `.claude/sdd/templates/`, `scripts/`, `tests/` | Nova fase `/eval` + agente + runner Python stdlib + template de relatório |
| Contratos | `WORKFLOW_CONTRACTS.yaml` (build, ship, status transitions) | Nova fase entre build e ship; `pre_ship_checklist` passa a exigir recibo |
| Templates afetados | DESIGN (nova seção `## Evals`), BUILD_REPORT (aponta para EVAL_REPORT), novo `EVAL_REPORT_TEMPLATE.md` | Mudança de formato, compatível com features antigas |
| Domínios KB Relevantes | `testing`, `genai`, `prompt-engineering`, `python` | Padrões de pytest para o runner, LLM-as-judge |
| Distribuição | `build-plugin.sh`, geradores Codex/Grok/DSH | Comando e agente novos precisam entrar nos bundles |
| IaC | N/A | — |

---

## Perguntas de Descoberta e Respostas

| # | Pergunta | Resposta | Impacto |
|---|----------|----------|---------|
| 1 | Papel principal da camada de evals entre `/build` e `/ship`? | **Gate bloqueante** | `/ship` recusa sem prova reexecutada independentemente |
| 2 | Onde e em que formato o eval nasce? | Usuário pensava em pós-build; após a distinção **escrever vs. rodar**, escolheu o **híbrido** | Evals-contrato no DESIGN (antes do código, congelados); eval-agent pós-build só acrescenta |
| 3 | Papel do JEV? | **Juiz graduado + escalonamento** | JEV só em critérios subjetivos, com rubrica decomposta; confiança baixa → `/judge` ou humano |
| 4 | Como o gate é executado no fluxo? | **Novo `/eval` + runner determinístico** | Fase nova com eval-agent sem permissão de editar código e `scripts/eval_runner.py` |
| 5 | Amostras disponíveis? | **Features já shipadas** | `KB_EVOLUTION` e `FRONTEND_ECOSYSTEM` viram fixtures e base de calibração |
| 6 | Como tratar ATs de runtime (agente, MCP, cloud)? | **Classificar + recibo humano** | `check_type: deterministic \| graded \| human`; `⏳` bloqueia; só passa com waiver nomeado |
| 7 | "OMP" é o oh-my-pi? | **Sim** | Registrado como referência; o AgentSpec acessa o Jev direto pelo OpenRouter, sem depender do `omp` |

---

## Inventário de Dados de Exemplo

| Tipo | Localização | Quantidade | Notas |
|------|-------------|------------|-------|
| Features shipadas (DEFINE/DESIGN/BUILD_REPORT) | `.claude/sdd/archive/KB_EVOLUTION/`, `.claude/sdd/archive/FRONTEND_ECOSYSTEM/` | 2 | 6 + 5 ATs; mistura de ATs determinísticos (preservação de estrutura, `_index.yaml`) e de runtime (execução de comando com Context7) |
| Exemplo negativo real | `archive/KB_EVOLUTION/BUILD_REPORT_KB_EVOLUTION.md` (tabela de ATs) | 1 | Shipado com todos os ATs `⏳` — caso que o gate deve bloquear |
| Formato de eval de referência | `task-spec/tasks/done/T-20260817-demo-doctor-host-floor.md:50-62` (pequeno), `T-20260818-task-spec-skills-pack.md:97-163` (completo) | 2 | Card YAML + `eval_N()` + Exit Check |
| Recibo de referência | `task-spec/.taskspec/acceptance/*/*.json` | vários | Shape de `AcceptanceRecord/v1` |
| Código relacionado | `scripts/judge.py`, `tools/spec-judge/` | 2 | Ledger de orçamento, `OPENROUTER_API_KEY`, veredito `PASS/WARN/FAIL` para reaproveitar |

**Como os exemplos serão usados:**

- Retroconverter os ATs das 2 features em evals (deterministic/graded/human) para testar o formato da seção `## Evals`.
- Fixtures do `tests/` do runner: um caso que passa, um que falha, um só de existência, um `⏳` sem waiver.
- Calibração do JEV: medir concordância JEV × `/judge` × usuário nos ATs graduados antes de deixar o JEV decidir.

---

## Abordagens Exploradas

### Abordagem A: gate de aceitação nativo, "task-spec-lite" ⭐ Recomendada

**Descrição:** o DESIGN ganha uma seção `## Evals` (card YAML + `eval_N()` bash + Exit Check, com digest congelado). No início do `/build`, uma checagem PRE confere que os evals rodam e ainda falham. Uma nova fase `/eval` (eval-agent sem Edit em código + `scripts/eval_runner.py` stdlib) reexecuta os evals, chama o JEV para os `graded`, coleta recibos humanos e grava `EVAL_REPORT_{F}.md` + `EVAL_{F}.json`. O `/ship` exige recibo PASS vinculado ao HEAD e ao digest do DESIGN.

**Prós:**

- Formato mora nos documentos que o usuário já usa; zero dependência externa.
- Preserva as duas ideias centrais do task-spec: eval escrito antes, prova reexecutada por quem não construiu.
- Veredito reprodutível (exit codes + recibo), não a palavra de um LLM.

**Contras:**

- Um script novo para manter (runner) e um cliente novo (JEV).
- DESIGN um pouco mais pesado.

**Por que Recomendada:** fecha exatamente o buraco observado (ATs `⏳` shipados) com o menor custo de adoção, sem trazer a cerimônia de HMAC/tiers do task-spec.

---

### Abordagem B: adotar o task-spec como motor

**Descrição:** o DESIGN geraria Task-Specs e o gate chamaria `taskspec gate/run/accept`.

**Prós:**

- HMAC, mutation audit, holdouts e registro já prontos e testados.

**Contras:**

- Todo usuário do plugin precisaria instalar task-spec + shellcheck.
- Contrato duplicado (AT no DEFINE + Task-Spec).
- Cerimônia de tiers/HMAC desproporcional para o SDD do AgentSpec.

---

### Abordagem C: eval-agent só por prompt

**Descrição:** um agente lê o DEFINE, roda testes via Bash e escreve o relatório, sem runner.

**Prós:**

- Quase zero código.

**Contras:**

- Veredito continua sendo afirmação de um LLM; sem reprodutibilidade nem recibo verificável — é o mesmo mecanismo que deixou o `KB_EVOLUTION` sair com `⏳`.

---

## Abordagem Selecionada

| Atributo | Valor |
|----------|-------|
| **Escolhida** | Abordagem A — task-spec-lite nativo |
| **Confirmação do Usuário** | 2026-09-23 |
| **Justificativa** | Gate bloqueante reprodutível sem dependência externa, alinhado ao formato atual dos documentos SDD |

---

## Principais Decisões Tomadas

| # | Decisão | Justificativa | Alternativa Rejeitada |
|---|---------|---------------|----------------------|
| 1 | Evals são **gate bloqueante** do `/ship` | Relatório consultivo já existe (BUILD_REPORT) e não impediu ship sem verificação | Relatório consultivo; gate + métricas históricas (histórico vai para `LIVING_MEMORY`) |
| 2 | **Escrever antes, rodar depois** (híbrido): evals-contrato no DESIGN, congelados por digest; eval-agent pós-build só **acrescenta** | Eval escrito vendo o código tende a confirmar a implementação; escrever antes permite provar que o eval falha sem código | Tudo pós-build (perde independência); tudo no DESIGN (rígido quando o comando exato só existe após o código) |
| 3 | PRE-check no início do `/build`: evals rodam sem erro de bash **e falham** | Barato e pega evals triviais (`test -f`) — equivalente ao broken-logic guard do task-spec | Gold-sanity no commit base (adiado) |
| 4 | Nova fase **`/eval`** com eval-agent sem permissão de editar código + runner determinístico | Separa quem constrói de quem aceita; permite loop `/eval` FAIL → `/continuar` | Embutir no `/ship` (mistura avaliar com arquivar); passo final do `/build` (autoavaliação) |
| 5 | `check_type: deterministic \| graded \| human` por eval; **determinístico primeiro** | Doutrina do task-spec: se dá para checar em bash, deve ser | Tudo via LLM |
| 6 | **JEV como juiz graduado** só para `graded`, rubrica decomposta em 2–5 perguntas Noul/Score; confiança baixa escala para `/judge` ou humano; JEV nunca reprova sozinho um AT determinístico | É o uso que a TypeSafe documenta (decisões tipadas pequenas + escalonamento); JEV não justifica e é fraco em multi-passo | JEV como juiz holístico; JEV fora do MVP |
| 7 | Teto de 50% de evals `graded` por feature (warning) | Critério subjetivo demais indica DEFINE/DESIGN mal especificado | Sem teto |
| 8 | ATs de runtime → `human` com recibo `{dono, data, evidência}`; `⏳` **bloqueia**; só passa com waiver `{supervisor, motivo}` registrado | Torna explícito e atribuído o que hoje é silencioso | Evals agênticos headless (adiado) |
| 9 | Recibo `EVAL_{F}.json` vinculado a `commit` + `design_digest`; `/ship` recusa se não baterem com o estado atual | Impede reaproveitar um PASS antigo após mudança no código ou no contrato | HMAC/assinatura (adiado) |
| 10 | Cliente JEV novo (`scripts/jev_client.py`) no endpoint de decisões do OpenRouter, reaproveitando `OPENROUTER_API_KEY` e o ledger de orçamento do `judge.py` | O Jev não responde em chat-completions; manter uma chave e um orçamento | Estender `judge.py` (protocolo diferente); depender do `omp` |

---

## Features Removidas (YAGNI)

| Feature Sugerida | Motivo da Remoção | Pode Adicionar Depois? |
|------------------|-------------------|----------------------|
| HMAC / assinatura do recibo | Digest do DESIGN + commit já pegam drift acidental; nem no task-spec o HMAC é barreira de segurança | Sim |
| Mutation audit e gold-sanity no commit base | O PRE-check ("tem que falhar antes do build") cobre o principal com custo zero | Sim |
| Evals agênticos headless (`claude -p "/cmd"` em worktree descartável) | Caros, lentos e instáveis; runtime fica com recibo humano no MVP | Sim |
| Holdouts (evals ocultos do executor) | Cerimônia alta para uso individual | Talvez |
| Histórico/tendências de evals entre features | Escopo da frente `LIVING_MEMORY` | Lá |
| Checagem de escopo do diff (arquivos fora do manifesto) | Útil, mas é outra camada; o manifesto do DESIGN já existe | Sim |
| Tiers de confiança (Tier 1/2/3) do task-spec | Substituídos por waiver nomeado, mais simples | Talvez |

---

## Validações Incrementais

| Seção | Apresentada | Feedback do Usuário | Ajustada? |
|-------|-------------|---------------------|-----------|
| Origem do eval (escrever vs. rodar) | ✅ | Pediu explicação de por que DEFINE → DESIGN; após a explicação escolheu o híbrido | Sim — virou híbrido |
| Fluxo do MVP + cortes YAGNI | ✅ | "Sim, fluxo e cortes ok" | Não |
| JEV, recibo e fronteiras | ✅ | "Sim, está certo" | Não |

---

## Fluxo Proposto (MVP)

```text
DEFINE (AT-xxx) ─► DESIGN ## Evals (card + eval_N + Exit Check, digest congelado)
                       │
/build ── PRE: eval_runner --pre → roda, sem erro de bash, e FALHA (senão avisa "já passa?")
                       │
/eval  ── eval-agent (sem Edit no código)
          ├─ eval_runner --post: deterministic → exit code por AT
          ├─ graded → JEV (Noul/Score); confiança < limiar → /judge ou humano
          ├─ human → recibo {dono, data, evidência}
          ├─ complementares: só ACRESCENTA (contrato intocado — digest confere)
          └─ grava EVAL_REPORT_{F}.md + EVAL_{F}.json
                       │
          FAIL ─► /continuar (volta ao build com os ATs que falharam)
                       │
/ship  ── exige EVAL_{F}.json PASS, commit == HEAD, design_digest == DESIGN atual
          ⏳ só com waiver {supervisor, motivo} registrado no recibo
```

**Esboço da seção `## Evals` no DESIGN:**

```yaml
evals:
  - id: eval_1
    verifies: [AT-001]
    check_type: deterministic
    description: "_index.yaml tem mcp_validated com a data de hoje após o ingest"
  - id: eval_2
    verifies: [AT-003]
    check_type: graded
    rubric:
      - {type: noul, question: "O relatório lista a API deprecada como issue 'stale'?"}
      - {type: noul, question: "A issue cita arquivo e linha?"}
  - id: eval_3
    verifies: [AT-002]
    check_type: human
    owner: "{nome}"
exit_check: "eval_1 && eval_2 && eval_3"
```

```bash
eval_1() {
  grep -A3 "^  dbt:" .claude/kb/_index.yaml | grep -q "mcp_validated: $(date +%Y-%m-%d)"
}
```

**Esboço do recibo `EVAL_{F}.json`:**

```json
{
  "feature": "KB_EVOLUTION",
  "commit": "<sha>",
  "design_digest": "sha256:<...>",
  "evaluated_at": "<UTC>",
  "evaluator": "eval-agent",
  "results": [
    {"at": "AT-001", "eval_id": "eval_1", "check_type": "deterministic", "status": "pass", "evidence": "exit 0"},
    {"at": "AT-003", "eval_id": "eval_2", "check_type": "graded", "status": "pass", "jev": {"model": "typesafe/jev-1.13", "answers": [0.94, 0.88], "confidence": 0.91}},
    {"at": "AT-002", "eval_id": "eval_3", "check_type": "human", "status": "waived"}
  ],
  "waivers": [{"at": "AT-002", "supervisor": "{nome}", "reason": "{motivo}"}],
  "verdict": "PASS"
}
```

---

## Dependências e Fronteiras com as Outras Frentes

| Frente | Onde encosta | Divisão de escopo |
|--------|--------------|-------------------|
| `LIVING_MEMORY` | Histórico de evals entre features e fases | Esta frente **produz** `EVAL_{F}.json` com formato estável e documentado; `LIVING_MEMORY` **consome e indexa**. Tendências, métricas e recall ficam lá. |
| `JEV_AGENT_SELECTION` | Ambas usam o Jev | Lá o Jev **roteia** (escolhe agentes por fase); aqui o Jev **julga** critérios graduados. Compartilham apenas o cliente `scripts/jev_client.py` — quem chegar primeiro ao build cria, a outra reaproveita. |
| `LLM_PHASE_ROUTING` | Modelo do eval-agent e do fallback `/judge` | Esta frente não fixa modelos; declara os papéis (`eval-agent`, `judge-fallback`) para o roteamento de fases decidir. |
| `KB_CONTEXT7_REFRESH` | Nenhuma sobreposição direta | Só se toca quando uma feature de KB for avaliada (os ATs do `KB_EVOLUTION` são fixtures aqui, não escopo). |

---

## Requisitos Sugeridos para /define

### Declaração do Problema (Rascunho)

Features do AgentSpec chegam ao `/ship` sem que os testes de aceitação do DEFINE tenham sido reexecutados por alguém além do próprio build — o `KB_EVOLUTION` foi arquivado com os 6 ATs como `⏳ não verificado`.

### Usuários-Alvo (Rascunho)

| Usuário | Dor |
|---------|-----|
| Dono da feature (usuário do AgentSpec) | Não tem prova reprodutível de que o que foi pedido foi entregue; confia no relato do build-agent |
| build-agent | Não tem alvo executável explícito durante o build; descobre o critério de aceitação só no fim |
| ship-agent | Só consegue checar a existência de artefatos, não a verdade do que eles afirmam |

### Critérios de Sucesso (Rascunho)

- [ ] `/ship` recusa (exit ≠ 0 / mensagem explícita) 100% das features cujo `EVAL_{F}.json` não existe, tem `verdict != PASS`, ou tem `commit`/`design_digest` diferentes do estado atual.
- [ ] Todo AT do DEFINE tem ≥ 1 eval com `verifies` apontando para ele; o validador reporta ATs órfãos e evals sem AT.
- [ ] O PRE-check no `/build` bloqueia evals com erro de bash e avisa quando algum eval já passa antes do build.
- [ ] Retroconversão dos ATs de `KB_EVOLUTION` e `FRONTEND_ECOSYSTEM` produz evals classificados e o runner roda nos dois sem erro de execução.
- [ ] Nenhum AT `⏳`/sem resultado passa pelo gate sem waiver `{supervisor, motivo}` no recibo.
- [ ] O eval-agent não consegue alterar evals-contrato (digest do bloco `## Evals` original confere após o `/eval`).
- [ ] Evals `graded` chamam o JEV com rubrica decomposta, registram respostas e confiança no recibo, e escalam abaixo do limiar; custo por feature fica dentro do ledger de orçamento existente.
- [ ] Features antigas sem seção `## Evals` continuam shipáveis via caminho legado explícito (waiver global registrado), sem quebrar o fluxo.

### Restrições Identificadas

- Runner em Python stdlib (mesmo padrão de `scripts/judge.py`); sem dependência do binário task-spec.
- Acesso ao Jev só via OpenRouter com `OPENROUTER_API_KEY`; endpoint de decisões está em **alpha**, e há dois caminhos conflitantes nas páginas do OpenRouter (`/api/alpha/decisions` vs `/api/v1/systemone`).
- Estado enviado ao Jev precisa caber em 32k tokens (limite OpenRouter).
- Documentos gerados em pt-BR; agentes, comandos e contratos em inglês.
- Comando e agente novos precisam entrar no `build-plugin.sh` e nos geradores Codex/Grok/DSH.

### Fora do Escopo (Confirmado)

- HMAC/assinatura, tiers, holdouts, mutation audit, gold-sanity.
- Evals agênticos headless.
- Histórico e tendências de evals (→ `LIVING_MEMORY`).
- Seleção de agentes via Jev (→ `JEV_AGENT_SELECTION`).
- Escolha de modelos por fase (→ `LLM_PHASE_ROUTING`).
- Checagem de escopo do diff contra o manifesto.

### Perguntas em Aberto (para o Define/Design)

| # | Pergunta | Por que importa |
|---|----------|-----------------|
| Q1 | Qual caminho do OpenRouter funciona de fato para o Jev (`/api/alpha/decisions` ou `/api/v1/systemone`)? | Fontes do próprio OpenRouter divergem; testar com chave real antes do Design fixar o cliente |
| Q2 | Qual a acurácia do Jev julgando código/relatórios? | Não há benchmark publicado para esse uso; calibração com as 2 features shipadas decide se o JEV pode reprovar ou só escalar |
| Q3 | Limiares iniciais de score e confiança do JEV? | Definir no DEFINE como números calibráveis |
| Q4 | Como congelar o bloco `## Evals` (digest de quê: só o bloco, ou DEFINE AT + bloco)? | Determina quando uma mudança via `/iterate` invalida o recibo |
| Q5 | O `/iterate` que altera ATs deve invalidar automaticamente o recibo e reabrir o `/eval`? | Cascata de contratos |
| Q6 | Onde ficam `EVAL_REPORT_{F}.md` e `EVAL_{F}.json` — `reports/` ou `features/`? E o ship-agent arquiva os dois? | Consistência com BUILD_REPORT e com `archive_contents` |
| Q7 | O eval-agent roda em sessão separada do build ou basta ser outro agente sem Edit? | Independência não é imposta nem pelo task-spec; decidir o nível mínimo aceitável |
| Q8 | Rate limit / disponibilidade do Jev ("pode mudar sem aviso", endpoint alpha): qual o fallback quando o Jev está fora? | Gate não pode travar por indisponibilidade do juiz — provável fallback para `/judge` ou humano |

---

## Resumo da Sessão

| Métrica | Valor |
|---------|-------|
| Perguntas Feitas | 7 (incl. amostras e confirmação do OMP) |
| Abordagens Exploradas | 3 |
| Features Removidas (YAGNI) | 7 |
| Validações Concluídas | 3 |
| Duração | ~1 sessão |

---

## Próximo Passo

**Pronto para:** `/define .claude/sdd/features/BRAINSTORM_POST_BUILD_EVALS.md`
