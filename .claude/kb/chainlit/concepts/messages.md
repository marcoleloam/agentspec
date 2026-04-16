# Messages

> **Purpose**: Send and stream responses in Chainlit for ShopAgent chat interactions
> **Confidence**: 0.95
> **MCP Validated**: 2026-04-12

## Overview

`cl.Message` is the primary way to send content to the user. For one-shot responses, create a message with content and call `send()`. For streaming (token-by-token), create an empty message, call `stream_token()` in a loop, then `send()` to finalize. Streaming provides a much better UX — the user sees the response being generated in real-time.

## The Pattern

```python
import chainlit as cl


# Non-streaming — complete response at once
@cl.on_message
async def simple(message: cl.Message):
    result = process(message.content)
    await cl.Message(content=result).send()


# Streaming — token by token
@cl.on_message
async def streaming(message: cl.Message):
    msg = cl.Message(content="")  # Start empty

    async for chunk in agent_stream(message.content):
        await msg.stream_token(chunk)  # Append each token

    await msg.send()  # Finalize AFTER all tokens streamed


# Streaming with LangChain agent
@cl.on_message
async def langchain_stream(message: cl.Message):
    agent = cl.user_session.get("agent")
    msg = cl.Message(content="")

    async for event in agent.astream_events(
        {"messages": [{"role": "user", "content": message.content}]},
        version="v2",
    ):
        if event["event"] == "on_chat_model_stream":
            token = event["data"]["chunk"].content
            if token:
                await msg.stream_token(token)

    await msg.send()
```

## Quick Reference

| Operation | Code | Notes |
|-----------|------|-------|
| Send complete | `await cl.Message(content="text").send()` | One-shot |
| Start streaming | `msg = cl.Message(content="")` | Empty message |
| Append token | `await msg.stream_token("token")` | In loop |
| Finalize | `await msg.send()` | After ALL tokens |
| Update sent msg | `await msg.update()` | Edit existing |

## Common Mistakes

### Wrong

```python
# Calling send() BEFORE streaming finishes — truncates output
msg = cl.Message(content="")
await msg.send()  # Sent empty!
async for chunk in stream:
    await msg.stream_token(chunk)  # Too late — message already finalized
```

### Correct

```python
# Stream ALL tokens first, THEN send
msg = cl.Message(content="")
async for chunk in stream:
    await msg.stream_token(chunk)  # Accumulates tokens
await msg.send()  # Finalize with complete content
```

## Related

- [Lifecycle](../concepts/lifecycle.md)
- [Steps](../concepts/steps.md)
- [LangChain Integration](../patterns/langchain-integration.md)
