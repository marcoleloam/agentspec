# Chainlit Knowledge Base

> **Purpose**: Chainlit conversational interface for ShopAgent — streaming chat with agent step visibility
> **MCP Validated**: 2026-04-12

## Quick Navigation

### Concepts (< 150 lines each)

| File | Purpose |
|------|---------|
| [concepts/lifecycle.md](concepts/lifecycle.md) | @cl.on_chat_start, @cl.on_message, cl.user_session |
| [concepts/messages.md](concepts/messages.md) | cl.Message, send(), stream_token(), streaming patterns |
| [concepts/steps.md](concepts/steps.md) | @cl.step decorator, Step context manager, nested UI elements |

### Patterns (< 200 lines each)

| File | Purpose |
|------|---------|
| [patterns/langchain-integration.md](patterns/langchain-integration.md) | **KEY**: Chainlit wrapping LangChain agent with streaming + step visibility |
| [patterns/crewai-integration.md](patterns/crewai-integration.md) | Chainlit wrapping CrewAI crew with per-agent step callbacks |

### Specs (Machine-Readable)

| File | Purpose |
|------|---------|
| [specs/chainlit-config.yaml](specs/chainlit-config.yaml) | Message, Step, user_session, lifecycle hooks, config.toml reference |

---

## Quick Reference

- [quick-reference.md](quick-reference.md) - Fast lookup tables

---

## Key Concepts

| Concept | Description |
|---------|-------------|
| **Lifecycle** | Async hooks: `on_chat_start` (init), `on_message` (every message), `on_stop` (cleanup) |
| **Message** | `cl.Message` with `send()` for one-shot and `stream_token()` for streaming |
| **Step** | Expandable UI element showing tool calls, LLM reasoning, or agent actions |
| **user_session** | Per-session key-value store for agent state (not global) |

---

## Learning Path

| Level | Files |
|-------|-------|
| **Beginner** | concepts/lifecycle.md, concepts/messages.md |
| **Intermediate** | concepts/steps.md |
| **Advanced** | patterns/langchain-integration.md, patterns/crewai-integration.md |

---

## Agent Usage

| Agent | Primary Files | Use Case |
|-------|---------------|----------|
| shopagent-builder | patterns/langchain-integration.md | Day 3-4 Chainlit interface for ShopAgent |
| genai-architect | patterns/crewai-integration.md | Multi-agent chat interfaces |
