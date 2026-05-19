# Lifecycle

> **Purpose**: Chainlit async lifecycle hooks for initializing ShopAgent and handling user messages
> **Confidence**: 0.95
> **MCP Validated**: 2026-04-12

## Overview

Chainlit uses decorator-based hooks to manage the chat lifecycle. `@cl.on_chat_start` fires once when a new browser session opens — use it to initialize the agent and store it in `cl.user_session`. `@cl.on_message` fires on every user message — retrieve the agent from session, invoke it, and send the response. All handlers must be `async`.

## The Pattern

```python
import chainlit as cl
from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent


@cl.on_chat_start
async def start():
    """Initialize agent ONCE per session."""
    llm = ChatAnthropic(model="claude-sonnet-4-20250514", streaming=True)
    agent = create_react_agent(model=llm, tools=[supabase_tool, qdrant_tool])

    # Store in session — NOT a global variable
    cl.user_session.set("agent", agent)

    await cl.Message(
        content="ShopAgent pronto! Pergunte sobre vendas, clientes ou reviews."
    ).send()


@cl.on_message
async def main(message: cl.Message):
    """Handle every user message."""
    agent = cl.user_session.get("agent")

    result = agent.invoke({
        "messages": [{"role": "user", "content": message.content}]
    })

    await cl.Message(content=result["messages"][-1].content).send()
```

## Quick Reference

| Hook | Fires | Input | Use For |
|------|-------|-------|---------|
| `@cl.on_chat_start` | New session | None | Init agent, send welcome |
| `@cl.on_message` | Every message | `cl.Message` | Invoke agent, respond |
| `@cl.on_stop` | User clicks stop | None | Cancel running tasks |

## Common Mistakes

### Wrong

```python
# Creating agent in on_message — new agent every message, no conversation state
@cl.on_message
async def main(message: cl.Message):
    agent = create_react_agent(model=llm, tools=[...])  # Created every time!
    result = agent.invoke(...)
```

### Correct

```python
# Create ONCE in on_chat_start, retrieve in on_message
@cl.on_chat_start
async def start():
    agent = create_react_agent(model=llm, tools=[...])
    cl.user_session.set("agent", agent)

@cl.on_message
async def main(message: cl.Message):
    agent = cl.user_session.get("agent")  # Retrieved from session
    result = agent.invoke(...)
```

## Related

- [Messages](../concepts/messages.md)
- [Steps](../concepts/steps.md)
- [LangChain Integration](../patterns/langchain-integration.md)
