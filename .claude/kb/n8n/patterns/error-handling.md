# Error Handling Pattern

> **Purpose**: Error triggers, retry logic, alerting, and dead letter patterns
> **MCP Validated**: 2026-04-14

## When to Use

- Any production workflow that runs unattended
- Workflows calling external APIs (may fail)
- Data pipelines where failures need alerting
- Webhook processors that must respond even on errors

## Implementation

### Error Trigger Workflow

```text
MAIN WORKFLOW:
  Schedule → HTTP Request → Postgres → Slack (success)

ERROR HANDLER WORKFLOW:
  Error Trigger → Code (format error) → Slack (alert) → Postgres (log error)
```

The Error Trigger fires when ANY workflow fails. Configure it as a separate workflow.

### Error Trigger Node Output

```javascript
// Available in Error Trigger workflow
{
  "execution": {
    "id": "abc123",
    "url": "https://n8n.example.com/execution/abc123",
    "error": {
      "message": "Request failed with status 500",
      "node": { "name": "HTTP Request", "type": "n8n-nodes-base.httpRequest" }
    }
  },
  "workflow": {
    "id": "wf123",
    "name": "TikTok Scraper"
  }
}
```

### Format Error for Slack

```javascript
const exec = $input.first().json.execution;
const wf = $input.first().json.workflow;

return [{
  json: {
    text: [
      `*Workflow Failed*`,
      `Workflow: ${wf.name}`,
      `Node: ${exec.error?.node?.name || 'Unknown'}`,
      `Error: ${exec.error?.message || 'No message'}`,
      `Execution: ${exec.url}`,
    ].join('\n'),
  }
}];
```

### Continue On Fail (Per-Node)

```json
{
  "node": "HTTP Request",
  "continueOnFail": true
}
```

Then check for errors:
```text
HTTP Request (continueOnFail: true)
  → IF ({{ $json.error }})
    → True: Log error + skip
    → False: Process normally
```

### Retry Pattern

```text
HTTP Request (maxRetries: 3, retryInterval: 2000)
  → IF (still failed?)
    → True: Dead letter (store failed item for manual retry)
    → False: Continue processing
```

### Dead Letter Pattern

```javascript
// Store failed items for manual retry
const failedItem = $input.first().json;
return [{
  json: {
    original_data: failedItem,
    error_message: failedItem.error?.message,
    failed_at: DateTime.now().toISO(),
    retry_count: (failedItem.retry_count || 0) + 1,
  }
}];
// → Insert into dead_letter_queue table
```

## Alerting Configuration

| Channel | Node | When |
|---------|------|------|
| Slack | Slack (sendMessage) | All failures |
| Email | Send Email | Critical failures |
| Database | Postgres (insert) | Error logging |
| HTTP | HTTP Request | External monitoring (PagerDuty) |

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| continueOnFail | false | Node-level: don't stop on error |
| maxRetries | 0 | HTTP Request: auto-retry count |
| retryInterval | 1000 | Milliseconds between retries |
| Error Trigger | — | Separate workflow, fires on any failure |

## Common Mistakes

### Wrong: No error handling at all
```text
Schedule → HTTP Request → Postgres
// Fails silently if HTTP returns 500
```

### Correct: Error handler + alerting
```text
Main: Schedule → HTTP Request → Postgres
Error: Error Trigger → Slack alert + DB log
```

## See Also

- [webhook-processing](webhook-processing.md) — Error handling in webhooks
- [api-integration](api-integration.md) — API retry patterns
- [scheduled-automation](scheduled-automation.md) — Reliable scheduled jobs
