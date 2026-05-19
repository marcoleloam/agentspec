# Escalation Workflow Pattern

> **Purpose**: Severity-based escalation with automatic routing and human-in-the-loop gates
> **MCP Validated**: 2026-02-17

## When to Use

- Pipeline failures need severity-based routing to different response teams
- Critical incidents require human approval before remediation
- Need automatic escalation when agent confidence is low
- Building a tiered support system (L1 auto-resolve, L2 human review, L3 page on-call)

## Implementation

```python
from crewai import Agent, Task, Crew, Process, Flow
from crewai.flow.flow import start, listen, router
from pydantic import BaseModel, Field
from typing import List, Literal

# --- State Model ---

class EscalationState(BaseModel):
    pipeline_name: str = ""
    severity: str = "unknown"
    root_cause: str = ""
    auto_resolved: bool = False
    escalated_to: str = ""
    human_approved: bool = False

# --- Agents ---

triage_agent = Agent(
    role="L1 Triage Responder",
    goal="Assess incident severity and attempt automatic resolution for low-severity issues",
    backstory=(
        "You are the first-line responder for data pipeline alerts. For low-severity "
        "issues like transient timeouts, you apply known fixes automatically. For "
        "anything medium or above, you escalate with full context."
    ),
    max_iter=5,
)

escalation_agent = Agent(
    role="L2 Escalation Manager",
    goal="Route incidents to the correct team and prepare escalation context",
    backstory=(
        "You manage incident escalation. You determine which team should handle "
        "the incident based on the failure domain (data quality, infrastructure, "
        "permissions, schema changes) and prepare a briefing package."
    ),
    max_iter=5,
)

remediation_agent = Agent(
    role="Auto-Remediation Agent",
    goal="Apply known fixes for common pipeline failures",
    backstory=(
        "You execute automated remediation playbooks. You can restart failed "
        "tasks, clear stuck queues, refresh materialized views, and trigger "
        "backfill jobs. You only act on pre-approved remediation actions."
    ),
    max_iter=5,
)

# --- Flow with Routing ---

class EscalationFlow(Flow[EscalationState]):

    @start()
    def assess_severity(self):
        """Phase 1: Triage and classify severity."""
        triage_crew = Crew(
            agents=[triage_agent],
            tasks=[Task(
                description=(
                    f"Assess the alert for pipeline '{self.state.pipeline_name}'. "
                    "Classify severity: low (transient/self-healing), medium "
                    "(needs attention within 4h), high (data loss risk), "
                    "critical (production SLA breach)."
                ),
                expected_output="Severity classification with justification",
                agent=triage_agent,
            )],
            process=Process.sequential,
        )
        result = triage_crew.kickoff()
        # Parse severity from result (simplified)
        raw = result.raw.lower()
        if "critical" in raw:
            self.state.severity = "critical"
        elif "high" in raw:
            self.state.severity = "high"
        elif "medium" in raw:
            self.state.severity = "medium"
        else:
            self.state.severity = "low"
        self.state.root_cause = result.raw
        return self.state.severity

    @router(assess_severity)
    def route_by_severity(self):
        """Route to different handlers based on severity."""
        if self.state.severity in ("critical", "high"):
            return "escalate"
        elif self.state.severity == "medium":
            return "auto_remediate"
        else:
            return "auto_resolve"

    @listen("auto_resolve")
    def handle_low_severity(self):
        """Auto-resolve low-severity issues (transient failures)."""
        self.state.auto_resolved = True
        self.state.escalated_to = "none"
        return "Auto-resolved: transient issue, no action needed"

    @listen("auto_remediate")
    def handle_medium_severity(self):
        """Attempt automated remediation for medium-severity issues."""
        remediation_crew = Crew(
            agents=[remediation_agent],
            tasks=[Task(
                description=(
                    f"Apply automated remediation for '{self.state.pipeline_name}'. "
                    f"Known issue: {self.state.root_cause}. "
                    "Try: restart task, clear queue, or trigger backfill."
                ),
                expected_output="Remediation action taken and result",
                agent=remediation_agent,
            )],
            process=Process.sequential,
        )
        result = remediation_crew.kickoff()
        self.state.auto_resolved = True
        self.state.escalated_to = "auto-remediation"
        return result.raw

    @listen("escalate")
    def handle_high_severity(self):
        """Escalate to human on-call for high/critical severity."""
        escalation_crew = Crew(
            agents=[escalation_agent],
            tasks=[Task(
                description=(
                    f"Prepare escalation package for '{self.state.pipeline_name}'. "
                    f"Severity: {self.state.severity}. Context: {self.state.root_cause}. "
                    "Determine the responsible team and prepare a briefing."
                ),
                expected_output="Escalation package with team routing and context",
                agent=escalation_agent,
            )],
            process=Process.sequential,
        )
        result = escalation_crew.kickoff()
        self.state.escalated_to = "human-oncall"
        self.state.auto_resolved = False
        return result.raw
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| Low severity | Auto-resolve | No action needed, log only |
| Medium severity | Auto-remediate | Apply known fix playbook |
| High severity | Escalate to L2 | Human review required |
| Critical severity | Page on-call | Immediate human intervention |

## Example Usage

```python
flow = EscalationFlow()
flow.state.pipeline_name = "daily_sales_etl"
result = flow.kickoff()

print(f"Severity: {flow.state.severity}")
print(f"Escalated to: {flow.state.escalated_to}")
print(f"Auto-resolved: {flow.state.auto_resolved}")
```

## See Also

- [Triage Pattern](../patterns/triage-investigation-report.md)
- [Circuit Breaker](../patterns/circuit-breaker.md)
- [Slack Integration](../patterns/slack-integration.md)
- [Processes](../concepts/processes.md)
