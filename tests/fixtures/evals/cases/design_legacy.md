# DESIGN: Legacy Case

> Nenhuma seção `## Evals` — este DESIGN é anterior à feature POST_BUILD_EVALS.
> `eval_runner` deve tratá-lo como legado: `verify` recusa a menos que exista
> um waiver global (`waive --legacy`).

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | LEGACY_CASE |
| **Status** | ✅ Complete (Built) |

## Decisões Principais

Este DESIGN não declara nenhum contrato de evals — comportamento esperado de
uma feature arquivada antes desta capacidade existir.

## Próximo Passo

**Pronto para:** fixture — não é uma feature real do AgentSpec.
