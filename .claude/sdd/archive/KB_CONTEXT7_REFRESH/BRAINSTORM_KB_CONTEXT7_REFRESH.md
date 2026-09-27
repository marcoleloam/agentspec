# BRAINSTORM: KB_CONTEXT7_REFRESH

> Sessão exploratória para decidir, com medição e não com opinião, se as KBs do AgentSpec devem ser mantidas, enxugadas ou substituídas por consulta ao Context7 em tempo de execução.

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | KB_CONTEXT7_REFRESH |
| **Data** | 2026-09-23 |
| **Autor** | brainstorm-agent |
| **Status** | Pronto para Define |

---

## Ideia Inicial

**Entrada Bruta:** "Atualização das KBs: o projeto task-spec não usa mais KBs e conduz isso via Context7. Avalie isso."

**Reenquadramento feito na sessão:** o usuário não soube apontar uma dor única e pediu para **testar KB x modelo task-spec** e ver se, ao final, a alternativa atinge o mesmo nível que o KB entrega hoje. A feature passa a ser um **experimento comparativo (bancada)**. A decisão sobre o futuro das KBs é consequência do resultado, não entrada.

**Contexto Coletado (AgentSpec):**

- 39 domínios em `.claude/kb/`, 471 arquivos `.md`, ~235 mil palavras (~3,0 MB). O maior é `microsoft-fabric` (~29,6 mil palavras); o menor, `qdrant` (~1,6 mil).
- `_index.yaml` (v2.2) registra `mcp_validated` entre **2026-02-17 e 2026-04-22**; 22 domínios estão em 2026-03-26. Hoje (2026-09-23) as KBs têm **5 a 7 meses**.
- Não existe nenhum `log.md` em `.claude/kb/`. O `/ingest-kb` grava nesse arquivo a cada ingestão; a ausência indica que **o refresh nunca rodou** desde o ship do KB_EVOLUTION (2026-04-23).
- O `kb-evolution-agent` declara `tools: [Read, Write, Edit, Grep, Glob, Bash, TodoWrite]`, **sem nenhuma ferramenta MCP**. Como subagent, ele não consegue chamar o Context7 que o próprio fluxo exige.
- 30 arquivos de agent citam Context7 e liberam o prefixo `mcp__upstash-context-7-mcp__*`. O ambiente do usuário não tem esse servidor configurado; o Context7 disponível é o conector `claude.ai Context7`, que usa outro prefixo e estava sem autenticação nesta sessão. **Na prática, os agents não alcançam o Context7.**
- 28 agents declaram "KB-FIRST RESOLUTION … mandatory". `kb_domains` aparece em ~70 arquivos de agent e alimenta o `scripts/generate-agent-router.py` (tabela "KB Domain → Agents").
- Distribuição: `build-plugin.sh` copia `kb/` para `plugin/` reescrevendo caminhos; `generate-grok-plugin.py` vendoriza `kb/`; `generate-codex-plugin.py` injeta "Consult these AgentSpec KB domains…" nas instruções. O `generate-dsh-bundle.py` não referencia `kb/` (a confirmar no Define).

**Contexto Coletado (task-spec, leitura):**

- O task-spec **nunca teve KB**: não há diretório de KB nem commits de remoção no histórico. A premissa "deixou de usar KB" não se confirma. Ele simplesmente nasceu sem KB.
- Modelo de conhecimento: (1) **leitura do repositório** (Phase 3 — SCAN), (2) **pesquisa externa opcional** (Phase 2 — RESEARCH), (3) **Fast Batch**, que pula a pesquisa quando o domínio é conhecido (`docs/authoring-workflow.md`).
- A pesquisa normaliza para o contrato `AuthoringEvidence/v1` (`spec/schemas/authoring-evidence.schema.json`): provider, query, `observed_at`, URL, `retrieved_at`, `content_digest`, afirmações com `source_refs` e estados explícitos (`unavailable`, `rate_limited`, `timeout`…).
- O Context7 aparece nas docs mais antigas (tríade CAW: "W = Context7, Exa, Ref"; `docs/runbooks/from-fuzzy-intent.md`; `docs/patterns/anti-patterns-extraction.md`; broker Kimi em `harness/engines/kimi.md`). A Phase 2 atual cita Firecrawl, Tavily e Exa. `docs/guides/research-providers.md` avisa que o repositório só comprova **adapters fake offline**.
- O uso de pesquisa externa no task-spec é **pontual e na autoria**: extrair anti-patterns reais e fatos de versão (ex.: endpoint OTEL do Langfuse v3). Não é um substituto geral para uma base de padrões.
- `docs/runbooks/first-spec-walkthrough.md` roda **100% local**, sem Context7.

**Contexto Técnico Observado (para o Define):**

| Aspecto | Observação | Implicação |
|---------|------------|------------|
| Localização Provável | `scripts/kb-bench/` (runner, tarefas, relatório) + `tests/` + alvo no `Makefile` | Segue o padrão de `scripts/judge.py` e da suíte pytest existente |
| Domínios KB Relevantes | dbt, airflow, medallion, data-modeling, microsoft-fabric, shadowtraffic (amostra); prompt-engineering, testing (para a bancada) | Amostra estratificada; ver Decisão 3 |
| Padrões IaC | N/A | Sem infraestrutura; execução local via `claude -p` |
| MCP | `@upstash/context7-mcp` local | Bate com o prefixo já declarado nos agents |

---

## Perguntas de Descoberta e Respostas

| # | Pergunta | Resposta | Impacto |
|---|----------|----------|---------|
| 1 | Qual é a dor principal que motiva rever as KBs? | "Não sei responder; vamos rodar testes KB x task-spec para ver se ao final atingimos o mesmo nível que o KB já faz hoje." | A feature vira experimento de medição; nenhuma migração entra no MVP |
| 2 | Quais configurações comparar? (com esclarecimento) | A + B + C + D | Quatro braços, incluindo controle sem nada e a KB enxuta híbrida |
| 3 | Qual amostra de domínios? | Estratificada 6 (2 por estrato) | Resultado e recomendação saem **por estrato** |
| 4 | Como medir a qualidade? | "Verificar se o eval passa, se precisa de retry ou se o humano revisa." | Métrica no modelo de aceite do task-spec: PASS de primeira / PASS com retry / humano |
| 5 | De onde vêm as tarefas de teste? | Mistas | Parte reais do usuário, parte sintéticas com eval executável |
| 6 | Como acessar o Context7? | MCP local upstash | Sem trocar prefixo nos agents; independente do conector claude.ai |
| 7 | Regra de "empate" (após explicação com exemplo) | Regra simples | Ver Decisão 5 |

---

## Inventário de Dados de Exemplo

| Tipo | Localização | Quantidade | Notas |
|------|-------------|------------|-------|
| Tarefas reais | A indicar pelo usuário no Define (BUILD_REPORTs, modelos dbt, DAGs, notebooks Fabric de projetos próprios) | ~9 (metade das 18) | Representam o uso real |
| Tarefas sintéticas | `scripts/kb-bench/tasks/` (a criar) | ~9 | Escritas para cobrir cada estrato; cada uma com eval executável |
| Ground truth | N/A | 0 | O critério é o eval da tarefa, não comparação com saída de referência |
| Código relacionado | `scripts/judge.py`, `tests/`, `Makefile`, `.claude/sdd/archive/KB_EVOLUTION/` | — | Padrão de script Python + pytest; histórico do desenho do refresh |
| Referência externa | `task-spec/spec/schemas/authoring-evidence.schema.json`, `task-spec/docs/authoring-workflow.md` | — | Modelo de evidência citada e de aceite eval → retry → humano |

**Como os exemplos serão usados:**

- As tarefas são a entrada idêntica para os quatro braços.
- O eval de cada tarefa decide o desfecho (PASS de primeira, PASS com retry, humano).
- As tarefas reais protegem contra o viés de sintéticas escritas "no formato que o KB já cobre".

---

## Abordagens Exploradas

> As abordagens tratam de **como rodar o experimento**. As opções de destino (manter, enxugar ou aposentar) são os braços do teste.

### Abordagem A: Bancada local no AgentSpec ⭐ Recomendada

**Descrição:** `scripts/kb-bench/` em Python. Cada tarefa é um YAML com prompt, domínio, estrato e comandos de eval. O runner executa cada braço em `claude -p` headless com contexto controlado, aplica o loop eval → retry (N=2) → fila humana e grava JSONL (desfecho, tentativas, tokens, latência). O relatório MD sai por braço e estrato.

**Prós:**
- Reproduzível e versionado no repositório; dá para repetir quando o modelo mudar.
- Usa exatamente o critério pedido pelo usuário.
- Segue padrões existentes (`judge.py`, pytest, Makefile).

**Contras:**
- Precisa ser construída.
- Custo de execução: 6 domínios × ~3 tarefas × 4 braços × até 3 tentativas.

**Por que Recomendada:** é a única opção que controla a variável do teste (a fonte de conhecimento) e produz um resultado repetível.

---

### Abordagem B: task-spec como bancada

**Descrição:** escrever as tarefas como `T-*.md` com evals e rodar `taskspec gate/run/accept` para cada braço.

**Prós:**
- Reaproveita um loop de aceite maduro, alinhado ao modelo citado pelo usuário.

**Contras:**
- Acopla o AgentSpec a outro repositório e ao binário Go.
- Não está claro como controlar o contexto por braço no backend de execução do task-spec, e essa é justamente a variável sob teste.

---

### Abordagem C: Rodada manual

**Descrição:** sessões manuais por braço e registro em planilha.

**Prós:**
- Começa imediatamente.

**Contras:**
- Não é reproduzível.
- O avaliador sabe qual braço está vendo (viés).
- Não dá para refazer quando o modelo mudar.

---

## Desenho dos Braços

| Braço | Conhecimento disponível | MCP | Papel no teste |
|-------|-------------------------|-----|----------------|
| **A — KB atual** | `.claude/kb/{domain}` completo (KB-first, como hoje) | Nenhum | Linha de base a bater |
| **B — Estilo task-spec** | Nenhuma KB | Context7 (upstash) | Consulta documentação oficial na hora |
| **C — KB enxuta + Context7** | Só conteúdo opinativo (anti-patterns, decisões, convenções), sem referência de API | Context7 (upstash) | Híbrido |
| **D — Controle** | Nada | Nenhum | Mede quanto o modelo já sabe sozinho |

**Amostra estratificada (6 domínios, ~3 tarefas cada = ~18):**

| Estrato | Domínios | Hipótese |
|---------|----------|----------|
| Biblioteca que muda rápido | dbt, airflow | B ou C iguala ou supera A (KB defasada 5–7 meses) |
| Conceitual/opinativo | medallion, data-modeling | Context7 sem cobertura; A ou C vence B |
| Nicho/proprietário | microsoft-fabric, shadowtraffic | Pouca cobertura externa; A vence com folga |

**Fluxo por tarefa:**

```text
Tarefa ──► braço (A|B|C|D) ──► eval executável
                                 ├─ passou             → PASS de primeira
                                 ├─ falhou → retry ≤2  → PASS com retry
                                 └─ ainda falhou       → fila de revisão humana
```

**Controles:** mesmo modelo, mesmo prompt e mesmos evals em todos os braços. Ordem de execução embaralhada. Na fila humana, a identidade do braço fica oculta.

---

## Abordagem Selecionada

| Atributo | Valor |
|----------|-------|
| **Escolhida** | Abordagem A — Bancada local no AgentSpec |
| **Confirmação do Usuário** | 2026-09-23 (Validação 1) |
| **Justificativa** | Reproduzível, controla a fonte de conhecimento como única variável e usa o critério eval → retry → humano |

---

## Principais Decisões Tomadas

| # | Decisão | Justificativa | Alternativa Rejeitada |
|---|---------|---------------|----------------------|
| 1 | Medir antes de migrar | O usuário não tem uma dor única; a decisão precisa de evidência | Migrar direto para Context7 "porque o task-spec faz" (a premissa não se confirmou) |
| 2 | Quatro braços, com controle D | Separa o ganho real do KB do conhecimento que o modelo já tem | Duelo A x B apenas |
| 3 | Amostra estratificada de 6 domínios | O resultado provavelmente difere por tipo de domínio | Todos os 39 (caro); 3 domínios (frágil) |
| 4 | Critério = eval pass / retry / humano | Pedido do usuário; mesmo modelo de aceite do task-spec | Juiz LLM como critério principal |
| 5 | **Regra simples de decisão, fixada antes de rodar:** num estrato, B ou C substitui o KB se resolver **pelo menos o mesmo número de tarefas que A (contando retry)** e **não mandar mais tarefas para revisão humana**. Tokens e latência servem só como desempate. Se D empatar com A, o KB daquele estrato é candidato a aposentar | Regra legível e robusta para amostra pequena; evita ajustar o critério depois do resultado | Limiares percentuais (≤5 pp, ≤1,5× tokens), que confundiram e são instáveis com ~6 tarefas por estrato |
| 6 | Context7 via MCP local `@upstash/context7-mcp` | Bate com o prefixo já declarado em 30 agents; independe do conector claude.ai; versão fixável | Conector claude.ai (exige trocar prefixos); API HTTP direta (foge do uso real) |
| 7 | KB enxuta (braço C) só nos 6 domínios da amostra | É o mínimo para testar a hipótese híbrida | Enxugar os 39 antes do resultado |

---

## Features Removidas (YAGNI)

| Feature Sugerida | Motivo da Remoção | Pode Adicionar Depois? |
|------------------|-------------------|----------------------|
| Migrar, enxugar ou apagar os 39 domínios | Depende do placar por estrato | Sim — feature seguinte, guiada pelo relatório |
| Alterar `build-plugin.sh` e os bundles Codex, Grok e DeepSeek | Só faz sentido se o KB mudar | Sim |
| Reescrever `kb_domains` e a "KB-first resolution" nos agents | Idem; também afeta o agent-router | Sim |
| Corrigir em massa o prefixo MCP nos 30 agents e dar MCP ao `kb-evolution-agent` | Fora do experimento; só os braços do teste recebem o ajuste | Sim — registrado como achado para correção independente |
| Refresh automático agendado das KBs | Só vale se o KB continuar existindo naquele estrato | Sim |
| Contrato `AuthoringEvidence/v1` completo | O MVP precisa só registrar fonte e uso; o contrato completo vem se o braço B/C vencer | Sim |
| Juiz LLM cruzado e dashboard | O critério escolhido é eval + humano | Sim |
| Rodar em vários modelos | Pertence a `LLM_PHASE_ROUTING`; aqui o modelo é fixo | Sim |

---

## Validações Incrementais

| Seção | Apresentada | Feedback do Usuário | Ajustada? |
|-------|-------------|---------------------|-----------|
| Abordagens de execução (A/B/C) | ✅ | Escolheu A — Bancada local | Não |
| Escopo, YAGNI e regra de decisão | ✅ | "Não entendi esse ponto" → reexplicado com fluxo e placar de exemplo → escolheu a regra simples | Sim — limiares percentuais trocados pela regra simples |
| Fronteiras com as outras frentes e escopo final | ✅ | "Sim, pode gerar" | Não |

---

## Dependências e Fronteiras com as Outras Frentes

| Frente | Onde encosta | O que fica aqui | O que fica lá |
|--------|--------------|-----------------|---------------|
| `LIVING_MEMORY` | Ambas tratam de "conhecimento" fornecido ao agent | **Conhecimento externo**: como a ferramenta funciona (KB/Context7). A KB enxuta guarda só convenções genéricas do AgentSpec | **Conhecimento do projeto**: o que foi decidido e feito em cada fase. Decisões de um projeto nunca entram na KB |
| `POST_BUILD_EVALS` | Ambas usam o loop eval → retry → humano | Loop **mínimo e descartável**, só para este experimento | A camada de evals do produto. Se nascer antes, a bancada pode migrar para ela |
| `LLM_PHASE_ROUTING` | Escolha de modelo | Modelo **fixo** em todos os braços, para isolar a variável | Qual modelo usar em cada fase |
| `JEV_AGENT_SELECTION` | `kb_domains` alimenta o agent-router | Nada muda no roteamento durante o experimento | Seleção de agents por fase; o impacto de um KB menor no sinal de roteamento é avaliado depois do placar |

---

## Requisitos Sugeridos para /define

### Declaração do Problema (Rascunho)

O AgentSpec mantém 39 domínios de KB (~235 mil palavras) defasados em 5 a 7 meses, sem refresh efetivo e sem saber quanto eles melhoram o resultado dos agents em relação a consultar documentação oficial na hora (Context7) ou a não usar nada. Falta evidência para decidir manter, enxugar ou aposentar cada tipo de domínio.

### Usuários-Alvo (Rascunho)

| Usuário | Dor |
|---------|-----|
| Mantenedor do AgentSpec | Manter 39 domínios sem saber se valem o custo; o refresh não acontece |
| Usuário do plugin | Pode receber padrões desatualizados sem perceber |

### Critérios de Sucesso (Rascunho)

- [ ] O MCP `@upstash/context7-mcp` responde a `resolve-library-id` e `query-docs` dentro dos braços B e C (smoke test registrado).
- [ ] ~18 tarefas (3 por domínio × 6 domínios, mistas) têm eval executável que falha num resultado vazio ou errado.
- [ ] A bancada roda os 4 braços com o mesmo modelo e grava por execução: braço, tarefa, desfecho (PASS de primeira / PASS com retry / humano), número de tentativas, tokens e latência.
- [ ] A fila de revisão humana esconde qual braço gerou a saída.
- [ ] O relatório mostra o placar por braço e estrato e aplica a regra da Decisão 5, com recomendação explícita por estrato (substituir, enxugar, manter ou aposentar).
- [ ] A bancada é repetível com um comando (`make kb-bench` ou equivalente).

### Restrições Identificadas

- O Context7 depende de rede e de um MCP externo. Uma falha dele deve ser registrada como desfecho próprio (`unavailable`), não como falha do braço.
- O custo é limitado pela amostra (~18 tarefas × 4 braços × até 3 tentativas).
- Com ~6 tarefas por estrato, o resultado é indicativo, não estatístico; o relatório deve dizer isso.
- As KBs atuais e os agents de produção não podem ser alterados durante o experimento (a KB enxuta do braço C fica isolada na bancada).
- Documentos SDD em pt-BR; código e comandos em inglês.

### Fora do Escopo (Confirmado)

- Qualquer mudança nos 39 domínios, no `_index.yaml`, no `build-plugin.sh` ou nos bundles gerados.
- Alterar `kb_domains`, a "KB-first resolution" ou o agent-router.
- Corrigir o prefixo MCP nos agents de produção e dar MCP ao `kb-evolution-agent` (registrado como achado).
- Refresh agendado, contrato `AuthoringEvidence/v1` completo, juiz LLM, dashboard e múltiplos modelos.

### Perguntas Abertas para o Define

1. Quais tarefas reais o usuário vai fornecer (repositórios e arquivos) para cada um dos 6 domínios?
2. Qual modelo fixo usar nos braços (padrão da sessão ou o `sonnet` declarado nos agents)?
3. O braço C: quem define o que é "opinativo" ao enxugar a KB? Proposta: anti-patterns, decisões com justificativa e convenções de nomenclatura ficam; tabelas de API e sintaxe saem.
4. Existe cobertura no Context7 para `shadowtraffic` e `microsoft-fabric`? Confirmar no smoke test, porque isso define se B e C são viáveis nesse estrato.
5. O `generate-dsh-bundle.py` vendoriza `kb/`? Confirmar, para medir o impacto de uma futura mudança.

---

## Achados Colaterais (fora do experimento)

| # | Achado | Evidência | Sugestão |
|---|--------|-----------|----------|
| 1 | O `kb-evolution-agent` não tem ferramenta MCP, então não consegue chamar o Context7 | `.claude/agents/dev/kb-evolution-agent.md` (frontmatter `tools`) | Corrigir em feature própria ou via `/iterate` |
| 2 | Agents liberam `mcp__upstash-context-7-mcp__*`, mas esse servidor não está configurado no ambiente do usuário | `grep` nos agents; `~/.claude.json` sem o servidor | A instalação do MCP upstash (Decisão 6) resolve para quem o configurar; documentar como pré-requisito |
| 3 | O `/ingest-kb` nunca registrou execução | Ausência de `log.md` em `.claude/kb/` | Explica a defasagem; entra no relatório como contexto |

---

## Resumo da Sessão

| Métrica | Valor |
|---------|-------|
| Perguntas Feitas | 7 (incluindo 2 esclarecimentos) |
| Abordagens Exploradas | 3 |
| Features Removidas (YAGNI) | 8 |
| Validações Concluídas | 3 |
| Duração | ~1 sessão |

---

## Próximo Passo

**Pronto para:** `/define .claude/sdd/features/BRAINSTORM_KB_CONTEXT7_REFRESH.md`
