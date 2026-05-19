# ShadowTraffic Knowledge Base

> **Purpose**: Declarative synthetic data generation for ShopAgent e-commerce pipeline — ShadowTraffic v1.17.0
> **MCP Validated**: 2026-04-12

## Quick Navigation

### Concepts (< 150 lines each)

| File | Purpose |
|------|---------|
| [concepts/generators.md](concepts/generators.md) | Define data shape and destination (table/row, topic/value, directory/data) |
| [concepts/connections.md](concepts/connections.md) | Configure Postgres, Kafka, filesystem endpoints |
| [concepts/functions.md](concepts/functions.md) | Built-in _gen functions: uuid, oneOf, lookup, uniformDistribution |
| [concepts/faker-expressions.md](concepts/faker-expressions.md) | Java Faker expressions for realistic text: names, emails, products |

### Patterns (< 200 lines each)

| File | Purpose |
|------|---------|
| [patterns/ecommerce-postgres.md](patterns/ecommerce-postgres.md) | **KEY**: Full ShopAgent config — customers+products+orders→Postgres, reviews→JSONL |
| [patterns/staged-seeding.md](patterns/staged-seeding.md) | schedule.stages to seed parent tables before child generators |

### Specs (Machine-Readable)

| File | Purpose |
|------|---------|
| [specs/shadowtraffic-config.yaml](specs/shadowtraffic-config.yaml) | Generator, connection, and function field reference |

---

## Quick Reference

- [quick-reference.md](quick-reference.md) - Fast lookup tables

---

## Key Concepts

| Concept | Description |
|---------|-------------|
| **Generator** | Declares data shape (fields with `_gen` functions) and destination connection |
| **Connection** | Named endpoint: Postgres, Kafka, or filesystem with connection-specific config |
| **Function** | Built-in data producers: uuid, oneOf, lookup, uniformDistribution, string+faker |
| **Faker Expression** | Java Faker integration via `#{Namespace.method}` syntax for realistic text |
| **Schedule/Stages** | Ordered execution: seed parent tables before streaming child records |

---

## Learning Path

| Level | Files |
|-------|-------|
| **Beginner** | concepts/generators.md, concepts/connections.md |
| **Intermediate** | concepts/functions.md, concepts/faker-expressions.md |
| **Advanced** | patterns/ecommerce-postgres.md, patterns/staged-seeding.md |

---

## Agent Usage

| Agent | Primary Files | Use Case |
|-------|---------------|----------|
| shopagent-builder | patterns/ecommerce-postgres.md | Generate ShopAgent Day 1 data pipeline |
| ai-data-engineer | concepts/generators.md, concepts/connections.md | Custom data generation configs |
