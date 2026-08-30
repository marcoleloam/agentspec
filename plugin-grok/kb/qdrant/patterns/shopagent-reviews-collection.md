# ShopAgent Reviews Collection

> **Purpose**: Qdrant collection configuration for ShopAgent e-commerce reviews with payload schema and filtered search
> **MCP Validated**: 2026-04-12

## When to Use

- Setting up Qdrant for Day 2 RAG pipeline
- Configuring the `shopagent_reviews` collection for semantic search on reviews
- Filtered search by rating or sentiment

## Implementation

```python
"""Configure Qdrant collection for ShopAgent reviews."""
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    PayloadSchemaType,
    PointStruct,
    VectorParams,
)

client = QdrantClient(url="http://localhost:6333")

# Create collection — 768 dims matches BAAI/bge-base-en-v1.5
client.recreate_collection(
    collection_name="shopagent_reviews",
    vectors_config=VectorParams(
        size=768,
        distance=Distance.COSINE,
    ),
)

# Create payload indexes for filtered search
client.create_payload_index(
    collection_name="shopagent_reviews",
    field_name="rating",
    field_schema=PayloadSchemaType.INTEGER,
)

client.create_payload_index(
    collection_name="shopagent_reviews",
    field_name="sentiment",
    field_schema=PayloadSchemaType.KEYWORD,
)
```

## Filtered Search Examples

```python
from qdrant_client.models import Filter, FieldCondition, MatchValue, Range

# Negative reviews only (rating <= 2)
negative_filter = Filter(
    must=[FieldCondition(key="rating", range=Range(lte=2))]
)

# Negative sentiment reviews
sentiment_filter = Filter(
    must=[FieldCondition(key="sentiment", match=MatchValue(value="negative"))]
)

results = client.search(
    collection_name="shopagent_reviews",
    query_vector=embedding,
    query_filter=negative_filter,
    limit=10,
    with_payload=True,
)
```

## Configuration

| Setting | Value | Description |
|---------|-------|-------------|
| `collection_name` | `"shopagent_reviews"` | ShopAgent reviews collection |
| `vector_size` | `768` | Matches BAAI/bge-base-en-v1.5 embedding dim |
| `distance` | `Cosine` | Standard for text embeddings |
| Payload: `rating` | integer index | Filter by star rating (1-5) |
| Payload: `sentiment` | keyword index | Filter by positive/neutral/negative |

## See Also

- [Collections and Points](../concepts/collections-and-points.md)
- [LlamaIndex JSONL to Qdrant](../../llamaindex/patterns/jsonl-to-qdrant.md)
