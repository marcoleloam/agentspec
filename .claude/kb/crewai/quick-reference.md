# CrewAI Quick Reference

> Fast lookup tables. For code examples, see linked files.
> **MCP Validated:** 2026-02-17

## Installation

| Command | Purpose |
|---------|---------|
| `pip install crewai` | Core framework |
| `pip install 'crewai[tools]'` | Framework + built-in tools |
| `crewai create crew my_project` | Scaffold new project |

## Core Components

| Component | Class | Key Parameters |
|-----------|-------|----------------|
| Agent | `Agent` | `role`, `goal`, `backstory`, `tools`, `llm`, `memory` |
| Task | `Task` | `description`, `expected_output`, `agent`, `tools`, `context` |
| Crew | `Crew` | `agents`, `tasks`, `process`, `memory`, `verbose` |
| Flow | `Flow` | `@start`, `@listen`, `@router`, state management |

## Process Types

| Process | Use Case | Manager Required |
|---------|----------|------------------|
| `Process.sequential` | Linear pipeline steps | No |
| `Process.hierarchical` | Manager delegates to agents | Yes (`manager_llm`) |

## Memory Types

| Type | Storage | Scope |
|------|---------|-------|
| Short-Term | ChromaDB + RAG | Current session |
| Long-Term | SQLite3 | Cross-session persistence |
| Entity | ChromaDB + RAG | People, places, concepts |

## Key Decorators

| Decorator | Target | Purpose |
|-----------|--------|---------|
| `@CrewBase` | Class | Auto-load YAML config |
| `@agent` | Method | Define agent from config |
| `@task` | Method | Define task from config |
| `@crew` | Method | Define crew assembly |
| `@tool` | Function | Create custom tool |
| `@start()` | Method | Flow entry point |
| `@listen()` | Method | Flow event listener |
| `@router()` | Method | Flow conditional branching |

## Decision Matrix

| Use Case | Choose |
|----------|--------|
| Simple linear pipeline | Sequential process, single crew |
| Requires delegation/oversight | Hierarchical process with manager |
| Multi-phase workflow | Flows orchestrating multiple crews |
| Need session memory | `memory=True` on Crew |
| Custom external integration | BaseTool or @tool decorator |

## Common Pitfalls

| Don't | Do |
|-------|-----|
| Skip `expected_output` on tasks | Always define structured output |
| Use hierarchical without `manager_llm` | Set `manager_llm` or `manager_agent` |
| Ignore token costs in loops | Implement circuit breaker pattern |
| Hardcode LLM in agents | Use env vars or config for LLM selection |

## Related Documentation

| Topic | Path |
|-------|------|
| Agent Definition | `concepts/agents.md` |
| Crew Composition | `concepts/crews.md` |
| Full Index | `index.md` |
