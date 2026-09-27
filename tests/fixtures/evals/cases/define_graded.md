# DEFINE: Graded Case

> Fixture com um único eval `graded`, usada para exercitar a classificação do
> JEV (calibrado, baixa confiança, indisponível, sem calibração).

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | GRADED_CASE |

## Testes de Aceitação

| ID | Cenário | Dado | Quando | Então |
|----|---------|------|--------|-------|
| AT-001 | Relatório apoiado por evidência | `report` e `evidence` no estado | JEV avalia | Decisão `pass`/`fail`/`escalated` conforme confiança |

## Próximo Passo

**Pronto para:** fixture — não é uma feature real do AgentSpec.
