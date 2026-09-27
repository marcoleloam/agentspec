# DEFINE: Bash Error Case

> Fixture para o PRE-check: dois evals sintaticamente válidos (passam
> `bash -n`) mas que falham em runtime — um por comando inexistente, outro
> simulando o erro de interpretador Python sem `pytest`.

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | BASH_ERROR_CASE |

## Testes de Aceitação

| ID | Cenário | Dado | Quando | Então |
|----|---------|------|--------|-------|
| AT-001 | Comando inexistente | — | eval roda | Bash sai com `command not found` |
| AT-002 | Interpretador quebrado | — | eval roda | Mensagem `No module named` |

## Próximo Passo

**Pronto para:** fixture — não é uma feature real do AgentSpec.
