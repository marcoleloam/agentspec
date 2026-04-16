# Qdrant Vector Database KB

> **MCP Validated:** 2026-02-24

> Purpose: Patterns and reference for Qdrant vector database operations
> Created: 2026-02-24

## Contents
- [Quick Reference](quick-reference.md) -- API endpoints, SDK usage, common operations
- [Concepts](concepts/) -- Collections, points, payloads, search
- [Patterns](patterns/) -- n8n integration, RAG pipelines, multi-tenant

## Key Facts
- **License**: Apache 2.0 (free self-hosted, cloud available)
- **Max dimensions**: 65,535 (dense), 4.3B (sparse)
- **Distance metrics**: Cosine, Euclidean, Dot Product, Manhattan
- **MCP Server**: `mcp-server-qdrant` (official, Python/PyPI)
- **n8n Node**: `n8n-nodes-langchain.vectorstoreqdrant` (native, 4 modes)

## When to Use Qdrant
- High-dimensional vector search (> 2,000 dims, where pgvector hits limits)
- Production RAG pipelines needing native metadata filtering
- Multi-tenant vector isolation without SQL complexity
- Self-hosted or cloud-managed vector database requirements

## Related KBs
- [genai](../genai/) -- RAG architecture, agentic workflows
- [supabase](../supabase/) -- The Ledger (structured queries complement vector search)
