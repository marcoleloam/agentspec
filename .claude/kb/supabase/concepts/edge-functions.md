# Edge Functions

> **Purpose**: Deno-based serverless functions for API middleware, webhooks, and custom business logic
> **Confidence**: 0.95
> **MCP Validated**: 2026-02-19

## Overview

Supabase Edge Functions are serverless TypeScript functions that run on the Deno runtime, deployed globally at the edge for low latency. They are bundled into ESZip format for fast cold starts (milliseconds). Edge Functions have access to environment variables including auto-injected Supabase credentials and are ideal for custom API endpoints, webhook handlers, and integrating with external services.

## Request/Response Handling

Edge Functions use `Deno.serve()` -- the modern Deno API. Access `req.method`, `req.headers`, `req.url`, and `await req.json()`. Return a `new Response(body, { status, headers })`.

## Environment Variables and Secrets

| Variable | Value | Auto-Injected |
|----------|-------|---------------|
| `SUPABASE_URL` | Project URL | Yes |
| `SUPABASE_ANON_KEY` | Anon key (client-safe) | Yes |
| `SUPABASE_SERVICE_ROLE_KEY` | Service key (server-only) | Yes |
| Custom secrets | Set via CLI | No |

Access with `Deno.env.get('VARIABLE_NAME')`. Set custom secrets with:

```bash
supabase secrets set MY_API_KEY=sk-abc123
```

## CORS Configuration

Browsers send a preflight OPTIONS request before the actual request. You must handle CORS manually in Edge Functions. For `@supabase/supabase-js` v2.95.0+, import CORS headers from the SDK:

```typescript
import { corsHeaders } from '@supabase/supabase-js/cors'
```

For older versions or custom CORS, define headers manually:

```typescript
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers':
    'authorization, x-client-info, apikey, content-type',
}
```

## The Pattern

```typescript
import { corsHeaders } from '@supabase/supabase-js/cors'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

Deno.serve(async (req) => {
  // 1. Handle CORS preflight FIRST
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    // 2. Create Supabase client
    const supabase = createClient(
      Deno.env.get('SUPABASE_URL')!,
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    )

    // 3. Parse request
    const { name } = await req.json()

    // 4. Business logic
    const { data, error } = await supabase
      .from('users')
      .select('*')
      .eq('name', name)
      .single()

    if (error) throw error

    // 5. Return success response
    return new Response(JSON.stringify({ data }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      status: 200,
    })
  } catch (error) {
    // 6. Return error response
    return new Response(JSON.stringify({ error: error.message }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      status: 400,
    })
  }
})
```

## Quick Reference

| Action | Command |
|--------|---------|
| Create function | `supabase functions new my-function` |
| Serve locally | `supabase functions serve` |
| Deploy | `supabase functions deploy my-function` |
| Deploy all | `supabase functions deploy` |
| Set secret | `supabase secrets set KEY=value` |
| View logs | `supabase functions logs my-function` |

## Common Mistakes

### Wrong

```typescript
// MISSING CORS: Browser requests will fail
Deno.serve(async (req) => {
  return new Response(JSON.stringify({ ok: true }))
})
// MISSING ERROR HANDLING: Unhandled errors crash the function
Deno.serve(async (req) => {
  const body = await req.json()  // Crashes if body is not JSON
  return new Response(JSON.stringify(await riskyOperation(body)))
})
```

### Correct

```typescript
// Proper CORS + error handling
Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }
  try {
    const body = await req.json()
    const result = await riskyOperation(body)
    return new Response(JSON.stringify(result), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    })
  } catch (error) {
    return new Response(JSON.stringify({ error: error.message }), {
      status: 400,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    })
  }
})
```

## Related

- [Webhook Edge Function Pattern](../patterns/webhook-edge-function.md)
- [RLS Policies](../concepts/rls-policies.md)
