# DESIGN: Bash Error Case

> `eval_missing_cmd` chama um comando inexistente — sintaxe válida (`bash -n`
> passa), mas falha em runtime com "command not found" (exit 127), o caso
> canônico de `_BASH_ERROR`. `eval_interpreter` imprime uma mensagem no
> formato do erro de interpretador Python (`No module named ...`) para
> exercitar `_INTERPRETER_ERROR` sem depender do Python real da máquina de
> CI.

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | BASH_ERROR_CASE |
| **Status** | Pronto para Build |
| **Evals Digest** | (não congelado) |

## Evals

<!-- agentspec:evals:contract -->
```toml
[[eval]]
id = "eval_missing_cmd"
verifies = ["AT-001"]
check_type = "deterministic"
description = "Chama um comando que não existe (erro de bash em runtime)"
run = '''
nonexistent_command_xyz_12345
'''

[[eval]]
id = "eval_unbound"
verifies = ["AT-001"]
check_type = "deterministic"
description = "Usa uma variável não definida sob set -u (bash sai com exit 1)"
run = '''
echo "$UNDEFINED_VARIABLE_XYZ_12345"
'''

[[eval]]
id = "eval_interpreter"
verifies = ["AT-002"]
check_type = "deterministic"
description = "Simula um interpretador Python sem pytest instalado"
run = '''
echo "python3.11: No module named pytest" >&2
exit 1
'''
```

## Próximo Passo

**Pronto para:** fixture — não é uma feature real do AgentSpec.
