# DESIGN: Too Many Graded Case

> 4 evals no contrato, 3 `graded` (75% > 50%) — `validate` deve emitir o aviso
> `TOO_MANY_GRADED` mas continuar com exit 0 (é aviso, não erro).

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | TOO_MANY_GRADED_CASE |
| **Status** | Pronto para Build |
| **Evals Digest** | (não congelado) |

## Evals

<!-- agentspec:evals:contract -->
```toml
[[eval]]
id = "eval_det"
verifies = ["AT-001"]
check_type = "deterministic"
description = "Único eval determinístico do contrato"
run = '''
true
'''

[[eval]]
id = "eval_g1"
verifies = ["AT-002"]
check_type = "graded"
description = "Primeiro critério subjetivo"

[eval.state]
report = "echo 'estado 1'"

[[eval.questions]]
id = "q1"
type = "noul"
instructions = "O relatório apoia o claim 1?"

[[eval.questions]]
id = "q2"
type = "score"
instructions = "Quão forte é a evidência do claim 1?"
criteria = ["fraca", "média", "forte"]

[[eval]]
id = "eval_g2"
verifies = ["AT-003"]
check_type = "graded"
description = "Segundo critério subjetivo"

[eval.state]
report = "echo 'estado 2'"

[[eval.questions]]
id = "q1"
type = "noul"
instructions = "O relatório apoia o claim 2?"

[[eval.questions]]
id = "q2"
type = "score"
instructions = "Quão forte é a evidência do claim 2?"
criteria = ["fraca", "média", "forte"]

[[eval]]
id = "eval_g3"
verifies = ["AT-004"]
check_type = "graded"
description = "Terceiro critério subjetivo"

[eval.state]
report = "echo 'estado 3'"

[[eval.questions]]
id = "q1"
type = "noul"
instructions = "O relatório apoia o claim 3?"

[[eval.questions]]
id = "q2"
type = "score"
instructions = "Quão forte é a evidência do claim 3?"
criteria = ["fraca", "média", "forte"]
```

## Próximo Passo

**Pronto para:** fixture — não é uma feature real do AgentSpec.
