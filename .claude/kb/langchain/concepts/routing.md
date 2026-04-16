# Routing

> **Purpose**: Conditional routing in LangGraph StateGraph for explicit control over tool dispatch
> **Confidence**: 0.95
> **MCP Validated**: 2026-04-12

## Overview

When `create_react_agent` isn't flexible enough, `StateGraph` provides explicit control over routing. The key pattern is `add_conditional_edges` with a routing function that inspects the last message's `tool_calls` to decide which node to execute next. This is useful for adding custom pre/post-processing per tool, or debugging which path the agent takes.

## The Pattern

```python
from typing import Annotated, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import MessagesState
from langgraph.prebuilt import ToolNode


tools = [supabase_execute_sql, qdrant_semantic_search]
tool_node = ToolNode(tools)
llm_with_tools = llm.bind_tools(tools)


def call_model(state: MessagesState):
    """Agent node — LLM decides which tool to call."""
    return {"messages": [llm_with_tools.invoke(state["messages"])]}


def should_continue(state: MessagesState) -> Literal["tools", "__end__"]:
    """Route based on whether the LLM wants to call a tool."""
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return END


# Build graph
workflow = StateGraph(MessagesState)
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)
workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", should_continue)
workflow.add_edge("tools", "agent")  # After tool execution, return to agent

app = workflow.compile()
result = app.invoke({"messages": [{"role": "user", "content": "..."}]})
```

## Quick Reference

| Component | Purpose |
|-----------|---------|
| `StateGraph(MessagesState)` | Create graph with messages state |
| `add_node(name, fn)` | Register a processing node |
| `add_edge(from, to)` | Always-taken edge between nodes |
| `add_conditional_edges(from, fn)` | Route based on function return value |
| `ToolNode(tools)` | Pre-built node that executes tool calls |

## Common Mistakes

### Wrong

```python
# Route to END before tools execute — tool results never processed
def should_continue(state):
    return END  # Always ends, even when tool_calls exist
```

### Correct

```python
# Check for tool_calls — route to tools node, then back to agent
def should_continue(state):
    if state["messages"][-1].tool_calls:
        return "tools"  # Execute tools
    return END           # No more tools needed — respond
```

## Related

- [ReAct Agent](../concepts/react-agent.md)
- [LangGraph Routing Pattern](../patterns/langgraph-routing.md)
