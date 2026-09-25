# BRAINSTORM: Living Memory (Segundo Cérebro entre Fases)

> Sessão exploratória para clarificar intenção e abordagem antes da captura de requisitos

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | LIVING_MEMORY |
| **Data** | 2026-09-23 |
| **Autor** | brainstorm-agent |
| **Status** | Pronto para Define |

---

## Ideia Inicial

**Entrada Bruta:** "Esse projeto gera os MDs, mas precisamos de uma memória mais viva. Nas fases de definição e de desenho, e talvez também no build (faça essa avaliação), precisamos dar mais contexto de tudo o que foi feito em cada etapa do projeto. Seria o segundo cérebro."

**Contexto Coletado:**

- **Memória em arquivo (2 níveis)** — `.claude/sdd/MEMORY.md` (projeto) e `${AGENTSPEC_MEMORY_DIR:-~/.agentspec}/MEMORY.md` (global). Escrita apenas por `/memory` (manual) e pelo Step 8 do `/ship`. O SessionStart (`plugin-extras/scripts/init-workspace.sh`, `surface_memory`) injeta só os headings `## ` como índice compacto.
- **Evidência de falha da captura no fim do fluxo:** este repositório **não tem** `.claude/sdd/MEMORY.md`, embora duas features tenham sido entregues (`archive/KB_EVOLUTION`, `archive/FRONTEND_ECOSYSTEM`). As lições ficaram presas nos `SHIPPED_*.md`.
- **Correção (2026-09-23, fase Design):** o Step 8 do `/ship` só existe desde v3.3.0 (2026-06-21); as duas features arquivadas foram entregues antes. A ausência de `MEMORY.md` abaixo **não** é evidência de falha da captura no fim do fluxo — só mostra que ela nunca foi exercitada.
- **Blackboard** (`BLACKBOARD_{FEATURE}.md`) — já é descrito em `WORKFLOW_CONTRACTS.yaml` como "the feature's living memory", com Log de Decisões append-only, Perguntas Abertas, Interfaces, Status de Arquivos e Melhorias. Porém **nasce só no Build** (seed pelo build-agent a partir do DESIGN).
- **`/work` + `.active`** — ponteiro da feature ativa; carrega DEFINE → DESIGN → BLACKBOARD → BUILD_REPORT e registra melhorias no Blackboard.
- **Carga de contexto atual dos agentes:** `define-agent` lê BRAINSTORM + template + CLAUDE.md + `_index.yaml` de KB; `design-agent` lê DEFINE + padrões KB. **Nenhum lê `MEMORY.md`, `archive/` ou Blackboards de outras features.**
- **Os DESIGNs já registram bem o porquê** — `archive/KB_EVOLUTION/DESIGN_KB_EVOLUTION.md` tem 4 decisões com "Alternativas Rejeitadas". O problema não é ausência de registro, é que **ninguém relê** esse registro depois.
- **`/iterate`** faz análise de cascata entre documentos, mas não deixa trilha do motivo da mudança fora do próprio documento editado.

**Referência externa — task-spec** (`/Users/marcoleloam/projetos/framework/task-spec`, leitura):

| O que o task-spec faz | Aproveitamos? |
|-----------------------|---------------|
| Contexto entre etapas = arquivos no git amarrados por hash (`evidence_refs {ref, role, digest}`, `TaskRevision`, `TaskHandoff`) | Não no MVP — prova autoridade, não ajuda a lembrar |
| Open Questions não resolvidas exigem `status: blocked` ("an agent may not silently decide them") | **Sim** — perguntas abertas bloqueiam transição de fase |
| Replanejamento por `supersedes: <id>` com motivo, sem editar no lugar | **Sim** — decisões novas substituem as antigas via "Substitui" |
| Índice derivado reconstruível (`_state.yaml`) + ledger append-only (`_metrics.jsonl`) | **Sim** — `MEMORY_INDEX.md` gerado e descartável |
| Pesquisa externa normalizada como `AuthoringEvidence/v1`, proibida como critério de aceite | Fronteira com `KB_CONTEXT7_REFRESH` (ver abaixo) |
| Lições, log de decisões entre tarefas, reuso de `tasks/done/` | **Não existe** no task-spec — precisamos desenhar isso nós mesmos |
| Sem DB/vector store no core ("files are the moat") | Alinhado com a remoção proposital do MemPalace MCP |

**Contexto Técnico Observado (para o Define):**

| Aspecto | Observação | Implicação |
|---------|------------|------------|
| Localização Provável | `.claude/sdd/templates/`, `.claude/agents/workflow/`, `.claude/commands/workflow/`, `.claude/sdd/architecture/WORKFLOW_CONTRACTS.yaml`, `plugin-extras/scripts/` | Mudança de framework (prompts + contrato + 1 script), não de código de aplicação |
| Domínios KB Relevantes | `genai` (multi-agent, memória), `python` (script do índice), `testing` (pytest do script) | Padrões a consultar no Design |
| Padrões existentes a reusar | `status-dashboard.py` (script determinístico que lê MDs e gera artefato), `memory_index()` em `init-workspace.sh` | Mesmo estilo: stdlib pura, sem LLM, sem rede |
| Distribuição | `build-plugin.sh` reescreve paths de `.claude/` → `plugin/`; `plugin-extras/` é mesclado | Script novo precisa entrar no build e nos mirrors (Codex, Grok, DeepSeek — commits recentes) |
| IaC | N/A | — |

---

## Perguntas de Descoberta e Respostas

| # | Pergunta | Resposta | Impacto |
|---|----------|----------|---------|
| 1 | Onde a falta de contexto mais dói: entre fases, entre features ou entre sessões? | **Os três igualmente** | A solução precisa cobrir 3 dimensões: diário por fase, índice entre features, retomada entre sessões |
| 2 | Quem registra o que acontece em cada fase? | **Automático pelos agentes de fase** | Cada agente anexa ao sair da fase; não depende de `/memory` manual (que comprovadamente falha) |
| 3 | Como o contexto volta ao agente ao entrar numa fase? | **Índice curto + leitura sob demanda** | Mesmo princípio do SessionStart: ponteiro, não payload. Limita custo de tokens |
| 4 | Que exemplos usar para ancorar e validar? | **Features arquivadas** (KB_EVOLUTION, FRONTEND_ECOSYSTEM) | Viram fixtures de teste do script e do resumo de entrada |
| 5 | Qual abordagem? | **A — Blackboard do ciclo todo** | Reaproveita artefato existente; sem sexto tipo de documento |
| 6 | O que cortar do MVP? | Usuário delegou → aplicada a recomendação | Ver YAGNI |

---

## Inventário de Dados de Exemplo

| Tipo | Localização | Quantidade | Notas |
|------|-------------|------------|-------|
| Feature arquivada completa (com BRAINSTORM) | `.claude/sdd/archive/KB_EVOLUTION/` | 5 MDs | DESIGN com 6 decisões e alternativas rejeitadas; SHIPPED com lições em 4 categorias |
| Feature arquivada (sem BRAINSTORM) | `.claude/sdd/archive/FRONTEND_ECOSYSTEM/` | 4 MDs | Caso de feature que começou direto no Define |
| Template do Blackboard | `.claude/sdd/templates/BLACKBOARD_TEMPLATE.md` | 1 | Base a estender (Log de Decisões, Perguntas, Melhorias) |
| Código relacionado | `plugin-extras/scripts/status-dashboard.py`, `init-workspace.sh` (`memory_index`, `surface_memory`) | 2 | Padrão de script determinístico e de injeção no SessionStart |
| Memória de projeto | `.claude/sdd/MEMORY.md` | 0 | **Ausente** — evidência do problema |

**Como os exemplos serão usados:**

- Fixtures de pytest para `memory-index.py`: o índice gerado a partir de `archive/` deve conter as 6 decisões do DESIGN do KB_EVOLUTION e as lições dos dois SHIPPED.
- Teste de aceite do resumo de entrada: um DEFINE novo que compartilhe o domínio `kb` deve receber no resumo a decisão "log.md por domínio, não central" do KB_EVOLUTION.
- Caso FRONTEND_ECOSYSTEM valida o caminho "brainstorm pulado → Blackboard nasce no Define".

---

## Abordagens Exploradas

### Abordagem A: Blackboard do Ciclo de Vida Inteiro ⭐ Recomendada

**Descrição:** o `BLACKBOARD_{FEATURE}.md` passa a nascer no `/brainstorm` (ou no `/define`, quando o brainstorm for pulado) em vez do `/build`. Cada agente de fase, ao sair, anexa um bloco na nova seção **Diário por Fase** (decisões com alternativa rejeitada, perguntas respondidas, premissas, mudanças de rumo com "Substitui"). Um script determinístico gera `.claude/sdd/MEMORY_INDEX.md` — uma linha por decisão/premissa/lição, cobrindo Blackboards ativos, `archive/` e `MEMORY.md`. Na entrada de cada fase o agente lê um resumo curto (≤ ~15 linhas); o SessionStart passa a mostrar também as últimas entradas do Diário da feature em `.active`.

**Prós:**

- Reaproveita um artefato que os agentes já sabem ler/escrever e que o contrato já chama de "living memory"
- Nenhum sexto tipo de documento; nenhuma dependência nova (arquivos + git + stdlib)
- Cobre as 3 dimensões: fase (Diário), feature (índice), sessão (`.active` + SessionStart)
- O índice é derivado e reconstruível — pode ser apagado e regenerado sem perda

**Contras:**

- "Blackboard" deixa de ser só coordenação do Build; o template cresce
- O resumo de entrada exige disciplina para não virar despejo de contexto

**Por que Recomendada:** ataca a causa observada (ninguém relê o que já foi escrito) com o menor número de peças novas, e ainda corrige a falha comprovada da captura manual no fim do fluxo.

---

### Abordagem B: Diário Separado (`JOURNAL_{FEATURE}.md`)

**Descrição:** novo arquivo append-only por feature alimentado por todas as fases; Blackboard continua exclusivo do Build.

**Prós:**

- Separação limpa entre coordenação (Build) e memória (ciclo todo)

**Contras:**

- Duplica o Log de Decisões do Blackboard
- Mais um artefato que todos os agentes precisam conhecer
- O índice entre features continua necessário do mesmo jeito

---

### Abordagem C: Grafo Consultável com Amarração por Hash (estilo task-spec)

**Descrição:** frontmatter com `relates_to`, `supersedes` e `evidence_refs` com digest em cada documento, mais um script de consulta (`memory-query`), possivelmente com SQLite local.

**Prós:**

- Rastreabilidade forte; consultas ricas ("o que decidimos sobre X?")

**Contras:**

- Maquinaria desproporcional ao volume (dezenas de MDs)
- Digest prova autorização, não ajuda a lembrar — e o próprio task-spec não resolve o "segundo cérebro"
- SQLite seria dependência nova sem justificativa

---

### Descartada de Saída: MCP / Vector Store (estilo MemPalace)

O MemPalace MCP foi removido de propósito no v3.3.0 em favor da memória em arquivo. O volume atual cabe folgado num índice em Markdown; reintroduzir um servidor ou embeddings violaria essa decisão sem ganho demonstrado. **Nenhuma dependência nova é proposta.**

---

## Abordagem Selecionada

| Atributo | Valor |
|----------|-------|
| **Escolhida** | Abordagem A — Blackboard do Ciclo de Vida Inteiro |
| **Confirmação do Usuário** | 2026-09-23 (sessão de brainstorm) |
| **Justificativa** | Menor número de peças novas; reaproveita o Blackboard; sem dependência nova; cobre fase, feature e sessão |

### O que cada fase registra (validado)

| Fase | Anexa ao Diário | Lê ao entrar |
|------|-----------------|--------------|
| **Brainstorm** | Cria o Blackboard. Perguntas respondidas (`Q`), abordagem escolhida e rejeitadas (`D`), cortes YAGNI | Linhas do `MEMORY_INDEX` que cruzam com o tema |
| **Define** | Cria o Blackboard se o brainstorm foi pulado (importando o BRAINSTORM se existir). Premissas (`A`), perguntas resolvidas ou abertas, mudanças de escopo vs. brainstorm (`D` com "Substitui") | Resumo do Blackboard + índice por domínios KB |
| **Design** | Uma linha `D` por ADR inline, **apontando** para a seção do DESIGN (sem copiar). Premissas validadas ou derrubadas | Resumo + decisões de features passadas nos mesmos domínios |
| **Build** | Já tem Log de Decisões e Perguntas. **Novo:** registro de **desvios do DESIGN** — `D` que substitui a decisão de Design e diz o motivo | Como hoje |
| **Iterate / Work** | Toda mudança de requisito/desenho vira `D` com "Substitui"; Melhorias continua | Resumo |
| **Ship** | Consolida 3–5 lições no `MEMORY.md`, regenera o índice, arquiva o Blackboard | — |

**Avaliação do Build (pedida pelo usuário):** é a fase que **menos** precisa de mudança — o Blackboard foi feito para ela. O ganho real está no **Define e no Design**, que hoje saem da fase sem rastro vivo. No Build o acréscimo é só o registro de desvios do DESIGN, o que mais se perde hoje (o BUILD_REPORT diz o que foi feito, não por que divergiu).

**Regra de ouro:** o Diário guarda **ponteiros + uma frase de porquê**, nunca cópias. DEFINE/DESIGN são a fonte da verdade do **resultado**; o Diário é a fonte da verdade da **trajetória**.

### Índice e recuperação (validado)

```text
| FEATURE      | fase   | tipo | id    | frase                            | domínios KB | onde ler                                  |
| KB_EVOLUTION | design | D    | D-003 | log.md por domínio, não central  | kb          | archive/KB_EVOLUTION/DESIGN…#decisao-3    |
```

- **Gerador:** `memory-index.py` (stdlib, sem LLM, sem rede), mesmo estilo do `status-dashboard.py`.
- **Regeneração:** ao sair de cada fase e no `/ship`; descartável e reconstruível a qualquer momento.
- **Entrada de fase:** ≤ ~15 linhas — decisões vigentes da feature (substituídas ficam de fora), perguntas abertas, e linhas de outras features com domínio KB em comum.
- **SessionStart:** além do índice do `MEMORY.md`, as últimas 5 entradas do Diário da feature em `.active`.
- **Ligações entre features:** derivadas dos domínios KB em comum + campo opcional `Relacionada a:` nos metadados do Blackboard. Sem grafo.

---

## Principais Decisões Tomadas

| # | Decisão | Justificativa | Alternativa Rejeitada |
|---|---------|---------------|----------------------|
| 1 | Captura automática pelos agentes de fase | `/memory` manual e o passo final do `/ship` não bastaram — repo sem `MEMORY.md` após 2 features entregues | Manter só `/memory` manual; captura bruta + curadoria humana |
| 2 | Estender o Blackboard ao ciclo todo | Artefato já existente, já chamado de "living memory" no contrato | `JOURNAL_{FEATURE}.md` separado (duplicaria o Log de Decisões) |
| 3 | Recuperação por índice curto + leitura sob demanda | Mesmo princípio do SessionStart; custo de tokens previsível | Carga completa do log; busca sem carga automática |
| 4 | Índice gerado por script determinístico | Reconstruível, testável, sem LLM (lição do `_state.yaml` do task-spec) | Índice mantido à mão pelo modelo |
| 5 | Nenhuma dependência nova | MemPalace MCP removido de propósito; volume cabe em arquivo | MCP, vector store, SQLite |
| 6 | Perguntas abertas bloqueiam a transição de fase | Impede o Design de decidir em silêncio o que o Define deixou aberto (padrão task-spec) | Perguntas só como anotação (comportamento atual fora do Build) |
| 7 | Decisões são substituídas, nunca editadas ("Substitui D-00X") | Preserva a trajetória; padrão `supersedes` do task-spec e já regra do Blackboard | Editar a decisão no lugar |

---

## Features Removidas (YAGNI)

| Feature Sugerida | Motivo da Remoção | Pode Adicionar Depois? |
|------------------|-------------------|----------------------|
| Amarração por hash (`evidence_refs` com digest) | Prova autorização/aceite, não ajuda a lembrar; o git já dá histórico | Sim — se `POST_BUILD_EVALS` precisar amarrar evidência |
| Busca por texto livre (`/memory search "X"`) | O `MEMORY_INDEX.md` já é grep-ável | Sim |
| Migração retroativa automática das features arquivadas | Só 2 features; viram fixtures. O índice já lê as lições dos `SHIPPED_*.md` | Sim |
| Grafo de links entre documentos | Domínios KB em comum + `Relacionada a:` cobrem o caso | Sim |
| MCP / vector store / embeddings | Decisão explícita de v3.3.0; volume não justifica | Não sem nova justificativa |
| Captura bruta + curadoria humana obrigatória | O usuário escolheu captura automática; o `/ship` já consolida no `MEMORY.md` | Sim |

---

## Validações Incrementais

| Seção | Apresentada | Feedback do Usuário | Ajustada? |
|-------|-------------|---------------------|-----------|
| Abordagens A/B/C | ✅ | Escolheu A | Não |
| O que cada fase registra (incl. avaliação do Build) | ✅ | "Está certa" | Não |
| Índice, recuperação e YAGNI | ✅ | Delegou os cortes → recomendação aplicada | Sim (cortes aplicados) |

---

## Fronteiras com as Outras Frentes

> Cinco frentes em paralelo. Aqui só registramos onde LIVING_MEMORY encosta nas demais — **não resolvemos** as outras.

| Frente | Onde encosta | Quem é dono de quê |
|--------|--------------|--------------------|
| `POST_BUILD_EVALS` | Resultado de eval é memória? | **Evals** é dona de rodar, pontuar e guardar o relatório. **Living Memory** só registra uma linha `E` no Diário (veredito + ponteiro para o relatório) e deixa um desvio/lição virar `D`/lição quando o eval mudar uma decisão. Amarração por hash, se necessária, nasce lá. |
| `KB_CONTEXT7_REFRESH` | Conhecimento externo × memória do projeto | **KB/Context7** é dona do conhecimento externo (como a ferramenta funciona). **Living Memory** é dona do que *este projeto decidiu*. Quando uma decisão depender de doc externa, o Diário guarda a fonte + data como ponteiro, sem copiar conteúdo. Nada de Context7 entra no `MEMORY_INDEX`. |
| `LLM_PHASE_ROUTING` | Qual modelo produziu cada fase | **Routing** decide o modelo. **Living Memory** pode reservar um campo opcional "modelo" no cabeçalho do bloco de fase do Diário para rastreabilidade — preenchido por Routing, não decidido aqui. |
| `JEV_AGENT_SELECTION` | Quais agentes atuaram / o índice como insumo de seleção | **JEV** decide quais agentes atuam. **Living Memory** já registra `@agente` nas entradas. Se o JEV consome o `MEMORY_INDEX` como insumo, é pergunta em aberto dessa frente — capacidades do JEV não foram avaliadas aqui. |

---

## Requisitos Sugeridos para /define

### Declaração do Problema (Rascunho)

As fases do AgentSpec produzem documentos de **resultado**, mas a **trajetória** (perguntas respondidas, alternativas rejeitadas, premissas, mudanças de rumo) não é relida pela fase seguinte, por features futuras nem por sessões posteriores — e a captura manual no fim do fluxo comprovadamente não acontece.

### Usuários-Alvo (Rascunho)

| Usuário | Dor |
|---------|-----|
| Mantenedor que usa AgentSpec em projetos de dados | Reexplica decisões ao retomar uma feature ou ao iniciar outra no mesmo domínio |
| Agentes de fase (define, design, build) | Decidem sem saber o que fases e features anteriores já decidiram ou rejeitaram |

### Critérios de Sucesso (Rascunho)

- [ ] Toda feature nova tem `BLACKBOARD_{FEATURE}.md` criado no Brainstorm ou no Define (não mais só no Build)
- [ ] Brainstorm, Define, Design, Build, Iterate e Ship anexam ao Diário ao sair da fase, sem comando manual
- [ ] `memory-index.py` gera `MEMORY_INDEX.md` a partir de Blackboards ativos, `archive/` e `MEMORY.md`, de forma determinística (duas execuções → saída idêntica), com cobertura de pytest
- [ ] Fixture: o índice gerado a partir de `archive/KB_EVOLUTION` contém as 6 decisões do DESIGN e as lições do SHIPPED
- [ ] Resumo de entrada de fase ≤ 15 linhas e exclui decisões substituídas
- [ ] Aceite: um DEFINE novo com domínio `kb` recebe no resumo a decisão "log.md por domínio" do KB_EVOLUTION
- [ ] SessionStart mostra as últimas 5 entradas do Diário da feature em `.active`
- [ ] Transição de fase é bloqueada quando há pergunta 🔴 aberta que a fase seguinte precisaria decidir
- [ ] Nenhuma dependência nova (sem MCP, DB, rede) — verificável no diff
- [ ] `build-plugin.sh` e os bundles gerados (plugin, Codex, Grok, DeepSeek) incluem o script e os templates atualizados

### Restrições Identificadas

- Core framework em inglês; seções do Diário e documentos gerados em pt-BR (política de idioma)
- Compatibilidade retroativa: Blackboards existentes (só Build) continuam válidos
- `WORKFLOW_CONTRACTS.yaml` precisa refletir o novo ciclo do Blackboard (`seed` deixa de ser só do build-agent)
- Custo de tokens na entrada de fase precisa ser limitado (teto de linhas)
- Local-first overrides: agentes customizados localmente não devem quebrar se ignorarem o Diário

### Fora do Escopo (Confirmado)

- Amarração por hash / digest de evidência
- Busca por texto livre dedicada
- Migração retroativa automática do `archive/`
- Grafo de documentos
- Qualquer MCP, vector store ou banco
- Rodar ou pontuar evals (`POST_BUILD_EVALS`), atualizar KBs (`KB_CONTEXT7_REFRESH`), escolher modelo (`LLM_PHASE_ROUTING`) ou agentes (`JEV_AGENT_SELECTION`)

### Perguntas Abertas para o Define

1. Manter o nome `BLACKBOARD` ou renomear (ex.: "Quadro da Feature") agora que cobre o ciclo todo? Renomear quebra compatibilidade.
2. O Diário vira uma seção única com blocos por fase, ou uma subseção por fase com as tabelas atuais (D/Q/A) marcadas com a coluna "Fase"?
3. Onde vive o script: `plugin-extras/scripts/` (como `status-dashboard.py`) ou `scripts/` (como `judge.py`)?
4. Qual o teto exato do resumo de entrada e o critério de ranqueamento quando há mais linhas relevantes que o teto?
5. O bloqueio por pergunta aberta vale para todas as transições ou só Define → Design e Design → Build?

---

## Resumo da Sessão

| Métrica | Valor |
|---------|-------|
| Perguntas Feitas | 6 (4 de descoberta, incluindo a de exemplos, + escolha de abordagem + YAGNI) |
| Abordagens Exploradas | 3 (+1 descartada de saída) |
| Features Removidas (YAGNI) | 6 |
| Validações Concluídas | 3 |
| Duração | 1 sessão |

---

## Próximo Passo

**Pronto para:** `/define .claude/sdd/features/BRAINSTORM_LIVING_MEMORY.md`
