# BRAINSTORM: Seleção de Agentes via JEV

> Sessão exploratória para clarificar intenção e abordagem antes da captura de requisitos

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | JEV_AGENT_SELECTION |
| **Data** | 2026-09-23 |
| **Autor** | brainstorm-agent |
| **Status** | Pronto para Define |

---

## Ideia Inicial

**Entrada Bruta:** "Existem novos projetos, como o JEV, que poderiam entrar para fazer a definição de quais agentes deveríamos usar em cada uma das etapas." O JEV está disponível pela OMP no OpenRouter.

**Contexto Coletado:**

- **O que é o JEV (fontes lidas: docs.typesafe.ai e código do jev-gateway):**
  - Modelo "System One" da TypeSafe. **Não gera texto**: recebe um `state` (texto) e perguntas tipadas, e devolve respostas estruturadas com probabilidades calibradas.
  - Três primitivas: **Choice** (uma opção entre até 255, com probabilidade por opção e `confidence` de 0 a 1), **Score** (nota numa rubrica de níveis ordenados) e **Noul** (probabilidade de "sim", de 0 a 1). Tipos diferentes podem ir na mesma chamada ("speculative fan-out").
  - Modelos: `jev-1.13.0`, com os aliases `jev-latest` e `jev-preview`. Janela de 64k tokens por requisição; 32k para `state` mais a maior pergunta. Só aceita texto.
  - Preço (página Models): US$ 0,042 por milhão de tokens de entrada; saída gratuita. Rate limit: 250k tokens/s e 1.200 req/min ("ajustando dinamicamente").
  - Latência: **não documentada** na página de modelos. No cookbook *Skill suggestion* (escolher no máximo 1 skill entre 182 em duas chamadas), o ranking levou cerca de 0,16–0,31 s e o re-ranking do top-3 cerca de 0,09–0,12 s. O resultado foi 2,3x menos carregamentos errados e 2,4x menos carregamentos desnecessários em 488 requisições, com limiares de 0,30.
  - A própria TypeSafe documenta **limitações do jev-1.13**: lê as perguntas ao pé da letra; a precisão cai com state grande e irrelevante; é suscetível a conteúdo adversarial; confunde-se com instruções contraditórias; não garante coerência entre perguntas relacionadas; não faz matemática nem comparação de datas.
  - A doc "Jev with coding agents" diz que o JEV **não** substitui o LLM de um coding agent e serve para roteamento, scoring, validação e saída estruturada *dentro* do sistema.
- **Como o JEV é chamado via OpenRouter (conforme `src/providers.json` e `src/jev.ts` do jev-gateway):**
  - Endpoint `https://openrouter.ai/api/alpha/decisions`, modelo `typesafe/jev-1.13`, header `Authorization: Bearer $OPENROUTER_API_KEY`.
  - Mesmo corpo da API nativa (`state`, `model`, `questions`) e mesmas respostas (`answers`, `usage`).
  - O endpoint está em **alpha**. O gateway normaliza respostas Choice que chegam **sem `confidence`**, usando a probabilidade vencedora no lugar.
- **O que o jev-gateway faz:** intercepta a decisão de *qual tool chamar* em Codex, Claude Code, OpenCode e Gemini CLI. Usa `JEV_MIN_CONFIDENCE=0.7`, `JEV_TIMEOUT_MS=4000` e, com confiança baixa ou falha, o modo `passthrough` (a decisão volta para o LLM). Ele mede economia de tokens e tempo por sessão, não a qualidade da seleção de agentes.
- **Como o AgentSpec escolhe hoje:**
  - **Variante:** o usuário digita `/define` ou `/define-m` (e `/design` ou `/design-m`). Dentro do `-m`, o LLM conta domínios de KB e volta para a variante simples se forem menos de 3 (`define-m.md:52`, `design-m.md:53`). As variantes simples nunca sugerem subir para multiagent.
  - **Especialistas:** as variantes `-multiagent` fazem "Select top 3-4 agents with highest domain overlap" comparando `kb_domains` do frontmatter com os domínios da spec (`design-multiagent.md:89-90,138`). Quem faz isso é o próprio LLM.
  - **Catálogo:** `scripts/generate-agent-router.py` gera `.claude/skills/agent-router/routing.json` (73 agentes com `category`, `tier`, `model`, `description`, `kb_domains` e `escalates_to`). É uma fonte determinística de candidatos.
  - **Precedente de OpenRouter:** `scripts/judge.py` (stdlib, urllib, ledger, `PHASE_MODEL_DEFAULTS`, testes em `tests/test_judge.py`).

**Contexto Técnico Observado (para o Define):**

| Aspecto | Observação | Implicação |
|---------|------------|------------|
| Localização Provável | `scripts/jev_select.py`, `tests/test_jev_select.py`, `.claude/commands/workflow/{define,design,define-m,design-m}.md`, `.claude/agents/workflow/{define,design}-{agent,multiagent}.md`, `.claude/sdd/templates/{DEFINE,DESIGN}_TEMPLATE.md` | Script novo no padrão do `judge.py`; comandos e agentes chamam via Bash |
| Distribuição no plugin | `plugin/scripts/` só contém `init-workspace.sh` e `status-dashboard.py`. `/judge` referencia `${CLAUDE_PLUGIN_ROOT}/scripts/judge.py`, que **não** é empacotado | `jev_select.py` precisa entrar no `build-plugin.sh`, senão falha em instalações via plugin |
| Domínios KB Relevantes | `genai`, `prompt-engineering`, `python`, `testing` | Padrões de roteamento com confiança, cliente HTTP e pytest |
| Padrões IaC | N/A | Sem infraestrutura; só chamada HTTP e variável de ambiente |
| Credencial | `OPENROUTER_API_KEY` (a mesma do Judge Layer); não estava exportada no shell desta sessão | A ausência da chave deve cair no fallback sem erro |

---

## Perguntas de Descoberta e Respostas

| # | Pergunta | Resposta | Impacto |
|---|----------|----------|---------|
| 1 | Qual é a dor principal que o JEV deve resolver? | **Agente errado escolhido** (precisão) | O critério de sucesso é acerto contra ground truth, não custo nem latência |
| 2 | Em que ponto o agente errado aparece ou dói mais? | **Escolha da variante** (single vs `-multiagent`) | O alvo principal é a regra "3+ KB domains" e a escolha manual do comando |
| 3 | Quanto controle o JEV deve ter? | "O JEV deve decidir qual agente ele precisa usar, derivado da especificação" | Decisão autônoma; a entrada é o documento da fase anterior, não a conversa |
| 4 | Quais decisões o JEV toma a partir da spec? | **Variante da fase** e **especialistas consultados** | `@agente` por arquivo no manifesto fica fora |
| 5 | Qual o fallback quando o JEV não decide? | **Heurística atual**, com registro do motivo | O fluxo nunca trava; é o mesmo espírito do `passthrough` do gateway |
| 6 | Há exemplos para ancorar e medir? | **Features arquivadas** e specs de outros projetos, rotuladas à mão | Viabiliza uma avaliação offline JEV vs heurística |

---

## Inventário de Dados de Exemplo

| Tipo | Localização | Quantidade | Notas |
|------|-------------|------------|-------|
| Arquivos de entrada (specs) | `.claude/sdd/archive/{FRONTEND_ECOSYSTEM,KB_EVOLUTION}/` | 2 features (1 BRAINSTORM, 2 DEFINE, 2 DESIGN) | FRONTEND_ECOSYSTEM é cross-domain (6 domínios frontend); KB_EVOLUTION é mais estreita |
| Arquivos de entrada (specs) | `/Users/marcoleloam/projetos/**/.claude/sdd/{features,archive}/` | ~30 DEFINE reais (40 encontrados, ~8 são cópias de template) | Specs de vários projetos de clientes (não nomeados neste repositório) |
| Exemplos de saída | N/A | 0 | Formato da seção "Seleção de Agentes" a definir no Design |
| Ground truth | A criar | ~20–30 rótulos | Rotular à mão, por spec: variante correta e conjunto correto de especialistas |
| Código relacionado | `scripts/judge.py`, `tests/test_judge.py`, `scripts/generate-agent-router.py`, `.claude/skills/agent-router/routing.json` | 4 | Cliente OpenRouter, padrão de testes e catálogo de candidatos |
| Referência externa | `github.com/vinilana/jev-gateway` (`src/jev.ts`, `src/providers.json`, `scripts/mock-jev.mjs`) | 3 | Transporte, normalização de `confidence` e mock sem chave |
| Referência externa | docs.typesafe.ai `cookbooks/skill_suggestion` | 1 | Padrão mais próximo: ranking amplo + Noul por candidato + limiares |

**Como os exemplos serão usados:**

- Conjunto de avaliação offline: rodar `jev_select.py` e a heurística atual sobre as mesmas specs e comparar com os rótulos.
- Calibração inicial dos limiares (variante 0.7; Noul de especialista a definir).
- Fixtures dos testes de pytest, com respostas do JEV gravadas e HTTP mockado.

---

## Abordagens Exploradas

### Abordagem A: script `jev_select.py` chamado pelos comandos ⭐ Recomendada

**Descrição:** script Python em stdlib, no padrão do `judge.py`. `/define`, `/design`, `/define-m` e `/design-m` o chamam via Bash antes de começar a fase.

- **State:** resumo curto da spec (problema, requisitos, domínios de KB citados).
- **Candidatos:** pré-filtro determinístico no `routing.json` por `kb_domains` e categoria.
- **Perguntas numa única chamada:** um `Choice` para a variante (`single` | `multiagent`) e um `Noul` por candidato ("a especialidade deste agente pesa materialmente nesta spec?").
- **Portão de confiança:** abaixo do limiar, ou com erro, timeout ou chave ausente, vale a heurística atual.
- **Saída:** JSON, que o agente grava numa seção "Seleção de Agentes" do documento.

**Prós:**
- Determinístico e auditável: probabilidades e fonte (`jev` | `fallback`) ficam gravadas na spec.
- Reaproveita `routing.json` e o padrão do `judge.py`; testável com pytest e mock, sem rede.
- Custo desprezível; o state pequeno respeita a limitação documentada de "large state full of irrelevant detail".
- Segue padrões publicados pela TypeSafe (speculative fan-out, confidence-gated routing, skill suggestion).

**Contras:**
- O endpoint do OpenRouter está em `alpha`, então pode mudar.
- É preciso manter o resumo da spec e os limiares.
- O pré-filtro por `kb_domains` continua sendo dependência (ver KB_CONTEXT7_REFRESH).

**Por que Recomendada:** é a única das três que decide **a partir da spec**, grava a decisão no documento e mantém o fluxo funcionando sem o JEV.

---

### Abordagem B: jev-gateway como proxy local do Claude Code

**Descrição:** rodar o jev-gateway na porta 8789 para interceptar a chamada da tool Agent e decidir o `subagent_type`.

**Prós:**
- Nenhum código novo no AgentSpec.
- Projeto já existente, com benchmarks publicados de economia de tokens e tempo.

**Contras:**
- Decide a partir da conversa, não da spec, e não decide a variante da fase.
- Exige um proxy rodando na máquina de cada usuário.
- Nada fica gravado no documento SDD, então a decisão não é auditável.
- Os benchmarks medem tokens e tempo, não precisão da seleção, que é a dor declarada.

---

### Abordagem C: skill oficial da TypeSafe (`npx skills add typesafe-ai/skills`)

**Descrição:** o Claude consulta o JEV através da skill oficial quando julgar necessário.

**Prós:**
- Mantida pela TypeSafe.

**Contras:**
- A chamada não é determinística e continua dependendo do julgamento do LLM principal, que é justamente a fonte do erro.
- O conteúdo da skill não foi lido nesta sessão (pergunta aberta).
- Não oferece portão nem fallback por si só.

---

## Abordagem Selecionada

| Atributo | Valor |
|----------|-------|
| **Escolhida** | Abordagem A: `scripts/jev_select.py` |
| **Confirmação do Usuário** | 2026-09-23, sessão de brainstorm |
| **Justificativa** | Decide a partir da especificação, é auditável no documento e tem fallback determinístico para a heurística atual |

**Fluxo validado:**

```text
/define <BRAINSTORM>   ou   /design <DEFINE>
        │
        ▼
 [1] resumo da spec (problema, requisitos, domínios KB citados)   ← agente da fase
        │
        ▼
 [2] pré-filtro determinístico: routing.json → candidatos por kb_domains/categoria
        │
        ▼
 [3] python3 scripts/jev_select.py --phase define|design ...
        │   1 chamada: POST openrouter.ai/api/alpha/decisions, model typesafe/jev-1.13
        │   questions: variant (Choice single|multiagent) + fit_<agente> (Noul por candidato)
        │   timeout curto (referência: 4 s do jev-gateway)
        ▼
 [4] portão
     ├─ confidence(variant) ≥ 0.7        → JEV decide a variante
     ├─ Noul(fit) ≥ limiar               → especialista entra (máx. 4, por probabilidade)
     └─ sem chave / erro / timeout / baixa confiança / resposta sem confidence utilizável
                                         → heurística atual (contagem e overlap de kb_domains)
        ▼
 [5] o comando segue na variante decidida e grava a seção "Seleção de Agentes":
     fonte (jev|fallback), probabilidades, especialistas escolhidos, motivo do fallback
```

**Regra de autonomia validada:**

| Comando digitado | Variante | Especialistas |
|------------------|----------|---------------|
| `/define` ou `/design` | **Decidida pelo JEV**: pode subir para `-multiagent` | Decididos pelo JEV, se a variante for multiagent |
| `/define-m` ou `/design-m` | **Respeitada** (escolha explícita do usuário) | Decididos pelo JEV |

---

## Principais Decisões Tomadas

| # | Decisão | Justificativa | Alternativa Rejeitada |
|---|---------|---------------|----------------------|
| 1 | A entrada do JEV é a **especificação** da fase anterior, resumida | Pedido explícito do usuário; resumo curto evita a queda de precisão com state grande | Conversa corrente (abordagem B); documento inteiro no state |
| 2 | Escopo: **variante da fase** e **especialistas consultados** | São os pontos onde a escolha errada dói (P2, P4) | `@agente` por arquivo no manifesto; roteamento ad-hoc |
| 3 | O JEV decide a variante de forma autônoma em `/define` e `/design`; `-m` explícito é respeitado | Autonomia pedida, sem atropelar escolha explícita | Só recomendar; JEV sobrescrevendo sempre; comando único |
| 4 | Fallback = heurística atual, com registro do motivo no documento | O fluxo nunca trava; o comportamento degradado é o de hoje | Perguntar ao usuário; o LLM principal decidir |
| 5 | Uma chamada com fan-out (Choice + N Nouls) sobre candidatos pré-filtrados | Padrão documentado pela TypeSafe; state pequeno; latência de uma ida e volta | Choice sobre os 73 agentes; duas chamadas (rank + rerank) no MVP |
| 6 | Transporte via OpenRouter `/api/alpha/decisions` com `OPENROUTER_API_KEY` | O usuário já tem acesso pela OMP; é a mesma chave do Judge Layer | API TypeSafe direta; Vercel AI Gateway |
| 7 | Sucesso medido **offline** contra ground truth rotulado | A dor é precisão; é preciso comparar com a heurística | Medir só tokens e latência, como o jev-gateway |

---

## Features Removidas (YAGNI)

| Feature Sugerida | Motivo da Remoção | Pode Adicionar Depois? |
|------------------|-------------------|----------------------|
| `@agente` por arquivo no manifesto do DESIGN | Não foi marcado pelo usuário como decisão do JEV | Sim |
| Seleção em `/brainstorm` e `brainstorm-multiagent` | Não há spec antes do brainstorm; a entrada da feature é a spec | Sim |
| Roteamento ad-hoc via `agent-router` fora do SDD | Não é o ponto de dor declarado | Sim |
| jev-gateway como proxy | Não decide a partir da spec nem é auditável | Sim (experimento separado) |
| Provedores TypeSafe direto e Vercel | Só OpenRouter no MVP; o URL pode ser sobrescrito por variável de ambiente | Sim |
| Limiares calibrados por fase | Limiar global de 0.7 para a variante no MVP | Sim |
| Ledger e orçamento diário de custo | Custo desprezível (~US$ 0,04 por milhão de tokens de entrada) | Sim |
| Cache de respostas do JEV | Uma chamada por fase; não há ganho relevante | Sim |
| Re-ranking em duas chamadas (como no cookbook) | O pré-filtro determinístico já reduz os candidatos | Sim |

---

## Validações Incrementais

| Seção | Apresentada | Feedback do Usuário | Ajustada? |
|-------|-------------|---------------------|-----------|
| Fluxo e regra de autonomia (`-m` explícito respeita a variante) | ✅ | "Correto, seguir" | Não |
| Escopo MVP, cortes YAGNI, critério de sucesso offline e fronteiras | ✅ | "Correto, gerar documento" | Não |

---

## Dependências e Fronteiras com as Outras Frentes

| Frente | Onde encosta | Fronteira (o que fica aqui × lá) |
|--------|--------------|----------------------------------|
| `LLM_PHASE_ROUTING` | As duas decidem "o que roda em cada fase" | **Aqui:** qual *agente* e qual *variante*. **Lá:** qual *modelo LLM* executa cada fase ou agente. A variante escolhida aqui pode ser um sinal de entrada para lá (ex.: multiagent → custo maior), mas o mapeamento é decisão daquela frente. |
| `POST_BUILD_EVALS` | Também pode usar o JEV (Score e Noul para avaliação) | Candidato a compartilhar o **cliente de transporte do JEV** (endpoint, auth, timeout, normalização de `confidence`). Quem cria e é dono desse módulo fica em aberto; esta frente não define evals. |
| `LIVING_MEMORY` | As decisões de seleção (probabilidades, fallback, acerto posterior) são contexto útil entre fases | Aqui só se grava a seção "Seleção de Agentes" no documento SDD. Indexar ou recuperar isso na memória viva é daquela frente. |
| `KB_CONTEXT7_REFRESH` | O pré-filtro de candidatos e a heurística de fallback dependem de `kb_domains` | **Dependência crítica:** se aquela frente eliminar ou mudar os KBs (como no task-spec, que não usa KBs), o pré-filtro e o fallback precisam de outro sinal (ex.: `category` + `description`). Não resolvido aqui. |

---

## Perguntas Abertas

| # | Pergunta | Por que importa |
|---|----------|-----------------|
| 1 | A conta OMP no OpenRouter tem acesso a `/api/alpha/decisions` com `typesafe/jev-1.13`? | Não verificado nesta sessão (a chave não estava exportada). É o primeiro passo do Build. |
| 2 | Preço e latência do JEV **via OpenRouter** | A doc informa só o preço da API TypeSafe; a latência não é documentada em lugar nenhum além dos números do cookbook. |
| 3 | O OpenRouter devolve `confidence` nas respostas Choice? | O jev-gateway normaliza a falta dela. O portão precisa de uma regra definida para esse caso. |
| 4 | Qual o limiar do Noul de especialista? | O cookbook usou 0,30; o gateway usa 0,7 para a tool. Calibrar com o conjunto rotulado. |
| 5 | O que a skill oficial da TypeSafe faz? | Não foi lida; pode ser uma alternativa ou complemento futuro. |
| 6 | Quem é dono do cliente JEV compartilhado com `POST_BUILD_EVALS`? | Evita duplicar o transporte. |
| 7 | Estabilidade do endpoint `alpha` | Pode quebrar sem aviso; o fallback cobre, mas convém fixar a versão do modelo (`jev-1.13`) e monitorar. |

---

## Requisitos Sugeridos para /define

### Declaração do Problema (Rascunho)

A escolha entre a variante simples e a `-multiagent` de `/define` e `/design`, e dos especialistas consultados, depende hoje do usuário digitar o comando certo e de uma contagem de domínios de KB feita pelo LLM. Isso leva a agente errado para a spec, sem registro auditável do porquê.

### Usuários-Alvo (Rascunho)

| Usuário | Dor |
|---------|-----|
| Desenvolvedor usando o AgentSpec | Precisa saber quando usar `-m`; recebe especialistas irrelevantes ou fica sem um domínio importante |
| Maintainer do AgentSpec | Não tem como medir nem auditar se a seleção de agentes está certa |

### Critérios de Sucesso (Rascunho)

- [ ] Em um conjunto de ~20–30 specs reais rotuladas à mão, o JEV acerta a variante com frequência **maior** que a heurística atual.
- [ ] No mesmo conjunto, o JEV produz **menos** especialistas errados (incluídos indevidamente ou omitidos) que o overlap de `kb_domains`.
- [ ] Sem `OPENROUTER_API_KEY`, com erro de rede ou com timeout, `/define` e `/design` completam normalmente via fallback, e o documento registra `fonte: fallback` e o motivo.
- [ ] Toda spec gerada por `/define` ou `/design` contém a seção "Seleção de Agentes" com fonte, probabilidades e especialistas.
- [ ] `jev_select.py` é distribuído no plugin (`build-plugin.sh`) e coberto por pytest com HTTP mockado.

### Restrições Identificadas

- O JEV não gera texto; só responde Choice, Score e Noul.
- State mais a maior pergunta devem caber em 32k tokens; manter o resumo da spec curto.
- O endpoint do OpenRouter está em `alpha`.
- Python stdlib, sem dependência nova (padrão do `judge.py`); o SDK `typesafe-sdk` não é obrigatório.
- A spec é conteúdo do próprio usuário, mas a TypeSafe documenta suscetibilidade a conteúdo adversarial: o state não deve conter instruções para o modelo.
- Os documentos gerados continuam em pt-BR; script, agentes e comandos em inglês.

### Fora do Escopo (Confirmado)

- `@agente` por arquivo no manifesto do DESIGN.
- Seleção de agentes no `/brainstorm`.
- Roteamento ad-hoc fora do fluxo SDD.
- Escolha do modelo LLM por fase (`LLM_PHASE_ROUTING`).
- Evals pós-build (`POST_BUILD_EVALS`).

---

## Resumo da Sessão

| Métrica | Valor |
|---------|-------|
| Perguntas Feitas | 6 (+ escolha de abordagem) |
| Abordagens Exploradas | 3 |
| Features Removidas (YAGNI) | 9 |
| Validações Concluídas | 2 |
| Duração | ~1 sessão |

---

## Fontes

- https://docs.typesafe.ai/introduction
- https://docs.typesafe.ai/introduction/quickstart
- https://docs.typesafe.ai/introduction/coding-agents
- https://docs.typesafe.ai/primitives/choice
- https://docs.typesafe.ai/models
- https://docs.typesafe.ai/model-jaggedness/jev-1.13
- https://docs.typesafe.ai/cookbooks/skill_suggestion
- https://github.com/vinilana/jev-gateway (README, `src/providers.json`, `src/jev.ts`)

---

## Próximo Passo

**Pronto para:** `/define .claude/sdd/features/BRAINSTORM_JEV_AGENT_SELECTION.md`
