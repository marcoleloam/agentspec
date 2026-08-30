# Agents

> **Purpose**: Define autonomous AI agents with roles, goals, and tools for DataOps workflows
> **Confidence**: 0.95
> **MCP Validated**: 2026-02-17

## Overview

A CrewAI Agent is an LLM-powered autonomous unit defined by a role, goal, and backstory. Each agent can execute tasks, call external tools, query memory, make decisions, and delegate work to other agents. Agents are the building blocks of every crew.

## The Pattern

```python
from crewai import Agent

# DataOps monitoring agent
pipeline_monitor = Agent(
    role="Pipeline Monitor",
    goal="Detect anomalies in data pipeline execution and report failures",
    backstory=(
        "You are a senior DataOps engineer with 10 years of experience "
        "monitoring ETL pipelines. You excel at identifying root causes "
        "of pipeline failures from logs and metrics."
    ),
    tools=[log_reader_tool, metrics_tool],
    llm="openai/gpt-4o",
    memory=True,
    verbose=True,
    max_iter=5,
    max_rpm=10,
    allow_delegation=False,
)
```

## Quick Reference

| Parameter | Type | Default | Notes |
|-----------|------|---------|-------|
| `role` | str | required | Agent's job title / function |
| `goal` | str | required | What the agent aims to achieve |
| `backstory` | str | required | Context for persona consistency |
| `tools` | list | `[]` | Tools available to the agent |
| `llm` | str/LLM | default | Model identifier or LLM instance |
| `memory` | bool | `False` | Enable agent-level memory |
| `verbose` | bool | `False` | Enable detailed logging |
| `max_iter` | int | `20` | Max reasoning iterations |
| `max_rpm` | int | `None` | Rate limit for API calls |
| `allow_delegation` | bool | `True` | Can delegate to other agents |
| `step_callback` | callable | `None` | Hook after each reasoning step |
| `function_calling_llm` | str | `None` | Separate LLM for tool calls |

## YAML Configuration

```yaml
# config/agents.yaml
pipeline_monitor:
  role: "Pipeline Monitor"
  goal: "Detect anomalies in data pipeline execution"
  backstory: >
    You are a senior DataOps engineer with deep expertise
    in monitoring ETL pipelines and identifying root causes.
  max_iter: 5
  verbose: true
```

```python
from crewai import Agent, CrewBase, agent

@CrewBase
class DataOpsCrew:
    agents_config = "config/agents.yaml"

    @agent
    def pipeline_monitor(self) -> Agent:
        return Agent(
            config=self.agents_config["pipeline_monitor"],
            tools=[log_reader_tool, metrics_tool],
        )
```

## Common Mistakes

### Wrong

```python
# Missing backstory leads to generic, unfocused responses
agent = Agent(
    role="Monitor",
    goal="Monitor things",
)
```

### Correct

```python
# Specific role, goal, and backstory produce focused behavior
agent = Agent(
    role="BigQuery Pipeline Monitor",
    goal="Detect row count anomalies exceeding 15% deviation in BigQuery loads",
    backstory=(
        "You specialize in BigQuery data quality. You compare daily "
        "row counts against 7-day rolling averages to catch anomalies."
    ),
    tools=[bigquery_tool],
    max_iter=5,
)
```

## Related

- [Tasks](../concepts/tasks.md)
- [Crews](../concepts/crews.md)
- [Tools](../concepts/tools.md)
- [Triage Pattern](../patterns/triage-investigation-report.md)
