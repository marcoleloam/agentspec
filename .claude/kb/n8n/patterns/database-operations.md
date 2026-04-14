# Database Operations Pattern

> **Purpose**: Read, write, and sync data with Postgres, MySQL, and other databases
> **MCP Validated**: 2026-04-14

## When to Use

- ETL: Extract from API → Transform → Load to database
- Data sync between systems
- Querying database for workflow logic
- Bulk upserts with deduplication

## Implementation

### Select (Query)

```json
{
  "operation": "select",
  "schema": "public",
  "table": "tiktok_videos",
  "where": {
    "values": [
      { "column": "status", "value": "new" },
      { "column": "views", "operator": ">=", "value": "10000" }
    ]
  },
  "limit": 50,
  "sort": { "column": "views", "direction": "DESC" }
}
```

### Insert

```json
{
  "operation": "insert",
  "schema": "public",
  "table": "tiktok_videos",
  "columns": {
    "mappingMode": "autoMapInputData"
  }
}
```

### Upsert (Insert or Update)

```json
{
  "operation": "upsert",
  "schema": "public",
  "table": "tiktok_videos",
  "columns": {
    "mappingMode": "autoMapInputData"
  },
  "conflictColumns": ["external_id"]
}
```

### Raw SQL Query

```json
{
  "operation": "executeQuery",
  "query": "SELECT v.*, COUNT(cj.id) as clone_count FROM tiktok_videos v LEFT JOIN clone_jobs cj ON cj.video_id = v.id WHERE v.status = 'new' GROUP BY v.id ORDER BY v.views DESC LIMIT {{ $json.limit }}"
}
```

## Bulk Ingest Pattern

```text
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Webhook    │────►│    Code      │────►│  Split in    │────►│   Postgres   │
│ (ingest API) │     │ (transform)  │     │  Batches(50) │     │  (upsert)    │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

```javascript
// Code: Transform API payload to DB rows
const videos = $input.first().json.videos;
return videos.map(v => ({
  json: {
    external_id: v.external_id,
    url: v.url,
    views: v.views || 0,
    likes: v.likes || 0,
    status: 'new',
    scraped_at: v.scraped_at || new Date().toISOString(),
  }
}));
```

## Sync Pattern (Incremental)

```text
Schedule (every 1h)
  → Postgres (SELECT max(updated_at) as watermark)
  → HTTP Request (GET /api/data?since={{ $json.watermark }})
  → Code (transform)
  → Postgres (upsert by external_id)
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| operation | select | select/insert/update/upsert/delete/executeQuery |
| schema | public | Database schema |
| table | — | Target table |
| conflictColumns | — | Upsert conflict resolution columns |
| mappingMode | autoMapInputData | How to map JSON fields to columns |

## Common Mistakes

### Wrong: Insert without dedup
```json
{ "operation": "insert", "table": "videos" }
// Fails on duplicate external_id
```

### Correct: Upsert with conflict key
```json
{ "operation": "upsert", "table": "videos", "conflictColumns": ["external_id"] }
```

### Wrong: SELECT * without limit
```json
{ "operation": "select", "table": "videos" }
// Returns entire table — OOM on large tables
```

### Correct: Always limit + filter
```json
{ "operation": "select", "table": "videos", "where": { "values": [{ "column": "status", "value": "new" }] }, "limit": 100 }
```

## See Also

- [api-integration](api-integration.md) — Fetching data from APIs
- [scheduled-automation](scheduled-automation.md) — Scheduling sync jobs
