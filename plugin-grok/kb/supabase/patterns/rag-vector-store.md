# RAG Vector Store

> **Purpose**: Complete RAG (Retrieval-Augmented Generation) pipeline using Supabase pgvector
> **MCP Validated**: 2026-02-19

## When to Use

- Building AI chatbots that need document/product knowledge
- Semantic search over documents, FAQs, or knowledge bases
- Any LLM application requiring external knowledge retrieval
- Hybrid search combining semantic similarity with metadata filtering

## Implementation

### SQL Schema and Match Function

```sql
-- 1. Enable pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Create documents table with vector column
CREATE TABLE public.documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  source TEXT DEFAULT 'manual',
  category TEXT DEFAULT 'general',
  metadata JSONB DEFAULT '{}',
  embedding vector(1536),  -- text-embedding-3-small (cost-effective)
  token_count INT,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- 3. Create HNSW index (default choice, works on empty tables)
CREATE INDEX idx_documents_embedding ON public.documents
  USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);

-- 4. Supporting indexes for filtered search
CREATE INDEX idx_documents_category ON public.documents (category);
CREATE INDEX idx_documents_source ON public.documents (source);

-- 5. Match function with optional filters
CREATE OR REPLACE FUNCTION match_documents(
  query_embedding vector(1536),
  filter_category TEXT DEFAULT NULL,
  match_threshold FLOAT DEFAULT 0.78,
  match_count INT DEFAULT 5
)
RETURNS TABLE (
  id UUID,
  title TEXT,
  content TEXT,
  category TEXT,
  metadata JSONB,
  similarity FLOAT
)
LANGUAGE plpgsql AS $$
BEGIN
  RETURN QUERY
  SELECT
    d.id, d.title, d.content, d.category, d.metadata,
    1 - (d.embedding <=> query_embedding) AS similarity
  FROM public.documents d
  WHERE 1 - (d.embedding <=> query_embedding) > match_threshold
    AND (filter_category IS NULL OR d.category = filter_category)
  ORDER BY d.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- 6. RLS policies
ALTER TABLE public.documents ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public read access" ON public.documents
  FOR SELECT USING (true);

CREATE POLICY "Service role write access" ON public.documents
  FOR ALL USING (auth.role() = 'service_role');
```

### TypeScript: Insert Embeddings

```typescript
import { createClient } from '@supabase/supabase-js'
import OpenAI from 'openai'

const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
)
const openai = new OpenAI()

async function insertDocument(
  title: string,
  content: string,
  category: string = 'general'
) {
  // Generate embedding
  const { data } = await openai.embeddings.create({
    model: 'text-embedding-3-small',
    input: content,
  })
  const embedding = data[0].embedding

  // Insert into Supabase
  const { error } = await supabase.from('documents').insert({
    title,
    content,
    category,
    embedding,
    token_count: content.split(/\s+/).length,
  })

  if (error) throw error
}
```

### TypeScript: Query for RAG Context

```typescript
async function searchDocuments(
  query: string,
  category?: string,
  limit: number = 5
) {
  // Generate query embedding
  const { data } = await openai.embeddings.create({
    model: 'text-embedding-3-small',
    input: query,
  })
  const queryEmbedding = data[0].embedding

  // Search via match function
  const { data: matches, error } = await supabase.rpc('match_documents', {
    query_embedding: queryEmbedding,
    filter_category: category ?? null,
    match_threshold: 0.78,
    match_count: limit,
  })

  if (error) throw error
  return matches
}

// Build RAG context for LLM prompt
async function buildRAGContext(userQuery: string): Promise<string> {
  const matches = await searchDocuments(userQuery, null, 3)
  return matches
    .map((m: any) => `[${m.title}] (score: ${m.similarity.toFixed(2)})\n${m.content}`)
    .join('\n\n---\n\n')
}
```

### Python: Insert and Query

```python
from supabase import create_client
from openai import OpenAI

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
openai_client = OpenAI()

def get_embedding(text: str) -> list[float]:
    response = openai_client.embeddings.create(
        model="text-embedding-3-small", input=text
    )
    return response.data[0].embedding

def search_documents(query: str, category: str = None, limit: int = 5):
    embedding = get_embedding(query)
    result = supabase.rpc("match_documents", {
        "query_embedding": embedding,
        "filter_category": category,
        "match_threshold": 0.78,
        "match_count": limit,
    }).execute()
    return result.data
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| Embedding model | `text-embedding-3-small` | OpenAI model (1536 dimensions, cost-effective) |
| Vector dimensions | `1536` | Must match embedding model output exactly |
| Distance function | Cosine (`<=>`) | Best for text similarity |
| Index type | HNSW | Default choice, auto-optimizes |
| `m` (HNSW) | 16 | Max connections per node |
| `ef_construction` | 64 | Build-time search depth |
| `match_threshold` | 0.78 | Minimum similarity score (0-1) |
| `match_count` | 5 | Maximum results to return |

## See Also

- [pgvector Fundamentals](../concepts/pgvector-fundamentals.md)
- [Multi-Tenant RLS](../patterns/multi-tenant-rls.md)
- [Webhook Edge Function](../patterns/webhook-edge-function.md)
