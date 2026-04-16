# Qdrant Quick Reference

> **MCP Validated:** 2026-02-24

## REST API Endpoints

| Operation | Method | Endpoint |
|-----------|--------|----------|
| Create collection | PUT | `/collections/{name}` |
| Delete collection | DELETE | `/collections/{name}` |
| Upsert points | PUT | `/collections/{name}/points` |
| Search | POST | `/collections/{name}/points/search` |
| Delete points | POST | `/collections/{name}/points/delete` |
| Get point | GET | `/collections/{name}/points/{id}` |
| Collection info | GET | `/collections/{name}` |
| List collections | GET | `/collections` |

## Create Collection (3072 dims, cosine)
```json
PUT /collections/ai-sdr-kb
{ "vectors": { "size": 3072, "distance": "Cosine" } }
```

## Upsert Points
```json
PUT /collections/ai-sdr-kb/points
{ "points": [{ "id": "uuid-here", "vector": [0.1, 0.2, ...],
    "payload": { "content": "text", "product_id": "slug", "content_type": "description",
      "is_active": true, "version": 2 } }] }
```

## Search with Filter
```json
POST /collections/ai-sdr-kb/points/search
{ "vector": [0.1, 0.2, ...], "limit": 5, "score_threshold": 0.72,
  "filter": { "must": [
    { "key": "is_active", "match": { "value": true } },
    { "key": "product_id", "match": { "value": "bootcamp-zero-prod-claude-code" } }
  ] }, "with_payload": true }
```

## Delete by Filter
```json
POST /collections/ai-sdr-kb/points/delete
{ "filter": { "must": [
    { "key": "product_id", "match": { "value": "bootcamp-zero-prod-claude-code" } }
] } }
```

## n8n Qdrant Vector Store Node

### Credential Setup

- Type: `qdrantApi`
- URL: `https://{cluster-id}.{region}.gcp.cloud.qdrant.io:6333` (Cloud) or `http://localhost:6333`
- API Key: from Qdrant Cloud dashboard

### Insert Mode

- Operation: Insert Documents
- Collection: `ai-sdr-kb`
- Connects to: Embeddings sub-node (OpenAI)

### AI Agent Tool Mode

- Operation: Retrieve Documents (as Tool for AI Agent)
- Collection: `ai-sdr-kb`
- Top K: 5
- Connects to: AI Agent's tool connector

## Payload Filtering Operators

| Operator | Example |
| -------- | ------- |
| `match` (exact) | `{"key": "content_type", "match": {"value": "pricing"}}` |
| `range` | `{"key": "version", "range": {"gte": 2}}` |
| `must` (AND) | `{"must": [filter1, filter2]}` |
| `should` (OR) | `{"should": [filter1, filter2]}` |
| `must_not` (NOT) | `{"must_not": [filter1]}` |

## Quantization (Cost Optimization)

```json
PUT /collections/ai-sdr-kb
{ "vectors": { "size": 3072, "distance": "Cosine" },
  "quantization_config": { "scalar": { "type": "int8", "always_ram": true } } }
```

Scalar quantization: 4x compression, ~99% accuracy with rescoring.

## Payload Index Types
`keyword`, `integer`, `float`, `bool`, `geo`, `datetime`, `text` (full-text)

## Distance Metrics
Cosine (text), Euclidean (images), Dot Product (pre-normalized), Manhattan (sparse)
