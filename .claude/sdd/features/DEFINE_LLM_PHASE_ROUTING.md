# DEFINE: LLM Phase Routing

> Um manifesto único diz qual papel de modelo atende cada fase do SDD; o OMP resolve papel → modelo, e as fases não interativas passam a rodar no modelo certo sem troca manual.

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | LLM_PHASE_ROUTING |
| **Data** | 2026-09-23 |
| **Autor** | define-agent |
| **Status** | Pronto para Design |
| **Clarity Score** | 14/15 |
| **Entrada** | `.claude/sdd/features/BRAINSTORM_LLM_PHASE_ROUTING.md` (brainstorm_document) |
| **Gerado por** | Claude Code — sessão principal, `claude-opus-5-5` (`/define` roda inline) |

---

## Declaração do Problema

Ao rodar `/brainstorm`, `/define`, `/design`, `/build` ou `/ship`, a fase usa o modelo da sessão, e não o recomendado para ela. O `model:` dos agents de workflow é ignorado porque os comandos rodam inline e não delegam ao agent. Hoje, o dono do AgentSpec, que roda o SDD no OMP com vários provedores configurados, precisa trocar de modelo à mão a cada fase ou roda tudo no mesmo modelo. E não há registro de qual modelo produziu cada documento, o que impede calibrar a escolha depois.

---

## Usuários-Alvo

| Usuário | Papel | Dor |
|---------|-------|-----|
| Dono do AgentSpec no OMP | Roda as 5 fases no OMP, com Codex, xAI, Anthropic e OpenRouter configurados em `modelRoles` | Troca `/model` a cada fase; o `model: opus`/`sonnet` dos agents não vale no `/design` digitado |
| Usuário do plugin no Claude Code | Roda o mesmo plugin no Claude Code | O mesmo problema: o `model:` do agent não vale no comando; `WORKFLOW_CONTRACTS.yaml` diverge da frontmatter (`define-agent`: `opus` × `sonnet`) |
| Frentes irmãs (`POST_BUILD_EVALS`, `LIVING_MEMORY`, `JEV_AGENT_SELECTION`) | Consomem artefatos do SDD | Não sabem qual papel ou modelo gerou cada documento |

---

## Objetivos

| Prioridade | Objetivo |
|------------|----------|
| **MUST** | **M1.** Criar `.claude/sdd/architecture/PHASE_MODEL_ROLES.yaml` como fonte única do mapeamento fase → papel (vocabulário dos `modelRoles` do OMP) → alias Claude → effort Codex, cobrindo `brainstorm`, `define`, `design`, `build`, `ship`, `iterate`, `continuar`, as variantes `-m` e `judge` |
| **MUST** | **M2.** Fases **não interativas** (`/design`, `/design-m`, `/ship`) delegam o trabalho ao agent da fase como subagent, para que o papel se aplique automaticamente no OMP |
| **MUST** | **M3.** Um comando gera o trecho `task.agentModelOverrides` (nome do agent → `@papel`) para o usuário colar no `~/.omp/agent/config.yml`. O gerador só **imprime** e nunca escreve fora do repositório |
| **MUST** | **M4.** Os 5 templates SDD (BRAINSTORM, DEFINE, DESIGN, BUILD_REPORT, SHIPPED) ganham a linha `Gerado por` (harness, papel, modelo), e os agents de workflow instruem o preenchimento |
| **MUST** | **M5.** `make check` falha quando a frontmatter dos agents de workflow, o `WORKFLOW_CONTRACTS.yaml` ou os artefatos gerados divergem do manifesto (inclui corrigir a divergência atual do `define-agent`) |
| **MUST** | **M6.** Documentação: tabela fase → papel → motivo em `docs/concepts/`, receita do OMP (overrides + abrir as fases interativas com `omp --model @plan`) e linha no `CLAUDE.md` |
| **SHOULD** | **S1.** Paridade com o Claude Code: a frontmatter `model:` dos agents de workflow vem do alias do manifesto, e a delegação de M2 funciona igual no Claude Code |
| **SHOULD** | **S2.** Aviso de família: a documentação (e, se barato, o `/status`) alerta quando o papel de revisão resolve para a mesma família de `plan`/`slow` |
| **SHOULD** | **S3.** `scripts/generate-codex-plugin.py` lê o effort do manifesto em vez de `EFFORT_BY_MODEL` para os agents de workflow |
| **COULD** | **C1.** `scripts/judge.py` lê do manifesto o slug OpenRouter por fase, substituindo os IDs antigos (`openai/gpt-4o`) de `PHASE_MODEL_DEFAULTS` |
| **COULD** | **C2.** O `/status` mostra a tabela fase → papel ativa |

### Mapeamento default (validado no brainstorm)

| Fase / comando | Modo | Papel OMP | Alias Claude | Effort Codex |
|----------------|------|-----------|--------------|--------------|
| `/brainstorm`, `/define`, `/define-m`, `/iterate` | Interativo, na sessão | `plan` (recomendado ao abrir a sessão) | `inherit` na execução; `opus` no agent | high |
| `/design`, `/design-m` | Delegado ao agent | `slow` | `opus` | high |
| `/build`, `/continuar` (orquestrador) | Sessão | `default` | `inherit` | high |
| `/build` (especialistas) | Subagent | inalterado (`model:` atual) | inalterado | inalterado |
| `/ship` | Delegado ao agent | `smol` | `haiku` | low |
| `--judge` / review | Externo (OpenRouter) | `REVIEWER` (papel customizado opcional) | — | — |

> O `/design` e o `/define` decidem os aliases e efforts finais; o mapeamento de **papel** e de **modo** está fechado.

---

## Critérios de Sucesso

- [ ] **100%** das fases listadas em M1 (9 agents de workflow + 9 comandos: `brainstorm`, `define`, `define-m`, `design`, `design-m`, `build`, `continuar`, `ship`, `iterate`) têm entrada no manifesto.
- [ ] **0** IDs concretos de modelo no manifesto e nos arquivos gerados de workflow. Verificado pela regex `(gpt-|grok-|claude-|gemini-|deepseek)[0-9a-z.-]+` no `make check`.
- [ ] **Em 2 de 2** fases delegadas (`/design`, `/ship`) rodadas no OMP com o trecho de M3 aplicado, a linha `Gerado por` do documento mostra o modelo que o OMP resolve para `@slow` e `@smol`, respectivamente.
- [ ] **1** comando (`make omp-roles` ou equivalente) gera o trecho de overrides em menos de 2 s, sem ler nem escrever `~/.omp`.
- [ ] **5 de 5** templates SDD com a linha `Gerado por`; nenhum documento gerado depois da feature fica com o campo vazio (valor mínimo aceito: `desconhecido`).
- [ ] `make check` falha em **100%** dos casos de divergência cobertos pelos testes (frontmatter ≠ manifesto, contrato ≠ manifesto, artefato gerado desatualizado) e passa no repositório limpo.
- [ ] O fluxo interativo não regride: `/brainstorm` e `/define` continuam fazendo perguntas ao usuário em **100%** das execuções (não viram subagent).

---

## Testes de Aceitação

| ID | Cenário | Dado | Quando | Então |
|----|---------|------|--------|-------|
| AT-001 | Design no papel `slow` (OMP) | Trecho de M3 aplicado ao `config.yml` e um DEFINE pronto | O usuário roda `/design DEFINE_X.md` no OMP | O trabalho roda no subagent `design-agent`; o DESIGN registra em `Gerado por` o modelo de `@slow` |
| AT-002 | Ship no papel `smol` (OMP) | Trecho de M3 aplicado e BUILD_REPORT pronto | O usuário roda `/ship X` | O subagent `ship-agent` roda no modelo de `@smol`; o SHIPPED registra isso |
| AT-003 | Sem override aplicado | O `config.yml` não tem o trecho de M3 | O usuário roda `/design` no OMP | O OMP usa o `model:` do agent (`opus` via fuzzy match) ou cai no modelo da sessão; a fase conclui e `Gerado por` mostra o modelo real |
| AT-004 | Divergência detectada | Alguém edita `model: sonnet` no `design-agent.md` sem mexer no manifesto | Roda `make check` | Falha com mensagem que aponta arquivo, campo e valor esperado |
| AT-005 | Contrato alinhado | `WORKFLOW_CONTRACTS.yaml` com `define-agent: opus` e frontmatter com `sonnet` (estado atual) | A feature é aplicada | Os dois ficam iguais ao manifesto, e o `make check` passa |
| AT-006 | Sem IDs no repositório | Manifesto e artefatos gerados | Roda `make check` | A regex de IDs concretos não encontra nada nos arquivos de workflow |
| AT-007 | Fase interativa preservada | OMP aberto com `omp --model @plan` | O usuário roda `/brainstorm "ideia"` | A fase roda inline, faz perguntas e registra em `Gerado por` o modelo da sessão |
| AT-008 | Gerador não toca no usuário | `~/.omp/agent/config.yml` com `modelRoles` próprios | Roda o gerador de M3 | A saída é só stdout; o `config.yml` fica igual (mesmo hash antes e depois) |
| AT-009 | Paridade Claude Code (SHOULD) | Plugin instalado no Claude Code | O usuário roda `/design DEFINE_X.md` | O trabalho roda no subagent `design-agent` com `model: opus`; o DESIGN registra isso |

---

## Fora do Escopo

- Troca automática de modelo nas fases interativas (brainstorm, define, iterate). Elas usam o modelo da sessão; a documentação recomenda abrir com `omp --model @plan`.
- Roteamento dinâmico por complexidade da feature.
- Escolha de modelo por benchmark ou JEV (frente `JEV_AGENT_SELECTION`).
- Papel por agent especialista (os 73 agents mantêm o `model:` atual).
- Bundle OMP dedicado (`.omp/agents`). O OMP já consome o plugin Claude; só volta ao escopo se A-001 falhar.
- Escrever no `~/.omp/agent/config.yml` do usuário.
- Mudanças no bundle DeepSeek (`plugin-dsh`), que continua copiando os agents sem alteração.
- Cadeias de fallback e telemetria de custo por fase.

---

## Restrições

| Tipo | Restrição | Impacto |
|------|-----------|---------|
| Técnica | O mesmo `plugin/` é instalado no Claude Code e no OMP, então a frontmatter precisa ser válida nos dois. `model: "@slow"` vale no OMP e não no Claude Code | A frontmatter leva aliases Claude; o papel do OMP entra por `task.agentModelOverrides`, que tem precedência maior que a frontmatter |
| Técnica | O OMP não documenta `model:` em comandos, nem comando que troque o modelo da sessão; no Claude Code, o `model:` do comando vale só até o fim do turno | Roteamento automático só em fases delegadas a subagent (M2); fases interativas ficam na sessão |
| Técnica | O OMP **não** escaneia `.claude/agents` (docs `subagent-authoring`) | Overrides locais (`.claude/agents/…`) não valem no OMP; o override por projeto no OMP é `.omp/agents` ou o `config.yml` |
| Técnica | Nenhum ID concreto de modelo versionado | Manifesto só com papéis e aliases; IDs ficam no `config.yml` do usuário |
| Idioma | Framework em inglês; documentos SDD em pt-BR | Manifesto, agents e comandos em inglês; templates com rótulos em pt-BR |
| Compatibilidade | Geradores Codex, Grok e DeepSeek existentes com `--check` | Toda mudança nos geradores mantém o `--check` verde |

---

## Contexto Técnico

| Aspecto | Valor | Notas |
|---------|-------|-------|
| **Localização de Deploy** | `.claude/sdd/architecture/PHASE_MODEL_ROLES.yaml`; `.claude/commands/workflow/{design,design-m,ship}.md`; `.claude/agents/workflow/*.md`; `.claude/sdd/templates/*.md`; `scripts/` (gerador de overrides + check); `Makefile`; `tests/`; `docs/concepts/` | Segue o padrão existente de fonte em `.claude/` e build via `build-plugin.sh` |
| **Domínios KB** | `genai` (orquestração multiagente) | Dependência baixa; a decisão é de harness |
| **Impacto IaC** | Nenhum | — |

**Fatos verificados que o Design deve usar:**

- OMP (`omp.sh/docs/subagent-authoring`, `/agents-and-roles`):
  - Descobre agents de plugins do marketplace do Claude.
  - O `model:` do agent aceita modelo concreto, `"@papel"` ou lista em ordem de fallback.
  - Precedência: `task.agentModelOverrides.<agent-name>` → `model:` do agent → modelo da sessão.
  - `modelRoles` aceita papéis customizados.
- Claude Code (`code.claude.com/docs`):
  - Comandos aceitam `model:` (só no turno), `context: fork` e `agent:`.
  - Subagents aceitam alias, ID completo ou `inherit`.
- Instalação atual: `agentspec@agentspec` 3.4.1 no OMP, com `model: opus` preservado em `agents/workflow/design-agent.md`.

---

## Premissas

| ID | Premissa | Se Errada, Impacto | Validada? |
|----|----------|-------------------|-----------|
| A-001 | A chave de `task.agentModelOverrides` casa com o nome que o OMP dá a um agent de plugin (`design-agent` ou forma namespaced) | M3 não tem efeito; seria preciso bundle `.omp/agents` com `model: "@slow"` | [ ] |
| A-002 | Um comando de plugin Claude no OMP consegue delegar a fase ao agent (via `context: fork`/`agent:` ou instrução de usar a ferramenta de task) | M2 falha no OMP; alternativa é o usuário invocar o agent direto | [ ] |
| A-003 | O Claude Code aceita alias `opus`/`sonnet`/`haiku` na frontmatter e respeita `context: fork` + `agent:` em comandos | S1 falha | [x] (docs oficiais) |
| A-004 | O OMP descobre agents de plugins do marketplace do Claude | O plano inteiro para o OMP cai | [x] (docs + instalação atual) |
| A-005 | O modelo em execução consegue informar o próprio ID para preencher `Gerado por` | Campo fica `desconhecido`; a calibração perde precisão | [ ] |
| A-006 | Delegar `/design` a um subagent, com contexto limpo, não piora o DESIGN, porque ele lê DEFINE e arquivos do repositório | Seria preciso passar mais contexto na delegação | [ ] |

**Nota:** A-001 e A-002 são críticas e devem ser validadas no início do `/design`: teste de no máximo 30 min no OMP com um agent de plugin e um override.

---

## Detalhamento do Clarity Score

| Elemento | Score (0-3) | Notas |
|----------|-------------|-------|
| Problema | 3 | Causa raiz identificada (comando inline ignora o `model:` do agent) e confirmada nas docs dos dois harnesses |
| Usuários | 3 | Três perfis com dor concreta, incluindo a divergência real do `define-agent` |
| Objetivos | 3 | MoSCoW com M1–M6 verificáveis; modo interativo × delegado decidido pelo usuário |
| Sucesso | 2 | Critérios numéricos e testáveis, mas AT-001/AT-002 dependem de A-001/A-002, ainda não validadas |
| Escopo | 3 | Fora do escopo explícito, herdado do YAGNI e ampliado com os achados do OMP |
| **Total** | **14/15** | |

---

## Questões em Aberto

1. **(A-001)** Qual nome o OMP usa para um agent de plugin na chave de `agentModelOverrides`: `design-agent` ou `agentspec:workflow:design-agent`? Validar no início do Design.
2. **(A-002)** Qual mecanismo de delegação o OMP respeita num comando de plugin Claude: `context: fork` + `agent:` ou instrução no corpo? Validar no início do Design.
3. Qual alias Claude final para `/ship`: `haiku` (mais barato) ou `sonnet` (atual)? O Design decide, dentro de M1.

Nenhuma bloqueia o início do Design; 1 e 2 são o primeiro passo dele.

---

## Histórico de Revisões

| Versão | Data | Autor | Mudanças |
|--------|------|-------|----------|
| 1.0 | 2026-09-23 | define-agent | Versão inicial a partir do BRAINSTORM; incorpora a doc do OMP (agents, papéis, precedência) e duas decisões do usuário: fases interativas no modelo da sessão; Claude Code como SHOULD |

---

## Próximo Passo

**Pronto para:** `/design .claude/sdd/features/DEFINE_LLM_PHASE_ROUTING.md`
