# Row Level Security (RLS)

> **Purpose**: Database-level access control using auth context for multi-tenant isolation
> **Confidence**: HIGH
> **MCP Validated**: 2026-02-19

## Overview

RLS in Supabase provides fine-grained access control at the database level. Every query is automatically filtered based on the authenticated user's JWT token, making it impossible for users to access data they shouldn't see - even if application code has bugs.

## The Pattern

```sql
-- Step 1: Enable RLS on the table
ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;

-- Step 2: Create policies for each operation
-- Users can read their own conversations
CREATE POLICY "users_read_own" ON public.conversations
  FOR SELECT USING (auth.uid() = user_id);

-- Users can create their own conversations
CREATE POLICY "users_create_own" ON public.conversations
  FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Users can update their own conversations
CREATE POLICY "users_update_own" ON public.conversations
  FOR UPDATE USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- Service role has full access (for backend/admin operations)
CREATE POLICY "service_role_all" ON public.conversations
  FOR ALL USING (auth.role() = 'service_role');
```

## Quick Reference

| Context Function | Returns | Use For |
|-----------------|---------|---------|
| `auth.uid()` | UUID | Row-level user filtering |
| `auth.role()` | TEXT | Role-based access (anon/authenticated/service_role) |
| `auth.jwt() ->> 'org_id'` | TEXT | Multi-tenant org filtering |

## Common Mistakes

### Wrong

```sql
-- Too permissive - anyone authenticated can see everything
CREATE POLICY "bad_policy" ON public.conversations
  FOR SELECT USING (auth.role() = 'authenticated');
```

### Correct

```sql
-- Properly scoped - users only see their own data
CREATE POLICY "good_policy" ON public.conversations
  FOR SELECT USING (auth.uid() = user_id);
```

## Related

- [Multi-Tenant RLS Pattern](../patterns/rls-multi-tenant.md)
- [Auth Concept](../concepts/auth.md)
