# DEFINE: Basic

> Feature mínima usada como fixture de teste do `eval_runner`: 3 ATs, todos
> cobertos por evals `deterministic` que passam quando os artefatos esperados
> existem no repositório.

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | BASIC |
| **Status** | ✅ Complete (Designed) |

## Testes de Aceitação

| ID | Cenário | Dado | Quando | Então |
|----|---------|------|--------|-------|
| AT-001 | Saudação gerada | Build cria `greeting.txt` | eval roda | `greeting.txt` contém exatamente `hello agentspec` |
| AT-002 | Config válida | Build cria `config.json` | eval roda | `config.json` é JSON válido com `ready: true` |
| AT-003 | Script de saudação | Build cria `greet.sh` | eval roda | `bash greet.sh` imprime `hi` |

## Próximo Passo

**Pronto para:** fixture — não é uma feature real do AgentSpec.
