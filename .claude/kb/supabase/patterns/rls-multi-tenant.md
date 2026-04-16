# Multi-Tenant RLS Pattern

> **Purpose**: Row Level Security policies for multi-tenant SaaS applications
> **MCP Validated**: 2026-02-19

## When to Use

- SaaS applications with multiple organizations
- Data isolation between tenants
- Shared database with per-tenant access control

## Implementation

```sql
-- Organization-based multi-tenancy
CREATE TABLE public.organizations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE public.org_members (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id UUID REFERENCES public.organizations(id),
  user_id UUID REFERENCES auth.users(id),
  role TEXT DEFAULT 'member' CHECK (role IN ('admin', 'member', 'viewer')),
  UNIQUE(org_id, user_id)
);

-- Example tenant-scoped table
CREATE TABLE public.contacts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id UUID REFERENCES public.organizations(id),
  name TEXT NOT NULL,
  email TEXT,
  phone TEXT,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Enable RLS
ALTER TABLE public.contacts ENABLE ROW LEVEL SECURITY;

-- Helper function: get user's organizations
CREATE OR REPLACE FUNCTION get_user_org_ids()
RETURNS SETOF UUID
LANGUAGE sql SECURITY DEFINER
STABLE
AS $$
  SELECT org_id FROM public.org_members WHERE user_id = auth.uid();
$$;

-- Policies
CREATE POLICY "tenant_isolation" ON public.contacts
  FOR ALL USING (org_id IN (SELECT get_user_org_ids()));

-- Service role bypass for backend operations
CREATE POLICY "service_full_access" ON public.contacts
  FOR ALL USING (auth.role() = 'service_role');
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `SECURITY DEFINER` | Required | Function runs with creator's permissions |
| `STABLE` | Recommended | Function result is stable within transaction |

## See Also

- [RLS Concept](../concepts/rls.md)
- [Auth Concept](../concepts/auth.md)
