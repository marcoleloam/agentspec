# Migration Patterns

> **Purpose**: Version-controlled schema changes for Supabase projects
> **MCP Validated**: 2026-02-19

## When to Use

- Any schema change (tables, indexes, functions, policies)
- Adding or modifying RLS policies
- Enabling extensions (pgvector, pg_cron, etc.)

## Implementation

```sql
-- File: supabase/migrations/20260219000000_initial_schema.sql

-- Extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Tables
CREATE TABLE IF NOT EXISTS public.conversations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  customer_phone TEXT NOT NULL,
  status TEXT DEFAULT 'active',
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_updated_at
  BEFORE UPDATE ON public.conversations
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- RLS
ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;
```

## Configuration

| Convention | Example | Description |
|-----------|---------|-------------|
| File naming | `20260219000000_description.sql` | Timestamp + snake_case description |
| Idempotent | `CREATE IF NOT EXISTS` | Safe to re-run |
| Rollback | Separate `down.sql` or comment | Document how to undo |

## See Also

- [RLS Concept](../concepts/rls.md)
- [pgvector Concept](../concepts/pgvector.md)
