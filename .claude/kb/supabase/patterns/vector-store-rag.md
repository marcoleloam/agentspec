# Vector Store RAG Pattern

> **Purpose**: Complete RAG (Retrieval-Augmented Generation) setup with Supabase pgvector
> **MCP Validated**: 2026-02-19

## When to Use

- Building AI chatbots that need product/document knowledge
- Semantic search over documents, FAQs, or product catalogs
- Any LLM application that needs external knowledge retrieval

## Implementation

```sql
-- 1. Enable pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Create documents table
CREATE TABLE public.knowledge_base (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  category TEXT DEFAULT 'general',
  metadata JSONB DEFAULT '{}',
  embedding vector(3072),  -- text-embedding-3-large
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- 3. Create HNSW index
CREATE INDEX idx_kb_embedding ON public.knowledge_base
  USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);

-- 4. Category index for filtered search
CREATE INDEX idx_kb_category ON public.knowledge_base (category);

-- 5. Match function with optional category filter
CREATE OR REPLACE FUNCTION match_knowledge(
  query_embedding vector(3072),
  filter_category TEXT DEFAULT NULL,
  match_threshold float DEFAULT 0.78,
  match_count int DEFAULT 5
)
RETURNS TABLE (
  id UUID,
  title TEXT,
  content TEXT,
  category TEXT,
  metadata JSONB,
  similarity float
)
LANGUAGE plpgsql AS $$
BEGIN
  RETURN QUERY
  SELECT kb.id, kb.title, kb.content, kb.category, kb.metadata,
         1 - (kb.embedding <=> query_embedding) as similarity
  FROM public.knowledge_base kb
  WHERE 1 - (kb.embedding <=> query_embedding) > match_threshold
    AND (filter_category IS NULL OR kb.category = filter_category)
  ORDER BY kb.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- 6. RLS (if needed)
ALTER TABLE public.knowledge_base ENABLE ROW LEVEL SECURITY;
CREATE POLICY "public_read" ON public.knowledge_base
  FOR SELECT USING (true);  -- Public knowledge base
CREATE POLICY "admin_write" ON public.knowledge_base
  FOR ALL USING (auth.role() = 'service_role');
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `vector dimensions` | 3072 | Must match embedding model (3072 for text-embedding-3-large) |
| `m` (HNSW) | 16 | Max connections per layer (16-64 typical) |
| `ef_construction` | 64 | Build-time search depth (higher = better quality) |
| `match_threshold` | 0.78 | Minimum similarity score to return |
| `match_count` | 5 | Maximum results to return |

## Example Usage

```typescript
import { createClient } from '@supabase/supabase-js'
import OpenAI from 'openai'

const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
const openai = new OpenAI()

// Generate embedding for query
const { data: [{ embedding }] } = await openai.embeddings.create({
  model: 'text-embedding-3-large',
  input: 'What course teaches traffic strategies?'
})

// Search knowledge base
const { data: matches } = await supabase.rpc('match_knowledge', {
  query_embedding: embedding,
  filter_category: 'products',
  match_threshold: 0.78,
  match_count: 3
})

// Use matches as context for LLM
const context = matches.map(m => m.content).join('\n\n')
```

## See Also

- [pgvector Concept](../concepts/pgvector.md)
- [Conversation Memory Pattern](../patterns/conversation-memory.md)
