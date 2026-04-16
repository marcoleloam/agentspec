# Staged Seeding

> **Purpose**: Use schedule.stages to seed parent tables before child generators with lookup references
> **MCP Validated**: 2026-04-12

## When to Use

- Any generator using `lookup` (FK relationships require referenced data to exist)
- Multi-table seeding where insertion order matters
- Workshop environments that need deterministic data setup before streaming

## Implementation

```json
{
  "generators": [
    {
      "topic": "users",
      "table": "users",
      "row": {
        "user_id": { "_gen": "uuid" },
        "name": { "_gen": "string", "expr": "#{Name.fullName}" }
      },
      "localConfigs": { "maxEvents": 100, "throttle": 0 }
    },
    {
      "topic": "orders",
      "table": "orders",
      "row": {
        "order_id": { "_gen": "uuid" },
        "user_id": {
          "_gen": "lookup",
          "topic": "users",
          "path": ["row", "user_id"]
        },
        "total": { "_gen": "uniformDistribution", "bounds": [10, 500] }
      },
      "localConfigs": { "throttle": 200 }
    }
  ],
  "connections": {
    "pg": {
      "kind": "postgres",
      "connectionConfigs": {
        "host": "postgres",
        "port": 5432,
        "db": "mydb",
        "username": "postgres",
        "password": "postgres"
      },
      "tablePolicy": "dropAndCreate"
    }
  },
  "schedule": {
    "stages": [
      {
        "generators": ["users"],
        "comment": "Stage 0: Seed 100 users — must complete before orders start"
      },
      {
        "generators": ["orders"],
        "comment": "Stage 1: Stream orders with user_id lookup"
      }
    ]
  }
}
```

## How Stages Work

```
Stage 0                          Stage 1
┌─────────────────────┐          ┌─────────────────────┐
│  users generator    │          │  orders generator   │
│  maxEvents: 100     │ ──────>  │  lookup: users      │
│  throttle: 0ms      │ waits    │  throttle: 200ms    │
│  (runs to complete) │          │  (continuous)       │
└─────────────────────┘          └─────────────────────┘

- Stage 0 generators run in PARALLEL with each other
- Stage 0 must COMPLETE (all maxEvents reached) before Stage 1 starts
- Stage 1 generators can lookup any data produced in Stage 0
- Generators in the same stage share execution time
```

## Configuration

| Setting | Description | Example |
|---------|-------------|---------|
| `stages[N].generators` | Array of generator topic names to run in this stage | `["customers", "products"]` |
| `maxEvents` on staged generators | Required for finite stages — defines when stage completes | `500` |
| `throttle: 0` in seeding stages | No delay — seed as fast as possible | Stage 0 seeding |
| `throttle: >0` in streaming stages | Paced output for realistic load | Stage 1 streaming |

## Common Mistakes

### Wrong — No stages with lookup dependencies

```json
{
  "generators": [
    { "topic": "users", "table": "users", "row": { "user_id": { "_gen": "uuid" } } },
    { "topic": "orders", "table": "orders", "row": {
        "user_id": { "_gen": "lookup", "topic": "users", "path": ["row", "user_id"] }
    }}
  ]
}
```

Without stages, both generators start simultaneously — `orders` may try to lookup before any users exist.

### Correct — Stages enforce ordering

```json
{
  "schedule": {
    "stages": [
      { "generators": ["users"] },
      { "generators": ["orders"] }
    ]
  }
}
```

## See Also

- [E-Commerce Postgres Pattern](../patterns/ecommerce-postgres.md)
- [Functions (lookup)](../concepts/functions.md)
