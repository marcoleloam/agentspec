# JSONL to Qdrant

> **Purpose**: Ingest ShopAgent reviews JSONL → FastEmbed embeddings → Qdrant collection via LlamaIndex
> **MCP Validated**: 2026-04-12

## When to Use

- Day 2 RAG pipeline: loading ShadowTraffic-generated reviews into Qdrant
- Building semantic search over e-commerce review text
- Any JSONL-to-vector-store ingestion with local embeddings (no API key required)

## Implementation

```python
"""ShopAgent Day 2: Ingest reviews JSONL into Qdrant via LlamaIndex."""
import qdrant_client
from llama_index.core import VectorStoreIndex, StorageContext, Settings
from llama_index.embeddings.fastembed import FastEmbedEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.readers.json import JSONReader


def ingest_reviews(
    jsonl_path: str = "./data/reviews/reviews.jsonl",
    qdrant_url: str = "http://localhost:6333",
    collection_name: str = "shopagent_reviews",
) -> VectorStoreIndex:
    """Load JSONL reviews, embed with FastEmbed, store in Qdrant.

    Args:
        jsonl_path: Path to ShadowTraffic-generated reviews JSONL.
        qdrant_url: Qdrant server URL (local Docker or cloud).
        collection_name: Target Qdrant collection name.

    Returns:
        VectorStoreIndex ready for querying.
    """
    # 1. Configure local embeddings (768 dims, no API key needed)
    Settings.embed_model = FastEmbedEmbedding(model_name="BAAI/bge-base-en-v1.5")

    # 2. Load JSONL — one Document per review line
    reader = JSONReader(is_jsonl=True, clean_json=True)
    documents = reader.load_data(input_file=jsonl_path)
    print(f"Loaded {len(documents)} reviews from {jsonl_path}")

    # 3. Connect to Qdrant
    client = qdrant_client.QdrantClient(url=qdrant_url)
    vector_store = QdrantVectorStore(
        client=client,
        collection_name=collection_name,
    )
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    # 4. Build index — embeds all documents and stores in Qdrant
    index = VectorStoreIndex.from_documents(
        documents,
        storage_context=storage_context,
        show_progress=True,
    )
    print(f"Indexed {len(documents)} reviews into Qdrant collection '{collection_name}'")

    return index


def query_reviews(
    question: str,
    qdrant_url: str = "http://localhost:6333",
    collection_name: str = "shopagent_reviews",
    top_k: int = 5,
) -> str:
    """Query existing Qdrant collection without re-indexing."""
    Settings.embed_model = FastEmbedEmbedding(model_name="BAAI/bge-base-en-v1.5")
    client = qdrant_client.QdrantClient(url=qdrant_url)
    vector_store = QdrantVectorStore(client=client, collection_name=collection_name)

    # Load from existing — NO re-embedding
    index = VectorStoreIndex.from_vector_store(vector_store)
    query_engine = index.as_query_engine(similarity_top_k=top_k)
    response = query_engine.query(question)

    return str(response)


if __name__ == "__main__":
    # Ingest
    index = ingest_reviews()

    # Query
    engine = index.as_query_engine(similarity_top_k=5)
    response = engine.query("Clientes reclamando de entrega")
    print(f"\nAnswer: {response.response}")
    print(f"\nSources ({len(response.source_nodes)} chunks):")
    for node in response.source_nodes:
        print(f"  [{node.score:.3f}] {node.text[:80]}...")
```

## Configuration

| Setting | Value | Description |
|---------|-------|-------------|
| `collection_name` | `"shopagent_reviews"` | Qdrant collection for reviews |
| `embed_model` | `BAAI/bge-base-en-v1.5` | 768 dims, local, no API key |
| `similarity_top_k` | `5` | Chunks retrieved per query |
| `qdrant_url` (local) | `http://localhost:6333` | Docker Qdrant (Days 1-3) |
| `qdrant_url` (cloud) | `https://xxx.cloud.qdrant.io:6333` | Qdrant Cloud (Day 4) |

## Example Usage

```python
# Day 2: Ingest + query
index = ingest_reviews("./data/reviews/reviews.jsonl")
engine = index.as_query_engine(similarity_top_k=5)

# Semantic search examples
print(engine.query("Clientes reclamando de entrega"))
print(engine.query("Reviews positivos sobre qualidade"))
print(engine.query("Problemas com pagamento via boleto"))
```

## See Also

- [RAG Query Pipeline](../patterns/rag-query-pipeline.md)
- [VectorStoreIndex](../concepts/vector-store-index.md)
- [Qdrant Reviews Collection](../../qdrant/patterns/shopagent-reviews-collection.md)
