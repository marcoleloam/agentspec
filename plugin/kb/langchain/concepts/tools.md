# Tools

> **Purpose**: Define callable tools that LangChain agents use for Supabase SQL and Qdrant semantic search
> **Confidence**: 0.95
> **MCP Validated**: 2026-04-12

## Overview

Tools are Python functions decorated with `@tool` that LangChain agents can invoke. The `docstring` is critical — the LLM reads it to decide WHEN to call each tool. For ShopAgent, two tools cover the dual-store architecture: `supabase_execute_sql` for exact data (The Ledger) and `qdrant_semantic_search` for meaning-based search (The Memory).

## The Pattern

```python
from langchain.tools import tool


@tool
def supabase_execute_sql(query: str) -> str:
    """Execute SQL query against Supabase Postgres for EXACT data.

    Use when the question asks for specific numbers, totals, or structured data:
    - Faturamento (revenue) by state, category, or period
    - Total de pedidos (order counts), ticket medio (average order value)
    - Payment method distribution, customer segment analysis
    - Any question requiring aggregation, GROUP BY, or JOINs
    """
    # Implementation: call MCP Supabase execute_sql
    return f"SQL Result for: {query}"


@tool
def qdrant_semantic_search(question: str) -> str:
    """Search customer reviews by MEANING using Qdrant vector database.

    Use when the question asks about opinions, complaints, or text patterns:
    - Reclamacoes (complaints) about delivery, quality, price
    - Customer sentiment (positive, negative, neutral)
    - Product feedback and review themes
    - Any question about what customers SAY or FEEL
    """
    # Implementation: call MCP Qdrant search
    return f"Semantic Result for: {question}"
```

## Quick Reference

| Param | Source | Description |
|-------|--------|-------------|
| `name` | Function name | `"supabase_execute_sql"` — LLM sees this |
| `description` | Docstring | **Routing logic** — LLM reads this to choose |
| `args_schema` | Type hints | Inferred from function signature |
| `return_direct` | Decorator param | `False` (default) — agent synthesizes final answer |

## Common Mistakes

### Wrong

```python
@tool
def search(query: str) -> str:
    """Search the database."""  # Too vague — LLM can't distinguish SQL vs semantic
    ...
```

### Correct

```python
@tool
def supabase_execute_sql(query: str) -> str:
    """Execute SQL for EXACT data: revenue, counts, averages, aggregations."""
    ...

@tool
def qdrant_semantic_search(question: str) -> str:
    """Search reviews by MEANING: complaints, sentiment, opinions, feedback."""
    ...
```

Precise docstrings are the #1 factor in correct tool routing.

## Related

- [Chat Models](../concepts/chat-models.md)
- [ReAct Agent](../concepts/react-agent.md)
- [Dual-Tool Pattern](../patterns/react-agent-dual-tools.md)
