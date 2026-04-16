# pgvector Fundamentals

> **Purpose**: Vector data types, distance functions, and index strategies for similarity search in Supabase
> **Confidence**: 0.95
> **MCP Validated**: 2026-02-19

## Overview

pgvector is a PostgreSQL extension that adds vector data types and similarity search operators to Supabase. It enables storing embeddings from LLMs (OpenAI, Cohere, etc.) and performing fast approximate nearest neighbor (ANN) searches. Vectors are stored alongside relational data, enabling hybrid semantic and keyword queries in a single database.

## Vector Data Types

| Type | Max Dimensions | Use Case |
|------|---------------|----------|
| `vector(1536)` | 2,000 | Standard embeddings (text-embedding-3-small) |
| `vector(3072)` | 2,000 | High-accuracy embeddings (text-embedding-3-large) |
| `halfvec(3072)` | 4,000 | Memory-efficient, supports higher dimensions |
| `bit(64000)` | 64,000 | Binary embeddings for fast approximate search |

Common models: text-embedding-3-small (1536, OpenAI), text-embedding-3-large (3072, OpenAI), embed-english-v3.0 (1024, Cohere), all-MiniLM-L6-v2 (384, Sentence Transformers).

## Distance Functions

| Function | Operator | Index Ops Class | Best For |
|----------|----------|-----------------|----------|
| Cosine distance | `<=>` | `vector_cosine_ops` | Text similarity (most common) |
| L2 (Euclidean) | `<->` | `vector_l2_ops` | Image embeddings, spatial data |
| Inner product | `<#>` | `vector_ip_ops` | Normalized vectors, dot product |

Cosine similarity = `1 - (a <=> b)` -- returns 0 to 1, where 1 is identical.

## Index Types

### HNSW (Default Choice)

Hierarchical Navigable Small World graph. Use as your default index.

```sql
CREATE INDEX ON documents
  USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);
```

| Parameter | Default | Description |
|-----------|---------|-------------|
| `m` | 16 | Max connections per node (higher = better recall, more memory) |
| `ef_construction` | 64 | Build-time search depth (higher = better quality, slower build) |

Characteristics: Can be created on empty tables. Auto-optimizes as data is added. Supports parallel builds (pgvector 0.6.2+). Better query performance than IVFFlat.

### IVFFlat (Memory Constrained)

Inverted File with Flat compression. Use when memory is limited and dataset is large.

```sql
CREATE INDEX ON documents
  USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);
```

| Parameter | Default | Recommendation |
|-----------|---------|----------------|
| `lists` | 100 | `rows / 1000` for general use, `rows / 200` for high performance |

Characteristics: Must be created after data is loaded. Requires periodic reindexing as data grows. Lower memory than HNSW but slower queries.

### For High-Dimensional Vectors (> 2000)

Use `halfvec` cast for dimensions exceeding the vector type limit:

```sql
CREATE INDEX ON documents
  USING hnsw ((embedding::halfvec(3072)) halfvec_cosine_ops);
```

## The Pattern

```sql
-- Enable pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Create table with vector column
CREATE TABLE public.documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  content TEXT NOT NULL,
  metadata JSONB DEFAULT '{}',
  embedding vector(1536),
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Create HNSW index
CREATE INDEX ON public.documents
  USING hnsw (embedding vector_cosine_ops);

-- Similarity search function
CREATE OR REPLACE FUNCTION match_documents(
  query_embedding vector(1536),
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

## Common Mistakes

### Wrong

```sql
-- Wrong dimension size: model outputs 1536 but column is 768
CREATE TABLE docs (embedding vector(768));
-- Insert from text-embedding-3-small will FAIL

-- No index: brute force O(n) scan on every query
SELECT * FROM documents ORDER BY embedding <=> query LIMIT 5;
```

### Correct

```sql
-- Match dimensions to your embedding model
CREATE TABLE docs (embedding vector(1536));  -- matches text-embedding-3-small

-- Always create an index (HNSW is the default choice)
CREATE INDEX ON docs USING hnsw (embedding vector_cosine_ops);

-- Use a match function with threshold filtering
SELECT * FROM match_documents(query_embedding, 0.78, 5);
```

## Related

- [RAG Vector Store Pattern](../patterns/rag-vector-store.md)
- [RLS Policies](../concepts/rls-policies.md)
