# RAG Query Pipeline

> **Purpose**: Complete ingest → embed → store → query flow as reusable functions for ShopAgent
> **MCP Validated**: 2026-04-12

## When to Use

- Building modular RAG pipeline with clear separation of ingest vs query
- Reusable across local Docker and Qdrant Cloud (just change URL)
- When you need to query an existing collection without re-indexing

## Implementation

```python
"""ShopAgent RAG pipeline — modular ingest and query functions."""
from pathlib import Path

import qdrant_client
from llama_index.core import VectorStoreIndex, StorageContext, Settings
from llama_index.embeddings.fastembed import FastEmbedEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.readers.json import JSONReader


# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------
EMBED_MODEL = "BAAI/bge-base-en-v1.5"  # 768 dims, local
QDRANT_URL = "http://localhost:6333"     # Docker local (override for cloud)
COLLECTION = "shopagent_reviews"
TOP_K = 5


def _init_settings() -> None:
    """Initialize LlamaIndex global settings."""
    Settings.embed_model = FastEmbedEmbedding(model_name=EMBED_MODEL)


def _get_vector_store(
    qdrant_url: str = QDRANT_URL,
    collection: str = COLLECTION,
) -> QdrantVectorStore:
    """Create Qdrant vector store adapter."""
    client = qdrant_client.QdrantClient(url=qdrant_url)
    return QdrantVectorStore(client=client, collection_name=collection)


# --------------------------------------------------------------------------
# Ingest: JSONL → Qdrant
# --------------------------------------------------------------------------
def ingest(jsonl_path: str, qdrant_url: str = QDRANT_URL) -> int:
    """Ingest JSONL file into Qdrant. Returns document count."""
    _init_settings()
    reader = JSONReader(is_jsonl=True, clean_json=True)
    documents = reader.load_data(input_file=jsonl_path)

    vector_store = _get_vector_store(qdrant_url)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    VectorStoreIndex.from_documents(
        documents, storage_context=storage_context, show_progress=True,
    )
    return len(documents)


# --------------------------------------------------------------------------
# Query: question → answer + sources
# --------------------------------------------------------------------------
def query(
    question: str,
    qdrant_url: str = QDRANT_URL,
    top_k: int = TOP_K,
) -> dict:
    """Query existing Qdrant collection. Returns answer + source chunks."""
    _init_settings()
    vector_store = _get_vector_store(qdrant_url)
    index = VectorStoreIndex.from_vector_store(vector_store)
    engine = index.as_query_engine(similarity_top_k=top_k)
    response = engine.query(question)

    return {
        "answer": str(response),
        "sources": [
            {"text": n.text[:200], "score": n.score, "metadata": n.metadata}
            for n in response.source_nodes
        ],
    }


if __name__ == "__main__":
    # Step 1: Ingest reviews
    count = ingest("./data/reviews/reviews.jsonl")
    print(f"Ingested {count} reviews")

    # Step 2: Query
    result = query("Clientes reclamando de entrega")
    print(f"\nAnswer: {result['answer']}")
    for src in result["sources"]:
        print(f"  [{src['score']:.3f}] {src['text'][:80]}...")
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `EMBED_MODEL` | `"BAAI/bge-base-en-v1.5"` | Local model, 768 dims |
| `QDRANT_URL` | `"http://localhost:6333"` | Override for cloud: `"https://xxx.cloud.qdrant.io:6333"` |
| `COLLECTION` | `"shopagent_reviews"` | Qdrant collection name |
| `TOP_K` | `5` | Chunks retrieved per query |

## Example Usage

```python
# Local development (Days 1-3)
count = ingest("./data/reviews/reviews.jsonl")

# Cloud migration (Day 4) — same code, different URL
count = ingest(
    "./data/reviews/reviews.jsonl",
    qdrant_url="https://xxx.cloud.qdrant.io:6333",
)

# Query with hybrid context (feeds into Supabase SQL)
result = query("Quem reclama de entrega no Sudeste?")
# Use result["sources"] to get customer_ids, then query Postgres for ticket medio
```

## See Also

- [JSONL to Qdrant](../patterns/jsonl-to-qdrant.md)
- [Query Engine](../concepts/query-engine.md)
