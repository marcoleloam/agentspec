# ReAct Agent

> **Purpose**: Reason+Act loop where ShopAgent autonomously decides which store to query
> **Confidence**: 0.95
> **MCP Validated**: 2026-04-12

## Overview

`create_react_agent` from `langgraph.prebuilt` creates an agent that follows the ReAct pattern: Thought (reasoning) → Action (tool call) → Observation (tool result) → Answer. The agent autonomously decides which tool to use based on tool docstrings, then synthesizes a final response from the tool output.

## The Pattern

```python
from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent

llm = ChatAnthropic(model="claude-sonnet-4-20250514", temperature=0)

# Create agent with dual-store tools
agent = create_react_agent(
    model=llm,
    tools=[supabase_execute_sql, qdrant_semantic_search],
)

# Invoke — agent decides which tool to use
result = agent.invoke({
    "messages": [{"role": "user", "content": "Qual o faturamento total por estado?"}]
})

# ReAct trace:
#   Thought: "User wants revenue by state — this is exact numerical data"
#   Action:  supabase_execute_sql("SELECT c.state, SUM(o.total)...")
#   Observe: "SP: 127430, RJ: 89210, MG: 68440"
#   Answer:  "O faturamento por estado é: SP R$ 127.430, RJ R$ 89.210..."

# Access final answer
final_message = result["messages"][-1]
print(final_message.content)
```

## Quick Reference

| Method | Input | Output | Notes |
|--------|-------|--------|-------|
| `agent.invoke(input)` | `{"messages": [...]}` | `{"messages": [...]}` | Synchronous, full result |
| `agent.stream(input)` | `{"messages": [...]}` | Iterator of state updates | Stream intermediate steps |
| `agent.astream_events(input, version="v2")` | `{"messages": [...]}` | Async event iterator | **Use with Chainlit** |

## Common Mistakes

### Wrong

```python
# LEGACY API — do NOT use
from langchain.agents import create_react_agent  # Old, deprecated
```

### Correct

```python
# MODERN API — use langgraph.prebuilt
from langgraph.prebuilt import create_react_agent  # Current, recommended
```

### Wrong

```python
# Raw string input — agent expects messages dict
result = agent.invoke("Qual o faturamento?")  # TypeError
```

### Correct

```python
# Messages dict format
result = agent.invoke({
    "messages": [{"role": "user", "content": "Qual o faturamento?"}]
})
```

## Related

- [Tools](../concepts/tools.md)
- [Chat Models](../concepts/chat-models.md)
- [Routing](../concepts/routing.md)
- [Dual-Tool Pattern](../patterns/react-agent-dual-tools.md)
