# LangChain Quick Reference

> Fast lookup tables. For code examples, see linked files.

## Installation

```bash
pip install langchain langchain-anthropic langgraph
```

## Core Classes

| Class | Import | Purpose |
|-------|--------|---------|
| `ChatAnthropic` | `langchain_anthropic` | Claude LLM wrapper |
| `create_react_agent` | `langgraph.prebuilt` | Build ReAct agent (modern API) |
| `StateGraph` | `langgraph.graph` | Custom graph-based agent |
| `ToolNode` | `langgraph.prebuilt` | Graph node that executes tools |
| `MessagesState` | `langgraph.graph.message` | TypedDict state with messages list |
| `@tool` | `langchain.tools` | Decorator to create LLM-callable tools |

## @tool Decorator

| Param | Default | Description |
|-------|---------|-------------|
| `name` | function name | Tool identifier the LLM sees |
| `description` | docstring | **LLM reads this to decide when to use the tool** |
| `args_schema` | inferred | Optional Pydantic model for input validation |
| `return_direct` | `False` | If True, tool output is the final answer (skip synthesis) |

## ChatAnthropic Parameters

| Param | Default | Description |
|-------|---------|-------------|
| `model` | — | `"claude-sonnet-4-20250514"` for ShopAgent |
| `temperature` | `1.0` | Use `0` for deterministic routing |
| `max_tokens` | `1024` | Max output tokens |
| `streaming` | `False` | Set `True` for Chainlit integration |
| `api_key` | env `ANTHROPIC_API_KEY` | Override API key |

## Decision Matrix

| Use Case | Choose |
|----------|--------|
| Simple agent with tools | `create_react_agent(model, tools)` from `langgraph.prebuilt` |
| Custom routing logic | `StateGraph(MessagesState)` with conditional edges |
| Single LLM call with tools | `llm.bind_tools([tools])` (no agent loop) |
| Legacy agents (avoid) | ~~`langchain.agents.create_react_agent`~~ — use `langgraph.prebuilt` |

## Common Pitfalls

| Don't | Do |
|-------|-----|
| `from langchain.agents import create_react_agent` | `from langgraph.prebuilt import create_react_agent` (modern API) |
| Vague docstring: "Search the database" | Precise: "Execute SQL for exact numbers: revenue, counts, averages" |
| Pass raw string to `agent.invoke()` | Pass `{"messages": [{"role": "user", "content": "..."}]}` |
| Forget to `bind_tools` before agent creation | Either bind or pass tools directly to `create_react_agent` |
| Use `agent.invoke` with Chainlit streaming | Use `agent.astream_events(input, version="v2")` |

## Related Documentation

| Topic | Path |
|-------|------|
| Tools | `concepts/tools.md` |
| Chat Models | `concepts/chat-models.md` |
| ReAct Agent | `concepts/react-agent.md` |
| Routing | `concepts/routing.md` |
| Dual-Tool Pattern | `patterns/react-agent-dual-tools.md` |
| Full Index | `index.md` |
