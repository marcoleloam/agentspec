# Slack Integration Pattern

> **Purpose**: Send pipeline alerts, incident reports, and escalation notifications to Slack channels
> **MCP Validated**: 2026-02-17

## When to Use

- Pipeline failures need to notify the on-call team in Slack
- Incident reports should be posted to a dedicated alerts channel
- Escalation events require threading context into Slack conversations
- Want agents to read Slack threads for incident collaboration

## Implementation

```python
from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool, tool
from pydantic import BaseModel, Field
from typing import Optional
import json

# --- Slack Tools ---

class SlackNotifierTool(BaseTool):
    name: str = "Slack Alert Sender"
    description: str = (
        "Send a formatted alert message to a Slack channel. "
        "Supports blocks for rich formatting, severity colors, "
        "and thread replies. Use this to notify teams of incidents."
    )

    def _run(
        self,
        channel: str,
        message: str,
        severity: str = "medium",
        thread_ts: Optional[str] = None,
    ) -> str:
        import requests

        color_map = {
            "low": "#36a64f",
            "medium": "#ff9900",
            "high": "#ff0000",
            "critical": "#8b0000",
        }

        payload = {
            "channel": channel,
            "attachments": [{
                "color": color_map.get(severity, "#ff9900"),
                "blocks": [
                    {
                        "type": "header",
                        "text": {"type": "plain_text", "text": f"Pipeline Alert [{severity.upper()}]"},
                    },
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": message},
                    },
                ],
            }],
        }

        if thread_ts:
            payload["thread_ts"] = thread_ts

        resp = requests.post(
            "https://slack.com/api/chat.postMessage",
            headers={"Authorization": f"Bearer {self._get_token()}"},
            json=payload,
        )
        data = resp.json()
        return json.dumps({"ok": data["ok"], "ts": data.get("ts")})

    def _get_token(self) -> str:
        import os
        return os.environ["SLACK_BOT_TOKEN"]


@tool("Slack Thread Reader")
def read_slack_thread(channel: str, thread_ts: str) -> str:
    """Read all messages in a Slack thread for incident context.
    Use this to gather updates from team members about an ongoing incident."""
    import requests, os

    resp = requests.get(
        "https://slack.com/api/conversations.replies",
        headers={"Authorization": f"Bearer {os.environ['SLACK_BOT_TOKEN']}"},
        params={"channel": channel, "ts": thread_ts},
    )
    messages = resp.json().get("messages", [])
    return "\n".join(
        f"[{m.get('user', 'bot')}]: {m.get('text', '')}"
        for m in messages
    )

# --- Alert Agent ---

alert_agent = Agent(
    role="Slack Alert Coordinator",
    goal="Send well-formatted, actionable alerts to the correct Slack channels",
    backstory=(
        "You are responsible for communicating pipeline incidents to "
        "engineering teams via Slack. You format messages with severity "
        "colors, include relevant context, and thread follow-ups to "
        "keep channels organized."
    ),
    tools=[SlackNotifierTool(), read_slack_thread],
    max_iter=5,
)

# --- Notification Task ---

notify_task = Task(
    description=(
        "Send a Slack alert for pipeline '{pipeline_name}' to channel "
        "'{slack_channel}'. Include:\n"
        "- Severity level: {severity}\n"
        "- Error summary: {error_summary}\n"
        "- Affected tables: {affected_tables}\n"
        "- Recommended action: {recommended_action}\n"
        "Format the message with Slack markdown for readability."
    ),
    expected_output="Confirmation that the Slack message was sent with timestamp",
    agent=alert_agent,
)

# --- Crew ---

slack_crew = Crew(
    agents=[alert_agent],
    tasks=[notify_task],
    process=Process.sequential,
    verbose=True,
)
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `SLACK_BOT_TOKEN` | env var | Slack Bot OAuth token |
| `slack_channel` | `#data-alerts` | Target notification channel |
| `severity` | `medium` | Alert severity level |
| `thread_ts` | `None` | Thread parent for replies |

## Example Usage

```python
result = slack_crew.kickoff(inputs={
    "pipeline_name": "daily_sales_etl",
    "slack_channel": "#data-alerts",
    "severity": "high",
    "error_summary": "BigQuery load failed: DEADLINE_EXCEEDED on sales_facts table",
    "affected_tables": "sales_facts, sales_summary_mv",
    "recommended_action": "Increase BigQuery slot reservation or partition the load",
})

# Integrate with triage pattern
from crewai import Flow
from crewai.flow.flow import start, listen

class AlertFlow(Flow):
    @start()
    def run_triage(self):
        return triage_crew.kickoff(inputs={"pipeline_name": "daily_sales_etl"})

    @listen(run_triage)
    def send_alert(self, triage_result):
        return slack_crew.kickoff(inputs={
            "pipeline_name": "daily_sales_etl",
            "slack_channel": "#data-alerts",
            "severity": "high",
            "error_summary": triage_result.raw,
            "affected_tables": "TBD",
            "recommended_action": "See triage report",
        })
```

## See Also

- [Escalation Workflow](../patterns/escalation-workflow.md)
- [Triage Pattern](../patterns/triage-investigation-report.md)
- [Tools](../concepts/tools.md)
