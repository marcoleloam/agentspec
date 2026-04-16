# Supabase Quick Reference

> Fast lookup tables. For code examples, see linked files.
> **MCP Validated:** 2026-02-19

## pgvector Operations

| Operation | SQL | Notes |
|-----------|-----|-------|
| Enable extension | `CREATE EXTENSION IF NOT EXISTS vector;` | Run once per database |
| Create vector column | `embedding vector(1536)` | Dimension must match model |
| Insert embedding | `INSERT INTO docs (embedding) VALUES ($1)` | Pass as array or vector literal |
| Cosine similarity | `1 - (a <=> b)` | Returns 0..1, higher = more similar |
| L2 distance | `a <-> b` | Lower = more similar |
| Inner product | `a <#> b` | Negative inner product |
| HNSW index | `USING hnsw (col vector_cosine_ops)` | Default choice, auto-optimizes |
| IVFFlat index | `USING ivfflat (col vector_cosine_ops) WITH (lists = 100)` | Lower memory, needs `lists` tuning |

## RLS Policy Syntax

| Component | Syntax | Example |
|-----------|--------|---------|
| Enable RLS | `ALTER TABLE t ENABLE ROW LEVEL SECURITY;` | Required before policies work |
| SELECT policy | `CREATE POLICY "name" ON t FOR SELECT USING (expr);` | `auth.uid() = user_id` |
| INSERT policy | `CREATE POLICY "name" ON t FOR INSERT WITH CHECK (expr);` | `auth.uid() = user_id` |
| UPDATE policy | `FOR UPDATE USING (expr) WITH CHECK (expr);` | Both USING and CHECK needed |
| DELETE policy | `CREATE POLICY "name" ON t FOR DELETE USING (expr);` | Only USING clause |
| Current user | `auth.uid()` | Returns UUID of authenticated user |
| JWT claims | `auth.jwt() ->> 'claim'` | Access custom claims |

## Edge Function Commands

| Command | Purpose |
|---------|---------|
| `supabase functions new <name>` | Create new Edge Function |
| `supabase functions serve` | Local development server |
| `supabase functions deploy <name>` | Deploy to production |
| `supabase secrets set KEY=value` | Set environment variable |
| `supabase secrets list` | List all secrets |

## Supabase CLI Cheat Sheet

| Command | Purpose |
|---------|---------|
| `supabase init` | Initialize local project |
| `supabase start` | Start local Supabase stack |
| `supabase stop` | Stop local stack |
| `supabase migration new <name>` | Create migration file |
| `supabase db reset` | Reset local DB, replay migrations |
| `supabase db push` | Push migrations to remote |
| `supabase db diff` | Diff schema changes |
| `supabase link --project-ref <ref>` | Link to remote project |

## Common Pitfalls

| Don't | Do |
|-------|-----|
| Disable RLS for convenience | Design proper policies per table |
| Use `service_role` key client-side | Use `anon` key client-side, `service_role` server-side |
| Store embeddings without an index | Add HNSW index immediately after table creation |
| Hardcode secrets in Edge Functions | Use `Deno.env.get('SECRET')` |
| Use text search for semantic queries | Use pgvector similarity with proper distance function |
| Skip migration files | Always use `supabase migration new` |

## Decision Matrix

| Use Case | Choose |
|----------|--------|
| Semantic/meaning-based search | pgvector cosine similarity |
| Keyword/exact match search | PostgreSQL full-text search (tsvector) |
| < 1M vectors, high recall needed | HNSW index |
| > 1M vectors, memory constrained | IVFFlat index |
| Custom API endpoint | Edge Function |
| Database-triggered logic | PostgreSQL function + trigger |
| Low-latency client messaging | Realtime Broadcast |
| Listen to DB changes | Realtime Postgres Changes |

## Related Documentation

| Topic | Path |
|-------|------|
| pgvector deep dive | `concepts/pgvector-fundamentals.md` |
| RLS patterns | `concepts/rls-policies.md` |
| Edge Functions | `concepts/edge-functions.md` |
| Full Index | `index.md` |
