# Webhook Processing Pattern

> **Purpose**: Receive HTTP requests, validate, process, and respond
> **MCP Validated**: 2026-04-14

## When to Use

- External service sends events (HeyGen callback, Stripe webhook, GitHub)
- Building API endpoints for internal services
- Receiving form submissions or data from frontend

## Implementation

```text
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Webhook    │────►│   Validate   │────►│   Process    │────►│   Respond    │
│   Trigger    │     │   (Code/IF)  │     │   (Action)   │     │   (Webhook   │
│              │     │              │     │              │     │    Response) │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

### Webhook Trigger Config

```json
{
  "httpMethod": "POST",
  "path": "video-callback",
  "responseMode": "responseNode",
  "options": {
    "rawBody": true
  }
}
```

**Response Modes:**

| Mode | Behavior | Use Case |
|------|----------|----------|
| `lastNode` | Responds with last node output | Simple processing |
| `responseNode` | Responds at specific Respond node | Complex flows |
| Immediately | 200 OK right away | Long processing (async) |

### Validation (Code Node)

```javascript
const body = $input.first().json;

// Validate required fields
if (!body.event_type || !body.event_data) {
  throw new Error('Missing required fields: event_type, event_data');
}

// Validate signature (if applicable)
const signature = $input.first().headers['x-signature'];
if (signature) {
  const crypto = require('crypto');
  const expected = crypto.createHmac('sha256', $env.WEBHOOK_SECRET)
    .update(JSON.stringify(body)).digest('hex');
  if (signature !== expected) {
    throw new Error('Invalid signature');
  }
}

return [{ json: body }];
```

### Process + Respond

```json
// HTTP Request to internal API
{
  "method": "POST",
  "url": "http://backend:8000/internal/process",
  "headers": { "X-Internal-Key": "={{ $env.INTERNAL_API_KEY }}" },
  "body": "={{ JSON.stringify($json) }}",
  "contentType": "application/json"
}

// Respond to Webhook node
{
  "respondWith": "json",
  "responseBody": "={{ JSON.stringify({ status: 'received', id: $json.id }) }}",
  "responseCode": 200
}
```

## Example: HeyGen Callback

```text
Webhook (POST /heygen-callback)
  → Code (validate signature + extract data)
  → HTTP Request (POST /internal/heygen/callback to backend)
  → Respond (200 OK)
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| httpMethod | POST | HTTP method to accept |
| path | — | URL path after /webhook/ |
| responseMode | lastNode | When to send HTTP response |
| authentication | none | headerAuth or none |
| rawBody | false | Include raw body for signature validation |

## See Also

- [api-integration](api-integration.md) — Outbound HTTP calls
- [error-handling](error-handling.md) — Handling webhook failures
- [credentials-auth](../concepts/credentials-auth.md) — Webhook authentication
