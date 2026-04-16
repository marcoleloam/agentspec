# Triage-Investigation-Report Pattern

> **Purpose**: Three-phase DataOps incident workflow: triage anomaly, investigate root cause, generate report
> **MCP Validated**: 2026-02-17

## When to Use

- Pipeline failure detected and needs structured incident response
- Anomaly in data quality metrics requires root cause analysis
- On-call team needs an automated first-pass investigation report
- Multiple data sources need correlation to identify failure origin

## Implementation

```python
from crewai import Agent, Task, Crew, Process
from crewai.tools import tool
from pydantic import BaseModel, Field
from typing import List, Literal

# --- Structured Output Models ---

class TriageResult(BaseModel):
    pipeline_name: str
    severity: Literal["low", "medium", "high", "critical"]
    affected_tables: List[str]
    error_summary: str
    needs_investigation: bool

class InvestigationResult(BaseModel):
    root_cause: str
    evidence: List[str]
    affected_downstream: List[str]
    estimated_impact: str

class IncidentReport(BaseModel):
    title: str
    severity: Literal["low", "medium", "high", "critical"]
    root_cause: str
    impact: str
    remediation_steps: List[str]
    owner: str

# --- Tools ---

@tool("Pipeline Log Reader")
def read_pipeline_logs(pipeline_name: str, hours: int = 2) -> str:
    """Read execution logs for a data pipeline from the last N hours.
    Use this to find error messages, stack traces, and failure timestamps."""
    # Implementation: query Cloud Logging, Airflow logs, etc.
    return f"Logs for {pipeline_name} (last {hours}h): ..."

@tool("BigQuery Metrics Checker")
def check_bq_metrics(dataset: str, table: str) -> str:
    """Check row counts, load times, and schema changes for a BigQuery table.
    Use this to verify data completeness after ETL runs."""
    return f"Metrics for {dataset}.{table}: ..."

# --- Agents ---

triage_agent = Agent(
    role="DataOps Triage Specialist",
    goal="Quickly assess pipeline alerts and classify severity",
    backstory=(
        "You are the first responder for data pipeline alerts. You rapidly "
        "assess failures, classify severity, and determine if deep investigation "
        "is needed. You never waste time on false alarms."
    ),
    tools=[read_pipeline_logs],
    max_iter=5,
)

investigator_agent = Agent(
    role="Root Cause Analyst",
    goal="Determine the exact root cause of pipeline failures",
    backstory=(
        "You are a senior data engineer who traces failures through dependency "
        "graphs, correlates logs across systems, and identifies root causes "
        "with precision. You always provide evidence for your conclusions."
    ),
    tools=[read_pipeline_logs, check_bq_metrics],
    max_iter=10,
)

reporter_agent = Agent(
    role="Incident Report Writer",
    goal="Generate clear, actionable incident reports for the on-call team",
    backstory=(
        "You write concise incident reports that engineering teams can act on "
        "immediately. You prioritize clarity and actionable remediation steps."
    ),
    max_iter=5,
)

# --- Tasks ---

triage_task = Task(
    description=(
        "Assess the alert for pipeline '{pipeline_name}'. "
        "Read the last 2 hours of logs. Classify severity as "
        "low/medium/high/critical. Determine if investigation is needed."
    ),
    expected_output="Triage assessment with severity and affected tables",
    agent=triage_agent,
    output_pydantic=TriageResult,
)

investigation_task = Task(
    description=(
        "Investigate the root cause of the failure in '{pipeline_name}'. "
        "Correlate logs, check downstream table metrics, and trace the "
        "dependency graph to find the origin of the failure."
    ),
    expected_output="Root cause analysis with evidence and impact assessment",
    agent=investigator_agent,
    context=[triage_task],
    output_pydantic=InvestigationResult,
)

report_task = Task(
    description=(
        "Generate an incident report for '{pipeline_name}'. Combine triage "
        "and investigation results into a clear report with remediation steps."
    ),
    expected_output="Complete incident report ready for the on-call team",
    agent=reporter_agent,
    context=[triage_task, investigation_task],
    output_pydantic=IncidentReport,
)

# --- Crew ---

triage_crew = Crew(
    agents=[triage_agent, investigator_agent, reporter_agent],
    tasks=[triage_task, investigation_task, report_task],
    process=Process.sequential,
    memory=True,
    verbose=True,
)
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `max_iter` (triage) | `5` | Fast assessment, limited iterations |
| `max_iter` (investigator) | `10` | Deep analysis, more iterations |
| `process` | `sequential` | Triage -> Investigate -> Report |
| `memory` | `True` | Learn from past incidents |

## Example Usage

```python
result = triage_crew.kickoff(inputs={
    "pipeline_name": "daily_sales_etl",
})

report = result.pydantic
print(f"Severity: {report.severity}")
print(f"Root Cause: {report.root_cause}")
for step in report.remediation_steps:
    print(f"  - {step}")
```

## See Also

- [Escalation Workflow](../patterns/escalation-workflow.md)
- [Log Analysis Agent](../patterns/log-analysis-agent.md)
- [Agents](../concepts/agents.md)
- [Tasks](../concepts/tasks.md)
