# Query Engine

> **Purpose**: Execute natural language queries against indexed data with configurable response synthesis
> **Confidence**: 0.95
> **MCP Validated**: 2026-04-12

## Overview

`QueryEngine` is created from a `VectorStoreIndex` via `as_query_engine()`. It retrieves the top-k most similar chunks, then synthesizes a response using the configured LLM. The `response` object contains both the final text (`.response`) and the retrieved source nodes (`.source_nodes`) for debugging and verification.

## The Pattern

```python
# Create query engine from index
query_engine = index.as_query_engine(
    similarity_top_k=5,
    response_mode="compact",
)

# Execute query
response = query_engine.query("Clientes reclamando de entrega")

# Access results
print(response.response)  # Synthesized answer text

# Access retrieved chunks (for debugging and evaluation)
for node in response.source_nodes:
    print(f"Score: {node.score:.3f}")
    print(f"Text: {node.text[:100]}...")
    print(f"Metadata: {node.metadata}")
    print("---")
```

## Quick Reference

| Parameter | Default | Description |
|-----------|---------|-------------|
| `similarity_top_k` | 2 | Number of chunks to retrieve |
| `response_mode` | `"default"` (refine) | How to synthesize the answer |
| `streaming` | `False` | Stream response tokens |
| `node_postprocessors` | `[]` | Filters applied after retrieval |
| `verbose` | `False` | Print retrieval details |

## Response Object

| Attribute | Type | Description |
|-----------|------|-------------|
| `response.response` | str | Synthesized answer text |
| `response.source_nodes` | List[NodeWithScore] | Retrieved chunks with similarity scores |
| `response.metadata` | dict | Response metadata |
| `node.text` | str | Chunk text content |
| `node.score` | float | Similarity score (0-1 for cosine) |
| `node.metadata` | dict | Document metadata (file path, etc.) |

## Common Mistakes

### Wrong

```python
# Ignoring source_nodes — can't verify what was retrieved
response = query_engine.query("Quem reclama de entrega?")
print(response)  # Only see the answer, not what it's based on
```

### Correct

```python
# Always check source_nodes for retrieval quality
response = query_engine.query("Quem reclama de entrega?")
print(f"Answer: {response.response}")
print(f"Based on {len(response.source_nodes)} chunks:")
for node in response.source_nodes:
    print(f"  [{node.score:.3f}] {node.text[:80]}...")
```

## Related

- [VectorStoreIndex](../concepts/vector-store-index.md)
- [RAG Query Pipeline Pattern](../patterns/rag-query-pipeline.md)
