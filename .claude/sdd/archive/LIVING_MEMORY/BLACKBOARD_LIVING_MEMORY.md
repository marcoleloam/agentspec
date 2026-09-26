# BLACKBOARD: Living Memory (Segundo Cérebro entre Fases)

> Quadro compartilhado da feature — o estado vivo e a memória da trajetória, do
> Brainstorm ao Ship. Regras completas: `WORKFLOW_CONTRACTS.yaml` → `living_memory`.
> Entradas de Brainstorm, Define e Design registradas retroativamente no Build (a
> feature que cria o protocolo não podia usá-lo antes de existir).

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | LIVING_MEMORY |
| **Fase** | Build |
| **Atualizado em** | 2026-09-24 |
| **Domínios KB** | genai, python, testing |
| **Relacionada a** | — |
| **DESIGN** | [DESIGN_LIVING_MEMORY.md](DESIGN_LIVING_MEMORY.md) |
| **Status** | ✅ Completo |

---

## Interfaces Compartilhadas

| # | Tipo | Nome / Assinatura | Definido por | Consumido por | Notas |
|---|------|-------------------|--------------|---------------|-------|
| I-001 | CLI | `memory-index.py brief FEATURE --phase P [--max 15] [--domains a,b]` | @build-agent | agentes de fase, `/work` | stdout, exit 0 |
| I-002 | CLI | `memory-index.py gate FEATURE --to design\|build` | @build-agent | design/build | exit 1 = bloqueado |
| I-003 | CLI | `memory-index.py tail [FEATURE] [--n 5]` | @build-agent | `init-workspace.sh` | FEATURE de `.active` |
| I-004 | CLI | `memory-index.py build [--verbose]` | @build-agent | todas as fases, `/ship` | escreve `MEMORY_INDEX.md` |
| I-005 | formato | tabelas do Blackboard com coluna `Fase`; status 🔴/🟡/🟢 | @build-agent | todos os agentes | template + contrato |

---

## Log de Decisões

| # | Fase | Agente | Decisão | Justificativa | Alternativa Rejeitada | Substitui | Onde Ler | Data |
|---|------|--------|---------|---------------|-----------------------|-----------|----------|------|
| D-001 | brainstorm | @brainstorm-agent | Captura automática pelos agentes de fase | memória que depende de lembrar no fim do fluxo não é escrita | /memory manual; captura bruta + curadoria | — | BRAINSTORM_LIVING_MEMORY.md#principais-decisões-tomadas | 2026-09-23 |
| D-002 | brainstorm | @brainstorm-agent | Estender o Blackboard ao ciclo todo (Abordagem A) | reaproveita artefato já chamado de living memory | B: JOURNAL separado; C: grafo com hash | — | BRAINSTORM_LIVING_MEMORY.md#abordagem-selecionada | 2026-09-23 |
| D-003 | brainstorm | @brainstorm-agent | Recuperação por índice curto + leitura sob demanda | custo de tokens previsível | carga completa; busca sem carga automática | — | BRAINSTORM_LIVING_MEMORY.md#principais-decisões-tomadas | 2026-09-23 |
| D-004 | brainstorm | @brainstorm-agent | Nenhuma dependência nova (sem MCP, DB, rede) | MemPalace removido de propósito; volume cabe em arquivo | MCP / vector store / SQLite | — | BRAINSTORM_LIVING_MEMORY.md#abordagens-exploradas | 2026-09-23 |
| D-005 | brainstorm | @brainstorm-agent | YAGNI: fora hash, busca livre, migração retroativa e grafo | não ajudam a lembrar no MVP | manter no escopo | — | BRAINSTORM_LIVING_MEMORY.md#features-removidas-yagni | 2026-09-23 |
| D-006 | define | @define-agent | Manter o nome BLACKBOARD | sem migração; /work, dashboard e overrides seguem | renomear com alias | — | DEFINE_LIVING_MEMORY.md#objetivos | 2026-09-23 |
| D-007 | define | @define-agent | Pergunta 🔴 bloqueia só Define→Design e Design→Build | onde decidir em silêncio sai caro | todas as transições; só aviso | — | DEFINE_LIVING_MEMORY.md#objetivos | 2026-09-23 |
| D-008 | design | @design-agent | Coluna Fase nas tabelas existentes | parser simples e dashboard intacto | seção Diário única; JOURNAL | — | DESIGN_LIVING_MEMORY.md#decisão-1-coluna-fase-nas-tabelas-existentes-não-uma-seção-diário-separada | 2026-09-23 |
| D-009 | design | @design-agent | Parser dirigido pelo cabeçalho, sem acento | um parser para formato antigo e novo | colunas por posição; YAML por entrada | — | DESIGN_LIVING_MEMORY.md#decisão-2-parser-dirigido-pelo-cabeçalho-da-tabela-normalizado-sem-acento | 2026-09-23 |
| D-010 | design | @design-agent | Um script com subcomandos em plugin-extras/scripts/ | build e Grok já copiam a pasta inteira | scripts/; quatro scripts | — | DESIGN_LIVING_MEMORY.md#decisão-3-um-script-com-subcomandos-em-plugin-extrasscripts | 2026-09-23 |
| D-011 | design | @design-agent | Gate por script + prompt; 🟡 Delegada não bloqueia | determinístico com fallback no prompt | só prompt; hook PreToolUse | — | DESIGN_LIVING_MEMORY.md#decisão-4-gate-por-script--instrução-de-prompt-status--delegada-não-bloqueia | 2026-09-23 |
| D-012 | design | @design-agent | Resumo em faixas fixas dentro de 15 linhas | o que bloqueia vem primeiro | TF-IDF; só recência | — | DESIGN_LIVING_MEMORY.md#decisão-5-ranqueamento-do-resumo-em-faixas-fixas-dentro-de-15-linhas | 2026-09-23 |
| D-013 | design | @design-agent | Domínios KB por cascata de fontes | cobre o archive sem migração | exigir domínio declarado; parser YAML | — | DESIGN_LIVING_MEMORY.md#decisão-6-domínios-kb-por-cascata-de-fontes | 2026-09-23 |
| D-014 | design | @design-agent | MEMORY_INDEX.md derivado e fora do git | evita conflito entre worktrees | versionar o índice | — | DESIGN_LIVING_MEMORY.md#decisão-7-memory_indexmd-é-artefato-derivado-e-fica-fora-do-git | 2026-09-23 |
| D-015 | design | @design-agent | Protocolo no contrato + bloco curto por agente | regra num lugar, instrução onde o agente lê | skill novo; protocolo duplicado | — | DESIGN_LIVING_MEMORY.md#decisão-8-protocolo-único-no-contrato-bloco-curto-em-cada-agente | 2026-09-23 |
| D-016 | design | @design-agent | Build cria o Blackboard só se não existir | evita apagar a trajetória | Blackboard de Build separado | — | DESIGN_LIVING_MEMORY.md#decisão-9-build-cria-o-blackboard-só-se-ele-não-existir | 2026-09-23 |
| D-017 | design | @design-agent | Evidência do problema corrigida no DEFINE v1.1 | Step 8 do /ship (2026-06-21) é posterior aos dois ships arquivados | manter o argumento 'repo sem MEMORY.md' | — | DEFINE_LIVING_MEMORY.md#histórico-de-revisões | 2026-09-23 |
| D-018 | build | @build-agent | Script e testes escritos direto pelo build-agent | parser e testes evoluíram juntos; menos repasse de contexto | delegar a @python-developer e @test-generator | — | reports/BUILD_REPORT_LIVING_MEMORY.md | 2026-09-23 |
| D-019 | build | @build-agent | Cascata de domínios: Blackboard → linha Domínios KB do DEFINE/BRAINSTORM → varredura do DEFINE; brief aceita --domains | feature nova no Define ainda não tem DEFINE nem Blackboard | só DEFINE como fonte | D-013 | plugin-extras/scripts/memory-index.py | 2026-09-23 |
| D-020 | build | @build-agent | Faixa entre features alterna decisão e lição (D, L, D, L) por recência | por recência pura as lições do SHIPPED escondiam as decisões | recência pura | D-012 | plugin-extras/scripts/memory-index.py | 2026-09-23 |
| D-021 | build | @build-agent | AT-007 usa o domínio genai | não existe domínio KB 'kb' em _index.yaml | manter 'kb' | — | DEFINE_LIVING_MEMORY.md#testes-de-aceitação | 2026-09-23 |
| D-022 | build | @build-agent | /ship passa a arquivar e limpar BRAINSTORM_{FEATURE}.md | o archive perdia o BRAINSTORM e a trajetória da fase 0 | manter como estava | — | .claude/commands/workflow/ship.md | 2026-09-23 |
| D-023 | build | @build-agent | Nova env AGENTSPEC_MEMORY_TAIL (padrão 5) no SessionStart | ajuste sem editar o hook | valor fixo | — | plugin-extras/scripts/init-workspace.sh | 2026-09-23 |
| D-024 | iterate | @claude | Hooks do plugin chamam brief, gate (criação do DESIGN) e build | E2E: agentes gravam o Blackboard mas pulam o script | só prompt | D-011 | DESIGN_LIVING_MEMORY.md#decisão-10-hooks-do-plugin-garantem-as-chamadas-ao-script | 2026-09-24 |
| D-025 | iterate | @claude | Parser aceita coluna ID e avisa (exit 2) sobre linhas ilegíveis | E2E: 8 entradas sumiram em silêncio | aceitar só '#' | D-009 | DESIGN_LIVING_MEMORY.md#decisão-11-parser-aceita-coluna-id-e-avisa-sobre-linhas-ilegíveis | 2026-09-24 |
| D-026 | iterate | @claude | Caminho do script: ${CLAUDE_PLUGIN_ROOT} exato → $AGENTSPEC_MEMORY_INDEX → repo fonte | a forma ':-.' não é substituída e o Bash não vê a variável | buscar no cache de plugins | — | DESIGN_LIVING_MEMORY.md#decisão-12-caminho-do-script-em-três-níveis | 2026-09-24 |
| D-027 | iterate | @claude | 🔴 fecha só com resposta do usuário; só Status/Resolução mudam na linha | E2E: design fechou a 🔴 por premissa | hook bloqueando 🔴→🟢 | — | DESIGN_LIVING_MEMORY.md#decisão-13--só-fecha-com-resposta-do-usuário-só-statusresolução-mudam-na-linha | 2026-09-24 |

---

## Premissas

| # | Fase | Premissa | Se Errada | Status | Onde Ler |
|---|------|----------|-----------|--------|----------|
| A-001 | define | Agentes seguem a instrução de anexar ao sair da fase | captura automática falha como a manual | ❌ Derrubada no E2E — mitigada por D-024…D-027 | DEFINE_LIVING_MEMORY.md#premissas |
| A-002 | define | Domínio KB em comum é bom critério de relevância entre features | ruído ou features relacionadas perdidas | ⏳ Não validada | DEFINE_LIVING_MEMORY.md#premissas |
| A-003 | define | Documentos arquivados são parseáveis por heading apesar dos acentos | SC-4 falharia | ✅ Validada | DEFINE_LIVING_MEMORY.md#premissas |
| A-004 | define | DEFINEs arquivados nem sempre declaram domínios KB | AT-007 dependeria de inferência | ✅ Validada | DEFINE_LIVING_MEMORY.md#premissas |
| A-005 | define | Volume de memória fica em dezenas de features / centenas de entradas | índice Markdown grande demais | ⏳ Não validada | DEFINE_LIVING_MEMORY.md#premissas |

---

## Perguntas Abertas e Bloqueadores

| # | Fase | Levantado por | Pergunta / Bloqueador | Status | Resolução |
|---|------|---------------|------------------------|--------|-----------|
| Q-001 | brainstorm | @brainstorm-agent | Onde a falta de contexto mais dói? | 🟢 Resolvido | os três: fase, feature e sessão |
| Q-002 | brainstorm | @brainstorm-agent | Quem registra o que acontece em cada fase? | 🟢 Resolvido | automático pelos agentes |
| Q-003 | brainstorm | @brainstorm-agent | Como o contexto volta ao entrar na fase? | 🟢 Resolvido | índice curto + leitura sob demanda |
| Q-004 | define | @define-agent | Formato do Diário | 🟢 Resolvido | D-008 |
| Q-005 | define | @define-agent | Local do script | 🟢 Resolvido | D-010 |
| Q-006 | define | @define-agent | Ranqueamento acima de 15 linhas | 🟢 Resolvido | D-012 → D-020 |
| Q-007 | define | @define-agent | Domínios KB de feature arquivada | 🟢 Resolvido | D-013 → D-019 |
| Q-008 | define | @define-agent | Mecanismo do bloqueio | 🟢 Resolvido | D-011 |
| Q-009 | build | @build-agent | Validar AT-001/002/003/011 (comportamento de prompt) numa feature real | 🟢 Resolvido | AT-001/002/003 validados no E2E após D-024…D-027; AT-011 segue para o /ship real — ver reports/BUILD_REPORT_LIVING_MEMORY.md#validação-e2e-q-009 |

---

## Status dos Arquivos

| Arquivo | Agente | Status | Verificado | Notas |
|---------|--------|--------|------------|-------|
| `.claude/sdd/templates/BLACKBOARD_TEMPLATE.md` | @build-agent | ✅ Completo | ✅ | — |
| `.claude/sdd/architecture/WORKFLOW_CONTRACTS.yaml` | @build-agent | ✅ Completo | ✅ | — |
| `plugin-extras/scripts/memory-index.py` | @build-agent | ✅ Completo | ✅ | — |
| `tests/fixtures/memory/` | @build-agent | ✅ Completo | ✅ | — |
| `tests/test_memory_index.py` | @build-agent | ✅ Completo | ✅ | — |
| `plugin-extras/scripts/init-workspace.sh` | @build-agent | ✅ Completo | ✅ | — |
| `.gitignore` | @build-agent | ✅ Completo | ✅ | — |
| `.claude/agents/workflow/*.md (9)` | @build-agent | ✅ Completo | ✅ | — |
| `.claude/commands/workflow/*.md (10)` | @build-agent | ✅ Completo | ✅ | — |
| `.claude/commands/core/memory.md` | @build-agent | ✅ Completo | ✅ | — |
| `docs/concepts/living-memory.md` | @build-agent | ✅ Completo | ✅ | — |
| `CHANGELOG.md` | @build-agent | ✅ Completo | ✅ | — |
| `bundles regenerados (plugin, .codex, grok, dsh)` | @build-agent | ✅ Completo | ✅ | — |

**Legenda:** ⏳ Pendente · 🔄 Em Andamento · ✅ Completo · ❌ Bloqueado

---

## Melhorias / Iterações

| # | Data | Pedido | Tipo | Agente | Status |
|---|------|--------|------|--------|--------|
