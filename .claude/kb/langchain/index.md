# LangChain Knowledge Base

> **Purpose**: LangChain + LangGraph agent framework for ShopAgent — autonomous routing between Supabase SQL and Qdrant semantic search
> **MCP Validated**: 2026-04-12

## Quick Navigation

### Concepts (< 150 lines each)

| File | Purpose |
|------|---------|
| [concepts/tools.md](concepts/tools.md) | @tool decorator for supabase_execute_sql + qdrant_semantic_search |
| [concepts/chat-models.md](concepts/chat-models.md) | ChatAnthropic init, bind_tools, streaming config |
| [concepts/react-agent.md](concepts/react-agent.md) | create_react_agent (langgraph.prebuilt), ReAct loop |
| [concepts/routing.md](concepts/routing.md) | Conditional edges, should_continue, tool-based routing |

### Patterns (< 200 lines each)

| File | Purpose |
|------|---------|
| [patterns/react-agent-dual-tools.md](patterns/react-agent-dual-tools.md) | **KEY**: Agent with supabase+qdrant tools deciding SQL vs semantic |
| [patterns/langgraph-routing.md](patterns/langgraph-routing.md) | Custom StateGraph with explicit conditional routing |

### Specs (Machine-Readable)

| File | Purpose |
|------|---------|
| [specs/langchain-config.yaml](specs/langchain-config.yaml) | ChatAnthropic, create_react_agent, StateGraph, @tool reference |

---

## Quick Reference

- [quick-reference.md](quick-reference.md) - Fast lookup tables

---

## Key Concepts

| Concept | Description |
|---------|-------------|
| **Tool** | Callable function with typed schema — LLM reads docstring to decide when to use it |
| **ChatAnthropic** | Claude LLM wrapper with `bind_tools` for tool-augmented conversations |
| **ReAct Agent** | Reason+Act loop: thinks, picks a tool, observes result, answers |
| **Routing** | Conditional graph edges that dispatch to different tool nodes based on LLM decisions |

---

## Learning Path

| Level | Files |
|-------|-------|
| **Beginner** | concepts/tools.md, concepts/chat-models.md |
| **Intermediate** | concepts/react-agent.md, concepts/routing.md |
| **Advanced** | patterns/react-agent-dual-tools.md, patterns/langgraph-routing.md |

---

## Agent Usage

| Agent | Primary Files | Use Case |
|-------|---------------|----------|
| shopagent-builder | patterns/react-agent-dual-tools.md | Day 3 autonomous agent with dual-store routing |
| genai-architect | concepts/routing.md, patterns/langgraph-routing.md | Custom agent architectures |
