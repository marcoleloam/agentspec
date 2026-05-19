# Crews

> **Purpose**: Compose teams of agents that collaborate to solve DataOps monitoring tasks
> **Confidence**: 0.95
> **MCP Validated**: 2026-02-17

## Overview

A Crew is a team of agents working together on a list of tasks through a defined process. Crews are the primary execution unit in CrewAI. You configure agents, tasks, process type, memory, and callbacks, then call `kickoff()` to run the workflow. Crews can be defined in Python or declaratively via YAML with the `@CrewBase` decorator.

## The Pattern

```python
from crewai import Agent, Task, Crew, Process

monitor = Agent(role="Pipeline Monitor", goal="Detect failures", backstory="...")
investigator = Agent(role="Root Cause Analyst", goal="Find root cause", backstory="...")

detect_task = Task(
    description="Check pipeline {pipeline_name} for failures in the last hour",
    expected_output="List of failed jobs with timestamps and error codes",
    agent=monitor,
)
investigate_task = Task(
    description="Analyze failures and determine root cause",
    expected_output="Root cause analysis with remediation steps",
    agent=investigator,
    context=[detect_task],
)

crew = Crew(
    agents=[monitor, investigator],
    tasks=[detect_task, investigate_task],
    process=Process.sequential,
    memory=True,
    verbose=True,
)

result = crew.kickoff(inputs={"pipeline_name": "daily_sales_etl"})
print(result.raw)
```

## Quick Reference

| Parameter | Type | Default | Notes |
|-----------|------|---------|-------|
| `agents` | list[Agent] | required | Participating agents |
| `tasks` | list[Task] | required | Tasks to execute |
| `process` | Process | `sequential` | Execution strategy |
| `memory` | bool | `False` | Enable crew memory |
| `cache` | bool | `True` | Cache tool results |
| `verbose` | bool | `False` | Detailed logging |
| `max_rpm` | int | `None` | Global rate limit |
| `manager_llm` | str | `None` | LLM for hierarchical manager |
| `manager_agent` | Agent | `None` | Custom manager agent |
| `planning` | bool | `False` | Enable auto-planning |
| `embedder` | dict | `None` | Custom embedder config |
| `output_log_file` | str | `None` | Save execution logs |
| `step_callback` | callable | `None` | Hook after each step |
| `task_callback` | callable | `None` | Hook after each task |

## YAML Configuration

```python
from crewai import CrewBase, agent, task, crew, Agent, Task, Crew, Process

@CrewBase
class DataOpsCrew:
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def pipeline_monitor(self) -> Agent:
        return Agent(config=self.agents_config["pipeline_monitor"])

    @agent
    def root_cause_analyst(self) -> Agent:
        return Agent(config=self.agents_config["root_cause_analyst"])

    @task
    def detect_failures(self) -> Task:
        return Task(config=self.tasks_config["detect_failures"])

    @task
    def analyze_root_cause(self) -> Task:
        return Task(config=self.tasks_config["analyze_root_cause"])

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            memory=True,
            verbose=True,
        )
```

## Execution Methods

| Method | Type | Use Case |
|--------|------|----------|
| `kickoff(inputs={})` | sync | Standard execution |
| `kickoff_for_each(inputs=[])` | sync | Batch processing |
| `akickoff(inputs={})` | async | Async execution |
| `akickoff_for_each(inputs=[])` | async | Async batch |

## CrewOutput Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `raw` | str | Default string output |
| `pydantic` | BaseModel | Structured Pydantic output |
| `json_dict` | dict | Dictionary representation |
| `tasks_output` | list | Per-task output list |
| `token_usage` | dict | LLM token metrics |

## Common Mistakes

### Wrong

```python
# Hierarchical process without manager LLM
crew = Crew(agents=[a1, a2], tasks=[t1], process=Process.hierarchical)
```

### Correct

```python
crew = Crew(
    agents=[a1, a2],
    tasks=[t1],
    process=Process.hierarchical,
    manager_llm="openai/gpt-4o",
)
```

## Related

- [Agents](../concepts/agents.md)
- [Tasks](../concepts/tasks.md)
- [Processes](../concepts/processes.md)
- [Crew Coordination](../patterns/crew-coordination.md)
