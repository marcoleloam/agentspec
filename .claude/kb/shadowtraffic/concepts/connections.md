# Connections

> **Purpose**: Configure destination endpoints where ShadowTraffic sends generated data
> **Confidence**: 0.95
> **MCP Validated**: 2026-04-12

## Overview

Connections are named targets in the `connections` object of a ShadowTraffic config. Each connection has a `kind` (postgres, kafka, fileSystem) and connection-specific settings. Generators implicitly route to the connection matching their field type (table/row → postgres).

## The Pattern

```json
{
  "connections": {
    "pg": {
      "kind": "postgres",
      "connectionConfigs": {
        "host": "postgres",
        "port": 5432,
        "db": "shopagent",
        "username": "shopagent",
        "password": "shopagent"
      },
      "tablePolicy": "dropAndCreate"
    },
    "fs": {
      "kind": "fileSystem"
    }
  }
}
```

## Quick Reference

| Kind | Required Fields | Optional Fields |
|------|----------------|-----------------|
| `postgres` | host, port, db, username, password | `tablePolicy` ("dropAndCreate" or "append") |
| `kafka` | bootstrapServers | schemaRegistryUrl, securityProtocol |
| `fileSystem` | _(none)_ | — |
| `s3` | bucket, region | accessKeyId, secretAccessKey |
| `webhook` | url | method, headers |
| `redis` | host, port | password, db |

## tablePolicy

| Value | Behavior | Use Case |
|-------|----------|----------|
| `"dropAndCreate"` | Drop existing table, recreate from generator schema | Workshop/dev — clean reset every run |
| `"append"` (default) | Insert into existing table, keep old data | Production — accumulate data over time |

## Common Mistakes

### Wrong

```json
{
  "connections": {
    "pg": {
      "kind": "postgres",
      "connectionConfigs": {
        "host": "localhost",
        "port": 5432,
        "db": "shopagent"
      }
    }
  }
}
```

Missing `tablePolicy` — data accumulates on every restart. Missing `username`/`password`.

### Correct

```json
{
  "connections": {
    "pg": {
      "kind": "postgres",
      "connectionConfigs": {
        "host": "postgres",
        "port": 5432,
        "db": "shopagent",
        "username": "shopagent",
        "password": "shopagent"
      },
      "tablePolicy": "dropAndCreate"
    }
  }
}
```

Explicit `tablePolicy: "dropAndCreate"` for workshop environments. All auth fields present.

## Related

- [Generators](../concepts/generators.md)
- [E-Commerce Postgres Pattern](../patterns/ecommerce-postgres.md)
