# Settings

> **Purpose**: Global configuration controlling embeddings, LLM, and chunking for all LlamaIndex operations
> **Confidence**: 0.95
> **MCP Validated**: 2026-04-12

## Overview

`Settings` is a global singleton that controls default behavior across all LlamaIndex operations. Set `embed_model` to choose the embedding provider, `llm` for response synthesis, and `chunk_size`/`chunk_overlap` for document splitting. For ShopAgent, we use `FastEmbedEmbedding` (BAAI/bge-base-en-v1.5) which runs locally with 768 dimensions and requires no API key.

## The Pattern

```python
from llama_index.core import Settings
from llama_index.embeddings.fastembed import FastEmbedEmbedding

# Configure BEFORE any index operations
Settings.embed_model = FastEmbedEmbedding(model_name="BAAI/bge-base-en-v1.5")
Settings.chunk_size = 512
Settings.chunk_overlap = 50

# Optional: set LLM for response synthesis
# from llama_index.llms.anthropic import Anthropic
# Settings.llm = Anthropic(model="claude-sonnet-4-20250514")
```

## Quick Reference

| Field | Type | Default | ShopAgent Value |
|-------|------|---------|-----------------|
| `embed_model` | BaseEmbedding | OpenAI ada-002 | `FastEmbedEmbedding("BAAI/bge-base-en-v1.5")` → 768 dims |
| `llm` | LLM | OpenAI GPT-3.5 | `Anthropic("claude-sonnet-4-20250514")` |
| `chunk_size` | int | 1024 | 512 (reviews are short) |
| `chunk_overlap` | int | 20 | 50 |
| `num_output` | int | 256 | 256 |
| `context_window` | int | 3900 | 3900 |
| `callback_manager` | CallbackManager | None | Optional: LangFuse callback for observability |

## Common Mistakes

### Wrong

```python
from llama_index.core import VectorStoreIndex, Settings
from llama_index.embeddings.fastembed import FastEmbedEmbedding

# Build index FIRST — uses default OpenAI embeddings
index = VectorStoreIndex.from_documents(documents)

# THEN set embed model — TOO LATE, index already used wrong embeddings
Settings.embed_model = FastEmbedEmbedding(model_name="BAAI/bge-base-en-v1.5")
```

### Correct

```python
from llama_index.core import VectorStoreIndex, Settings
from llama_index.embeddings.fastembed import FastEmbedEmbedding

# Configure FIRST
Settings.embed_model = FastEmbedEmbedding(model_name="BAAI/bge-base-en-v1.5")

# THEN build index — uses correct local embeddings
index = VectorStoreIndex.from_documents(documents)
```

## Related

- [Readers](../concepts/readers.md)
- [VectorStoreIndex](../concepts/vector-store-index.md)
- [JSONL to Qdrant Pattern](../patterns/jsonl-to-qdrant.md)
