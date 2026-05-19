# Test Cases

> **Purpose**: Structure LLMTestCase to evaluate ShopAgent tool routing and response quality
> **Confidence**: 0.95
> **MCP Validated**: 2026-04-12

## Overview

`LLMTestCase` is the fundamental unit of evaluation in DeepEval. It wraps the agent's input and output alongside optional metadata — tool calls and retrieval context — that specific metrics require. For ShopAgent, two routing paths need coverage: SQL queries routed to `supabase_execute_sql` and semantic queries routed to `qdrant_semantic_search`.

## The Pattern

```python
from deepeval.test_case import LLMTestCase, ToolCall

# SQL routing test — structured data query
sql_test = LLMTestCase(
    input="Qual o faturamento total por estado?",
    actual_output="SP: R$ 127.430, RJ: R$ 89.210, MG: R$ 68.440",
    tools_called=[
        ToolCall(
            name="supabase_execute_sql",
            input={"query": "SELECT c.state, SUM(o.total) FROM orders o JOIN customers c ON o.customer_id = c.customer_id GROUP BY c.state"},
        )
    ],
    expected_tools=[ToolCall(name="supabase_execute_sql")],
)

# Semantic routing test — unstructured text search
semantic_test = LLMTestCase(
    input="Quais clientes reclamam de entrega?",
    actual_output="23 clientes mencionaram problemas com entrega.",
    retrieval_context=[
        "Demorou 15 dias para chegar, absurdo.",
        "Nao recebi meu pedido ainda.",
        "Frete muito caro e demorou demais.",
    ],
    tools_called=[
        ToolCall(
            name="qdrant_semantic_search",
            input={"question": "reclamacao entrega"},
        )
    ],
    expected_tools=[ToolCall(name="qdrant_semantic_search")],
)
```

## Quick Reference

| Field | When to Populate | Example |
|-------|-----------------|---------|
| `input` | Always | `"Qual o faturamento total?"` |
| `actual_output` | Always | Agent's response string |
| `expected_output` | When ground truth known | `"R$ 284.080"` |
| `retrieval_context` | For FaithfulnessMetric | Chunks from Qdrant |
| `tools_called` | For ToolCorrectnessMetric | `[ToolCall(name="supabase_execute_sql")]` |
| `expected_tools` | For ToolCorrectnessMetric | `[ToolCall(name="supabase_execute_sql")]` |

## Common Mistakes

### Wrong

```python
# Passing tool names as strings — TypeError
test = LLMTestCase(
    input="Faturamento por estado?",
    actual_output="...",
    tools_called=["supabase_execute_sql"],     # WRONG: strings
    expected_tools=["supabase_execute_sql"],    # WRONG: strings
)
```

### Correct

```python
# Use ToolCall objects
test = LLMTestCase(
    input="Faturamento por estado?",
    actual_output="...",
    tools_called=[ToolCall(name="supabase_execute_sql", input={"query": "SELECT..."})],
    expected_tools=[ToolCall(name="supabase_execute_sql")],
)
```

## Related

- [Metrics](../concepts/metrics.md)
- [Agent Evaluation Pattern](../patterns/agent-evaluation.md)
