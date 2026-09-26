# DESIGN: Basic

> Fixture mínima com contrato de evals válido: 3 evals `deterministic`, um
> por AT, cobrindo o caminho feliz do `eval_runner`.

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | BASIC |
| **Status** | Pronto para Build |
| **Evals Digest** | (não congelado) |

## Evals

<!-- agentspec:evals:contract -->
```toml
[[eval]]
id = "eval_1"
verifies = ["AT-001"]
check_type = "deterministic"
description = "greeting.txt existe e contém a saudação esperada"
run = '''
if [ ! -f greeting.txt ]; then echo "greeting.txt not found" >&2; exit 1; fi
grep -qx "hello agentspec" greeting.txt || { echo "content mismatch" >&2; exit 1; }
'''

[[eval]]
id = "eval_2"
verifies = ["AT-002"]
check_type = "deterministic"
description = "config.json é JSON válido com ready=true"
run = '''
"$AGENTSPEC_PYTHON" -c "import json,sys; d=json.load(open('config.json')); sys.exit(0 if d.get('ready') is True else 1)"
'''

[[eval]]
id = "eval_3"
verifies = ["AT-003"]
check_type = "deterministic"
description = "greet.sh imprime hi"
run = '''
bash greet.sh | grep -qx "hi"
'''
```

## Próximo Passo

**Pronto para:** fixture — não é uma feature real do AgentSpec.
