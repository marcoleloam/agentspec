# n8n RAG Pipeline with Qdrant

> **MCP Validated:** 2026-02-24

## Ingestion Pattern (WF0)
```
Load Data -> Parse Chunks -> Generate Embeddings (OpenAI) ->
  HTTP Request (PUT /collections/{name}/points) -> Validate
```

### Delete old points before insert
```javascript
// HTTP Request: POST /collections/ai-sdr-kb/points/delete
{
  "filter": {
    "must": [
      { "key": "product_id", "match": { "value": "bootcamp-zero-prod-claude-code" } }
    ]
  }
}
```

### Upsert new points
```javascript
// HTTP Request: PUT /collections/ai-sdr-kb/points
{
  "points": chunks.map(chunk => ({
    id: crypto.randomUUID(),
    vector: chunk.embedding,
    payload: {
      content: chunk.content,
      product_id: chunk.slug,
      content_type: chunk.content_type,
      section_heading: chunk.section_heading,
      metadata: {
        chunk_order: chunk.chunk_order,
        token_estimate: chunk.token_estimate
      },
      version: chunk.version,
      is_active: true
    }
  }))
}
```

## Retrieval Pattern (WF1A)
Use n8n's native Qdrant Vector Store node in "Retrieve Documents (as Tool for AI Agent)" mode:
```
AI Agent -> [tool connector] -> Qdrant Vector Store (Tool mode)
                                     |
                              OpenAI Embeddings (sub-node)
```

### Node Configuration
- Collection: `ai-sdr-kb`
- Top K: 5
- Metadata Filter: `is_active = true` (optional -- all points should be active)

## n8n HTTP Request Node for Qdrant API

### Headers
```
Content-Type: application/json
api-key: {{$credentials.qdrantApi.apiKey}}
```

### Base URL Pattern
```
https://{cluster-id}.{region}.gcp.cloud.qdrant.io:6333
```

### Search via HTTP Request (when native node is insufficient)
```javascript
// POST /collections/ai-sdr-kb/points/search
{
  "vector": $json.embedding,
  "limit": 5,
  "score_threshold": 0.72,
  "filter": {
    "must": [
      { "key": "is_active", "match": { "value": true } },
      { "key": "product_id", "match": { "value": $json.product_id } }
    ]
  },
  "with_payload": true
}
```

## Collection Health Check Pattern
```javascript
// GET /collections/ai-sdr-kb
// Response includes:
// - points_count: total points
// - indexed_vectors_count: indexed points
// - status: "green" | "yellow" | "red"
```

## Key Difference from Supabase
- No SQL functions needed (no match_documents, no PostgREST)
- No PGRST202 errors (direct API, not function resolution by parameter names)
- No dimension limits (65,535 vs pgvector's 2,000)
- Metadata filtering is native (payload filters, not SQL WHERE)
- No RLS complexity (API key + payload filtering for multi-tenancy)
- Built-in quantization (no extension management)

## Migration from Supabase pgvector

### Steps
1. Export existing vectors from Supabase (SELECT id, content, embedding, metadata)
2. Create Qdrant collection with matching dimensions
3. Create payload indexes on frequently filtered fields
4. Batch upsert points (recommend batches of 100-500)
5. Update n8n workflow: replace Supabase Vector Store node with Qdrant Vector Store node
6. Update retrieval: swap match_documents SQL for Qdrant search API
7. Test score thresholds (Qdrant cosine scores may differ slightly from pgvector)

### Batch Upsert for Large Datasets
```javascript
// Process in batches of 100
const BATCH_SIZE = 100;
for (let i = 0; i < points.length; i += BATCH_SIZE) {
  const batch = points.slice(i, i + BATCH_SIZE);
  // PUT /collections/ai-sdr-kb/points
  // { "points": batch }
}
```
