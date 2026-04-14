# n8n Quick Reference

> Fast lookup tables. For code examples, see linked files.

## Trigger Types

| Trigger | When to Use | Frequency |
|---------|-------------|-----------|
| Webhook | External events (API calls, form submissions) | On-demand |
| Schedule | Recurring tasks (ETL, sync, cleanup) | Cron/interval |
| Manual | Testing, one-off runs | On-click |
| Polling | Watch for changes (email, RSS, files) | Interval |

## Common Nodes

| Node | Purpose | Key Config |
|------|---------|------------|
| HTTP Request | Call REST APIs | method, url, authentication |
| Code | Custom JS/Python logic | language, code |
| Set | Map/transform fields | assignments |
| IF | Conditional branching | conditions |
| Switch | Multi-branch routing | rules |
| Merge | Combine data streams | mode (append/combine/chooseBranch) |
| Split in Batches | Process items in chunks | batchSize |
| Postgres/MySQL | Database operations | operation, query |
| Slack | Send messages/alerts | channel, text |

## Expression Syntax

| Expression | Returns |
|------------|---------|
| `{{ $json.field }}` | Current item field |
| `{{ $input.all() }}` | All input items |
| `{{ $node["Name"].json }}` | Output of named node |
| `{{ $env.VAR_NAME }}` | Environment variable |
| `{{ DateTime.now() }}` | Current timestamp |
| `{{ $items().length }}` | Item count |
| `{{ $json.field ?? "default" }}` | With fallback |

## Workflow Patterns

| Pattern | Nodes | Use Case |
|---------|-------|----------|
| Webhook → Process → Respond | 3-5 | API endpoints, callbacks |
| Schedule → Fetch → Transform → Store | 4-6 | ETL, data sync |
| Trigger → AI Agent → Output | 3-5 | Chatbots, smart processing |
| Main Flow + Error Handler | 5-10 | Production workflows |

## Decision Matrix

| Need | Choose |
|------|--------|
| Transform data | Set node (simple) or Code node (complex) |
| Branch logic | IF (2 paths) or Switch (3+ paths) |
| Combine data | Merge node (mode depends on use case) |
| Process large lists | Split in Batches + loop |
| External API | HTTP Request (generic) or dedicated node |
| Custom logic | Code node (JS preferred, Python available) |

## Common Pitfalls

| Don't | Do |
|-------|-----|
| Hardcode credentials | Use n8n Credential system |
| Build 20+ node workflows | Split into sub-workflows |
| Ignore errors | Add Error Trigger workflow |
| Use Code for everything | Prefer native nodes |
| Skip testing | Use Manual Trigger for dev |
