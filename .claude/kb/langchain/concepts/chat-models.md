# Chat Models

> **Purpose**: Configure Claude as the LLM backbone for ShopAgent agents with tool-binding
> **Confidence**: 0.95
> **MCP Validated**: 2026-04-12

## Overview

`ChatAnthropic` is the LangChain wrapper for Claude models. It supports `bind_tools` to attach tool schemas that the LLM can invoke, and `streaming=True` for token-by-token output in Chainlit. For ShopAgent, use `claude-sonnet-4-20250514` with `temperature=0` for deterministic tool routing.

## The Pattern

```python
from langchain_anthropic import ChatAnthropic

# Initialize Claude for ShopAgent
llm = ChatAnthropic(
    model="claude-sonnet-4-20250514",
    temperature=0,        # Deterministic routing
    max_tokens=1024,
    streaming=True,       # Required for Chainlit token streaming
)

# Bind tools — LLM can now invoke these
llm_with_tools = llm.bind_tools([supabase_execute_sql, qdrant_semantic_search])

# Direct call (no agent loop)
response = llm_with_tools.invoke("Qual o faturamento de SP?")
# response.tool_calls → [{"name": "supabase_execute_sql", "args": {"query": "..."}}]
```

## Quick Reference

| Method | Input | Output | Use Case |
|--------|-------|--------|----------|
| `ChatAnthropic(model=...)` | Config params | LLM instance | Initialize Claude |
| `llm.bind_tools(tools)` | List of tools | New LLM with tools | Attach tools for routing |
| `llm.invoke(prompt)` | String or messages | AIMessage | Single LLM call |
| `llm.stream(prompt)` | String or messages | Iterator[chunk] | Streaming output |

## Common Mistakes

### Wrong

```python
from langchain_anthropic import ChatAnthropic

llm = ChatAnthropic(model="claude-sonnet-4-20250514")

# Passing LLM to agent WITHOUT binding tools
agent = create_react_agent(model=llm, tools=[])  # No tools available!
```

### Correct

```python
from langchain_anthropic import ChatAnthropic

llm = ChatAnthropic(model="claude-sonnet-4-20250514", temperature=0)

# Option 1: Pass tools directly to create_react_agent (it binds internally)
agent = create_react_agent(model=llm, tools=[supabase_tool, qdrant_tool])

# Option 2: Bind explicitly for custom StateGraph usage
llm_with_tools = llm.bind_tools([supabase_tool, qdrant_tool])
```

## Related

- [Tools](../concepts/tools.md)
- [ReAct Agent](../concepts/react-agent.md)
- [Chainlit Integration](../../chainlit/patterns/langchain-integration.md)
