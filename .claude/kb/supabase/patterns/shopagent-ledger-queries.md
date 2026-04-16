# ShopAgent Ledger Queries

> **Purpose**: Common e-commerce SQL queries for ShopAgent via MCP Supabase — The Ledger
> **MCP Validated**: 2026-04-12

## When to Use

- AnalystAgent executing SQL queries against the ShopAgent Postgres database
- Implementing the `supabase_execute_sql` LangChain tool
- Testing SQL routing correctness with DeepEval
- Day 2-4 Ledger demonstrations

## Implementation

```python
"""ShopAgent canonical SQL queries for The Ledger (Supabase/Postgres)."""


def revenue_by_state() -> str:
    """Revenue breakdown by customer state."""
    return """
    SELECT c.state, COUNT(o.order_id) AS pedidos, SUM(o.total) AS faturamento
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    GROUP BY c.state
    ORDER BY faturamento DESC
    """


def orders_by_status() -> str:
    """Order count and revenue by status."""
    return """
    SELECT status, COUNT(*) AS total, SUM(total) AS faturamento
    FROM orders
    GROUP BY status
    ORDER BY total DESC
    """


def top_products_by_revenue(limit: int = 10) -> str:
    """Top products by total revenue."""
    return f"""
    SELECT p.name, p.category, p.brand,
           COUNT(o.order_id) AS pedidos, SUM(o.total) AS faturamento
    FROM orders o
    JOIN products p ON o.product_id = p.product_id
    GROUP BY p.product_id, p.name, p.category, p.brand
    ORDER BY faturamento DESC
    LIMIT {limit}
    """


def payment_distribution() -> str:
    """Payment method distribution."""
    return """
    SELECT payment, COUNT(*) AS total,
           ROUND(COUNT(*)::NUMERIC / SUM(COUNT(*)) OVER() * 100, 1) AS percentual
    FROM orders
    GROUP BY payment
    ORDER BY total DESC
    """


def segment_analysis() -> str:
    """Customer segment analysis with average ticket."""
    return """
    SELECT c.segment, COUNT(DISTINCT c.customer_id) AS clientes,
           COUNT(o.order_id) AS pedidos,
           ROUND(AVG(o.total), 2) AS ticket_medio
    FROM customers c
    LEFT JOIN orders o ON c.customer_id = o.customer_id
    GROUP BY c.segment
    ORDER BY ticket_medio DESC
    """
```

## Configuration

| Query | Expected Output | When LLM Should Trigger |
|-------|----------------|------------------------|
| `revenue_by_state()` | state, pedidos, faturamento | "faturamento por estado", "revenue by region" |
| `orders_by_status()` | status, total, faturamento | "pedidos por status", "quantos entregues" |
| `top_products_by_revenue()` | name, category, pedidos, faturamento | "top produtos", "mais vendidos" |
| `payment_distribution()` | payment, total, percentual | "formas de pagamento", "distribuicao pix" |
| `segment_analysis()` | segment, clientes, pedidos, ticket_medio | "segmentos", "ticket medio premium" |

## MCP Connection

```json
{
  "mcpServers": {
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres",
               "postgresql://shopagent:shopagent@localhost:5432/shopagent"]
    }
  }
}
```

Day 4 cloud migration — switch to Supabase MCP:
```json
{
  "mcpServers": {
    "supabase": {
      "command": "npx",
      "args": ["-y", "mcp-server-supabase", "--supabase-url", "https://xxxxx.supabase.co",
               "--supabase-key", "your-anon-key"]
    }
  }
}
```

## See Also

- [LangChain Tools](../../langchain/concepts/tools.md)
- [ReAct Agent Dual Tools](../../langchain/patterns/react-agent-dual-tools.md)
