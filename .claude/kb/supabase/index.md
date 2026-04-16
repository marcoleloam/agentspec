# Supabase Knowledge Base

> **Purpose**: Supabase platform patterns for pgvector, RLS, Edge Functions, Auth, Realtime, and migrations
> **MCP Validated**: 2026-02-19

## Quick Navigation

### Concepts (< 150 lines each)

| File | Purpose |
|------|---------|
| [concepts/pgvector-fundamentals.md](concepts/pgvector-fundamentals.md) | Vector data types, distance functions, HNSW/IVFFlat indexes |
| [concepts/rls-policies.md](concepts/rls-policies.md) | Row-Level Security policy types, auth context, multi-tenant access |
| [concepts/edge-functions.md](concepts/edge-functions.md) | Deno runtime, CORS, request handling, environment variables |

### Patterns (< 200 lines each)

| File | Purpose |
|------|---------|
| [patterns/rag-vector-store.md](patterns/rag-vector-store.md) | Complete RAG pipeline with pgvector, embeddings, and match functions |
| [patterns/multi-tenant-rls.md](patterns/multi-tenant-rls.md) | Multi-tenant RLS for SaaS with org-level and user-level policies |
| [patterns/webhook-edge-function.md](patterns/webhook-edge-function.md) | Edge Function for receiving webhooks with signature validation |
| [patterns/e2e-testing-cleanup.md](patterns/e2e-testing-cleanup.md) | FK-safe test data cleanup, MCP validation, multi-project repo patterns |

---

## Quick Reference

- [quick-reference.md](quick-reference.md) - Fast lookup tables

---

## Key Concepts

| Concept | Description |
|---------|-------------|
| **pgvector** | PostgreSQL extension for vector similarity search with HNSW/IVFFlat indexes |
| **RLS** | Row-Level Security policies that add WHERE clauses to every query automatically |
| **Edge Functions** | Deno-based serverless functions deployed globally at the edge |
| **Auth** | Built-in authentication with JWT, OAuth providers, and custom claims |
| **Realtime** | WebSocket channels for Postgres Changes, Broadcast, and Presence |
| **Migrations** | Versioned SQL files managed via Supabase CLI for schema changes |

---

## Learning Path

| Level | Files |
|-------|-------|
| **Beginner** | concepts/pgvector-fundamentals.md, concepts/rls-policies.md |
| **Intermediate** | concepts/edge-functions.md, patterns/rag-vector-store.md |
| **Advanced** | patterns/multi-tenant-rls.md, patterns/webhook-edge-function.md, patterns/e2e-testing-cleanup.md |

---

## Agent Usage

| Agent | Primary Files | Use Case |
|-------|---------------|----------|
| supabase-specialist | All files in this KB | Supabase database design, pgvector RAG, RLS policies, Edge Functions |
