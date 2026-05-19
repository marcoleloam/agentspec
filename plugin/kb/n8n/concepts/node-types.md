# Node Types

> **Purpose**: Node categories, configuration patterns, operation-aware setup
> **Confidence**: 0.90
> **MCP Validated**: 2026-04-14

## Overview

n8n nodes fall into four categories: triggers, actions, transformations, and flow control. Each node type has operation-aware configuration — fields change based on the selected operation.

## Trigger Nodes

| Node | Config | Use Case |
|------|--------|----------|
| Webhook | httpMethod, path, responseMode | API endpoints, callbacks |
| Schedule Trigger | rule (cron/interval) | Recurring tasks |
| Manual Trigger | — | Testing |
| Email Trigger (IMAP) | host, mailbox, action | Email processing |

## Action Nodes

| Node | Key Operations | Config |
|------|---------------|--------|
| HTTP Request | GET/POST/PUT/DELETE | url, authentication, headers, body |
| Postgres | select, insert, update, upsert, delete | schema, table, columns |
| Slack | sendMessage, getChannel, updateMessage | channel, text, blocks |
| Google Sheets | append, read, update, clear | spreadsheetId, sheetName, range |

## Transformation Nodes

### Set Node (Data Mapping)
```json
{
  "assignments": [
    { "name": "fullName", "value": "={{ $json.first }} {{ $json.last }}" },
    { "name": "timestamp", "value": "={{ DateTime.now().toISO() }}" }
  ]
}
```

### Code Node (Custom Logic)
```javascript
// JavaScript mode
const items = $input.all();
return items.map(item => ({
  json: {
    ...item.json,
    processed: true,
    score: item.json.value * 1.5,
  }
}));
```

### IF Node (Conditional)
```json
{
  "conditions": {
    "options": { "caseSensitive": true },
    "combinator": "and",
    "conditions": [
      { "leftValue": "={{ $json.status }}", "rightValue": "active", "operator": { "type": "string", "operation": "equals" } }
    ]
  }
}
```

### Switch Node (Multi-Branch)
Routes items to different outputs based on rules. Each rule defines an output branch.

### Merge Node
| Mode | Behavior |
|------|----------|
| Append | Concatenate all inputs |
| Combine | Match items by field (join) |
| Choose Branch | Pick one input based on condition |

## Flow Control Nodes

| Node | Purpose |
|------|---------|
| Split in Batches | Process N items at a time (pagination, rate limiting) |
| Wait | Pause execution (delay, webhook resume) |
| Execute Workflow | Call sub-workflow |
| No Operation | Pass-through (for branching clarity) |

## Operation-Aware Configuration

Fields change based on selected operation:
```text
Postgres Node:
  operation: "select"  → shows: schema, table, where, limit, sort
  operation: "insert"  → shows: schema, table, columns, values
  operation: "upsert"  → shows: schema, table, columns, conflictKey
```

Use `mcp__n8n-mcp__get_node` with `detail: "standard"` to discover fields per operation.

## Common Mistakes

### Wrong: Code node for simple mapping
```javascript
return items.map(i => ({ json: { name: i.json.firstName + ' ' + i.json.lastName } }));
```

### Correct: Set node with expression
```json
{ "name": "fullName", "value": "={{ $json.firstName }} {{ $json.lastName }}" }
```

## Related

- [workflow-fundamentals](workflow-fundamentals.md) — Core workflow concepts
- [expressions-data](expressions-data.md) — Expression syntax
