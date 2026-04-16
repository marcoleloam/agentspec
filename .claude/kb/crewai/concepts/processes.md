# Processes

> **Purpose**: Control execution flow with sequential and hierarchical process strategies
> **Confidence**: 0.95
> **MCP Validated**: 2026-02-17

## Overview

CrewAI Processes define how tasks are distributed and executed within a crew. There are two process types: Sequential (tasks run one after another in order) and Hierarchical (a manager agent coordinates and delegates tasks to workers). The process type determines the collaboration pattern between agents.

## The Pattern

```python
from crewai import Crew, Process

# Sequential: tasks execute in list order
sequential_crew = Crew(
    agents=[collector, analyzer, reporter],
    tasks=[collect_task, analyze_task, report_task],
    process=Process.sequential,
    verbose=True,
)

# Hierarchical: manager delegates tasks to best-fit agents
hierarchical_crew = Crew(
    agents=[collector, analyzer, reporter],
    tasks=[collect_task, analyze_task, report_task],
    process=Process.hierarchical,
    manager_llm="openai/gpt-4o",
    verbose=True,
)
```

## Quick Reference

| Feature | Sequential | Hierarchical |
|---------|------------|--------------|
| Execution order | Fixed (list order) | Manager decides |
| Manager required | No | Yes |
| Delegation | No delegation | Manager delegates |
| Task reassignment | Not supported | Manager can reassign |
| Best for | Linear workflows | Complex decision trees |
| Predictability | High | Medium |
| Token cost | Lower | Higher (manager overhead) |

## Sequential Process

```python
from crewai import Agent, Task, Crew, Process

# Agents execute tasks in defined order
# Each task output is available to subsequent tasks via context
collector = Agent(
    role="Metrics Collector",
    goal="Gather pipeline execution metrics from BigQuery and Airflow",
    backstory="You collect raw metrics from monitoring systems.",
)
analyzer = Agent(
    role="Anomaly Detector",
    goal="Identify statistical anomalies in collected metrics",
    backstory="You apply statistical analysis to find deviations.",
)
reporter = Agent(
    role="Incident Reporter",
    goal="Generate actionable incident reports for the on-call team",
    backstory="You write clear, actionable incident reports.",
)

collect = Task(description="Collect metrics for last 4 hours", expected_output="...", agent=collector)
analyze = Task(description="Detect anomalies", expected_output="...", agent=analyzer, context=[collect])
report = Task(description="Write incident report", expected_output="...", agent=reporter, context=[analyze])

crew = Crew(
    agents=[collector, analyzer, reporter],
    tasks=[collect, analyze, report],
    process=Process.sequential,
)
result = crew.kickoff()
```

## Hierarchical Process

```python
from crewai import Agent, Task, Crew, Process

# Manager agent decides which agent handles each task
# Manager can reassign tasks if results are unsatisfactory
crew = Crew(
    agents=[collector, analyzer, reporter],
    tasks=[collect, analyze, report],
    process=Process.hierarchical,
    manager_llm="openai/gpt-4o",
    verbose=True,
)

# Or use a custom manager agent
manager = Agent(
    role="DataOps Lead",
    goal="Coordinate incident response and ensure thorough analysis",
    backstory="You are the on-call DataOps lead managing incident response.",
)

crew = Crew(
    agents=[collector, analyzer, reporter],
    tasks=[collect, analyze, report],
    process=Process.hierarchical,
    manager_agent=manager,
)
```

## Choosing a Process

| Scenario | Recommended |
|----------|-------------|
| ETL pipeline monitoring (collect-analyze-report) | Sequential |
| Multi-source investigation with unknowns | Hierarchical |
| Cost-sensitive production workloads | Sequential |
| Complex triage with possible reassignment | Hierarchical |
| Deterministic, auditable workflows | Sequential |
| Tasks that may need re-routing on failure | Hierarchical |

## Common Mistakes

### Wrong

```python
# Hierarchical without manager_llm causes runtime error
crew = Crew(
    agents=[a1, a2], tasks=[t1, t2],
    process=Process.hierarchical,  # Missing manager_llm!
)
```

### Correct

```python
crew = Crew(
    agents=[a1, a2], tasks=[t1, t2],
    process=Process.hierarchical,
    manager_llm="openai/gpt-4o",
)
```

## Related

- [Crews](../concepts/crews.md)
- [Agents](../concepts/agents.md)
- [Crew Coordination](../patterns/crew-coordination.md)
- [Escalation Workflow](../patterns/escalation-workflow.md)
