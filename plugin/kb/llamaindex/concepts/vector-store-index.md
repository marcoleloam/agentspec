# VectorStoreIndex

> **Purpose**: Bridge between LlamaIndex documents and Qdrant via StorageContext
> **Confidence**: 0.95
> **MCP Validated**: 2026-04-12

## Overview

`VectorStoreIndex` embeds documents and stores the resulting vectors in a vector database. The connection to external stores (Qdrant, Pinecone, Weaviate) is established through `StorageContext`, which wraps a `VectorStore` adapter. Two entry points: `from_documents` (build new index) and `from_vector_store` (query existing collection without re-indexing).

## The Pattern

```python
import qdrant_client
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.vector_stores.qdrant import QdrantVectorStore

# Connect to Qdrant
client = qdrant_client.QdrantClient(url="http://localhost:6333")
vector_store = QdrantVectorStore(client=client, collection_name="shopagent_reviews")
storage_context = StorageContext.from_defaults(vector_store=vector_store)

# Build NEW index (embeds + stores in Qdrant)
index = VectorStoreIndex.from_documents(
    documents,
    storage_context=storage_context,
    show_progress=True,
)

# Load EXISTING index (no re-indexing — query only)
loaded_index = VectorStoreIndex.from_vector_store(vector_store)
```

## Quick Reference

| Method | Input | When to Use |
|--------|-------|-------------|
| `from_documents(docs, storage_context)` | List[Document] | First-time indexing — embeds and stores |
| `from_vector_store(vector_store)` | VectorStore | Querying existing collection — no re-embedding |
| `storage_context.from_defaults(vector_store=vs)` | VectorStore | Create context wrapping external store |

## StorageContext Flow

```
Documents ──> VectorStoreIndex.from_documents()
                    │
                    ├── Settings.embed_model (generates embeddings)
                    │
                    └── StorageContext
                            │
                            └── QdrantVectorStore
                                    │
                                    └── Qdrant (localhost:6333)
```

## Common Mistakes

### Wrong

```python
# Missing storage_context — vectors stored in memory, NOT Qdrant
index = VectorStoreIndex.from_documents(documents)
# Data lost when process exits!
```

### Correct

```python
# Always pass storage_context for external stores
vector_store = QdrantVectorStore(client=client, collection_name="reviews")
storage_context = StorageContext.from_defaults(vector_store=vector_store)
index = VectorStoreIndex.from_documents(documents, storage_context=storage_context)
# Vectors persisted in Qdrant
```

## Related

- [Settings](../concepts/settings.md)
- [Query Engine](../concepts/query-engine.md)
- [JSONL to Qdrant Pattern](../patterns/jsonl-to-qdrant.md)
