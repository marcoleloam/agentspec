# Chainlit Quick Reference

> Fast lookup tables. For code examples, see linked files.

## Installation

```bash
pip install chainlit
chainlit run app.py -w   # -w enables hot reload
```

## Lifecycle Decorators

| Decorator | Fires When | Async | Notes |
|-----------|-----------|-------|-------|
| `@cl.on_chat_start` | New session begins | Yes | Initialize agent, store in user_session |
| `@cl.on_message` | User sends message | Yes | Receives `cl.Message` object |
| `@cl.on_stop` | User clicks stop | Yes | Cleanup resources |
| `@cl.on_audio_chunk` | Audio input received | Yes | Voice interface |

## Message API

| Method | Description | Example |
|--------|-------------|---------|
| `cl.Message(content="text").send()` | Send complete message | One-shot response |
| `msg = cl.Message(content="")` | Create empty message | Prepare for streaming |
| `await msg.stream_token(token)` | Append token to message | Token-by-token streaming |
| `await msg.send()` | Finalize and send | **Call AFTER streaming completes** |
| `await msg.update()` | Update existing message | Edit already-sent message |

## Message Parameters

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `content` | str | `""` | Message text (markdown supported) |
| `author` | str | `"Assistant"` | Display name |
| `elements` | list | `[]` | Attachments (images, files) |
| `actions` | list | `[]` | Interactive buttons |
| `parent_id` | str | `None` | Nest under another message |

## user_session

| Method | Description |
|--------|-------------|
| `cl.user_session.set("key", value)` | Store value for this session |
| `cl.user_session.get("key")` | Retrieve value |

## Step Types

| Type | Use For | Example |
|------|---------|---------|
| `"llm"` | Model thinking/reasoning | Claude generating response |
| `"tool"` | Tool execution | SQL query, Qdrant search |
| `"run"` | Agent/crew action | CrewAI agent executing |
| `"embedding"` | Embedding generation | LlamaIndex indexing |
| `"retrieval"` | RAG retrieval | Qdrant similarity search |

## Decision Matrix

| Use Case | Choose |
|----------|--------|
| Simple one-shot response | `cl.Message(content=result).send()` |
| Streaming LLM output | `stream_token()` loop → `send()` |
| Show tool execution | `@cl.step(type="tool")` or `cl.Step` context manager |
| Show agent reasoning | `@cl.step(type="llm")` |
| LangChain agent streaming | `agent.astream_events(input, version="v2")` |

## Common Pitfalls

| Don't | Do |
|-------|-----|
| Create agent in `on_message` (new every message) | Create in `on_chat_start`, store in `user_session` |
| Call `send()` before streaming finishes | Stream all tokens first, then `send()` |
| Use module-level globals for agent state | Use `cl.user_session` (per-session isolation) |
| Forget `async` on handler functions | All Chainlit handlers must be `async def` |
| Use `agent.invoke()` for streaming UI | Use `agent.astream_events(version="v2")` |

## Related Documentation

| Topic | Path |
|-------|------|
| Lifecycle | `concepts/lifecycle.md` |
| Messages | `concepts/messages.md` |
| Steps | `concepts/steps.md` |
| LangChain Integration | `patterns/langchain-integration.md` |
| Full Index | `index.md` |
