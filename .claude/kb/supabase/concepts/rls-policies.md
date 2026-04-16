# RLS Policies

> **Purpose**: Row-Level Security policy types, auth context functions, and access control patterns
> **Confidence**: 0.95
> **MCP Validated**: 2026-02-19

## Overview

Row-Level Security (RLS) in Supabase adds a WHERE clause to every query automatically at the database level. Policies are SQL expressions evaluated on every table access, making it impossible for users to see data they should not -- even if application code has bugs. RLS is PostgreSQL-native and enforced regardless of how the database is accessed (client SDK, REST API, or direct connection).

## Policy Types

| Operation | Clause | Purpose |
|-----------|--------|---------|
| SELECT | `USING (expr)` | Filter which rows can be read |
| INSERT | `WITH CHECK (expr)` | Validate new rows before insert |
| UPDATE | `USING (expr) WITH CHECK (expr)` | Filter rows to update + validate new values |
| DELETE | `USING (expr)` | Filter which rows can be deleted |
| ALL | `USING (expr)` | Shorthand for all operations |

**Key distinction:** `USING` filters existing rows. `WITH CHECK` validates new/modified row values. UPDATE needs both because it reads then writes.

## Auth Context Functions

| Function | Returns | Example |
|----------|---------|---------|
| `auth.uid()` | UUID | ID of the currently authenticated user |
| `auth.role()` | TEXT | Role: `anon`, `authenticated`, or `service_role` |
| `auth.jwt()` | JSONB | Full JWT payload (access custom claims) |
| `auth.jwt() ->> 'email'` | TEXT | User email from JWT |
| `auth.jwt() -> 'app_metadata' ->> 'org_id'` | TEXT | Custom claim from app_metadata |
| `current_setting('request.jwt.claims', true)` | TEXT | Alternative JWT access |

## The Pattern

### User-Scoped Policies (Most Common)

```sql
-- Step 1: Always enable RLS first
ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;

-- Step 2: Users can only read their own rows
CREATE POLICY "Users read own data"
  ON public.conversations FOR SELECT
  USING (auth.uid() = user_id);

-- Step 3: Users can only insert rows they own
CREATE POLICY "Users insert own data"
  ON public.conversations FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- Step 4: Users can only update their own rows
CREATE POLICY "Users update own data"
  ON public.conversations FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- Step 5: Users can only delete their own rows
CREATE POLICY "Users delete own data"
  ON public.conversations FOR DELETE
  USING (auth.uid() = user_id);
```

### Org-Scoped Policies (Multi-Tenant)

```sql
-- Users can access rows belonging to their organization
CREATE POLICY "Org members read"
  ON public.projects FOR SELECT
  USING (
    org_id IN (
      SELECT org_id FROM public.org_members
      WHERE user_id = auth.uid()
    )
  );
```

### Public Read, Private Write

```sql
CREATE POLICY "Public read" ON public.articles
  FOR SELECT USING (true);  -- Anyone can read
CREATE POLICY "Authors write" ON public.articles
  FOR INSERT WITH CHECK (auth.uid() = author_id);
```

### Service Role Bypass

```sql
CREATE POLICY "Service role full access" ON public.conversations
  FOR ALL USING (auth.role() = 'service_role');
```

## Quick Reference

| Scenario | Policy Expression |
|----------|-------------------|
| User owns row | `auth.uid() = user_id` |
| User belongs to org | `org_id IN (SELECT org_id FROM org_members WHERE user_id = auth.uid())` |
| Public read access | `true` |
| Authenticated only | `auth.role() = 'authenticated'` |
| Admin role (JWT claim) | `auth.jwt() -> 'app_metadata' ->> 'role' = 'admin'` |
| Service role only | `auth.role() = 'service_role'` |

## Common Mistakes

### Wrong

```sql
-- MISTAKE 1: Forgetting to enable RLS (table is wide open)
CREATE POLICY "my_policy" ON public.data FOR SELECT USING (auth.uid() = user_id);
-- Policy exists but RLS is not enabled -- NO PROTECTION

-- MISTAKE 2: Overly permissive (any authenticated user sees everything)
ALTER TABLE public.data ENABLE ROW LEVEL SECURITY;
CREATE POLICY "bad" ON public.data FOR SELECT
  USING (auth.role() = 'authenticated');

-- MISTAKE 3: Missing WITH CHECK on UPDATE (can modify user_id to steal rows)
CREATE POLICY "update" ON public.data FOR UPDATE
  USING (auth.uid() = user_id);
  -- Missing: WITH CHECK (auth.uid() = user_id)
```

### Correct

```sql
-- Always enable RLS before creating policies
ALTER TABLE public.data ENABLE ROW LEVEL SECURITY;

-- Scope to specific user, not just "authenticated"
CREATE POLICY "read_own" ON public.data FOR SELECT
  USING (auth.uid() = user_id);

-- Include WITH CHECK on UPDATE to prevent user_id manipulation
CREATE POLICY "update_own" ON public.data FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);
```

## Performance Tips

Index columns used in RLS policies (`user_id`, `org_id`). Use `SECURITY DEFINER STABLE` helper functions for complex lookups. Prefer JWT claims over subqueries for faster evaluation.

## Related

- [Multi-Tenant RLS Pattern](../patterns/multi-tenant-rls.md)
- [pgvector Fundamentals](../concepts/pgvector-fundamentals.md)
