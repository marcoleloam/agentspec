# Log Analysis Agent Pattern

> **Purpose**: Automated pipeline log ingestion, parsing, and anomaly detection agent
> **MCP Validated**: 2026-02-17

## When to Use

- Pipeline logs need automated parsing for error patterns
- Need to detect recurring failures across multiple pipeline runs
- Want to extract structured error information from unstructured logs
- Building a self-healing system that reads logs before taking action

## Implementation

```python
from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool, tool
from pydantic import BaseModel, Field
from typing import List, Optional
import json

# --- Structured Output ---

class LogEntry(BaseModel):
    timestamp: str
    level: str
    component: str
    message: str
    error_code: Optional[str] = None

class LogAnalysisReport(BaseModel):
    pipeline_name: str
    total_errors: int
    unique_error_patterns: List[str]
    most_frequent_error: str
    time_of_first_failure: str
    suggested_root_cause: str
    is_recurring: bool

# --- Tools ---

class CloudLoggingTool(BaseTool):
    name: str = "GCP Cloud Logging Reader"
    description: str = (
        "Query Google Cloud Logging for pipeline execution logs. "
        "Supports filtering by severity, component, and time range. "
        "Use this to retrieve raw log entries for analysis."
    )

    def _run(self, pipeline_name: str, hours: int = 4, severity: str = "ERROR") -> str:
        from google.cloud import logging as cloud_logging

        client = cloud_logging.Client()
        filter_str = (
            f'resource.type="cloud_run_revision" '
            f'AND jsonPayload.pipeline="{pipeline_name}" '
            f'AND severity>="{severity}" '
            f'AND timestamp>="{hours}h ago"'
        )
        entries = client.list_entries(filter_=filter_str, max_results=100)
        results = []
        for entry in entries:
            results.append({
                "timestamp": str(entry.timestamp),
                "severity": entry.severity,
                "message": entry.payload.get("message", str(entry.payload)),
            })
        return json.dumps(results, indent=2)

@tool("Airflow Task Log Reader")
def read_airflow_logs(dag_id: str, task_id: str, execution_date: str) -> str:
    """Read Airflow task instance logs for a specific DAG run.
    Use this to get detailed execution logs including stack traces."""
    import requests
    resp = requests.get(
        f"https://airflow.internal/api/v1/dags/{dag_id}/dagRuns/"
        f"{execution_date}/taskInstances/{task_id}/logs/1",
        headers={"Authorization": "Bearer ${AIRFLOW_TOKEN}"},
    )
    return resp.text[:5000]  # Truncate for token efficiency

@tool("Error Pattern Matcher")
def match_error_patterns(log_text: str) -> str:
    """Match log text against known error patterns from historical incidents.
    Use this to identify if a current error matches a previously seen pattern."""
    known_patterns = {
        "DEADLINE_EXCEEDED": "BigQuery job timeout - likely large scan",
        "PERMISSION_DENIED": "IAM permission issue - check service account",
        "NOT_FOUND": "Missing table or dataset - check dependency order",
        "RESOURCE_EXHAUSTED": "Quota exceeded - check concurrent job limits",
    }
    matches = []
    for pattern, description in known_patterns.items():
        if pattern in log_text:
            matches.append(f"{pattern}: {description}")
    return "\n".join(matches) if matches else "No known patterns matched"

# --- Agent ---

log_analyst = Agent(
    role="Pipeline Log Analyst",
    goal=(
        "Parse pipeline execution logs to identify error patterns, "
        "classify failure types, and determine if failures are recurring"
    ),
    backstory=(
        "You are an expert at reading data pipeline logs. You can parse "
        "Cloud Logging, Airflow, and BigQuery audit logs. You identify "
        "error patterns, correlate timestamps, and detect recurring issues "
        "that indicate systemic problems vs one-time failures."
    ),
    tools=[CloudLoggingTool(), read_airflow_logs, match_error_patterns],
    memory=True,
    max_iter=8,
    verbose=True,
)

# --- Task ---

analyze_logs_task = Task(
    description=(
        "Analyze logs for pipeline '{pipeline_name}' over the last {hours} hours. "
        "1. Retrieve error-level logs from Cloud Logging. "
        "2. Parse and group errors by pattern. "
        "3. Match against known error patterns. "
        "4. Determine if this is a recurring failure. "
        "5. Suggest a root cause based on evidence."
    ),
    expected_output="Structured log analysis report with error patterns and root cause",
    agent=log_analyst,
    output_pydantic=LogAnalysisReport,
)

# --- Crew ---

log_analysis_crew = Crew(
    agents=[log_analyst],
    tasks=[analyze_logs_task],
    process=Process.sequential,
    memory=True,
    verbose=True,
)
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `hours` | `4` | Log lookback window |
| `severity` | `ERROR` | Minimum log severity |
| `max_results` | `100` | Max log entries to retrieve |
| `max_iter` | `8` | Agent reasoning iterations |

## Example Usage

```python
result = log_analysis_crew.kickoff(inputs={
    "pipeline_name": "daily_sales_etl",
    "hours": 6,
})

report = result.pydantic
if report.is_recurring:
    print(f"RECURRING ISSUE: {report.most_frequent_error}")
    print(f"Root cause: {report.suggested_root_cause}")
else:
    print(f"One-time failure: {report.suggested_root_cause}")
```

## See Also

- [Triage Pattern](../patterns/triage-investigation-report.md)
- [Escalation Workflow](../patterns/escalation-workflow.md)
- [Tools](../concepts/tools.md)
