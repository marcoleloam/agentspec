# Supabase Auth

> **Purpose**: Built-in authentication with JWT tokens, OAuth providers, and user management
> **Confidence**: HIGH
> **MCP Validated**: 2026-02-19

## Overview

Supabase Auth provides a complete authentication system built on GoTrue. It supports email/password, magic links, OAuth (Google, GitHub, etc.), and phone authentication. Every authenticated request includes a JWT token that RLS policies can use for access control.

## The Pattern

```typescript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY)

// Sign up
const { data, error } = await supabase.auth.signUp({
  email: 'user@example.com',
  password: 'secure-password'
})

// Sign in
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'secure-password'
})

// Get current user
const { data: { user } } = await supabase.auth.getUser()

// Sign out
await supabase.auth.signOut()
```

## Quick Reference

| Auth Method | Use Case | Config |
|-------------|----------|--------|
| Email/Password | Standard registration | Default enabled |
| Magic Link | Passwordless via email | Enable in dashboard |
| OAuth | Social login (Google, GitHub) | Configure provider keys |
| Phone/SMS | SMS OTP verification | Configure SMS provider |

## Related

- [RLS Concept](../concepts/rls.md)
- [Multi-Tenant RLS Pattern](../patterns/rls-multi-tenant.md)
