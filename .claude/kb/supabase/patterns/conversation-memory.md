# Conversation Memory Pattern

> **Purpose**: Store and retrieve AI conversation history with vector search for context retrieval
> **MCP Validated**: 2026-02-19

## When to Use

- AI chatbots that need conversation history across sessions
- WhatsApp bots that need to remember previous interactions
- Any conversational AI requiring long-term memory

## Implementation

```sql
-- Conversations table
CREATE TABLE public.conversations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  customer_phone TEXT NOT NULL,
  customer_name TEXT,
  status TEXT DEFAULT 'active' CHECK (status IN ('active', 'closed', 'handoff', 'followup')),
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Messages table with embeddings for semantic search
CREATE TABLE public.messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id UUID REFERENCES public.conversations(id) ON DELETE CASCADE,
  role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
  content TEXT NOT NULL,
  embedding vector(3072),
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes
CREATE INDEX idx_messages_conversation ON public.messages (conversation_id, created_at);
CREATE INDEX idx_messages_embedding ON public.messages
  USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
CREATE INDEX idx_conversations_phone ON public.conversations (customer_phone);

-- Get recent messages (buffer memory)
CREATE OR REPLACE FUNCTION get_recent_messages(
  conv_id UUID,
  message_limit int DEFAULT 20
)
RETURNS TABLE (role TEXT, content TEXT, created_at TIMESTAMPTZ)
LANGUAGE plpgsql AS $$
BEGIN
  RETURN QUERY
  SELECT m.role, m.content, m.created_at
  FROM public.messages m
  WHERE m.conversation_id = conv_id
  ORDER BY m.created_at DESC
  LIMIT message_limit;
END;
$$;

-- Search similar past conversations
CREATE OR REPLACE FUNCTION search_similar_messages(
  query_embedding vector(3072),
  phone TEXT DEFAULT NULL,
  match_threshold float DEFAULT 0.80,
  match_count int DEFAULT 5
)
RETURNS TABLE (content TEXT, role TEXT, similarity float, conversation_id UUID)
LANGUAGE plpgsql AS $$
BEGIN
  RETURN QUERY
  SELECT m.content, m.role,
         1 - (m.embedding <=> query_embedding) as similarity,
         m.conversation_id
  FROM public.messages m
  JOIN public.conversations c ON c.id = m.conversation_id
  WHERE 1 - (m.embedding <=> query_embedding) > match_threshold
    AND (phone IS NULL OR c.customer_phone = phone)
  ORDER BY m.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- RLS
ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;

CREATE POLICY "service_role_conversations" ON public.conversations
  FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "service_role_messages" ON public.messages
  FOR ALL USING (auth.role() = 'service_role');
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `message_limit` | 20 | Buffer memory size (last N messages) |
| `match_threshold` | 0.80 | Similarity threshold for past conversations |
| `match_count` | 5 | Max similar messages to retrieve |

## Example Usage

```typescript
// Store new message with embedding
const embedding = await generateEmbedding(message.content)
await supabase.from('messages').insert({
  conversation_id: convId,
  role: 'user',
  content: message.content,
  embedding
})

// Retrieve recent buffer (last 20 messages)
const { data: recentMessages } = await supabase.rpc('get_recent_messages', {
  conv_id: convId,
  message_limit: 20
})

// Search similar past interactions
const { data: similar } = await supabase.rpc('search_similar_messages', {
  query_embedding: embedding,
  phone: customerPhone,
  match_threshold: 0.80,
  match_count: 5
})
```

## See Also

- [Vector Store RAG Pattern](../patterns/vector-store-rag.md)
- [pgvector Concept](../concepts/pgvector.md)
