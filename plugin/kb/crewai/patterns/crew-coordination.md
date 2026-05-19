# Multi-Crew Coordination Pattern

> **Purpose**: Orchestrate multiple specialized crews via Flows for complex DataOps workflows
> **MCP Validated**: 2026-02-17

## When to Use

- Workflow requires multiple distinct phases (detect, investigate, remediate, report)
- Different phases need different agent compositions and tools
- Need conditional branching between workflow stages
- Want state persistence across multiple crew executions
- Building a full DataOps incident response system

## Implementation

```python
from crewai import Agent, Task, Crew, Process, Flow
from crewai.flow.flow import start, listen, router
from pydantic import BaseModel, Field
from typing import List, Optional

# --- Flow State ---

class DataOpsState(BaseModel):
    pipeline_name: str = ""
    severity: str = "unknown"
    triage_result: str = ""
    investigation_result: str = ""
    remediation_result: str = ""
    notification_sent: bool = False
    phase: str = "init"

# --- Crew Factories ---

def build_triage_crew() -> Crew:
    triage_agent = Agent(
        role="DataOps Triage Specialist",
        goal="Classify pipeline alert severity and identify affected systems",
        backstory="First responder for data pipeline alerts with 10y experience.",
        max_iter=5,
    )
    return Crew(
        agents=[triage_agent],
        tasks=[Task(
            description=(
                "Assess pipeline '{pipeline_name}' alert. Classify severity "
                "as low/medium/high/critical. List affected downstream systems."
            ),
            expected_output="Severity classification and affected systems list",
            agent=triage_agent,
        )],
        process=Process.sequential,
    )

def build_investigation_crew() -> Crew:
    log_analyst = Agent(role="Log Analyst", goal="Parse logs and identify error patterns",
                        backstory="Expert at Cloud Logging and Airflow logs.", max_iter=8)
    rca_analyst = Agent(role="Root Cause Analyst", goal="Determine root cause from logs",
                        backstory="Traces failures through dependency graphs.", max_iter=8)
    log_task = Task(description="Analyze logs for pipeline '{pipeline_name}'",
                    expected_output="Error patterns and timeline", agent=log_analyst)
    rca_task = Task(description="Determine root cause from log analysis",
                    expected_output="Root cause with evidence", agent=rca_analyst,
                    context=[log_task])
    return Crew(agents=[log_analyst, rca_analyst], tasks=[log_task, rca_task],
                process=Process.sequential, memory=True)

def build_remediation_crew() -> Crew:
    agent = Agent(role="Auto-Remediation Agent", goal="Apply known fixes",
                  backstory="Executes remediation playbooks.", max_iter=5)
    return Crew(agents=[agent], tasks=[Task(
        description="Apply remediation for '{pipeline_name}': {root_cause}",
        expected_output="Remediation action and outcome", agent=agent,
    )], process=Process.sequential)

def build_notification_crew() -> Crew:
    agent = Agent(role="Incident Notifier", goal="Send incident notifications",
                  backstory="Communicates incidents to teams.", max_iter=3)
    return Crew(agents=[agent], tasks=[Task(
        description="Compose incident summary for '{pipeline_name}'. "
                    "Severity: {severity}. Root cause: {root_cause}.",
        expected_output="Formatted incident notification", agent=agent,
    )], process=Process.sequential)

# --- Orchestration Flow ---

class DataOpsIncidentFlow(Flow[DataOpsState]):
    """Full incident response: triage -> investigate -> remediate -> notify."""

    @start()
    def triage_phase(self):
        self.state.phase = "triage"
        crew = build_triage_crew()
        result = crew.kickoff(inputs={"pipeline_name": self.state.pipeline_name})
        self.state.triage_result = result.raw

        raw = result.raw.lower()
        if "critical" in raw:
            self.state.severity = "critical"
        elif "high" in raw:
            self.state.severity = "high"
        elif "medium" in raw:
            self.state.severity = "medium"
        else:
            self.state.severity = "low"
        return self.state.severity

    @router(triage_phase)
    def route_severity(self):
        if self.state.severity in ("high", "critical"):
            return "deep_investigate"
        elif self.state.severity == "medium":
            return "quick_investigate"
        return "auto_resolve"

    @listen("deep_investigate")
    def investigate_phase(self):
        self.state.phase = "investigation"
        crew = build_investigation_crew()
        result = crew.kickoff(inputs={"pipeline_name": self.state.pipeline_name})
        self.state.investigation_result = result.raw
        return result.raw

    @listen("quick_investigate")
    def quick_check(self):
        self.state.phase = "quick_check"
        self.state.investigation_result = "Medium severity - standard remediation"
        return self.state.investigation_result

    @listen("auto_resolve")
    def auto_resolve(self):
        self.state.phase = "resolved"
        self.state.remediation_result = "Auto-resolved: transient issue"
        self.state.notification_sent = False
        return "resolved"

    @listen(investigate_phase)
    def remediate_phase(self, investigation_result):
        self.state.phase = "remediation"
        crew = build_remediation_crew()
        result = crew.kickoff(inputs={
            "pipeline_name": self.state.pipeline_name,
            "root_cause": self.state.investigation_result,
        })
        self.state.remediation_result = result.raw
        return result.raw

    @listen(remediate_phase)
    def notify_phase(self, remediation_result):
        self.state.phase = "notification"
        crew = build_notification_crew()
        result = crew.kickoff(inputs={
            "pipeline_name": self.state.pipeline_name,
            "severity": self.state.severity,
            "root_cause": self.state.investigation_result,
            "remediation_result": self.state.remediation_result,
        })
        self.state.notification_sent = True
        return result.raw
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| Triage `max_iter` | `5` | Fast assessment |
| Investigation `max_iter` | `8` | Deep analysis |
| Remediation `max_iter` | `5` | Apply known fix |
| Notification `max_iter` | `3` | Format and send |
| Investigation `memory` | `True` | Cross-task context |

## Example Usage

```python
flow = DataOpsIncidentFlow()
flow.state.pipeline_name = "daily_sales_etl"
result = flow.kickoff()

print(f"Phase: {flow.state.phase}")
print(f"Severity: {flow.state.severity}")
print(f"Notified: {flow.state.notification_sent}")

# Visualize the flow
flow.plot("incident_flow")
```

## See Also

- [Triage Pattern](../patterns/triage-investigation-report.md)
- [Escalation Workflow](../patterns/escalation-workflow.md)
- [Circuit Breaker](../patterns/circuit-breaker.md)
- [Crews](../concepts/crews.md)
- [Processes](../concepts/processes.md)
