# LlamaIndex Knowledge Base

> **Purpose**: RAG ingestion and query framework for ShopAgent — JSONL reviews → embeddings → Qdrant via LlamaIndex
> **MCP Validated**: 2026-04-12

## Quick Navigation

### Concepts (< 150 lines each)

| File | Purpose |
|------|---------|
| [concepts/settings.md](concepts/settings.md) | Global Settings: embed_model, llm, chunk_size, chunk_overlap |
| [concepts/readers.md](concepts/readers.md) | SimpleDirectoryReader vs JSONReader for JSONL loading |
| [concepts/vector-store-index.md](concepts/vector-store-index.md) | VectorStoreIndex + StorageContext + QdrantVectorStore bridge |
| [concepts/query-engine.md](concepts/query-engine.md) | as_query_engine(), similarity_top_k, response modes |

### Patterns (< 200 lines each)

| File | Purpose |
|------|---------|
| [patterns/jsonl-to-qdrant.md](patterns/jsonl-to-qdrant.md) | **KEY**: JSONReader → FastEmbed → QdrantVectorStore → QueryEngine |
| [patterns/rag-query-pipeline.md](patterns/rag-query-pipeline.md) | Complete ingest → embed → store → query as reusable functions |

### Specs (Machine-Readable)

| File | Purpose |
|------|---------|
| [specs/llamaindex-config.yaml](specs/llamaindex-config.yaml) | Settings, VectorStoreIndex, QueryEngine, JSONReader field reference |

---

## Quick Reference

- [quick-reference.md](quick-reference.md) - Fast lookup tables

---

## Key Concepts

| Concept | Description |
|---------|-------------|
| **Settings** | Global singleton controlling embed model, LLM, and chunking for all operations |
| **Reader** | Loads files into Document objects — JSONReader for JSONL, SimpleDirectoryReader for generic |
| **VectorStoreIndex** | Embeds documents and stores vectors in an external vector DB via StorageContext |
| **QueryEngine** | Executes natural language queries with configurable retrieval and response synthesis |
| **StorageContext** | Bridge that connects LlamaIndex to external stores (Qdrant, Pinecone, etc.) |

---

## Learning Path

| Level | Files |
|-------|-------|
| **Beginner** | concepts/settings.md, concepts/readers.md |
| **Intermediate** | concepts/vector-store-index.md, concepts/query-engine.md |
| **Advanced** | patterns/jsonl-to-qdrant.md, patterns/rag-query-pipeline.md |

---

## Agent Usage

| Agent | Primary Files | Use Case |
|-------|---------------|----------|
| shopagent-builder | patterns/jsonl-to-qdrant.md | Day 2 RAG pipeline: reviews JSONL → Qdrant |
| ai-data-engineer | concepts/readers.md, concepts/settings.md | Custom ingestion configurations |
