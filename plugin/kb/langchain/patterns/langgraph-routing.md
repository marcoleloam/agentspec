# LangGraph Routing

> **Purpose**: Custom LangGraph StateGraph for ShopAgent with explicit conditional routing between Supabase and Qdrant nodes
> **MCP Validated**: 2026-04-12

## When to Use

- Need more control than `create_react_agent` provides
- Want explicit routing logic (not implicit via tool docstrings)
- Debugging tool selection by inspecting graph state at each step
- Adding custom pre/post-processing per tool (e.g., SQL validation, result formatting)

## Implementation

```python
"""ShopAgent with explicit LangGraph routing."""
from typing import Literal

from langchain_anthropic import ChatAnthropic
from langchain.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import MessagesState
from langgraph.prebuilt import ToolNode


@tool
def supabase_execute_sql(query: str) -> str:
    """Execute SQL for exact data: revenue, counts, averages."""
    return f"[SQL] {query}"


@tool
def qdrant_semantic_search(question: str) -> str:
    """Search reviews by meaning: complaints, sentiment, opinions."""
    return f"[Semantic] {question}"


# LLM with tools bound
llm = ChatAnthropic(model="claude-sonnet-4-20250514", temperature=0)
tools = [supabase_execute_sql, qdrant_semantic_search]
llm_with_tools = llm.bind_tools(tools)
tool_node = ToolNode(tools)


def agent(state: MessagesState):
    """Agent node — LLM reasons and decides which tool to call."""
    return {"messages": [llm_with_tools.invoke(state["messages"])]}


def route_after_agent(state: MessagesState) -> Literal["tools", "__end__"]:
    """Route based on whether the LLM wants to call a tool."""
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return END


# Build the graph
workflow = StateGraph(MessagesState)
workflow.add_node("agent", agent)
workflow.add_node("tools", tool_node)

workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", route_after_agent)
workflow.add_edge("tools", "agent")  # Loop back for multi-step reasoning

app = workflow.compile()

# Execute
result = app.invoke({
    "messages": [{"role": "user", "content": "Faturamento por estado?"}]
})
print(result["messages"][-1].content)
```

## Graph Visualization

```
START ──> [agent] ──> route_after_agent()
              ^              │
              │         ┌────┴────┐
              │    tool_calls?    no tool_calls?
              │         │              │
              │         v              v
              └── [tools] ──┘       [END]
```

## Configuration

| Setting | Value | Description |
|---------|-------|-------------|
| State schema | `MessagesState` | Built-in TypedDict with messages list |
| Agent node | LLM with bound tools | Decides which tool to call |
| Tool node | `ToolNode(tools)` | Executes all pending tool calls |
| Conditional edge | `route_after_agent` | Checks `tool_calls` on last message |

## Example Usage

```python
# Stream intermediate steps for debugging
for event in app.stream(
    {"messages": [{"role": "user", "content": "Ticket medio por segmento?"}]}
):
    for node_name, state_update in event.items():
        print(f"[{node_name}] {state_update}")
```

## See Also

- [ReAct Agent Dual Tools](../patterns/react-agent-dual-tools.md)
- [Routing Concept](../concepts/routing.md)
