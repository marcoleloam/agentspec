# DESIGN: Trivial Case

> `eval_1` passa sem nenhuma implementação — o PRE-check deve avisar que o
> eval não discrimina, sem bloquear o build.

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | TRIVIAL_CASE |
| **Status** | Pronto para Build |
| **Evals Digest** | (não congelado) |

## Evals

<!-- agentspec:evals:contract -->
```toml
[[eval]]
id = "eval_1"
verifies = ["AT-001"]
check_type = "deterministic"
description = "Passa antes de qualquer implementação"
run = '''
true
'''
```

## Próximo Passo

**Pronto para:** fixture — não é uma feature real do AgentSpec.
