# DESIGN: Orphan Case

> AT-002 não tem nenhum eval com `verifies` apontando para ele (`ORPHAN_AT`);
> `eval_2` aponta para `AT-099`, que não existe no DEFINE (`UNKNOWN_AT`).

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | ORPHAN_CASE |
| **Status** | Pronto para Build |
| **Evals Digest** | (não congelado) |

## Evals

<!-- agentspec:evals:contract -->
```toml
[[eval]]
id = "eval_1"
verifies = ["AT-001"]
check_type = "deterministic"
description = "Cobre AT-001"
run = '''
true
'''

[[eval]]
id = "eval_2"
verifies = ["AT-099"]
check_type = "deterministic"
description = "Aponta para um AT que não existe no DEFINE"
run = '''
true
'''
```

## Próximo Passo

**Pronto para:** fixture — não é uma feature real do AgentSpec.
