# Steps

> **Purpose**: Display tool calls and agent reasoning as expandable UI elements in Chainlit
> **Confidence**: 0.95
> **MCP Validated**: 2026-04-12

## Overview

Steps are expandable UI elements that show what the agent is doing behind the scenes — tool calls, LLM reasoning, RAG retrieval. Without steps, the user sees a black box. With steps, they see the agent thinking: "Searching Qdrant for delivery complaints..." → "Found 23 reviews" → "Calculating average ticket...". Two ways to create: `@cl.step` decorator or `cl.Step` context manager.

## The Pattern

```python
import chainlit as cl


# Option 1: Decorator
@cl.step(type="tool", name="SQL Query")
async def execute_sql(query: str) -> str:
    """Executes SQL and shows as a step in the UI."""
    result = await run_sql(query)
    return result  # Return value shown as step output


# Option 2: Context manager (more control)
async def search_reviews(question: str) -> str:
    async with cl.Step(name="Qdrant Search", type="tool") as step:
        step.input = question
        result = await qdrant_search(question)
        step.output = f"Found {len(result)} reviews"
    return result


# In on_message — steps appear nested under the response
@cl.on_message
async def main(message: cl.Message):
    # These steps appear as expandable elements in the UI
    sql_result = await execute_sql("SELECT COUNT(*) FROM orders")
    reviews = await search_reviews("delivery complaints")
    await cl.Message(content=f"Results: {sql_result}, {reviews}").send()
```

## Quick Reference

| Step Type | Use For | Icon |
|-----------|---------|------|
| `"tool"` | Tool execution (SQL, search) | Wrench |
| `"llm"` | LLM thinking/generation | Brain |
| `"run"` | Agent or crew action | Play |
| `"retrieval"` | RAG chunk retrieval | Magnifying glass |
| `"embedding"` | Embedding generation | Layers |

## Step Parameters

| Param | Type | Description |
|-------|------|-------------|
| `name` | str | Display name in UI (e.g., "SQL Query") |
| `type` | str | One of: llm, tool, run, embedding, retrieval |
| `input` | str | Input shown when step is expanded |
| `output` | str | Output shown when step is expanded |
| `parent_id` | str | Nest under another step |

## Common Mistakes

### Wrong

```python
# No steps — user sees nothing while agent thinks for 5+ seconds
@cl.on_message
async def main(message: cl.Message):
    result = agent.invoke({"messages": [...]})  # Black box
    await cl.Message(content=result).send()
```

### Correct

```python
# Steps show reasoning — user sees progress
@cl.on_message
async def main(message: cl.Message):
    async with cl.Step(name="Thinking", type="llm") as step:
        step.input = message.content
        result = agent.invoke({"messages": [...]})
        step.output = "Decided to use SQL query"
    await cl.Message(content=result["messages"][-1].content).send()
```

## Related

- [Messages](../concepts/messages.md)
- [LangChain Integration](../patterns/langchain-integration.md)
