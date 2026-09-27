# BLACKBOARD: Demo

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | DEMO |
| **Fase** | Build |
| **Atualizado em** | 2026-09-20 |
| **Domínios KB** | genai |
| **Relacionada a** | — |

---

## Interfaces Compartilhadas

| # | Tipo | Nome / Assinatura | Definido por | Consumido por | Notas |
|---|------|-------------------|--------------|---------------|-------|
| I-001 | função | `load()` | @python-developer | @test-generator | retorna dict |

---

## Log de Decisões

| # | Fase | Agente | Decisão | Justificativa | Alternativa Rejeitada | Substitui | Onde Ler | Data |
|---|------|--------|---------|---------------|-----------------------|-----------|----------|------|
| D-001 | {brainstorm/define/design/build/iterate} | @{agente} | {o que foi decidido} | {por quê, 1 frase} | {o que não foi feito} | — | {DESIGN_{FEATURE}.md#decisão-1-…} | {YYYY-MM-DD} |
| D-001 | brainstorm | @brainstorm-agent | Abordagem A: arquivo único | menos peças | Abordagem B | — | BRAINSTORM_DEMO.md#abordagem-selecionada | 2026-09-10 |
| D-002 | design | @design-agent | Saída em JSON | legível por máquina | YAML | — | DESIGN_DEMO.md#decisão-1-saída-em-json | 2026-09-12 |
| D-003 | design | @design-agent | Script stdlib | sem dependência | pydantic | — | — | 2026-09-12 |
| D-004 | build | @python-developer | Saída em YAML | consumidor já lê YAML | JSON | D-002 | — | 2026-09-15 |

---

## Premissas

| # | Fase | Premissa | Se Errada | Status | Onde Ler |
|---|------|----------|-----------|--------|----------|
| A-001 | define | Volume abaixo de 1k linhas | precisaria de streaming | ⏳ Não validada | DEFINE_DEMO.md#premissas |
| A-002 | define | Python 3.10+ disponível | fallback manual | ✅ Validada | DEFINE_DEMO.md#premissas |

---

## Perguntas Abertas e Bloqueadores

| # | Fase | Levantado por | Pergunta / Bloqueador | Status | Resolução |
|---|------|---------------|------------------------|--------|-----------|
| Q-001 | brainstorm | @brainstorm-agent | Quem consome a saída? | 🟢 Resolvido | time de dados |
| Q-002 | define | @define-agent | Formato exato da saída | 🟡 Delegada ao design | D-002 |

---

## Status dos Arquivos

| Arquivo | Agente | Status | Verificado | Notas |
|---------|--------|--------|------------|-------|
| `src/demo.py` | @python-developer | ✅ Completo | ✅ | — |

---

## Melhorias / Iterações

| # | Data | Pedido | Tipo | Agente | Status |
|---|------|--------|------|--------|--------|
| M-001 | 2026-09-20 | melhora a mensagem de erro | código | @python-developer | ✅ |
