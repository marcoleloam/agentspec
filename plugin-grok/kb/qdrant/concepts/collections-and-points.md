# Collections and Points

> **MCP Validated:** 2026-02-24

## Collection
A collection is the primary unit of data organization in Qdrant (analogous to a table in SQL or an index in Elasticsearch).

Each collection has:
- **Vector configuration**: dimensions, distance metric
- **Optional quantization**: scalar (int8), binary, product
- **Shard count**: for distributed deployments
- **Replication factor**: for HA

## Point
A point is a single vector with an associated payload (metadata). Each point has:
- **id**: UUID or unsigned integer
- **vector**: dense float array (e.g., 3072 floats for text-embedding-3-large)
- **payload**: arbitrary JSON metadata (no size limit in software)

## Payload Indexes
Create payload indexes for fields you filter on frequently:
```json
PUT /collections/{name}/index
{
  "field_name": "product_id",
  "field_schema": "keyword"
}
```

Field types: `keyword`, `integer`, `float`, `bool`, `geo`, `datetime`, `text` (full-text)

## Multi-tenancy Pattern
Use payload-based filtering for multi-tenant isolation:
- Store `tenant_id` in payload
- Create payload index on `tenant_id`
- Filter every query by tenant
- Alternative: separate collections per tenant (higher overhead)

## Distance Metrics

| Metric | Use Case | Range |
|--------|----------|-------|
| Cosine | Text embeddings (most common) | 0 to 1 (normalized) |
| Euclidean | Image/audio features | 0 to infinity |
| Dot Product | When vectors are pre-normalized | -infinity to infinity |
| Manhattan | Sparse, high-dimensional data | 0 to infinity |

## Vector Configuration Variants

### Named Vectors (multiple vector types per point)
```json
PUT /collections/multimodal
{
  "vectors": {
    "text": { "size": 3072, "distance": "Cosine" },
    "image": { "size": 512, "distance": "Cosine" }
  }
}
```

### Sparse Vectors (for hybrid search)
```json
PUT /collections/hybrid
{
  "vectors": { "dense": { "size": 3072, "distance": "Cosine" } },
  "sparse_vectors": { "sparse": {} }
}
```

## Indexing

### HNSW (default, used for dense vectors)
- Approximate nearest neighbor search
- Configurable `m` (connections per node, default 16) and `ef_construct` (build quality, default 100)
- Trade-off: higher values = better recall, more memory

### Scalar Quantization
- Reduces memory by 4x (float32 -> int8)
- Minimal accuracy loss with rescoring enabled
- Recommended for large collections (>100k points)
