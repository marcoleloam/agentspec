# LangChain Integration

> **Purpose**: Wrap ShopAgent LangChain/LangGraph agent in Chainlit with streaming and step visibility
> **MCP Validated**: 2026-04-12

## When to Use

- Day 3-4 Chainlit interface for ShopAgent
- Connecting LangChain `create_react_agent` to a chat UI
- Showing tool calls (Supabase SQL, Qdrant search) as expandable steps
- Token-by-token streaming for responsive UX

## Implementation

```python
"""ShopAgent Chainlit app with LangChain agent streaming."""
import chainlit as cl
from langchain_anthropic import ChatAnthropic
from langchain.tools import tool
from langgraph.prebuilt import create_react_agent


@tool
def supabase_execute_sql(query: str) -> str:
    """Execute SQL for exact data: revenue, counts, averages."""
    return f"[SQL] {query}"


@tool
def qdrant_semantic_search(question: str) -> str:
    """Search reviews by meaning: complaints, sentiment, opinions."""
    return f"[Semantic] {question}"


@cl.on_chat_start
async def start():
    """Initialize ShopAgent and store in session."""
    llm = ChatAnthropic(
        model="claude-sonnet-4-20250514",
        temperature=0,
        streaming=True,
    )
    agent = create_react_agent(
        model=llm,
        tools=[supabase_execute_sql, qdrant_semantic_search],
    )
    cl.user_session.set("agent", agent)
    await cl.Message(
        content="ShopAgent conectado! Pergunte sobre vendas, clientes ou reviews."
    ).send()


@cl.on_message
async def main(message: cl.Message):
    """Stream agent response with tool step visibility."""
    agent = cl.user_session.get("agent")
    msg = cl.Message(content="")
    current_step = None

    async for event in agent.astream_events(
        {"messages": [{"role": "user", "content": message.content}]},
        version="v2",
    ):
        kind = event["event"]

        # Stream LLM tokens
        if kind == "on_chat_model_stream":
            token = event["data"]["chunk"].content
            if token:
                await msg.stream_token(token)

        # Show tool call as expandable step
        elif kind == "on_tool_start":
            current_step = cl.Step(
                name=event["name"],
                type="tool",
            )
            await current_step.__aenter__()
            current_step.input = str(event["data"].get("input", ""))

        # Close tool step with result
        elif kind == "on_tool_end":
            if current_step:
                current_step.output = str(event["data"].get("output", ""))
                await current_step.__aexit__(None, None, None)
                current_step = None

    await msg.send()
```

## Configuration

| Setting | Value | Description |
|---------|-------|-------------|
| `streaming` | `True` | Required on ChatAnthropic for token streaming |
| `astream_events version` | `"v2"` | LangGraph event streaming API version |
| `Step type` | `"tool"` | Shows wrench icon for tool calls |

## Example Usage

```bash
# Run the Chainlit app
chainlit run app.py -w

# The UI shows:
# 1. User types: "Qual o faturamento por estado?"
# 2. Step appears: [SQL Query] supabase_execute_sql
#    Input: "SELECT c.state, SUM(o.total)..."
#    Output: "SP: 127430, RJ: 89210..."
# 3. Streaming response: "O faturamento por estado é..."
```

## See Also

- [CrewAI Integration](../patterns/crewai-integration.md)
- [Lifecycle](../concepts/lifecycle.md)
- [LangChain ReAct Agent](../../langchain/patterns/react-agent-dual-tools.md)
