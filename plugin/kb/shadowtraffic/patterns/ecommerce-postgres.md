# E-Commerce Postgres

> **Purpose**: Complete ShopAgent e-commerce data generation — customers+products+orders→Postgres, reviews→JSONL via schedule.stages
> **MCP Validated**: 2026-04-12

## When to Use

- ShopAgent Day 1 data pipeline setup
- Generating relational e-commerce data with foreign key dependencies
- Producing both structured (SQL-queryable) and unstructured (text for RAG) data
- Workshop environment with clean-reset capability

## Implementation

```json
{
  "generators": [
    {
      "topic": "customers",
      "table": "customers",
      "row": {
        "customer_id": { "_gen": "uuid" },
        "name": { "_gen": "string", "expr": "#{Name.fullName}" },
        "email": { "_gen": "string", "expr": "#{Internet.emailAddress}" },
        "city": { "_gen": "string", "expr": "#{Address.city}" },
        "state": {
          "_gen": "oneOf",
          "choices": ["SP", "RJ", "MG", "RS", "PR", "SC", "BA", "PE"]
        },
        "segment": {
          "_gen": "oneOf",
          "choices": ["premium", "standard", "basic"]
        }
      },
      "localConfigs": { "maxEvents": 500, "throttle": 0 }
    },
    {
      "topic": "products",
      "table": "products",
      "row": {
        "product_id": { "_gen": "uuid" },
        "name": { "_gen": "string", "expr": "#{Commerce.productName}" },
        "category": { "_gen": "string", "expr": "#{Commerce.department}" },
        "price": {
          "_gen": "uniformDistribution",
          "bounds": [19.90, 999.90],
          "decimals": 2
        },
        "brand": { "_gen": "string", "expr": "#{Company.name}" }
      },
      "localConfigs": { "maxEvents": 200, "throttle": 0 }
    },
    {
      "topic": "orders",
      "table": "orders",
      "row": {
        "order_id": { "_gen": "uuid" },
        "customer_id": {
          "_gen": "lookup",
          "topic": "customers",
          "path": ["row", "customer_id"]
        },
        "product_id": {
          "_gen": "lookup",
          "topic": "products",
          "path": ["row", "product_id"]
        },
        "qty": {
          "_gen": "uniformDistribution",
          "bounds": [1, 10],
          "decimals": 0
        },
        "total": {
          "_gen": "uniformDistribution",
          "bounds": [29.90, 999.90],
          "decimals": 2
        },
        "status": {
          "_gen": "weightedOneOf",
          "choices": ["delivered", "shipped", "processing", "cancelled"],
          "weights": [0.50, 0.20, 0.20, 0.10]
        },
        "payment": {
          "_gen": "weightedOneOf",
          "choices": ["pix", "credit_card", "boleto"],
          "weights": [0.45, 0.40, 0.15]
        },
        "created_at": { "_gen": "now" }
      },
      "localConfigs": { "throttle": 100 }
    },
    {
      "topic": "reviews",
      "directory": "/data/reviews",
      "data": {
        "review_id": { "_gen": "uuid" },
        "order_id": {
          "_gen": "lookup",
          "topic": "orders",
          "path": ["row", "order_id"]
        },
        "rating": {
          "_gen": "weightedOneOf",
          "choices": [1, 2, 3, 4, 5],
          "weights": [0.05, 0.10, 0.20, 0.30, 0.35]
        },
        "comment": { "_gen": "string", "expr": "#{Lorem.paragraph}" },
        "sentiment": {
          "_gen": "weightedOneOf",
          "choices": ["positive", "neutral", "negative"],
          "weights": [0.35, 0.30, 0.35]
        }
      },
      "localConfigs": { "throttle": 500 },
      "fileConfigs": { "fileName": "reviews.jsonl" }
    }
  ],
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
  },
  "schedule": {
    "stages": [
      {
        "generators": ["customers", "products"],
        "comment": "Stage 0: Seed parent tables first (500 customers + 200 products)"
      },
      {
        "generators": ["orders", "reviews"],
        "comment": "Stage 1: Stream orders with FK lookups + reviews to JSONL"
      }
    ]
  }
}
```

## Configuration

| Entity | maxEvents | Throttle | Destination | Notes |
|--------|-----------|----------|-------------|-------|
| customers | 500 | 0ms | Postgres | Seeded in stage 0 |
| products | 200 | 0ms | Postgres | Seeded in stage 0 |
| orders | continuous | 100ms | Postgres | Streamed in stage 1 with lookup FKs |
| reviews | continuous | 500ms | JSONL file | Streamed in stage 1, ingested by LlamaIndex on Day 2 |

## Example Usage

```bash
# Dev mode — dry run to stdout
docker run --env-file .env \
  -v $(pwd)/shadowtraffic.json:/home/config.json \
  shadowtraffic/shadowtraffic:latest \
  --config /home/config.json --sample 10 --stdout

# Production — stream to Postgres + filesystem
docker run --env-file .env \
  -v $(pwd)/shadowtraffic.json:/home/config.json \
  -v reviews_data:/data/reviews \
  shadowtraffic/shadowtraffic:latest \
  --config /home/config.json
```

## See Also

- [Staged Seeding](../patterns/staged-seeding.md)
- [Connections](../concepts/connections.md)
- [Functions](../concepts/functions.md)
- [Faker Expressions](../concepts/faker-expressions.md)
