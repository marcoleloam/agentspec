# BRAINSTORM: LLM Phase Routing

> Sessão exploratória para clarificar intenção e abordagem antes da captura de requisitos

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | LLM_PHASE_ROUTING |
| **Data** | 2026-09-23 |
| **Autor** | brainstorm-agent |
| **Status** | Pronto para Define |
| **Gerado por** | Claude Code — sessão principal, `claude-opus-5-5` (o `/brainstorm` roda inline; o `model: sonnet` do brainstorm-agent não foi aplicado) |

---

## Ideia Inicial

**Entrada Bruta:** "Colocar quais LLMs eu devo usar em cada uma das etapas: brainstorm, define, design, build e ship."

**Contexto Coletado:**

- **O `model:` dos agents de workflow não vale quando o usuário digita o comando.** `/brainstorm`, `/define`, `/design`, `/build` e `/ship` (`.claude/commands/workflow/*.md`) não têm `model:` na frontmatter e não delegam ao agent da fase. O arquivo do agent aparece só como "Reference" no fim do comando. A fase roda na sessão principal, com o modelo escolhido no `/model`.
- **Frontmatter atual dos agents de workflow** (`.claude/agents/workflow/`): `sonnet` em brainstorm, define, iterate e ship; `opus` em design, build e nas três variantes `-multiagent`. Isso só vale quando o agent roda como subagent.
- **Especialistas delegados pelo `/build`:** usam o `model:` de cada um. No repositório inteiro, 17 agents estão em `opus` e 57 em `sonnet` (um deles com comentário na mesma linha).
- **Claude Code** (docs oficiais, `code.claude.com/docs/en/slash-commands` e `/sub-agents`):
  - Comandos e skills aceitam `model:`, que vale até o fim do turno e não fica salvo. Aceitam também `context: fork` + `agent:` para rodar dentro de um subagent.
  - O `model:` de subagent aceita alias (`opus`, `sonnet`, `haiku`, `fable`), ID completo ou `inherit`.
  - Precedência do modelo do subagent: parâmetro da invocação → frontmatter → `CLAUDE_CODE_SUBAGENT_MODEL` → modelo da sessão.
  - Agents em `.claude/agents/` do projeto têm prioridade sobre os de plugin.
- **Bundles derivados de `.claude/`:**
  - `scripts/generate-codex-plugin.py` converte `opus`/`sonnet`/`haiku` em `model_reasoning_effort` `high`/`medium`/`low` e **não** fixa modelo, de propósito (os IDs do Codex mudam e dependem da conta).
  - `scripts/generate-grok-plugin.py` **remove** a linha `model:`.
  - `scripts/generate-dsh-bundle.py` copia os agents de workflow sem alteração.
- **Judge Layer** (`scripts/judge.py`): já tem `PHASE_MODEL_DEFAULTS` por fase via OpenRouter, mas com IDs antigos (`openai/gpt-4o`, `gpt-4o-mini`). Precedência: `--model` → `JUDGE_MODEL` → padrão da fase.
- **OMP** (oh-my-pi, `omp` v18.2.11) é o harness onde o usuário quer rodar o SDD:
  - Já tem o AgentSpec instalado como plugin no formato Claude Code (`~/.omp/plugins/installed_plugins.json` → `agentspec@agentspec` 3.4.1, marketplace local apontando para o repositório). O `model: opus` foi preservado nos agents instalados.
  - Tem roteamento por papel nativo: `modelRoles` em `~/.omp/agent/config.yml`, com `plan`, `slow`, `smol`, `task`, `tiny`, `vision`, `commit`, `advisor` e `REVIEWER`.
  - Também tem `task.agentModelOverrides` (nome do agent → `@papel`), `retry.fallbackChains` e flags de CLI (`--model`, `--plan`, `--slow`, `--smol`, `--thinking`).
  - Config atual: `plan` = `openai-codex/gpt-6-astra:high`, `slow` = `gpt-6-astra:max`, `REVIEWER` = `gpt-6-astra:high`; `smol`/`task`/`commit`/`tiny` = `xai-oauth/grok-4.6:xhigh`.
- **task-spec** (referência): o contrato de agente (C9, `docs/concepts/agent-contract.md`) trata o modelo dentro do engine como caixa-preta e permite roteamento por iteração. Pede família de modelo **diferente** para as passagens de revisão e adversariais (`docs/runbooks/dispatching-a-task-spec.md`, engine `codex`).

**Contexto Técnico Observado (para o Define):**

| Aspecto | Observação | Implicação |
|---------|------------|------------|
| Localização Provável | `.claude/sdd/architecture/`, `.claude/commands/workflow/`, `.claude/agents/workflow/`, `build-plugin.sh`, `scripts/generate-*.py`, `.claude/sdd/templates/` | Um manifesto novo e ajustes nos geradores e templates; nenhum código de runtime novo |
| Domínios KB Relevantes | `genai`, `prompt-engineering` | Pouca dependência de KB; a decisão é de plataforma e harness |
| Padrões IaC | N/A | — |
| Harness-alvo | OMP (principal); Claude Code, Codex, Grok e DeepSeek recebem o equivalente | O manifesto precisa ser independente de harness |

---

## Perguntas de Descoberta e Respostas

| # | Pergunta | Resposta | Impacto |
|---|----------|----------|---------|
| 1 | Qual resultado principal você espera: aplicar automático, só documentar, roteamento dinâmico ou multi-provedor? | "Multi-provedor via OMP ou colocar a CLI necessária" | O escopo vai além da família Claude; a fase precisa conseguir cair em outro provedor |
| 2 | Onde as fases do SDD rodam no dia a dia? | "Tudo no OMP" | O OMP é o alvo principal; Claude Code e os outros bundles recebem o equivalente como efeito colateral |
| 3 | Quais provedores entram no roteamento? | "Todos, já temos configurado no OMP; usar os modelos do config" | **O AgentSpec não fixa IDs de modelo**: cada fase aponta para um papel do OMP, e o modelo concreto fica no `config.yml` do usuário |
| 4 | (Amostras) Há evidência para calibrar fase → modelo? | "Features passadas" | Verificado: `FRONTEND_ECOSYSTEM` e `KB_EVOLUTION` não registram o modelo que rodou cada fase, então passa a ser requisito gravar isso |
| 5 | Abordagem e mapeamento fase → papel | "A + mapeamento como está" | Manifesto único gerado para cada harness; tabela abaixo como default |
| 6 | O recorte do MVP está correto? | "Sim, confirmo o recorte" | Lista YAGNI abaixo fechada |

---

## Inventário de Dados de Exemplo

| Tipo | Localização | Quantidade | Notas |
|------|-------------|------------|-------|
| Features passadas | `agentspec/.claude/sdd/archive/{FRONTEND_ECOSYSTEM,KB_EVOLUTION}/` | 2 | Registram o `model:` dos **agents criados**, não o modelo que **rodou a fase**. Não servem para calibrar, mas mostram a lacuna |
| Config de papéis | `~/.omp/agent/config.yml` | 1 | Fonte de verdade dos modelos concretos por papel (fora do repositório) |
| Referência de mapeamento | `scripts/generate-codex-plugin.py` (`EFFORT_BY_MODEL`), `scripts/judge.py` (`PHASE_MODEL_DEFAULTS`) | 2 | Padrões existentes de "tier → equivalente" a reaproveitar |
| Ground truth | N/A | 0 | Ainda não existe; o requisito de metadados vai gerar isso |

**Como os exemplos serão usados:**

- `EFFORT_BY_MODEL` como modelo de tabela de tradução por harness.
- O `config.yml` do OMP como fixture do spike (sem versionar IDs nem chaves).
- As próximas features, já com papel e modelo gravados nos metadados, viram a base de calibração (e insumo para `POST_BUILD_EVALS` e `JEV_AGENT_SELECTION`).

---

## Abordagens Exploradas

### Abordagem A: Manifesto fase → papel, gerado para cada harness ⭐ Recomendada

**Descrição:** um arquivo único `.claude/sdd/architecture/PHASE_MODEL_ROLES.yaml` define, por fase, o papel semântico (vocabulário dos `modelRoles` do OMP), o alias Claude equivalente e o effort do Codex. `build-plugin.sh` e os geradores aplicam isso na frontmatter dos comandos e agents de workflow, cada um no formato nativo do seu harness. Um trecho gerado de `agentModelOverrides` ajuda a configurar o OMP sem tocar nos modelos que o usuário já escolheu.

**Prós:**

- Uma única fonte de verdade; nenhum ID de modelo no repositório, porque o OMP resolve o papel para o modelo.
- Resolve o problema central (comando inline ignora o `model:` do agent), já que o papel vai para o comando.
- Claude Code, Codex e Grok ganham o equivalente pelo mesmo manifesto.

**Contras:**

- Depende de um spike: não está verificado se o OMP respeita `model:`/`@papel` na frontmatter de comandos e agents de plugin.
- Um arquivo a mais para manter em sincronia (mitigado com o `--check` dos geradores, como já é feito hoje).

**Por que Recomendada:** é a única opção que faz o `/design` digitado mudar de modelo sem troca manual, mantendo o AgentSpec agnóstico de provedor e respeitando o `config.yml` do usuário.

---

### Abordagem B: Só receita de `config.yml` + documentação

**Descrição:** tabela recomendada em `docs/` e um trecho de `agentModelOverrides` para colar no OMP. Nenhum código no AgentSpec.

**Prós:**

- Custo quase zero.
- Nada para sincronizar.

**Contras:**

- `agentModelOverrides` só vale quando a fase roda como subagent. O `/design` digitado continua no modelo da sessão, então o problema central fica sem solução.
- Sem propagação para os outros bundles.

---

### Abordagem C: Runner por fase (`omp -p --model @papel`)

**Descrição:** um script dispara cada fase como processo OMP separado, no modelo do papel.

**Prós:**

- Isolamento total entre fases e troca de provedor garantida.

**Contras:**

- Perde a interação: brainstorm e define dependem de perguntas ao usuário.
- Perde o contexto da sessão; só serve para fases em lote (design e ship headless).

---

## Abordagem Selecionada

| Atributo | Valor |
|----------|-------|
| **Escolhida** | Abordagem A |
| **Confirmação do Usuário** | 2026-09-23 (pergunta 5) |
| **Justificativa** | Aplica o modelo certo por fase no OMP sem troca manual, sem fixar IDs, e propaga para os outros harnesses a partir de uma única fonte |

### Mapeamento default fase → papel (validado)

| Fase / comando | Papel OMP | Resolve hoje para (config do usuário) | Alias Claude | Effort Codex | Por quê |
|----------------|-----------|---------------------------------------|--------------|--------------|---------|
| `/brainstorm` (+ `-multiagent`) | `plan` | gpt-6-astra:high | `opus`* | high | Diálogo exploratório; raciocínio sobre abordagens |
| `/define` (+ `/define-m`) | `plan` | gpt-6-astra:high | `sonnet`/`opus`* | medium/high | Precisão de requisitos, Clarity Score |
| `/design` (+ `/design-m`) | `slow` | gpt-6-astra:max | `opus` | high | Decisão de arquitetura; onde o erro sai mais caro |
| `/build` (orquestrador) | sessão/default | — | `inherit` | — | Coordena e lê DESIGN e BLACKBOARD |
| `/build` (especialistas) | mantém o `model:` atual | — | atual | atual | Fora do MVP (ver YAGNI) |
| `/ship` | `smol` | grok-4.6:xhigh | `haiku`/`sonnet`* | low | Arquivar e resumir |
| `/iterate`, `/continuar` | `plan` | gpt-6-astra:high | `sonnet`* | medium | Atualização com cascata |
| `--judge` / review | `REVIEWER` | gpt-6-astra:high | — (OpenRouter) | — | Família diferente de quem produziu |

\* Aliases Claude e efforts marcados ficam para o `/define` fechar. O mapeamento de papel é o que foi validado.

**Observação registrada:** com o config atual, `REVIEWER` e `plan`/`slow` resolvem para a mesma família (gpt-6-astra). Revisar um DESIGN com a mesma família que o escreveu fere o princípio de família diferente (task-spec, Judge Layer). O manifesto deve permitir declarar isso, e o `/status` ou a documentação deve avisar, sem trocar o modelo por conta própria.

---

## Principais Decisões Tomadas

| # | Decisão | Justificativa | Alternativa Rejeitada |
|---|---------|---------------|----------------------|
| 1 | O AgentSpec declara **papéis**, não modelos | Os IDs mudam e dependem da conta (mesma razão do gerador Codex); o usuário já escolhe modelos no OMP | Fixar `gpt-6-astra`/`grok-4.6`/`opus` no repositório |
| 2 | Vocabulário de papéis = `modelRoles` do OMP | O OMP é o harness principal e já resolve papel → modelo → fallback | Vocabulário próprio (`deep`/`fast`/`exec`) exigiria outra tabela de tradução |
| 3 | O papel vai para o **comando** da fase, não só para o agent | O comando roda inline; o `model:` do agent é ignorado no caminho do `/design` digitado | Confiar só no `model:` do agent (situação de hoje) |
| 4 | Spike do OMP antes de qualquer código | Não está verificado se o OMP respeita `model:`/`@papel` em comandos e agents de plugin | Assumir compatibilidade com o Claude Code |
| 5 | Gravar papel e modelo nos metadados dos documentos SDD | Sem esse registro não existe calibração nem eval por modelo | Telemetria separada (já está no backlog) |
| 6 | Não criar bundle OMP novo | O OMP já instala o plugin Claude (`agentspec@agentspec` 3.4.1) | `plugin-omp/` dedicado, só se o spike falhar |

---

## Features Removidas (YAGNI)

| Feature Sugerida | Motivo da Remoção | Pode Adicionar Depois? |
|------------------|-------------------|----------------------|
| Roteamento dinâmico por complexidade da feature | Sem dados para calibrar; a decisão 5 vai gerar esses dados | Sim |
| Escolha de modelo por benchmark/JEV | Encosta em `JEV_AGENT_SELECTION`/`POST_BUILD_EVALS`; capacidades do JEV não verificadas nesta frente | Sim, depois da frente JEV |
| Papel por especialista (73 agents) | Especialistas mantêm o `model:` atual; o MVP cobre só a camada de workflow | Sim |
| Bundle OMP dedicado | O OMP já consome o plugin Claude | Só se o spike falhar |
| Cadeias de fallback no AgentSpec | O OMP já tem `retry.fallbackChains` | Não |
| Telemetria de custo por fase | Já está no backlog ("Add telemetry") | Sim |
| Atualizar IDs antigos do `judge.py` para o manifesto | Não é roteamento de fase; vai como correção separada ou COULD | Sim (COULD) |

---

## Validações Incrementais

| Seção | Apresentada | Feedback do Usuário | Ajustada? |
|-------|-------------|---------------------|-----------|
| Abordagens A/B/C + mapeamento fase → papel | ✅ | "A + mapeamento como está" | Não |
| Recorte do MVP (entra/sai, YAGNI) | ✅ | "Sim, confirmo o recorte" | Não |

---

## Dependências e Fronteiras com as Outras Frentes

| Frente | Onde encosta | Regra de fronteira |
|--------|--------------|--------------------|
| `JEV_AGENT_SELECTION` | As duas escolhem "quem executa" a fase | **Esta frente escolhe o MODELO (papel → modelo); aquela escolhe os AGENTES.** Se o JEV passar a recomendar modelo, ele alimenta o manifesto (ou o `config.yml`), sem substituí-lo. Nada de JEV aqui |
| `POST_BUILD_EVALS` | Evals pós-build querem comparar resultado por modelo; o reviewer deve ser de outra família | Esta frente **fornece** papel e modelo gravados nos metadados e o papel `REVIEWER`. O desenho dos evals, métricas e gates fica lá |
| `LIVING_MEMORY` | O "qual modelo gerou este documento" é um fato que a memória viva pode indexar | Esta frente só grava o campo nos metadados do documento. Como isso vira memória entre fases fica lá |
| `KB_CONTEXT7_REFRESH` | `kb-evolution-agent` e `/ingest-kb` têm `model:` próprio | Fora do escopo: comandos de KB não são fases do SDD. Se aquela frente mudar o fluxo, ela decide o papel usando o mesmo manifesto |

---

## Perguntas em Aberto (para o spike ou o /define)

1. O OMP respeita `model:` na frontmatter de **comandos** de plugin Claude? Aceita `@papel` (ex.: `model: "@slow"`) ou só ID/alias?
2. O OMP respeita `model:` na frontmatter de **agents** de plugin? E `agentModelOverrides` casa com nomes namespaced (`agentspec:workflow:design-agent`)?
3. O OMP suporta `context: fork` + `agent:` como o Claude Code? Se sim, o `/design` pode delegar ao design-agent e herdar o papel dele.
4. Como um papel do OMP (`@slow`) é traduzido no Claude Code, que não conhece papéis? A proposta é o alias do manifesto, mas o valor fica para o `/define` decidir.
5. O que acontece com o bundle DeepSeek (`plugin-dsh`), que hoje copia os agents sem alteração? Passa adiante, traduz ou remove?
6. O "JEV via OMP no OpenRouter" não foi verificado nesta frente. Se virar papel no OMP, entra pelo `config.yml` do usuário, sem mudança no AgentSpec.

---

## Requisitos Sugeridos para /define

### Declaração do Problema (Rascunho)

Ao rodar `/brainstorm`, `/define`, `/design`, `/build` ou `/ship`, o modelo usado é o da sessão, e não o recomendado para a fase. O `model:` dos agents de workflow é ignorado nesse caminho, e o usuário não tem como declarar, uma vez só e para todos os harnesses, qual provedor ou modelo deve atender cada fase.

### Usuários-Alvo (Rascunho)

| Usuário | Dor |
|---------|-----|
| Dono do AgentSpec rodando no OMP com vários provedores | Troca `/model` na mão a cada fase ou roda tudo no mesmo modelo |
| Usuário do plugin no Claude Code, Codex ou Grok | O `model:` dos agents não vale nos comandos; o Grok remove o campo |
| Futuras frentes (evals, JEV, memória) | Não sabem qual modelo produziu cada artefato |

### Critérios de Sucesso (Rascunho)

- [ ] Rodar `/design` no OMP usa o modelo do papel `slow` do `config.yml` sem troca manual. Verificado por log ou metadado do DESIGN.
- [ ] Rodar `/ship` no OMP usa o papel `smol`. Mesma verificação.
- [ ] Nenhum ID concreto de modelo (`gpt-*`, `grok-*`, `claude-*`) nos arquivos gerados de workflow. Verificado por grep no CI.
- [ ] `PHASE_MODEL_ROLES.yaml` é a única fonte, e os geradores falham no `--check` se houver divergência.
- [ ] Os 5 templates SDD ganham o campo papel/modelo nos metadados, preenchido pela fase.
- [ ] Documentação da tabela fase → papel e do trecho de `config.yml` para o OMP.

### Restrições Identificadas

- Não versionar IDs de modelo, chaves nem o `config.yml` do usuário.
- Compatibilidade com Claude Code (plugin atual) e com os geradores Codex, Grok e DeepSeek existentes.
- Brainstorm e define precisam continuar interativos (perguntas ao usuário), sem virar processo headless.
- Documentos SDD em pt-BR; framework (agents, comandos, manifesto) em inglês.

### Fora do Escopo (Confirmado)

- Roteamento dinâmico por complexidade.
- Seleção de modelo via JEV ou benchmark.
- Papel por agent especialista.
- Bundle OMP dedicado (salvo se o spike falhar).
- Telemetria de custo e cadeias de fallback.

---

**Próximo passo:** `/define .claude/sdd/features/BRAINSTORM_LLM_PHASE_ROUTING.md`
