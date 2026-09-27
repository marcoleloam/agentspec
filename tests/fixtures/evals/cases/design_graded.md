# DESIGN: Graded Case

> Um eval `graded` com estado estruturado (`report`, `evidence`) e duas
> perguntas (Noul + Score), no formato do Padrão 2 do DESIGN.

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | GRADED_CASE |
| **Status** | Pronto para Build |
| **Evals Digest** | (não congelado) |

## Evals

<!-- agentspec:evals:contract -->
```toml
[[eval]]
id = "eval_g1"
verifies = ["AT-001"]
check_type = "graded"
description = "A evidência apoia o claim do relatório?"

[eval.state]
report = "echo 'O build reporta PASS para o AT-001.'"
evidence = "echo 'eval_1 saiu com exit 0, sem stderr.'"

[[eval.questions]]
id = "consistent"
type = "noul"
instructions = "A `evidence` apoia o `report`?"

[[eval.questions]]
id = "quality"
type = "score"
instructions = "Quão forte é a evidência em relação ao claim?"
criteria = ["contradiz o claim", "sem evidência", "evidência fraca", "evidência forte"]
```

## Próximo Passo

**Pronto para:** fixture — não é uma feature real do AgentSpec.
