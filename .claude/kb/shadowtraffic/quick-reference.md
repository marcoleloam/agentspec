# ShadowTraffic Quick Reference

> Fast lookup tables. For code examples, see linked files.

## Generator Types

| Connection | Data Key | Shape Key | Example |
|------------|----------|-----------|---------|
| Postgres | `table` | `row` | `{"table": "customers", "row": {...}}` |
| Kafka | `topic` | `value` | `{"topic": "events", "value": {...}}` |
| Filesystem | `directory` | `data` | `{"directory": "/data", "data": {...}}` |

## Connection Kinds

| Kind | Required Fields | Optional |
|------|----------------|----------|
| `postgres` | host, port, db, username, password | `tablePolicy` (dropAndCreate / append) |
| `kafka` | bootstrapServers | schemaRegistryUrl |
| `fileSystem` | _(none)_ | — |

## Core Functions

| Function | Params | Output | Example |
|----------|--------|--------|---------|
| `uuid` | — | UUID string | `{"_gen": "uuid"}` |
| `oneOf` | `choices[]` | Random element | `{"_gen": "oneOf", "choices": ["a","b"]}` |
| `weightedOneOf` | `choices[]`, `weights[]` | Weighted pick | `{"_gen": "weightedOneOf", "choices": [1,2], "weights": [0.7,0.3]}` |
| `uniformDistribution` | `bounds:[min,max]` | Random float | `{"_gen": "uniformDistribution", "bounds": [10, 100]}` |
| `normalDistribution` | `mean`, `sd` | Gaussian float | `{"_gen": "normalDistribution", "mean": 50, "sd": 10}` |
| `lookup` | `topic`, `path[]` | FK reference | `{"_gen": "lookup", "topic": "customers", "path": ["row","customer_id"]}` |
| `string` | `expr` | Faker text | `{"_gen": "string", "expr": "#{Name.fullName}"}` |
| `var` | `var` | Variable ref | `{"_gen": "var", "var": "myVar"}` |
| `now` | `offset` (opt) | ISO timestamp | `{"_gen": "now"}` |

## Faker Expressions (E-Commerce)

| Expression | Example Output |
|------------|---------------|
| `#{Name.fullName}` | Maria Silva |
| `#{Name.firstName}` | Maria |
| `#{Internet.emailAddress}` | maria@example.com |
| `#{Commerce.productName}` | Ergonomic Granite Chair |
| `#{Commerce.department}` | Electronics |
| `#{Address.city}` | São Paulo |
| `#{Address.stateAbbr}` | SP |
| `#{Company.name}` | TechCorp Ltda |
| `#{Lorem.paragraph}` | Realistic text block |
| `#{Lorem.sentence}` | Single sentence |
| `#{PhoneNumber.phoneNumber}` | (11) 98765-4321 |

## Decision Matrix

| Use Case | Choose |
|----------|--------|
| Relational data with SQL queries | Postgres generators (`table`/`row`) |
| Text/review data for RAG | Filesystem generators (`directory`/`data`) → JSONL |
| Foreign key relationships | `lookup` function + `schedule.stages` |
| Realistic names/emails/products | Faker expressions via `string` + `expr` |
| Workshop/dev reset on restart | `tablePolicy: "dropAndCreate"` on connection |
| Weighted distributions | `weightedOneOf` with `weights[]` array |

## Common Pitfalls

| Don't | Do |
|-------|-----|
| `"path": "customer_id"` | `"path": ["row", "customer_id"]` (Postgres lookup) |
| Omit `tablePolicy` (defaults to append) | Set `"tablePolicy": "dropAndCreate"` for dev |
| Multiple `lookup` calls in one generator | Use `vars` to capture one lookup, then `var` to reuse |
| Skip `schedule.stages` with FK dependencies | Seed parent tables in stage 0, stream children in stage 1 |
| Use Python Faker syntax `fake.name()` | Use Java Faker syntax `#{Name.fullName}` |

## Related Documentation

| Topic | Path |
|-------|------|
| Generators | `concepts/generators.md` |
| Connections | `concepts/connections.md` |
| Functions | `concepts/functions.md` |
| Faker Expressions | `concepts/faker-expressions.md` |
| E-Commerce Pattern | `patterns/ecommerce-postgres.md` |
| Full Index | `index.md` |
