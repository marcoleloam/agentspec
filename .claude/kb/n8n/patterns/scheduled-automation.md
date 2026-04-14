# Scheduled Automation Pattern

> **Purpose**: Cron triggers, batch processing, idempotency, and state tracking
> **MCP Validated**: 2026-04-14

## When to Use

- Periodic data sync (scraping, ETL, cleanup)
- Recurring reports or notifications
- Polling external services for changes
- Batch processing queues

## Implementation

```text
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Schedule    │────►│   Fetch      │────►│  Transform   │────►│    Store     │
│  Trigger     │     │ (HTTP/DB)    │     │  (Code/Set)  │     │ (DB/API)     │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

### Schedule Trigger Config

```json
{
  "rule": {
    "interval": [{ "field": "hours", "hoursInterval": 6 }]
  }
}
```

| Schedule Type | Config | Example |
|---------------|--------|---------|
| Every N minutes | `minutesInterval: 30` | Every 30 min |
| Every N hours | `hoursInterval: 6` | Every 6 hours |
| Cron | `cronExpression: "0 8 * * 1-5"` | Weekdays at 8am |
| Specific times | `cronExpression: "0 8,12,18 * * *"` | 8am, 12pm, 6pm |

### Incremental Processing (Watermark)

```text
Schedule (every 1h)
  → Postgres (SELECT MAX(scraped_at) as watermark FROM tiktok_videos)
  → HTTP Request (GET /api/data?since={{ $json.watermark }})
  → Code (transform + deduplicate)
  → Postgres (upsert by external_id)
```

```javascript
// Code: Dedup by external_id
const existing = new Set(
  $("Postgres - Get Existing").all().map(i => i.json.external_id)
);
const newItems = $input.all().filter(i => !existing.has(i.json.external_id));
return newItems;
```

### Batch Processing Queue

```text
Schedule (every 5 min)
  → Postgres (SELECT * FROM jobs WHERE status = 'pending' LIMIT 10)
  → IF (items.length > 0?)
    → True:
      → Split in Batches (1)
      → HTTP Request (process item)
      → Postgres (UPDATE status = 'completed')
    → False: No Operation
```

### Idempotency

```javascript
// Generate deterministic ID to prevent duplicate processing
const crypto = require('crypto');
const item = $input.first().json;
const idempotencyKey = crypto.createHash('md5')
  .update(`${item.external_id}-${item.scraped_at}`)
  .digest('hex');

return [{
  json: {
    ...item,
    idempotency_key: idempotencyKey,
  }
}];
// Then upsert with conflictColumns: ["idempotency_key"]
```

### Cleanup Job

```text
Schedule (daily at 3am)
  → Postgres (DELETE FROM clone_jobs WHERE status = 'rejected' AND created_at < NOW() - INTERVAL '30 days')
  → Code (delete orphan media files)
  → Slack (report: "Cleanup: deleted {{ $json.deletedCount }} items")
```

```javascript
// Code: Cleanup orphan media files
const fs = require('fs');
const path = require('path');
const mediaDir = $env.MEDIA_DIR || './media';

const dbFiles = new Set($("Postgres - Active Files").all().map(i => i.json.video_file_path));
const diskFiles = fs.readdirSync(mediaDir).filter(f => f.endsWith('.mp4'));

let deletedCount = 0;
for (const file of diskFiles) {
  const fullPath = path.join(mediaDir, file);
  if (!dbFiles.has(fullPath)) {
    fs.unlinkSync(fullPath);
    deletedCount++;
  }
}

return [{ json: { deletedCount, totalOnDisk: diskFiles.length } }];
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| rule.interval | — | Interval-based schedule |
| rule.cronExpression | — | Cron-based schedule |
| timezone | UTC | Execution timezone |

## Common Mistakes

### Wrong: Full sync every run
```text
Schedule → GET /api/all-data → Truncate table → Insert all
```

### Correct: Incremental with watermark
```text
Schedule → GET /api/data?since=watermark → Upsert new/changed only
```

### Wrong: No idempotency
Processing same item twice creates duplicates.

### Correct: Upsert with unique key
Always use `conflictColumns` on upsert to handle re-processing.

## See Also

- [database-operations](database-operations.md) — DB read/write patterns
- [error-handling](error-handling.md) — Scheduled job error recovery
- [api-integration](api-integration.md) — Fetching data on schedule
