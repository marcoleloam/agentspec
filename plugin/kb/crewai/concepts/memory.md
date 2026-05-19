# Memory

> **Purpose**: Enable agents to retain context across tasks and sessions for continuous DataOps learning
> **Confidence**: 0.95
> **MCP Validated**: 2026-02-17

## Overview

CrewAI Memory allows agents to retain historical context during and across task executions. There are three built-in memory types: Short-Term Memory (session context via ChromaDB), Long-Term Memory (cross-session persistence via SQLite3), and Entity Memory (structured knowledge about entities via ChromaDB). Memory is enabled at the crew level and shared across all agents in that crew.

## The Pattern

```python
from crewai import Crew, Agent, Task, Process

monitor = Agent(
    role="Pipeline Monitor",
    goal="Detect recurring pipeline failures and learn from past incidents",
    backstory="You track data pipeline health and remember past failure patterns.",
)

investigate = Agent(
    role="Incident Analyst",
    goal="Correlate current failures with historical incidents",
    backstory="You analyze incidents and recall similar past events.",
)

crew = Crew(
    agents=[monitor, investigate],
    tasks=[...],
    process=Process.sequential,
    memory=True,  # Enables STM, LTM, and Entity memory
    verbose=True,
)

result = crew.kickoff(inputs={"pipeline": "daily_sales_etl"})
```

## Quick Reference

| Memory Type | Storage | Embeddings | Scope |
|-------------|---------|------------|-------|
| Short-Term (STM) | ChromaDB | Yes (RAG) | Current session |
| Long-Term (LTM) | SQLite3 | No | Cross-session |
| Entity | ChromaDB | Yes (RAG) | People, systems, concepts |

## Custom Embedder Configuration

```python
crew = Crew(
    agents=[monitor, investigate],
    tasks=[...],
    process=Process.sequential,
    memory=True,
    embedder={
        "provider": "openai",
        "config": {
            "model": "text-embedding-3-small",
        },
    },
    verbose=True,
)
```

## Memory Reset Operations

```python
# Reset specific memory types
crew.reset_memories(command_type="short")     # Short-term
crew.reset_memories(command_type="long")      # Long-term
crew.reset_memories(command_type="entity")    # Entity
crew.reset_memories(command_type="knowledge") # Knowledge store
```

## Storage Configuration

```bash
# Default: platform-specific via appdirs package
# Custom: set environment variable
export CREWAI_STORAGE_DIR="/data/crewai/memory"
```

## DataOps Memory Use Case

```python
# Agents learn from past pipeline failures
# STM: Current investigation context
# LTM: Historical failure patterns persisted across runs
# Entity: Knowledge about specific pipelines, tables, owners

crew = Crew(
    agents=[monitor, investigate],
    tasks=[detect_task, correlate_task, report_task],
    process=Process.sequential,
    memory=True,
    embedder={
        "provider": "openai",
        "config": {"model": "text-embedding-3-small"},
    },
)

# First run: learns about daily_sales_etl failures
crew.kickoff(inputs={"pipeline": "daily_sales_etl"})

# Second run: recalls past daily_sales_etl incidents
crew.kickoff(inputs={"pipeline": "daily_sales_etl"})
```

## Common Mistakes

### Wrong

```python
# Enabling memory without an embedder when using non-OpenAI models
crew = Crew(agents=[a], tasks=[t], memory=True, llm="anthropic/claude-3")
```

### Correct

```python
# Explicitly set embedder when not using OpenAI as primary LLM
crew = Crew(
    agents=[a], tasks=[t], memory=True,
    embedder={"provider": "openai", "config": {"model": "text-embedding-3-small"}},
)
```

## Related

- [Crews](../concepts/crews.md)
- [Agents](../concepts/agents.md)
- [Triage Pattern](../patterns/triage-investigation-report.md)
