# Multi-Tenant RLS

> **Purpose**: Row-Level Security patterns for SaaS applications with organization and user-level isolation
> **MCP Validated**: 2026-02-19

## When to Use

- SaaS applications with multiple organizations sharing one database
- Team-based access where users belong to one or more organizations
- Data isolation between tenants without separate schemas
- Role-based access within organizations (admin, member, viewer)

## Implementation

### Schema: Organizations and Membership

```sql
-- Organizations table
CREATE TABLE public.organizations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  slug TEXT UNIQUE NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Organization membership with roles
CREATE TABLE public.org_members (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  role TEXT NOT NULL DEFAULT 'member'
    CHECK (role IN ('owner', 'admin', 'member', 'viewer')),
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(org_id, user_id)
);

-- Index for RLS policy performance
CREATE INDEX idx_org_members_user_id ON public.org_members (user_id);
CREATE INDEX idx_org_members_org_id ON public.org_members (org_id);
```

### Helper Functions for RLS

```sql
-- Get all org IDs the current user belongs to
CREATE OR REPLACE FUNCTION get_user_org_ids()
RETURNS SETOF UUID
LANGUAGE sql SECURITY DEFINER STABLE
AS $$
  SELECT org_id FROM public.org_members
  WHERE user_id = auth.uid();
$$;

-- Check if user has a specific role in an org
CREATE OR REPLACE FUNCTION user_has_org_role(
  target_org_id UUID,
  required_role TEXT
)
RETURNS BOOLEAN
LANGUAGE sql SECURITY DEFINER STABLE
AS $$
  SELECT EXISTS (
    SELECT 1 FROM public.org_members
    WHERE user_id = auth.uid()
      AND org_id = target_org_id
      AND role = required_role
  );
$$;

-- Check if user has at least a minimum role level
CREATE OR REPLACE FUNCTION user_has_min_role(
  target_org_id UUID,
  min_role TEXT
)
RETURNS BOOLEAN
LANGUAGE sql SECURITY DEFINER STABLE
AS $$
  SELECT EXISTS (
    SELECT 1 FROM public.org_members
    WHERE user_id = auth.uid()
      AND org_id = target_org_id
      AND CASE min_role
        WHEN 'viewer' THEN role IN ('viewer', 'member', 'admin', 'owner')
        WHEN 'member' THEN role IN ('member', 'admin', 'owner')
        WHEN 'admin'  THEN role IN ('admin', 'owner')
        WHEN 'owner'  THEN role = 'owner'
      END
  );
$$;
```

### Example: AI Chatbot Conversations Table

```sql
-- Conversations belong to an org and a user
CREATE TABLE public.conversations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users(id),
  title TEXT NOT NULL DEFAULT 'New Conversation',
  model TEXT NOT NULL DEFAULT 'gpt-4o-mini',
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Performance indexes
CREATE INDEX idx_conversations_org_id ON public.conversations (org_id);
CREATE INDEX idx_conversations_user_id ON public.conversations (user_id);

-- Enable RLS
ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;

-- Policy: Users can read conversations in their orgs
CREATE POLICY "Org members read conversations"
  ON public.conversations FOR SELECT
  USING (org_id IN (SELECT get_user_org_ids()));

-- Policy: Users can create conversations in their orgs
CREATE POLICY "Org members create conversations"
  ON public.conversations FOR INSERT
  WITH CHECK (
    org_id IN (SELECT get_user_org_ids())
    AND auth.uid() = user_id
  );

-- Policy: Users can update their own conversations
CREATE POLICY "Users update own conversations"
  ON public.conversations FOR UPDATE
  USING (auth.uid() = user_id AND org_id IN (SELECT get_user_org_ids()))
  WITH CHECK (auth.uid() = user_id AND org_id IN (SELECT get_user_org_ids()));

-- Policy: Admins can delete any conversation in their org
CREATE POLICY "Admins delete org conversations"
  ON public.conversations FOR DELETE
  USING (user_has_min_role(org_id, 'admin'));

-- Policy: Service role bypass for backend operations
CREATE POLICY "Service role full access"
  ON public.conversations FOR ALL
  USING (auth.role() = 'service_role');
```

### RLS on the Membership Table Itself

```sql
ALTER TABLE public.org_members ENABLE ROW LEVEL SECURITY;

-- Users can see members of orgs they belong to
CREATE POLICY "See org members"
  ON public.org_members FOR SELECT
  USING (org_id IN (SELECT get_user_org_ids()));

-- Only admins/owners can add members
CREATE POLICY "Admins add members"
  ON public.org_members FOR INSERT
  WITH CHECK (user_has_min_role(org_id, 'admin'));

-- Only owners can remove members
CREATE POLICY "Owners remove members"
  ON public.org_members FOR DELETE
  USING (user_has_min_role(org_id, 'owner'));
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `SECURITY DEFINER` | Required | Helper functions run with creator privileges |
| `STABLE` | Required | Functions return same result within a transaction |
| Role hierarchy | owner > admin > member > viewer | Used by `user_has_min_role()` |

## Example Usage

```typescript
import { createClient } from '@supabase/supabase-js'

// Client-side: user only sees their org's data automatically
const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY)

// RLS filters automatically -- user only gets their org's conversations
const { data } = await supabase
  .from('conversations')
  .select('*')
  .order('updated_at', { ascending: false })

// Insert: RLS validates org membership and user_id match
const { error } = await supabase.from('conversations').insert({
  org_id: currentOrgId,
  user_id: currentUserId,
  title: 'New Chat',
})
```

## See Also

- [RLS Policies Concept](../concepts/rls-policies.md)
- [RAG Vector Store](../patterns/rag-vector-store.md)
- [Webhook Edge Function](../patterns/webhook-edge-function.md)
