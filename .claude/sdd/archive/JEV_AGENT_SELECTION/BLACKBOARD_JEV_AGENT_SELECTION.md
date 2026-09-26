# BLACKBOARD: Seleção de Agentes por Rubrica

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | JEV_AGENT_SELECTION |
| **Fase** | Ship |
| **Atualizado em** | 2026-09-26 |
| **Domínios KB** | genai, prompt-engineering, python, testing |
| **Relacionada a** | POST_BUILD_EVALS |
| **DESIGN** | [DESIGN_JEV_AGENT_SELECTION.md](DESIGN_JEV_AGENT_SELECTION.md) |
| **Status** | ✅ Completo |

---

## Interfaces Compartilhadas

| # | Tipo | Nome / Assinatura | Definido por | Consumido por | Notas |
|---|------|-------------------|-------------|---------------|-------|
| I-001 | contrato | `AGENT_SELECTION_RUBRIC.md` | @iterate-agent | comandos de fase e baseline | Mesmo bloco da rubrica em quatro comandos e no benchmark |

---

## Log de Decisões

| # | Fase | Agente | Decisão | Justificativa | Alternativa Rejeitada | Substitui | Onde Ler | Data |
|---|------|--------|---------|---------------|-----------------------|-----------|----------|------|
| D-001 | iterate | @iterate-agent | Aceitar a solução v1.3 por rubrica com evals executáveis e medição retrospectiva identificada | O JEV como decisor não atingiu os critérios originais; o BUILD_REPORT mediu ganho da LLM e deixou o aceite desalinhado | Declarar sucesso do JEV pelas metas originais | DESIGN v1.3 Decisão 16 | DESIGN_JEV_AGENT_SELECTION.md#decisão-17-v14-aceite-da-rubrica-com-medição-retrospectiva-e-execução-real | 2026-09-26 |
| D-002 | ship | @ship-agent | Arquivar o aceite v1.4 com sete evals PASS | O contrato vigente substituiu as metas históricas do JEV como decisor | Tratar o waiver legado como prova | — | SHIPPED_2026-09-26.md#gate-de-eval | 2026-09-26 |
| D-003 | ship | @ship-agent | Preservar no resumo as falhas antigas e limites do benchmark | Rótulos Claude e corpus retrospectivo não provam generalização | Declarar validação humana | — | SHIPPED_2026-09-26.md#limites-da-evidência | 2026-09-26 |
| D-004 | ship | @ship-agent | Recomendar nova amostra rotulada pelo maintainer após a entrega | A medição atual usa 46 casos não versionados | Inferir acurácia de produção | — | SHIPPED_2026-09-26.md#recomendações | 2026-09-26 |


---

## Premissas

| # | Fase | Premissa | Se Errada | Status | Onde Ler |
|---|------|----------|-----------|--------|----------|
| A-001 | iterate | O corpus retrospectivo está disponível neste worktree, mas seus rótulos não são humanos | A métrica não serve como prova de generalização | ✅ Validada | DESIGN_JEV_AGENT_SELECTION.md#decisão-17-v14-aceite-da-rubrica-com-medição-retrospectiva-e-execução-real |

---

## Perguntas Abertas e Bloqueadores

| # | Fase | Levantado por | Pergunta / Bloqueador | Status | Resolução |
|---|------|---------------|------------------------|--------|-----------|

---

## Status dos Arquivos

| Arquivo | Agente | Status | Verificado | Notas |
|---------|--------|--------|------------|-------|
| `DEFINE_JEV_AGENT_SELECTION.md` | @iterate-agent | 🔄 Em Andamento | — | Critérios v1.4 em verificação |
| `DESIGN_JEV_AGENT_SELECTION.md` | @iterate-agent | 🔄 Em Andamento | — | Contrato v1.4 em verificação |

---

## Melhorias / Iterações

| # | Data | Pedido | Tipo | Agente | Status |
|---|------|--------|------|--------|--------|
| M-001 | 2026-09-26 | Atualizar ou cumprir os critérios, obter evidências e repetir /eval antes de /ship | design | @iterate-agent | 🔄 |
