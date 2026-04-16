# Tasks

> **Purpose**: Define actionable units of work assigned to agents with structured outputs
> **Confidence**: 0.95
> **MCP Validated**: 2026-02-17

## Overview

A Task is the actionable unit that an agent executes within a crew. Each task has a description, expected output, and is assigned to a specific agent. Tasks can depend on other tasks via the `context` parameter, enabling data flow between pipeline stages. Tasks support structured output via Pydantic models.

## The Pattern

```python
from crewai import Task, Agent
from pydantic import BaseModel
from typing import List

class PipelineReport(BaseModel):
    pipeline_name: str
    status: str
    failed_jobs: List[str]
    root_cause: str
    recommended_action: str

monitor_agent = Agent(role="Pipeline Monitor", goal="...", backstory="...")

check_pipeline = Task(
    description=(
        "Check the {pipeline_name} pipeline for failures in the last {hours} hours. "
        "Query the execution logs and identify any jobs that failed or timed out."
    ),
    expected_output="Structured report with pipeline status and failed jobs",
    agent=monitor_agent,
    output_pydantic=PipelineReport,
)

result = check_pipeline.execute()
```

## Quick Reference

| Parameter | Type | Default | Notes |
|-----------|------|---------|-------|
| `description` | str | required | What the agent should do |
| `expected_output` | str | required | What the output should look like |
| `agent` | Agent | `None` | Agent assigned to execute |
| `tools` | list | `[]` | Task-specific tools (override agent) |
| `context` | list[Task] | `[]` | Upstream tasks providing input |
| `output_pydantic` | BaseModel | `None` | Structured output model |
| `output_json` | type | `None` | JSON output schema |
| `output_file` | str | `None` | Write output to file |
| `async_execution` | bool | `False` | Run asynchronously |
| `human_input` | bool | `False` | Require human approval |
| `callback` | callable | `None` | Post-execution hook |

## YAML Configuration

```yaml
# config/tasks.yaml
check_pipeline:
  description: >
    Check the {pipeline_name} pipeline for failures
    in the last {hours} hours. Query execution logs
    and identify failed or timed-out jobs.
  expected_output: >
    Structured report including pipeline status,
    list of failed jobs, and error messages.
  agent: pipeline_monitor

investigate_failure:
  description: >
    Investigate the root cause of failures found in
    {pipeline_name}. Analyze logs and dependency graph.
  expected_output: >
    Root cause analysis with remediation steps.
  agent: root_cause_analyst
  context:
    - check_pipeline
```

## Task Context (Dependencies)

```python
# Task B receives Task A output as context
task_a = Task(
    description="Collect pipeline metrics for the last 24 hours",
    expected_output="JSON metrics summary",
    agent=collector,
)

task_b = Task(
    description="Analyze metrics and flag anomalies above 2 std deviations",
    expected_output="List of anomalous metrics with severity",
    agent=analyst,
    context=[task_a],  # task_b receives task_a output
)
```

## Structured Output

```python
from pydantic import BaseModel, Field
from typing import List, Literal

class AnomalyReport(BaseModel):
    metric_name: str = Field(description="Name of the metric")
    current_value: float = Field(description="Current observed value")
    expected_range: str = Field(description="Expected min-max range")
    severity: Literal["low", "medium", "high", "critical"]
    recommendation: str = Field(description="Suggested remediation")

task = Task(
    description="Analyze BigQuery load metrics and detect anomalies",
    expected_output="Anomaly report with severity ratings",
    agent=analyst,
    output_pydantic=AnomalyReport,
)
```

## Common Mistakes

### Wrong

```python
# Missing expected_output leads to unfocused agent behavior
task = Task(description="Check the pipeline", agent=monitor)
```

### Correct

```python
task = Task(
    description="Check the daily_sales_etl pipeline for failures in the last 2 hours",
    expected_output="JSON list of failed jobs with error codes and timestamps",
    agent=monitor,
)
```

## Related

- [Agents](../concepts/agents.md)
- [Crews](../concepts/crews.md)
- [Triage Pattern](../patterns/triage-investigation-report.md)
