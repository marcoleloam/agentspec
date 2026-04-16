# Edge Function API Pattern

> **Purpose**: Production-ready Edge Function with auth, validation, and error handling
> **MCP Validated**: 2026-02-19

## When to Use

- Custom API endpoints not covered by PostgREST
- Webhook receivers (WhatsApp, payment gateways)
- Integrating with external APIs (OpenAI, CRM, etc.)

## Implementation

```typescript
import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from "https://esm.sh/@supabase/supabase-js@2"

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

interface RequestBody {
  action: string
  payload: Record<string, unknown>
}

serve(async (req) => {
  // CORS preflight
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    // Validate method
    if (req.method !== 'POST') {
      throw new Error('Method not allowed')
    }

    // Parse and validate body
    const body: RequestBody = await req.json()
    if (!body.action || !body.payload) {
      throw new Error('Missing required fields: action, payload')
    }

    // Create Supabase client
    const supabase = createClient(
      Deno.env.get('SUPABASE_URL')!,
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    )

    // Route by action
    let result: unknown
    switch (body.action) {
      case 'search':
        result = await handleSearch(supabase, body.payload)
        break
      case 'update':
        result = await handleUpdate(supabase, body.payload)
        break
      default:
        throw new Error(`Unknown action: ${body.action}`)
    }

    return new Response(JSON.stringify({ success: true, data: result }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    })
  } catch (err) {
    const status = err.message.includes('not allowed') ? 405 : 400
    return new Response(JSON.stringify({ success: false, error: err.message }), {
      status,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    })
  }
})
```

## See Also

- [Edge Functions Concept](../concepts/edge-functions.md)
- [Auth Concept](../concepts/auth.md)
