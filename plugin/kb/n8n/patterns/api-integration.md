# API Integration Pattern

> **Purpose**: Call REST APIs with authentication, pagination, and error retry
> **MCP Validated**: 2026-04-14

## When to Use

- Fetching data from external APIs (Apify, HeyGen, Stripe)
- Sending data to internal services (backend API)
- Syncing data between systems

## Implementation

```text
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Trigger    │────►│ HTTP Request │────►│  Transform   │────►│    Store     │
│ (Schedule/   │     │ (API Call)   │     │  (Code/Set)  │     │ (DB/HTTP/    │
│  Manual)     │     │              │     │              │     │  File)       │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

### Basic GET Request

```json
{
  "method": "GET",
  "url": "https://api.example.com/v1/data",
  "authentication": "predefinedCredentialType",
  "nodeCredentialType": "myApiCredential",
  "options": {
    "timeout": 30000
  }
}
```

### POST with JSON Body

```json
{
  "method": "POST",
  "url": "http://backend:8000/internal/videos/ingest",
  "headers": {
    "X-Internal-Key": "={{ $env.INTERNAL_API_KEY }}"
  },
  "body": {
    "contentType": "application/json",
    "jsonBody": "={{ JSON.stringify({ videos: $json.videos }) }}"
  }
}
```

### Pagination Pattern

```text
Schedule Trigger
  → Set (page=1, hasMore=true)
  → Loop:
    → HTTP Request (GET /api/data?page={{ $json.page }})
    → Code (extract items, check hasMore)
    → IF (hasMore?)
      → True: Set (page+1) → back to HTTP Request
      → False: → Merge all results → Process
```

```javascript
// Code node for pagination check
const response = $input.first().json;
const items = response.data || [];
const hasMore = response.pagination?.has_more || false;
const nextPage = response.pagination?.next_page || null;

return [{
  json: {
    items,
    hasMore,
    nextPage,
    totalCollected: ($json.totalCollected || 0) + items.length,
  }
}];
```

### Batch Requests (Rate Limiting)

```text
Input Items (100+)
  → Split in Batches (batchSize: 10)
  → HTTP Request (process batch)
  → Wait (1 second — rate limit)
  → Loop back to Split in Batches
```

### Retry on Failure

```json
{
  "method": "POST",
  "url": "https://api.example.com/v1/action",
  "options": {
    "timeout": 30000,
    "retry": {
      "maxRetries": 3,
      "retryInterval": 1000
    }
  }
}
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| method | GET | HTTP method |
| url | — | Full URL or expression |
| authentication | none | Auth type |
| timeout | 10000 | Request timeout (ms) |
| retry.maxRetries | 0 | Number of retries |
| continueOnFail | false | Don't stop on error |

## Example: Apify TikTok Scraper via n8n

```text
Schedule (every 6h)
  → Apify Node (run APIDojo TikTok Scraper)
  → Code (transform to ingest format)
  → HTTP Request (POST /internal/videos/ingest)
```

## Common Mistakes

### Wrong: No error handling on API call
```json
{ "method": "GET", "url": "https://api.example.com/data" }
// Workflow stops on 4xx/5xx
```

### Correct: continueOnFail + error check
```json
{ "method": "GET", "url": "https://api.example.com/data", "options": { "continueOnFail": true } }
// Then IF node: {{ $json.error }} → handle error branch
```

## See Also

- [webhook-processing](webhook-processing.md) — Receiving API calls
- [error-handling](error-handling.md) — Error recovery patterns
- [scheduled-automation](scheduled-automation.md) — Scheduling API calls
