# Tools

> **Purpose**: Integrate external capabilities into agents via BaseTool and @tool decorator
> **Confidence**: 0.95
> **MCP Validated**: 2026-02-17

## Overview

CrewAI Tools are external capabilities registered to agents at runtime. Tools give agents deterministic access to APIs, databases, file systems, and services. There are two ways to create tools: the `@tool` decorator for simple functions and subclassing `BaseTool` for complex integrations. The `crewai-tools` package provides built-in tools.

## The Pattern

```python
from crewai.tools import tool

@tool("BigQuery Row Counter")
def bigquery_row_count(dataset: str, table: str, date: str) -> str:
    """Count rows loaded into a BigQuery table for a given date.
    Use this when you need to verify data completeness after ETL runs."""
    from google.cloud import bigquery
    client = bigquery.Client()
    query = f"""
        SELECT COUNT(*) as row_count
        FROM `{dataset}.{table}`
        WHERE DATE(load_timestamp) = '{date}'
    """
    result = client.query(query).result()
    row = list(result)[0]
    return f"Table {dataset}.{table} has {row.row_count} rows for {date}"
```

## Quick Reference

| Approach | Best For | Complexity |
|----------|----------|------------|
| `@tool` decorator | Simple stateless functions | Low |
| `BaseTool` subclass | Stateful, validated inputs | Medium |
| Built-in tools | Common operations | None |

## BaseTool Pattern

```python
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

class PipelineStatusInput(BaseModel):
    pipeline_id: str = Field(description="Unique pipeline identifier")
    environment: str = Field(default="production", description="Target environment")

class PipelineStatusTool(BaseTool):
    name: str = "Pipeline Status Checker"
    description: str = (
        "Check the current execution status of a data pipeline. "
        "Returns status, last run time, and error details if failed."
    )
    args_schema: type[BaseModel] = PipelineStatusInput

    def _run(self, pipeline_id: str, environment: str = "production") -> str:
        # Query pipeline orchestrator API
        import requests
        resp = requests.get(
            f"https://orchestrator.internal/api/pipelines/{pipeline_id}",
            params={"env": environment},
        )
        data = resp.json()
        return f"Pipeline {pipeline_id}: {data['status']} (last run: {data['last_run']})"
```

## Built-in Tools

| Tool | Package | Purpose |
|------|---------|---------|
| `SerperDevTool` | crewai-tools | Web search |
| `ScrapeWebsiteTool` | crewai-tools | Web scraping |
| `FileReadTool` | crewai-tools | Read files |
| `DirectoryReadTool` | crewai-tools | List directory |
| `CodeInterpreterTool` | crewai-tools | Execute code |
| `JSONSearchTool` | crewai-tools | Search JSON/RAG |

## Registering Tools to Agents

```python
from crewai import Agent

# Tools registered at agent level
monitor = Agent(
    role="Pipeline Monitor",
    goal="Check pipeline health",
    backstory="...",
    tools=[bigquery_row_count, PipelineStatusTool()],
)

# Tools can also be set at task level (overrides agent tools)
task = Task(
    description="Check row counts",
    expected_output="Row count report",
    agent=monitor,
    tools=[bigquery_row_count],  # Only this tool available
)
```

## Common Mistakes

### Wrong

```python
# Missing docstring means agents cannot decide when to use the tool
@tool("My Tool")
def my_tool(x: str) -> str:
    return x.upper()
```

### Correct

```python
@tool("Text Normalizer")
def normalize_text(text: str) -> str:
    """Normalize text by converting to uppercase and stripping whitespace.
    Use this when pipeline field values need standardization before loading."""
    return text.upper().strip()
```

## Related

- [Agents](../concepts/agents.md)
- [Tasks](../concepts/tasks.md)
- [Log Analysis Agent](../patterns/log-analysis-agent.md)
