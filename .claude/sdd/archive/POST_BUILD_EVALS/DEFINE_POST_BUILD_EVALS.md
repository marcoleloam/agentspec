# DEFINE: Post-Build Evals

> Gate de aceitação executável entre `/build` e `/ship`: evals escritos no DESIGN antes do código, reexecutados por um agente independente, com JEV como juiz dos critérios subjetivos e recibo auditável exigido pelo `/ship`.

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | POST_BUILD_EVALS |
| **Data** | 2026-09-23 |
| **Autor** | define-agent |
| **Status** | ✅ Shipped |
| **Clarity Score** | 14/15 |
| **Origem** | `.claude/sdd/features/BRAINSTORM_POST_BUILD_EVALS.md` |

---

## Declaração do Problema

Features do AgentSpec chegam ao `/ship` sem que os Testes de Aceitação do DEFINE tenham sido reexecutados por alguém além do próprio build-agent: a tabela de ATs do BUILD_REPORT é preenchida pelo executor, em prosa, e o `pre_ship_checklist` (`acceptance_tests_verified`) só confere que o relatório existe. Evidência: `archive/KB_EVOLUTION/BUILD_REPORT_KB_EVOLUTION.md` foi arquivado com os 6 ATs como `⏳ Runtime — Validar executando…`, e `archive/FRONTEND_ECOSYSTEM/` não tem a tabela de ATs preenchida.

---

## Usuários-Alvo

| Usuário | Papel | Dor |
|---------|-------|-----|
| Dono da feature | Pessoa que usa o AgentSpec para entregar uma feature (ex.: engenheiro de dados) | Não tem prova reprodutível de que o que pediu foi entregue; depende do relato do build-agent |
| build-agent | Executor da Fase 3 | Não tem alvo executável durante o build; o critério de aceitação só é cobrado (em prosa) no final |
| ship-agent | Arquivador da Fase 4 | Só confere a existência de artefatos, não a verdade do que eles afirmam |
| Mantenedor do AgentSpec | Evolui o framework | Não consegue distinguir features realmente verificadas de features "verificadas no papel" no `archive/` |

---

## Objetivos

| Prioridade | Objetivo |
|------------|----------|
| **MUST** | O DESIGN declara uma seção `## Evals` com ≥ 1 eval por AT do DEFINE, cada um com `id`, `verifies`, `check_type` (`deterministic \| graded \| human`) e um `exit_check` único |
| **MUST** | Os evals-contrato são congelados por digest; nenhuma fase posterior ao DESIGN pode alterá-los ou removê-los sem passar por `/iterate` |
| **MUST** | Checagem PRE no início do `/build`: evals `deterministic` rodam sem erro de bash e falham; erro de bash bloqueia; eval que já passa gera aviso |
| **MUST** | Nova fase `/eval` (comando + `eval-agent` sem permissão de editar código) que reexecuta os evals através de um runner determinístico e produz `EVAL_REPORT_{FEATURE}.md` + recibo `EVAL_{FEATURE}.json` |
| **MUST** | O `/ship` recusa quando o recibo não existe, tem `verdict != PASS`, ou tem `commit`/`design_digest` diferentes do estado atual |
| **MUST** | AT sem resultado (`⏳`/pendente) bloqueia o gate; só passa com waiver `{supervisor, motivo}` registrado no recibo |
| **MUST** | Evals `human` exigem recibo `{dono, data, evidência}` |
| **SHOULD** | Evals `graded` são julgados pelo JEV (`typesafe/jev-1.13` via OpenRouter) com rubrica decomposta em 2–5 perguntas Noul/Score; abaixo do limiar de confiança, escalam para `/judge` ou humano |
| **SHOULD** | O JEV só pode decidir um AT após um recibo de calibração mostrar concordância mínima com a referência; antes disso, `graded` é decidido por `/judge` ou humano, e o JEV fica registrado como consultivo |
| **SHOULD** | O `eval-agent` pode acrescentar evals complementares (bordas, regressão) marcados como `origin: complementary`; o gate exige contrato + complementares |
| **SHOULD** | Quando o gate falha, o fluxo aponta para `/continuar` com a lista de ATs reprovados |
| **SHOULD** | Validador de rastreabilidade: reporta ATs órfãos (sem eval) e evals sem AT; avisa quando > 50% dos evals são `graded` ou quando um eval só checa existência de arquivo |
| **COULD** | Retroconverter os ATs de `KB_EVOLUTION` e `FRONTEND_ECOSYSTEM` em seções `## Evals` de exemplo, versionadas como fixtures/documentação |
| **COULD** | `/status` exibe o estado do gate (sem recibo / FAIL / PASS / PASS com waivers) da feature ativa |

---

## Critérios de Sucesso

- [ ] **100%** das tentativas de `/ship` são recusadas nos 4 casos: recibo ausente; `verdict != PASS`; `commit` ≠ `HEAD`; `design_digest` ≠ digest atual do bloco `## Evals` — verificado por 4 testes automatizados.
- [ ] **100%** dos ATs do DEFINE têm ≥ 1 eval com `verifies` apontando para eles; o validador sai com código ≠ 0 e lista cada AT órfão e cada eval sem AT.
- [ ] O PRE-check detecta **100%** dos casos de fixture com erro de bash (sintaxe, variável não definida, comando inexistente) e emite aviso em **100%** dos casos de fixture em que o eval já passa antes do build.
- [ ] **0** ATs `⏳`/pendentes passam pelo gate sem waiver `{supervisor, motivo}` no recibo.
- [ ] Após o `/eval`, o digest do bloco de evals-contrato é **idêntico** ao registrado no DESIGN em 100% dos casos de teste, inclusive no caso de teste em que o agente tenta alterá-lo.
- [ ] O runner executa as seções `## Evals` retroconvertidas de **2** features shipadas (`KB_EVOLUTION`, `FRONTEND_ECOSYSTEM`) sem erro de execução.
- [ ] Cada eval `graded` registra no recibo o modelo, as respostas por pergunta e a confiança; custo do JEV por feature ≤ **US$ 0,01** no conjunto de fixtures e sempre dentro do ledger diário existente.
- [ ] Indisponibilidade do JEV (timeout, 4xx/5xx, orçamento esgotado) **nunca** produz PASS: o eval vira `escalated` e segue para `/judge` ou humano — verificado por teste com cliente simulado.
- [ ] A suíte `tests/` nova roda **offline** (JEV e `/judge` simulados), sem `OPENROUTER_API_KEY`, e passa em CI.
- [ ] Features sem seção `## Evals` (legado) continuam shipáveis apenas por um waiver global explícito registrado no recibo — **0** ships legados silenciosos.

---

## Testes de Aceitação

| ID | Cenário | Dado | Quando | Então |
|----|---------|------|--------|-------|
| AT-001 | Caminho feliz | DESIGN com `## Evals` (deterministic), build concluído e evals passando | `/eval` e depois `/ship` | `EVAL_{F}.json` com `verdict: PASS`, `commit == HEAD` e `design_digest` correto; `/ship` arquiva normalmente e inclui `EVAL_REPORT_{F}.md` + `EVAL_{F}.json` no `archive/` |
| AT-002 | Eval reprovado | Um eval `deterministic` retorna exit ≠ 0 após o build | `/eval` | Recibo com `verdict: FAIL` e o AT marcado `fail` com stdout/stderr como evidência; o relatório indica `/continuar` com os ATs reprovados; `/ship` recusa |
| AT-003 | Ship sem recibo | Build concluído, `/eval` nunca executado | `/ship` | Recusa com mensagem explícita indicando `/eval`; nada é movido para `archive/` |
| AT-004 | Recibo obsoleto por código | Recibo PASS gerado no commit A; novo commit B altera código | `/ship` | Recusa por `commit` ≠ `HEAD`; pede novo `/eval` |
| AT-005 | Recibo obsoleto por contrato | Recibo PASS; `/iterate` altera um AT e o bloco `## Evals` | `/ship` | Recusa por `design_digest` divergente; pede novo `/eval` |
| AT-006 | PRE-check com erro de bash | Eval com erro de sintaxe ou comando inexistente | Início do `/build` | Build bloqueado antes de gerar código, com o eval e a linha do erro apontados |
| AT-007 | PRE-check com eval trivial | Eval que já passa sem nenhuma implementação | Início do `/build` | Aviso "eval já passa antes do build — verifique se discrimina"; build prossegue |
| AT-008 | AT órfão | DEFINE com AT-004 sem nenhum eval com `verifies: [AT-004]` | Validação do DESIGN / início do `/eval` | Falha listando AT-004 como órfão |
| AT-009 | Tentativa de alterar contrato | O eval-agent edita ou remove um eval-contrato durante o `/eval` | Fim do `/eval` | Digest diverge; recibo `verdict: FAIL` com motivo `CONTRACT_TAMPERED`; evals `complementary` acrescentados são aceitos |
| AT-010 | AT pendente sem waiver | Eval `human` sem recibo humano registrado | `/eval` | AT fica `pending`; `verdict: FAIL`; `/ship` recusa |
| AT-011 | AT pendente com waiver | Mesmo caso, com waiver `{supervisor, motivo}` registrado | `/eval` e `/ship` | AT `waived`; `verdict: PASS` com `waivers[]` preenchido; ship prossegue e o SHIPPED lista o waiver |
| AT-012 | Graded com confiança alta (JEV calibrado) | Eval `graded` com rubrica de 2 perguntas; calibração aprovada; JEV acima dos limiares | `/eval` | AT `pass`; recibo registra modelo, respostas e confiança |
| AT-013 | Graded com confiança baixa | JEV abaixo do limiar de confiança | `/eval` | AT `escalated`; decisão final vem de `/judge` ou humano e fica registrada no recibo com o JEV como consultivo |
| AT-014 | JEV indisponível | Endpoint do JEV retorna erro, timeout ou orçamento esgotado | `/eval` | Nenhum PASS pelo JEV; AT `escalated` com o motivo; o gate não trava por erro de rede |
| AT-015 | JEV sem calibração | Nenhum recibo de calibração aprovado | `/eval` com evals `graded` | JEV roda apenas como consultivo; decisão vem de `/judge` ou humano |
| AT-016 | Feature legada | DESIGN antigo sem seção `## Evals` | `/ship` | Recusa, a menos que haja waiver global `{supervisor, motivo}`; com waiver, ship prossegue e registra `legacy_waiver` no recibo |
| AT-017 | Excesso de graded | DESIGN com 4 evals, 3 `graded` | Validação do DESIGN | Aviso (não bloqueio) "> 50% graded — critérios subjetivos demais" |

---

## Fora do Escopo

- HMAC, assinatura criptográfica e tiers de confiança no recibo.
- Mutation audit e gold-sanity (rodar os evals no commit base).
- Evals agênticos headless (disparar `claude -p "/cmd"` em worktree descartável).
- Holdouts (evals ocultos do executor).
- Checagem de escopo do diff contra o manifesto do DESIGN.
- Histórico, tendências e métricas de evals entre features — pertence a `LIVING_MEMORY` (esta feature só garante formato estável do recibo).
- Seleção de agentes via JEV — pertence a `JEV_AGENT_SELECTION`.
- Escolha de modelos por fase (inclusive do `eval-agent` e do fallback `/judge`) — pertence a `LLM_PHASE_ROUTING`.
- Mudanças na atualização de KBs — pertence a `KB_CONTEXT7_REFRESH`.
- Dependência do binário task-spec ou do CLI `omp` (oh-my-pi).
- Retroativar recibos para features já arquivadas (a retroconversão é só fixture/exemplo).

---

## Restrições

| Tipo | Restrição | Impacto |
|------|-----------|---------|
| Técnica | Runner e cliente JEV em Python stdlib, mesmo padrão de `scripts/judge.py` | Sem dependências novas para quem usa o plugin |
| Técnica | O JEV não fala chat-completions. O acesso é pelo endpoint de decisões do OpenRouter; os dois caminhos documentados (`/api/v1/systemone` e `/api/alpha/decisions`) responderam no teste de 2026-09-23, mas a página do OpenRouter ainda marca o endpoint como alpha | Cliente novo e isolado atrás de uma interface, com `/api/v1/systemone` primário e `/api/alpha/decisions` como fallback |
| Técnica | O `state` enviado ao JEV precisa ser um objeto com campos nomeados, referenciados nas perguntas | O schema do eval `graded` declara os campos do estado, e não um texto livre |
| Técnica | Estado enviado ao JEV ≤ 32k tokens (limite no OpenRouter) | Evals `graded` avaliam artefatos recortados, nunca o repositório inteiro |
| Técnica | O JEV não justifica, é fraco em raciocínio multi-passo e em conteúdo adversarial | JEV nunca decide AT determinístico nem é o único juiz sem calibração |
| Técnica | Reaproveitar `OPENROUTER_API_KEY` e o ledger `.claude/storage/judge-ledger.jsonl` do `judge.py` | Um orçamento e uma chave para `/judge` e JEV |
| Idioma | Agentes, comandos e contratos em inglês; `EVAL_REPORT` em pt-BR | Segue a política de idioma do `CLAUDE.md` |
| Distribuição | Comando e agente novos precisam entrar em `build-plugin.sh` e nos geradores Codex/Grok/DSH, e passar no drift check de CI | Tarefas de empacotamento no manifesto do DESIGN |
| Compatibilidade | Features em andamento sem `## Evals` não podem quebrar | Caminho legado via waiver global explícito (AT-016) |
| Recurso | Uso individual, sem infraestrutura nova | Tudo local, arquivos no repositório |

---

## Contexto Técnico

| Aspecto | Valor | Notas |
|---------|-------|-------|
| **Localização de Deploy** | `.claude/commands/workflow/eval.md`, `.claude/agents/workflow/eval-agent.md`, `scripts/eval_runner.py`, `scripts/jev_client.py`, `.claude/sdd/templates/EVAL_REPORT_TEMPLATE.md`, `tests/` | Espelhados em `plugin/` pelo `build-plugin.sh` |
| **Arquivos alterados** | `WORKFLOW_CONTRACTS.yaml` (nova fase, `pre_ship_checklist`, status), `DESIGN_TEMPLATE.md` (seção `## Evals`), `BUILD_REPORT_TEMPLATE.md` (aponta para o EVAL_REPORT), `build-agent.md` (PRE-check), `ship-agent.md` + `ship.md` (gate), `iterate-agent.md` (invalidação do recibo), `design-agent.md` (autoria dos evals), `CLAUDE.md`, docs de referência | Mudança de contrato entre fases |
| **Domínios KB** | `testing`, `genai`, `prompt-engineering`, `python` | pytest/fixtures para o runner; LLM-as-judge e rubricas |
| **Impacto IaC** | Nenhum | — |

---

## Premissas

| ID | Premissa | Se Errada, Impacto | Validada? |
|----|----------|-------------------|-----------|
| A-001 | Um dos dois caminhos do OpenRouter para o JEV funciona com a `OPENROUTER_API_KEY` do usuário | `graded` fica sem JEV no MVP e cai sempre em `/judge` ou humano | [x] 2026-09-23 — **os dois** respondem HTTP 200 com o mesmo schema (ver "Evidência do teste do JEV") |
| A-002 | Evals `deterministic` escritos em bash cobrem a maioria dos ATs das features típicas (dados, frontend, framework) | Mais ATs viram `human`, e o gate perde valor | [ ] |
| A-003 | Um digest do bloco `## Evals` (canonizado) basta para detectar alteração do contrato | Precisaríamos incluir a tabela de ATs do DEFINE no digest | [ ] |
| A-004 | Um agente sem ferramenta Edit/Write sobre código, invocado em fase própria, é independência suficiente para o MVP | Exigiria sessão separada, que é mais difícil de impor | [ ] |
| A-005 | Limiares iniciais do JEV (revisados após o teste de 2026-09-23): PASS exige **todas** as perguntas Noul ≥ 0,85 **e** ≥ 1 pergunta Score com `confidence` ≥ 0,75 e a maior probabilidade no nível de topo; calibração aprovada com concordância ≥ 80% contra a referência (`/judge` + decisão do usuário) nas fixtures | Ajuste dos limiares; o JEV permanece consultivo por mais tempo | [ ] parcialmente — o teste mostrou que Noul ≥ 0,70 sozinho aprovaria um AT pendente; calibração completa segue pendente |
| A-006 | `EVAL_REPORT_{F}.md` e `EVAL_{F}.json` ficam em `.claude/sdd/reports/`, ao lado do BUILD_REPORT, e são arquivados pelo ship-agent | Ajuste de caminhos no Design | [ ] |
| A-007 | O endpoint alpha do JEV pode mudar sem aviso; o cliente isolado absorve a mudança | Retrabalho concentrado em um arquivo | [ ] |

**Nota:** A-005 são defaults calibráveis e não constantes de produto.

### Evidência do teste do JEV (2026-09-23)

Chamadas reais a `typesafe/jev-1.13` via OpenRouter, usando a credencial OpenRouter do usuário obtida com `omp token openrouter` (sem gravar a chave). O modelo resolvido foi `typesafe/jev-1.13-20260917`, com provider `TypeSafe`.

| Teste | Resultado |
|-------|-----------|
| `POST https://openrouter.ai/api/alpha/decisions` | HTTP 200, ~0,6 s, `{model, answers, usage{input_tokens, output_tokens, cost}, id, provider}` |
| `POST https://openrouter.ai/api/v1/systemone` | HTTP 200, ~0,6 s, mesmo schema e respostas equivalentes |
| Custo por chamada (2 perguntas, ~350 tokens) | ~US$ 0,000015–0,000017 |

Discriminação com `state` **estruturado** (`{build_report_claim, evidence}`, com as perguntas referenciando os campos entre crases):

| Caso | Noul "evidência apoia o claim?" | Score (4 níveis) | Confiança do Score |
|------|---------------------------------|------------------|--------------------|
| Relatório diz PASS; eval com exit 0 | 0,94 | 2,97 (97% "strong evidence") | 0,97 |
| Relatório diz PASS; eval com exit 1 e AssertionError | 0,21 | 0,35 (85% "contradicts it") | 0,65 |
| Relatório diz PASS; nenhum eval executado (pendente) | **0,70** | 1,94 (dividido entre níveis) | **0** |
| Mesmo caso positivo, mas com `state` em **texto corrido** | 0,70 | 1,78 | 0,67 |

**Implicações para o Design:**

1. **Os dois caminhos funcionam.** Preferir `/api/v1/systemone`, que espelha o path da API da TypeSafe (`api.typesafe.ai/v1/systemone`) e permite trocar só a base URL entre OpenRouter e TypeSafe. Usar `/api/alpha/decisions` como fallback.
2. **Noul sozinho não basta.** No caso pendente, o Noul deu 0,70 ("apoia") com confiança 0. Por isso o PASS passa a exigir Noul alto **e** confiança alta no Score (A-005 revisada).
3. **O `state` precisa ser estruturado.** O mesmo caso positivo caiu de 0,94 para 0,70 quando enviado como texto corrido. Evals `graded` devem declarar campos nomeados, e as perguntas devem referenciá-los.
4. **A amostra é pequena** (4 chamadas). Isso orienta os limiares, mas não substitui a calibração.

---

## Detalhamento do Clarity Score

| Elemento | Score (0-3) | Notas |
|----------|-------------|-------|
| Problema | 3 | Específico, com evidência no repositório (`KB_EVOLUTION` com 6 ATs `⏳`) |
| Usuários | 3 | Quatro papéis com dor concreta |
| Objetivos | 3 | MoSCoW explícito, alinhado às decisões do brainstorm |
| Sucesso | 3 | Critérios numéricos, verificáveis por teste automatizado offline |
| Escopo | 2 | Fronteiras claras e acesso ao JEV validado (A-001); a autoridade de decisão do JEV ainda depende da calibração (A-005) |
| **Total** | **14/15** | |

---

## Questões em Aberto

Nenhuma bloqueia o Design. As decisões abaixo ficam para o `/design`, com os defaults das Premissas:

| # | Questão | Default proposto |
|---|---------|------------------|
| Q1 | ~~Qual caminho do OpenRouter usar para o JEV?~~ | **Resolvida em 2026-09-23:** os dois funcionam. Primário `/api/v1/systemone`, fallback `/api/alpha/decisions` |
| Q2 | Digest de quê: só o bloco `## Evals` ou bloco + tabela de ATs do DEFINE? | Só o bloco `## Evals` canonizado (A-003); o validador de rastreabilidade cobre o DEFINE |
| Q3 | O `/iterate` invalida o recibo automaticamente? | Sim, implicitamente: qualquer mudança no bloco muda o digest e o `/ship` recusa (AT-005). O iterate-agent apenas avisa |
| Q4 | Formato exato da referência de calibração do JEV | Arquivo `EVAL_CALIBRATION.json` com casos, respostas do JEV, decisão de referência e taxa de concordância |

---

## Histórico de Revisões

| Versão | Data | Autor | Mudanças |
| 1.2 | 2026-09-24 | ship-agent | Entregue e arquivado (recibo `/eval` PASS, 17/17) |
|--------|------|-------|----------|
| 1.0 | 2026-09-23 | define-agent | Versão inicial a partir de `BRAINSTORM_POST_BUILD_EVALS.md` |
| 1.1 | 2026-09-23 | define-agent | Teste real do JEV: A-001 validada, Q1 resolvida, A-005 revisada (Noul + confiança do Score), nova restrição de `state` estruturado |

---

## Próximo Passo

**Pronto para:** `/eval POST_BUILD_EVALS`
