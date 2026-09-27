# DESIGN: Human Case

> Um único eval `human`, sem atestação inicial — deve ficar `pending` até que
> alguém rode `eval_runner.py attest` ou `waive`.

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | HUMAN_CASE |
| **Status** | Pronto para Build |
| **Evals Digest** | (não congelado) |

## Evals

<!-- agentspec:evals:contract -->
```toml
[[eval]]
id = "eval_h1"
verifies = ["AT-001"]
check_type = "human"
owner = "Marco"
description = "Revisão manual do resultado"
instructions = "Confira o artefato gerado e registre pass ou fail via eval_runner.py attest."
```

## Próximo Passo

**Pronto para:** fixture — não é uma feature real do AgentSpec.
