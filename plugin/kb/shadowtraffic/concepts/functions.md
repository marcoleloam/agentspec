# Functions

> **Purpose**: Built-in _gen functions that produce realistic synthetic values
> **Confidence**: 0.95
> **MCP Validated**: 2026-04-12

## Overview

Every field in a ShadowTraffic generator uses `{"_gen": "functionName", ...params}` to produce data. Functions range from simple scalars (uuid, boolean) to relational references (lookup) and text generation (string with Faker expressions). Function modifiers like `decimals` and `cast` control output formatting.

## The Pattern

```json
{
  "table": "orders",
  "vars": {
    "customerId": { "_gen": "lookup", "topic": "customers", "path": ["row", "customer_id"] }
  },
  "row": {
    "order_id": { "_gen": "uuid" },
    "customer_id": { "_gen": "var", "var": "customerId" },
    "total": { "_gen": "uniformDistribution", "bounds": [29.90, 999.90], "decimals": 2 },
    "qty": { "_gen": "uniformDistribution", "bounds": [1, 10], "decimals": 0 },
    "status": {
      "_gen": "weightedOneOf",
      "choices": ["delivered", "shipped", "processing", "cancelled"],
      "weights": [0.50, 0.20, 0.20, 0.10]
    },
    "payment": { "_gen": "oneOf", "choices": ["pix", "credit_card", "boleto"] },
    "note": { "_gen": "string", "expr": "Order for #{Name.firstName}" },
    "created_at": { "_gen": "now" }
  }
}
```

## Quick Reference

| Function | Required Params | Output | Notes |
|----------|----------------|--------|-------|
| `uuid` | — | UUID string | `"a1b2c3d4-..."` |
| `oneOf` | `choices[]` | Random element | Uniform distribution |
| `weightedOneOf` | `choices[]`, `weights[]` | Weighted pick | Weights must sum to 1.0 |
| `uniformDistribution` | `bounds:[min,max]` | Random float | Use `decimals` to control precision |
| `normalDistribution` | `mean`, `sd` | Gaussian float | Bell curve around mean |
| `lookup` | `topic`, `path[]` | Value from another generator | FK reference — path varies by connection |
| `string` | `expr` | Faker-templated text | Uses `#{Namespace.method}` syntax |
| `var` | `var` | Named variable value | Reference `vars` block in same generator |
| `now` | `offset` (optional) | ISO timestamp | Offset in ms (e.g., -86400000 = yesterday) |
| `boolean` | — | true/false | Random boolean |
| `sequentialInteger` | `start` (optional) | Auto-increment int | Starts at 0 by default |

## Lookup Path by Connection Type

| Connection | Path Format | Example |
|------------|-------------|---------|
| Postgres | `["row", "field_name"]` | `["row", "customer_id"]` |
| Kafka | `["value", "field_name"]` | `["value", "user_id"]` |
| Filesystem | `["data", "field_name"]` | `["data", "order_id"]` |

**This is the #1 mistake.** The `path` must start with the shape key of the referenced generator.

## Common Mistakes

### Wrong

```json
{ "_gen": "lookup", "topic": "customers", "path": "customer_id" }
```

Path must be an array starting with the shape key, not a plain string.

### Correct

```json
{ "_gen": "lookup", "topic": "customers", "path": ["row", "customer_id"] }
```

Array path: `["row", "customer_id"]` for Postgres generators.

## Related

- [Faker Expressions](../concepts/faker-expressions.md)
- [Generators](../concepts/generators.md)
- [Staged Seeding](../patterns/staged-seeding.md)
