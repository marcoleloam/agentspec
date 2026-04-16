# pgvector - Vector Embeddings in PostgreSQL

> **Purpose**: Store and query vector embeddings for semantic search, RAG, and similarity matching
> **Confidence**: HIGH
> **MCP Validated**: 2026-02-19

## Overview

pgvector is a PostgreSQL extension that adds vector data types and similarity search operators. In Supabase, it enables storing embeddings from LLMs (OpenAI, Anthropic, etc.) and performing fast approximate nearest neighbor (ANN) searches using HNSW or IVFFlat indexes.

## The Pattern

```sql
-- Enable the extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create table with embedding column
CREATE TABLE public.documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  content TEXT NOT NULL,
  metadata JSONB DEFAULT '{}',
  embedding vector(3072),  -- text-embedding-3-large
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Create HNSW index for fast similarity search
CREATE INDEX idx_documents_embedding ON public.documents
  USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);

-- Similarity search function
CREATE OR REPLACE FUNCTION match_documents(
  query_embedding vector(3072),
  match_threshold float DEFAULT 0.78,
  match_count int DEFAULT 5
)
RETURNS TABLE (id UUID, content TEXT, metadata JSONB, similarity float)
LANGUAGE plpgsql AS $$
BEGIN
  RETURN QUERY
  SELECT d.id, d.content, d.metadata,
         1 - (d.embedding <=> query_embedding) as similarity
  FROM public.documents d
  WHERE 1 - (d.embedding <=> query_embedding) > match_threshold
  ORDER BY d.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;
```

## Quick Reference

| Parameter | Recommended | Notes |
|-----------|------------|-------|
| `m` (HNSW) | 16 | Higher = better recall, more memory |
| `ef_construction` | 64 | Higher = better index quality, slower build |
| `match_threshold` | 0.78 | Adjust based on precision needs |
| `vector dimensions` | 3072 | Must match embedding model output |

## Common Mistakes

### Wrong

```sql
-- No index = brute force scan on every query
CREATE TABLE documents (
  id SERIAL, content TEXT, embedding vector(3072)
);
SELECT * FROM documents ORDER BY embedding <=> query LIMIT 5;
```

### Correct

```sql
-- HNSW index = fast approximate nearest neighbor
CREATE INDEX ON documents USING hnsw (embedding vector_cosine_ops);
-- Use match function with threshold
SELECT * FROM match_documents(query_embedding, 0.78, 5);
```

## Related

- [Vector Store RAG Pattern](../patterns/vector-store-rag.md)
- [Conversation Memory Pattern](../patterns/conversation-memory.md)
