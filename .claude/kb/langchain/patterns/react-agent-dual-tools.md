# ReAct Agent Dual Tools

> **Purpose**: ShopAgent LangChain agent with supabase + qdrant tools that autonomously routes SQL vs semantic queries
> **MCP Validated**: 2026-04-12

## When to Use

- Day 3 single-agent ShopAgent with autonomous query routing
- Demonstrating ReAct pattern with real MCP-connected tools
- Agent that decides: "this needs exact numbers" (SQL) vs "this needs meaning" (semantic)

## Implementation

```python
"""ShopAgent Day 3: ReAct agent with dual-store routing."""
from langchain_anthropic import ChatAnthropic
from langchain.tools import tool
from langgraph.prebuilt import create_react_agent


@tool
def supabase_execute_sql(query: str) -> str:
    """Execute SQL query against Supabase Postgres for EXACT data.

    Use when the question asks for specific numbers, totals, or structured data:
    - Faturamento (revenue) by state, category, or period
    - Total de pedidos (order counts), ticket medio (average order value)
    - Payment method distribution, customer segment analysis
    - Any question requiring aggregation, GROUP BY, or JOINs

    Args:
        query: SQL query string to execute against the shopagent database.
    """
    # In production: call MCP Supabase execute_sql tool
    # result = mcp_supabase.execute_sql(query=query)
    return f"[SQL] Executed: {query}"


@tool
def qdrant_semantic_search(question: str) -> str:
    """Search customer reviews by MEANING using Qdrant vector database.

    Use when the question asks about opinions, complaints, or text patterns:
    - Reclamacoes (complaints) about delivery, quality, price
    - Customer sentiment analysis (positive, negative, neutral)
    - Product feedback themes and review patterns
    - Any question about what customers SAY, THINK, or FEEL

    Args:
        question: Natural language question for semantic similarity search.
    """
    # In production: call MCP Qdrant search tool
    # result = mcp_qdrant.search(collection="shopagent_reviews", query=question)
    return f"[Semantic] Searched: {question}"


# Initialize Claude with deterministic routing
llm = ChatAnthropic(
    model="claude-sonnet-4-20250514",
    temperature=0,
    streaming=True,
)

# Create ReAct agent with both tools
agent = create_react_agent(
    model=llm,
    tools=[supabase_execute_sql, qdrant_semantic_search],
)


def ask(question: str) -> str:
    """Ask ShopAgent a question — it routes to the right store."""
    result = agent.invoke({
        "messages": [{"role": "user", "content": question}]
    })
    return result["messages"][-1].content


if __name__ == "__main__":
    # SQL routing — exact numbers
    print(ask("Qual o faturamento total por estado?"))
    # Agent thinks: "revenue by state = exact numbers" → supabase_execute_sql

    # Semantic routing — meaning-based search
    print(ask("Quais clientes reclamam de entrega?"))
    # Agent thinks: "complaints about delivery = text meaning" → qdrant_semantic_search

    # Hybrid — agent may call both tools sequentially
    print(ask("Qual o ticket medio dos clientes que reclamam de entrega no Sudeste?"))
    # Agent thinks: "find complainers (semantic) then calculate average (SQL)"
```

## Configuration

| Setting | Value | Description |
|---------|-------|-------------|
| `model` | `"claude-sonnet-4-20250514"` | Claude Sonnet for balanced speed/quality |
| `temperature` | `0` | Deterministic tool routing |
| `streaming` | `True` | Required for Chainlit integration |
| `max_iterations` | default (25) | Max ReAct loops before stopping |

## Example Usage

```python
# Day 3 demo questions — the agent routes each correctly:

# → supabase_execute_sql
ask("Quantos pedidos foram feitos por pix?")
ask("Top 5 produtos por faturamento")
ask("Distribuicao de clientes por segmento")

# → qdrant_semantic_search
ask("O que os clientes falam sobre qualidade?")
ask("Reviews negativos sobre frete")
ask("Clientes satisfeitos com o produto")
```

## See Also

- [LangGraph Routing](../patterns/langgraph-routing.md)
- [Tools](../concepts/tools.md)
- [Supabase Ledger Queries](../../supabase/patterns/shopagent-ledger-queries.md)
- [Chainlit Integration](../../chainlit/patterns/langchain-integration.md)
