# BLACKBOARD: Legacy

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | LEGACY |
| **Fase** | Build |
| **Atualizado em** | 2026-07-01 |

## Interfaces Compartilhadas

| # | Tipo | Nome / Assinatura | Definido por | Consumido por | Notas |
|---|------|-------------------|--------------|---------------|-------|
| I-001 | tabela | `stg_orders` | @dbt-specialist | @data-quality-analyst | PK order_id |

## Log de Decisões

| # | Agente | Decisão | Justificativa | Substitui | Data |
|---|--------|---------|---------------|-----------|------|
| D-001 | @dbt-specialist | Materializar como incremental | volume alto | — | 2026-07-01 |

## Perguntas Abertas e Bloqueadores

| # | Levantado por | Pergunta / Bloqueador | Status | Resolução |
|---|---------------|------------------------|--------|-----------|
| Q-001 | @dbt-specialist | Chave de dedupe? | 🟢 Resolvido | order_id |

## Status dos Arquivos

| Arquivo | Agente | Status | Verificado | Notas |
|---------|--------|--------|------------|-------|
| `models/stg_orders.sql` | @dbt-specialist | ✅ Completo | ✅ | — |

## Melhorias / Iterações

| # | Data | Pedido | Tipo | Agente | Status |
|---|------|--------|------|--------|--------|
