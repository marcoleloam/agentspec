# Generators

> **Purpose**: Define what data ShadowTraffic produces and where it goes
> **Confidence**: 0.95
> **MCP Validated**: 2026-04-12

## Overview

A generator is the fundamental unit of ShadowTraffic. It declares the shape of data — fields with `_gen` functions — and which connection receives the output. The field names vary by connection type: `table`/`row` for Postgres, `topic`/`value` for Kafka, `directory`/`data` for filesystem.

## The Pattern

```json
{
  "generators": [
    {
      "table": "customers",
      "row": {
        "customer_id": { "_gen": "uuid" },
        "name": { "_gen": "string", "expr": "#{Name.fullName}" },
        "email": { "_gen": "string", "expr": "#{Internet.emailAddress}" },
        "segment": { "_gen": "oneOf", "choices": ["premium", "standard", "basic"] }
      },
      "localConfigs": {
        "throttle": 100,
        "maxEvents": 500
      }
    },
    {
      "directory": "/data/reviews",
      "data": {
        "review_id": { "_gen": "uuid" },
        "comment": { "_gen": "string", "expr": "#{Lorem.paragraph}" }
      },
      "localConfigs": {
        "throttle": 500
      },
      "fileConfigs": {
        "fileName": "reviews.jsonl"
      }
    }
  ]
}
```

## Quick Reference

| Field | Connection | Description |
|-------|-----------|-------------|
| `table` | Postgres | Target table name |
| `row` | Postgres | Object with field generators |
| `topic` | Kafka | Target topic name |
| `value` | Kafka | Message payload with field generators |
| `directory` | Filesystem | Output directory path |
| `data` | Filesystem | Record object with field generators |
| `localConfigs.throttle` | All | Milliseconds between events (0 = no delay) |
| `localConfigs.maxEvents` | All | Stop after N events (omit for continuous) |
| `fileConfigs.fileName` | Filesystem | Output filename (e.g., "reviews.jsonl") |

## Common Mistakes

### Wrong

```json
{
  "topic": "customers",
  "value": {
    "name": { "_gen": "string", "expr": "#{Name.fullName}" }
  }
}
```

Using `topic`/`value` with a Postgres connection — data won't reach the database.

### Correct

```json
{
  "table": "customers",
  "row": {
    "name": { "_gen": "string", "expr": "#{Name.fullName}" }
  }
}
```

Use `table`/`row` for Postgres, `topic`/`value` for Kafka, `directory`/`data` for filesystem.

## Related

- [Connections](../concepts/connections.md)
- [Functions](../concepts/functions.md)
- [E-Commerce Postgres Pattern](../patterns/ecommerce-postgres.md)
