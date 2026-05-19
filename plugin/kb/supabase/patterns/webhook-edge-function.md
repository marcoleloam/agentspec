# Webhook Edge Function

> **Purpose**: Edge Function pattern for receiving webhooks with signature validation, parsing, and database operations
> **MCP Validated**: 2026-02-19

## When to Use

- Receiving webhooks from payment providers (Stripe, Eduzz, Hotmart)
- Processing incoming events from third-party services
- Building API middleware that validates and transforms external data

## Implementation

```typescript
import { corsHeaders } from '@supabase/supabase-js/cors'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const VALID_EVENTS = ['payment.confirmed', 'payment.refunded',
  'subscription.created', 'subscription.cancelled'] as const

const jsonResponse = (body: object, status = 200) =>
  new Response(JSON.stringify(body), {
    status, headers: { ...corsHeaders, 'Content-Type': 'application/json' },
  })

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: corsHeaders })
  if (req.method !== 'POST') return jsonResponse({ error: 'Method not allowed' }, 405)

  try {
    // 1. Validate webhook signature (HMAC-SHA256)
    const signature = req.headers.get('x-webhook-signature')
    const secret = Deno.env.get('WEBHOOK_SECRET')
    if (!signature || !secret) return jsonResponse({ error: 'Missing signature' }, 401)

    const rawBody = await req.text()
    const encoder = new TextEncoder()
    const key = await crypto.subtle.importKey(
      'raw', encoder.encode(secret),
      { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']
    )
    const sig = await crypto.subtle.sign('HMAC', key, encoder.encode(rawBody))
    const expected = Array.from(new Uint8Array(sig))
      .map((b) => b.toString(16).padStart(2, '0')).join('')

    if (signature !== expected) {
      console.error('Invalid webhook signature')
      return jsonResponse({ error: 'Invalid signature' }, 401)
    }

    // 2. Parse and validate payload
    const payload = JSON.parse(rawBody)
    if (!payload.event || !payload.data) {
      return jsonResponse({ error: 'Missing event or data' }, 400)
    }
    if (!VALID_EVENTS.includes(payload.event)) {
      return jsonResponse({ received: true, ignored: true })
    }

    // 3. Database operations
    const supabase = createClient(
      Deno.env.get('SUPABASE_URL')!,
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    )

    // Log the event
    await supabase.from('webhook_events').insert({
      event_type: payload.event,
      payload: payload.data,
      source: req.headers.get('user-agent') ?? 'unknown',
      received_at: new Date().toISOString(),
    })

    // 4. Route by event type
    switch (payload.event) {
      case 'payment.confirmed':
        await supabase.from('payments')
          .update({ status: 'confirmed', confirmed_at: new Date().toISOString() })
          .eq('external_id', payload.data.payment_id)
        break
      case 'payment.refunded':
        await supabase.from('payments')
          .update({ status: 'refunded', refunded_at: new Date().toISOString() })
          .eq('external_id', payload.data.payment_id)
        break
      case 'subscription.created':
        await supabase.from('subscriptions').insert({
          user_email: payload.data.customer_email,
          plan: payload.data.plan,
          external_id: payload.data.subscription_id,
          status: 'active',
        })
        break
      case 'subscription.cancelled':
        await supabase.from('subscriptions')
          .update({ status: 'cancelled', cancelled_at: new Date().toISOString() })
          .eq('external_id', payload.data.subscription_id)
        break
    }

    // 5. Always return 200 to prevent provider retries
    return jsonResponse({ received: true, event: payload.event })
  } catch (error) {
    console.error('Webhook error:', error.message)
    return jsonResponse({ received: true, error: 'Processing failed' })
  }
})
```

## Webhook Events Table (Supporting Schema)

```sql
CREATE TABLE public.webhook_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  event_type TEXT NOT NULL,
  payload JSONB NOT NULL,
  source TEXT,
  received_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE public.webhook_events ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Service role only" ON public.webhook_events
  FOR ALL USING (auth.role() = 'service_role');
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `WEBHOOK_SECRET` | (required) | HMAC secret for signature validation |
| Signature header | `x-webhook-signature` | Header containing HMAC-SHA256 hex digest |
| Algorithm | HMAC-SHA256 | Signature algorithm (Web Crypto API) |
| Response code | Always 200 | Prevents provider from retrying on errors |

## Example Usage

```bash
# Set the webhook secret
supabase secrets set WEBHOOK_SECRET=whsec_your_secret_here

# Deploy the function
supabase functions deploy webhook-handler

# Test locally
curl -X POST http://localhost:54321/functions/v1/webhook-handler \
  -H "Content-Type: application/json" \
  -H "x-webhook-signature: <computed-hmac>" \
  -d '{"event":"payment.confirmed","data":{"payment_id":"pay_123"}}'
```

## See Also

- [Edge Functions Concept](../concepts/edge-functions.md)
- [RLS Policies](../concepts/rls-policies.md)
- [Multi-Tenant RLS](../patterns/multi-tenant-rls.md)
