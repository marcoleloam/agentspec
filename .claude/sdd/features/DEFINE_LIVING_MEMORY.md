# DEFINE: Living Memory (Segundo Cérebro entre Fases)

> Estender o `BLACKBOARD_{FEATURE}.md` ao ciclo de vida inteiro e gerar um índice de memória entre features, para que cada fase, cada feature nova e cada sessão retomada recebam a trajetória (decisões, alternativas rejeitadas, premissas, mudanças de rumo), e não só o resultado.

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | LIVING_MEMORY |
| **Data** | 2026-09-23 |
| **Autor** | define-agent |
| **Status** | Pronto para Design |
| **Clarity Score** | 14/15 |
| **Origem** | [BRAINSTORM_LIVING_MEMORY.md](BRAINSTORM_LIVING_MEMORY.md) |

---

## Declaração do Problema

As fases do AgentSpec geram documentos de **resultado** (DEFINE, DESIGN, BUILD_REPORT), mas a **trajetória** — perguntas respondidas, alternativas rejeitadas, premissas, mudanças de rumo — não é relida pela fase seguinte, por features futuras nem por sessões posteriores: `define-agent` e `design-agent` não leem `MEMORY.md`, `archive/` nem Blackboards de outras features, e o Blackboard só nasce no Build. Além disso, a única memória entre features (`.claude/sdd/MEMORY.md`) depende de um passo no fim do fluxo (Step 8 do `/ship`, desde v3.3.0) ou de `/memory` manual, e só guarda headings — a trajetória de Define e Design nunca chega lá.

---

## Usuários-Alvo

| Usuário | Papel | Dor |
|---------|-------|-----|
| Mantenedor / usuário do AgentSpec | Conduz features de dados com o fluxo SDD, em várias sessões e máquinas | Reexplica decisões ao retomar uma feature dias depois e ao iniciar outra no mesmo domínio; lições ficam presas nos `SHIPPED_*.md` |
| Agentes de fase (`define-agent`, `design-agent`, `build-agent`, `iterate-agent`, `ship-agent`) | Produzem os artefatos de cada fase | Decidem sem saber o que fases e features anteriores já decidiram ou rejeitaram; perguntas deixadas em aberto no Define são decididas em silêncio no Design |
| Contribuidor que customiza agentes (local-first overrides) | Mantém cópias locais de agentes de workflow | Não pode ter o override quebrado por uma mudança de formato do Blackboard |

---

## Objetivos

| Prioridade | Objetivo |
|------------|----------|
| **MUST** | **G1** — O `BLACKBOARD_{FEATURE}.md` nasce no `/brainstorm`; quando o brainstorm é pulado, nasce no `/define` (importando o BRAINSTORM se existir). O nome do arquivo e do template **não muda** |
| **MUST** | **G2** — Brainstorm, Define, Design, Build, Iterate e Ship anexam ao Blackboard, **ao sair da fase e sem comando manual**, as entradas da trajetória: decisões (`D`) com alternativa rejeitada, perguntas (`Q`) respondidas ou abertas, premissas (`A`) e mudanças de rumo (`D` com "Substitui") |
| **MUST** | **G3** — No Build, todo desvio do DESIGN é registrado como `D` que substitui a decisão de Design correspondente, com o motivo |
| **MUST** | **G4** — Um script determinístico (stdlib, sem LLM, sem rede) gera `.claude/sdd/MEMORY_INDEX.md` a partir dos Blackboards ativos, de `archive/` (Blackboards, DESIGNs e SHIPPED) e de `.claude/sdd/MEMORY.md` |
| **MUST** | **G5** — Ao entrar numa fase, o agente recebe um resumo de no máximo 15 linhas: decisões vigentes da feature (substituídas excluídas), perguntas abertas e linhas de outras features com domínio KB em comum; o detalhe é lido sob demanda pelo ponteiro "onde ler" |
| **MUST** | **G6** — Pergunta 🔴 aberta no Blackboard **bloqueia** as transições Define→Design e Design→Build. Brainstorm→Define e Build→Ship não bloqueiam por essa regra (o Build já exige zero bloqueadores hoje) |
| **MUST** | **G7** — Nenhuma dependência nova: sem MCP, banco, vector store ou rede |
| **SHOULD** | **G8** — O SessionStart mostra, além do índice do `MEMORY.md`, as últimas 5 entradas do Blackboard da feature em `.active` |
| **SHOULD** | **G9** — O `/ship` consolida 3–5 lições no `.claude/sdd/MEMORY.md` (criando o arquivo se não existir) e regenera o índice; a consolidação deixa de depender de lembrança |
| **SHOULD** | **G10** — `WORKFLOW_CONTRACTS.yaml` reflete o novo ciclo de vida do Blackboard (seed, read, append, archive por fase) e a regra de bloqueio |
| **COULD** | **G11** — Campo opcional `Relacionada a:` nos metadados do Blackboard, lido pelo índice como ligação explícita entre features |
| **COULD** | **G12** — Campo opcional "modelo" no cabeçalho do bloco de fase, reservado para `LLM_PHASE_ROUTING` preencher |

---

## Critérios de Sucesso

- [ ] **SC-1** — 100% das features iniciadas após o build têm `BLACKBOARD_{FEATURE}.md` criado no Brainstorm ou no Define (verificável: arquivo existe logo após `/define`)
- [ ] **SC-2** — Cada uma das 6 fases (brainstorm, define, design, build, iterate, ship) deixa ≥ 1 entrada datada e marcada com a fase no Blackboard ao terminar
- [ ] **SC-3** — `memory-index.py` é determinístico: 2 execuções consecutivas sobre a mesma árvore produzem saída byte a byte idêntica
- [ ] **SC-4** — Sobre `archive/` atual, o índice contém as **10** decisões de DESIGN (6 do KB_EVOLUTION + 4 do FRONTEND_ECOSYSTEM) e as lições dos **2** SHIPPED, tolerando títulos com e sem acento ("Decisao"/"Decisão", "Licoes"/"Lições")
- [ ] **SC-5** — Resumo de entrada de fase tem ≤ 15 linhas e 0 decisões marcadas como substituídas
- [ ] **SC-6** — Cobertura de pytest ≥ 80% das linhas de `memory-index.py`, rodando no `make test` e na CI existente
- [ ] **SC-7** — Execução do índice sobre o repositório atual em < 2 s
- [ ] **SC-8** — Diff da feature adiciona 0 dependências de runtime (nenhum import fora da stdlib, nenhum MCP novo em configs)
- [ ] **SC-9** — `build-plugin.sh` e os bundles gerados (plugin, Codex, Grok, DeepSeek) incluem o script e os templates/agentes atualizados; testes existentes dos geradores continuam verdes
- [ ] **SC-10** — Um Blackboard no formato antigo (só Build) continua sendo lido por `/work`, `status-dashboard.py` e pelo índice sem erro

---

## Testes de Aceitação

| ID | Cenário | Dado | Quando | Então |
|----|---------|------|--------|-------|
| AT-001 | Blackboard nasce no Brainstorm | Nenhum Blackboard para a feature X | `/brainstorm X` termina | `BLACKBOARD_X.md` existe com entradas `Q` (perguntas respondidas) e `D` (abordagem escolhida + rejeitadas) marcadas com fase `brainstorm` |
| AT-002 | Blackboard nasce no Define (brainstorm pulado) | Nenhum BRAINSTORM nem Blackboard para Y | `/define Y` termina | `BLACKBOARD_Y.md` existe com entradas de fase `define` (premissas `A`, perguntas `Q`) |
| AT-003 | Design aponta, não copia | DEFINE com 3 decisões de arquitetura a tomar | `/design` termina | Blackboard tem ≥ 3 entradas `D` de fase `design`, cada uma com ponteiro para a seção do DESIGN e ≤ 1 frase de porquê |
| AT-004 | Desvio no Build | DESIGN decide "formato JSON" (D-005) | Build implementa em YAML | Blackboard ganha `D` de fase `build` com "Substitui D-005" e o motivo; o resumo seguinte mostra só a decisão nova |
| AT-005 | Bloqueio Define→Design | Blackboard de Z tem Q-003 🔴 aberta | Usuário roda `/design Z` | Design **não** gera o DESIGN; lista Q-003 e pede resolução (via resposta ou `/iterate`) |
| AT-006 | Sem bloqueio Brainstorm→Define | BRAINSTORM deixou pergunta aberta | `/define` roda | Define prossegue; a pergunta aparece no resumo de entrada e deve ser resolvida ou mantida aberta explicitamente |
| AT-007 | Memória entre features | Índice gerado sobre `archive/` atual | `/define` de feature nova com domínio KB comum a uma feature arquivada | Resumo de entrada inclui ≥ 1 linha de decisão dessa feature arquivada com ponteiro válido (arquivo e âncora existentes) |
| AT-008 | Retomada entre sessões | `.active` aponta para W com 8 entradas no Blackboard | Nova sessão inicia | Saída do SessionStart contém as 5 entradas mais recentes de W |
| AT-009 | Índice determinístico e descartável | `MEMORY_INDEX.md` apagado | Script roda 2 vezes | Arquivo recriado; as 2 saídas são idênticas |
| AT-010 | Compatibilidade retroativa | Blackboard no formato antigo (sem entradas por fase) | `/work --status` e o script rodam | Ambos concluem sem erro; o índice trata as entradas antigas como fase `build` |
| AT-011 | Ship consolida | Feature com lições no SHIPPED e sem `MEMORY.md` | `/ship` termina | `.claude/sdd/MEMORY.md` criado com bloco `## {data} — {resumo}` de 3–5 itens e índice regenerado |
| AT-012 | Tamanho limitado | Feature com 40 entradas vigentes | Entrada de fase | Resumo tem ≤ 15 linhas e informa quantas foram omitidas e onde ler |

---

## Fora do Escopo

- Amarração por hash / `evidence_refs` com digest (estilo task-spec)
- Busca por texto livre dedicada (`/memory search`) — o índice já é grep-ável
- Migração retroativa automática: o `archive/` é **lido** pelo índice, não reescrito
- Grafo de documentos ou banco de links
- Qualquer MCP, vector store, embeddings, SQLite ou chamada de rede
- Renomear `BLACKBOARD` (decidido: manter o nome)
- Rodar, pontuar ou armazenar evals → `POST_BUILD_EVALS` (aqui só uma linha `E` com veredito + ponteiro, se aquela frente quiser)
- Atualizar KBs ou trazer documentação externa → `KB_CONTEXT7_REFRESH`
- Escolher modelo por fase → `LLM_PHASE_ROUTING` (aqui só o campo opcional reservado)
- Escolher agentes por fase → `JEV_AGENT_SELECTION`
- Mudanças no `/memory` manual além do que o índice já lê

---

## Restrições

| Tipo | Restrição | Impacto |
|------|-----------|---------|
| Técnica | Só stdlib Python 3 e Bash; sem rede, sem LLM no script | Parser por regex/heading; testes com fixtures locais |
| Técnica | Nome `BLACKBOARD_{FEATURE}.md` e `BLACKBOARD_TEMPLATE.md` preservados | Mudança só aditiva no template (nova seção/coluna) |
| Técnica | Blackboards e documentos antigos têm formatos variados (acentos, títulos) | Parser tolerante; formato antigo não pode falhar |
| Técnica | `build-plugin.sh` reescreve paths `.claude/` → `plugin/`; bundles Codex/Grok/DeepSeek são gerados | Script e templates novos precisam entrar nos geradores e nos testes deles |
| Técnica | Local-first overrides podem ignorar o Blackboard | Ausência de entradas não pode quebrar fase nem script; bloqueio só dispara com 🔴 explícito |
| Custo | Resumo de entrada ≤ 15 linhas; SessionStart +5 linhas no máximo | Controla o gasto de tokens por fase e por sessão |
| Idioma | Core (agentes, comandos, contratos, script) em inglês; conteúdo do Blackboard em pt-BR | Seções e rótulos do template em pt-BR, código em inglês |
| Arquitetura | Decisão de v3.3.0: memória em arquivo, MemPalace MCP removido | Reforça G7 |

---

## Contexto Técnico

| Aspecto | Valor | Notas |
|---------|-------|-------|
| **Localização de Deploy** | `.claude/sdd/templates/BLACKBOARD_TEMPLATE.md`, `.claude/agents/workflow/*.md`, `.claude/commands/workflow/*.md`, `.claude/sdd/architecture/WORKFLOW_CONTRACTS.yaml`, `plugin-extras/scripts/init-workspace.sh`, script novo (local a definir no Design), `tests/` | Mudança de framework, não de aplicação |
| **Domínios KB** | `genai` (memória e coordenação multi-agente), `python` (script do índice), `testing` (pytest + fixtures) | Todos existem em `.claude/kb/_index.yaml` |
| **Impacto IaC** | Nenhum | — |

**Padrões existentes a reusar:** `plugin-extras/scripts/status-dashboard.py` (lê MDs e gera artefato de forma determinística), `memory_index()`/`surface_memory()` em `init-workspace.sh` (injeção compacta no SessionStart), `tests/test_generate_*.py` (padrão de teste de script).

---

## Premissas

| ID | Premissa | Se Errada, Impacto | Validada? |
|----|----------|-------------------|-----------|
| A-001 | Os agentes de fase seguem com confiabilidade a instrução de prompt de anexar ao Blackboard ao sair da fase | A captura automática falha como a manual falhou; exigiria um checklist de Quality Gate mais rígido ou validação por script | [x] derrubada no E2E de 2026-09-24 (captura 2/4 e chamadas ao script puladas) → mitigada por prompt reforçado + hooks do plugin; ver DESIGN Decisões 10–13 |
| A-002 | Domínios KB em comum são um bom critério de relevância entre features | O resumo traria ruído ou perderia features relacionadas; exigiria `Relacionada a:` (G11) como critério principal | [ ] |
| A-003 | Os documentos arquivados são parseáveis por heading (`### Decisão N:`, `## Lições Aprendidas`) apesar da variação de acentos | SC-4 não seria atingido; exigiria normalização de acentos ou lista de padrões por documento | [x] parcial — observados `### Decisao N:` (KB_EVOLUTION) e `### Decisão N:` (FRONTEND_ECOSYSTEM); `## Licoes Aprendidas` e `## Lições Aprendidas` |
| A-004 | Os DEFINEs arquivados nem sempre declaram domínios KB de forma estruturada | AT-007 dependeria de inferência; o Design precisa definir de onde vêm os domínios de uma feature arquivada | [x] observado — `DEFINE_FRONTEND_ECOSYSTEM.md` cita domínios em texto, não em campo "Domínios KB" |
| A-005 | O volume de memória por projeto fica na ordem de dezenas de features / centenas de entradas | Índice em Markdown ficaria grande demais; reabriria a discussão de busca | [ ] |

---

## Detalhamento do Clarity Score

| Elemento | Score (0-3) | Notas |
|----------|-------------|-------|
| Problema | 3 | Específico, com evidência observada (agentes de Define/Design não leem histórico; Blackboard só no Build) |
| Usuários | 3 | Três perfis com dor concreta, incluindo overrides locais |
| Objetivos | 3 | 12 objetivos MoSCoW; nome e escopo do bloqueio resolvidos com o usuário |
| Sucesso | 3 | Critérios numéricos e verificáveis (contagens do archive, ≤ 15 linhas, < 2 s, ≥ 80%) |
| Escopo | 2 | Fronteiras claras; formato exato do Diário e local do script ficam para o Design |
| **Total** | **14/15** | |

---

## Questões em Aberto

Nenhuma bloqueia o Design. As decisões abaixo são **delegadas ao Design** (não são perguntas 🔴):

1. Formato do Diário: seção única com blocos por fase, ou coluna "Fase" nas tabelas atuais (Log de Decisões, Perguntas) mais uma tabela de Premissas.
2. Local do script: `plugin-extras/scripts/` (como `status-dashboard.py`) ou `scripts/` (como `judge.py`), e como ele entra no `build-plugin.sh` e nos geradores.
3. Critério de ranqueamento quando há mais de 15 linhas relevantes (ex.: feature atual > perguntas abertas > outras features por data).
4. De onde vêm os domínios KB de uma feature arquivada que não os declara (A-004).
5. Mecanismo de bloqueio (G6): verificação no prompt do agente de Design/Build ou checagem pelo script.

---

## Histórico de Revisões

| Versão | Data | Autor | Mudanças |
|--------|------|-------|----------|
| 1.0 | 2026-09-23 | define-agent | Versão inicial a partir do BRAINSTORM; decisões do usuário: manter nome `BLACKBOARD`; bloqueio só em Define→Design e Design→Build |
| 1.1 | 2026-09-23 | design-agent | Correção factual: o Step 8 do `/ship` (consolidação no `MEMORY.md`) entrou em 2026-06-21 (v3.3.0, commit `510aa81`), depois dos dois ships arquivados (2026-03-29 e 2026-04-23). A ausência de `MEMORY.md` não prova que a captura no fim do fluxo falha; removida da Declaração do Problema. Requisitos inalterados. |
| 1.2 | 2026-09-24 | iterate (pós-E2E) | A-001 marcada como derrubada e mitigada, com o resultado do teste E2E da Q-009 (ver BUILD_REPORT → Validação E2E). Requisitos inalterados. |

---

## Próximo Passo

**Pronto para:** `/design .claude/sdd/features/DEFINE_LIVING_MEMORY.md`
