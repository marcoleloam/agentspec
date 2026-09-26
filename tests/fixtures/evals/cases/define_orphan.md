# DEFINE: Orphan Case

> Fixture: dois ATs, mas o contrato do DESIGN só cobre um deles e ainda
> referencia um AT inexistente — exercita `ORPHAN_AT` e `UNKNOWN_AT`.

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | ORPHAN_CASE |

## Testes de Aceitação

| ID | Cenário | Dado | Quando | Então |
|----|---------|------|--------|-------|
| AT-001 | Coberto | — | — | Tem eval com `verifies: [AT-001]` |
| AT-002 | Órfão | — | — | Nenhum eval o cobre |

## Próximo Passo

**Pronto para:** fixture — não é uma feature real do AgentSpec.
