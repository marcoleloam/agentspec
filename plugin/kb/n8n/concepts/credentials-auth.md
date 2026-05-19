# Credentials & Authentication

> **Purpose**: n8n credential management, authentication patterns, security
> **Confidence**: 0.90
> **MCP Validated**: 2026-04-14

## Overview

n8n stores credentials separately from workflows. Credentials are encrypted at rest and referenced by ID, never exposing secrets in workflow JSON. This enables safe sharing and version control of workflows.

## Authentication Types

| Type | Use Case | Config |
|------|----------|--------|
| API Key | Simple REST APIs | key, value, placement (header/query) |
| Header Auth | Custom headers | name, value |
| OAuth2 | Google, Slack, GitHub | clientId, clientSecret, scopes |
| Basic Auth | Legacy APIs | username, password |
| Custom Auth | Non-standard | custom headers/params |

## HTTP Request Authentication

```json
{
  "authentication": "predefinedCredentialType",
  "nodeCredentialType": "myApiCredential",
  "url": "https://api.example.com/data",
  "method": "GET"
}
```

### API Key in Header
```json
{
  "authentication": "genericCredentialType",
  "genericAuthType": "httpHeaderAuth",
  "url": "https://api.example.com/data"
}
// Credential config: { "name": "X-Api-Key", "value": "secret123" }
```

### Bearer Token
```json
{
  "authentication": "genericCredentialType",
  "genericAuthType": "httpHeaderAuth"
}
// Credential config: { "name": "Authorization", "value": "Bearer token123" }
```

## Environment Variables

Access via expressions:
```javascript
{{ $env.API_KEY }}
{{ $env.DATABASE_URL }}
{{ $env.INTERNAL_API_KEY }}
```

Set in Docker:
```yaml
environment:
  - API_KEY=your-key
  - DATABASE_URL=postgres://user:pass@host:5432/db
```

## Internal API Authentication

For service-to-service calls (n8n → backend):
```javascript
// In HTTP Request node headers
{
  "X-Internal-Key": "={{ $env.INTERNAL_API_KEY }}"
}
```

## Webhook Authentication

### Webhook with Header Auth
```json
{
  "authentication": "headerAuth",
  "httpMethod": "POST",
  "path": "my-webhook"
}
// Validates incoming X-Auth-Header against stored credential
```

### Webhook Signature Validation (Code Node)
```javascript
const crypto = require('crypto');
const signature = $input.first().headers['x-signature'];
const body = JSON.stringify($input.first().json);
const expected = crypto.createHmac('sha256', $env.WEBHOOK_SECRET)
  .update(body).digest('hex');

if (signature !== expected) {
  throw new Error('Invalid webhook signature');
}
return $input.all();
```

## Common Mistakes

### Wrong: Hardcoded secrets in Code node
```javascript
const apiKey = "sk-abc123"; // NEVER DO THIS
```

### Correct: Use credentials or environment variables
```javascript
const apiKey = $env.API_KEY; // From environment
// Or use HTTP Request node with credential reference
```

### Wrong: Sharing workflows with credentials
Credentials are not exported with workflows. Recipients must create their own.

### Correct: Document required credentials
```markdown
## Required Credentials
1. HeyGen API Key (Header Auth: X-Api-Key)
2. Postgres connection (host, port, database, user, password)
3. Slack Bot Token (OAuth2)
```

## Related

- [webhook-processing](../patterns/webhook-processing.md) — Webhook auth patterns
- [api-integration](../patterns/api-integration.md) — API authentication
