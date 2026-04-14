# Workflow Fundamentals

> **Purpose**: Core n8n concepts — triggers, nodes, connections, data flow
> **Confidence**: 0.90
> **MCP Validated**: 2026-04-14

## Overview

An n8n workflow is a directed graph of nodes connected by edges. Data flows as **items** (JSON objects) from trigger to output. Each node receives items, processes them, and passes results downstream.

## Core Components

### Triggers (Entry Points)

```text
Webhook Trigger  → Receives HTTP requests (POST/GET/PUT/DELETE)
Schedule Trigger → Runs on cron expression or interval
Manual Trigger   → User clicks "Execute" (dev/testing)
Polling Trigger  → Checks source at intervals (email, RSS)
```

### Data Flow Model

```text
┌──────────┐    items[]    ┌──────────┐    items[]    ┌──────────┐
│ Trigger  │──────────────►│ Process  │──────────────►│  Output  │
│          │  [{json:{}}]  │          │  [{json:{}}]  │          │
└──────────┘               └──────────┘               └──────────┘
```

Each item is:
```json
{
  "json": { "name": "John", "email": "john@example.com" },
  "binary": {}
}
```

### Execution Modes

| Mode | Behavior | Use Case |
|------|----------|----------|
| Production | Runs on trigger events | Live workflows |
| Manual | Single execution on click | Testing |
| Test | Runs with test data | Development |

## Node Categories

| Category | Examples | Purpose |
|----------|----------|---------|
| Trigger | Webhook, Schedule, Manual | Start workflow |
| Action | HTTP Request, Slack, Postgres | External operations |
| Transform | Set, Code, IF, Switch | Data manipulation |
| Flow | Merge, Split in Batches, Wait | Control execution |

## Connections

Nodes connect via **output → input** edges. Key rules:
- A node can have multiple outputs (IF, Switch)
- A node can receive from multiple inputs (Merge)
- Data flows left to right by convention
- Each output branch runs independently

## Common Mistakes

### Wrong: One massive workflow
```text
Trigger → 25 nodes in sequence → Output
```

### Correct: Modular sub-workflows
```text
Main:     Trigger → Sub-Workflow 1 → Sub-Workflow 2 → Output
Sub-WF 1: Process data (5-8 nodes)
Sub-WF 2: Send notifications (3-5 nodes)
```

## Related

- [node-types](node-types.md) — Detailed node categories
- [expressions-data](expressions-data.md) — Data access syntax
- [error-handling](../patterns/error-handling.md) — Production error handling
