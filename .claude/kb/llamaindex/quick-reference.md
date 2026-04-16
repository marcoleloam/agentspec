# LlamaIndex Quick Reference

> Fast lookup tables. For code examples, see linked files.

## Installation

```bash
pip install llama-index \
  llama-index-vector-stores-qdrant \
  llama-index-embeddings-fastembed \
  llama-index-readers-json
```

## Core Objects

| Object | Import | Purpose |
|--------|--------|---------|
| `Settings` | `llama_index.core` | Global config: embed_model, llm, chunk_size |
| `SimpleDirectoryReader` | `llama_index.core` | Load all files from a directory |
| `JSONReader` | `llama_index.readers.json` | Load JSON/JSONL files (set `is_jsonl=True`) |
| `VectorStoreIndex` | `llama_index.core` | Build/query index over vector store |
| `StorageContext` | `llama_index.core` | Bridge to external vector stores |
| `QdrantVectorStore` | `llama_index.vector_stores.qdrant` | Qdrant vector store adapter |
| `FastEmbedEmbedding` | `llama_index.embeddings.fastembed` | Local embedding model (no API key) |

## Settings Fields

| Field | Default | Description |
|-------|---------|-------------|
| `embed_model` | OpenAI | Embedding model — use `FastEmbedEmbedding` for local |
| `llm` | OpenAI GPT-3.5 | LLM for response synthesis |
| `chunk_size` | 1024 | Tokens per chunk when splitting documents |
| `chunk_overlap` | 20 | Overlap tokens between adjacent chunks |
| `num_output` | 256 | Max tokens for LLM response |

## Response Modes

| Mode | Behavior | Use Case |
|------|----------|----------|
| `default` (refine) | Iteratively refine answer through each chunk | Best quality, slower |
| `compact` | Stuff max chunks into one prompt | Good balance, faster |
| `tree_summarize` | Hierarchical summarization of chunks | Long documents |
| `no_text` | Return retrieved nodes only, no synthesis | Debugging retrieval |
| `accumulate` | Concatenate answers from each chunk | When all chunks matter |

## Decision Matrix

| Use Case | Choose |
|----------|--------|
| Generic files (txt, pdf, csv) | `SimpleDirectoryReader("./data/")` |
| JSONL files (reviews, logs) | `JSONReader(is_jsonl=True)` |
| Build new index from documents | `VectorStoreIndex.from_documents(docs, storage_context=sc)` |
| Query existing Qdrant collection | `VectorStoreIndex.from_vector_store(vector_store)` |
| Local embeddings (no API key) | `FastEmbedEmbedding(model_name="BAAI/bge-base-en-v1.5")` → 768 dims |

## Common Pitfalls

| Don't | Do |
|-------|-----|
| Set `Settings.embed_model` after building index | Configure `Settings` at module load, before any index operations |
| Use `SimpleDirectoryReader` for JSONL | Use `JSONReader(is_jsonl=True)` — splits per line into separate docs |
| Call `from_documents` without `storage_context` | Always pass `storage_context` to route to Qdrant (not in-memory) |
| Ignore `response.source_nodes` | Check `source_nodes` to verify retrieval quality and debug |
| Re-index on every query | Use `from_vector_store()` to load existing collection |

## Related Documentation

| Topic | Path |
|-------|------|
| Settings | `concepts/settings.md` |
| Readers | `concepts/readers.md` |
| VectorStoreIndex | `concepts/vector-store-index.md` |
| QueryEngine | `concepts/query-engine.md` |
| JSONL to Qdrant | `patterns/jsonl-to-qdrant.md` |
| Full Index | `index.md` |
