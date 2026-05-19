# Supabase Realtime

> **Purpose**: WebSocket-based real-time data sync, presence tracking, and broadcast
> **Confidence**: HIGH
> **MCP Validated**: 2026-02-19

## Overview

Supabase Realtime enables listening to database changes (INSERT, UPDATE, DELETE), presence tracking (who's online), and broadcasting custom events - all via WebSocket channels. Useful for live dashboards, chat notifications, and collaborative features.

## The Pattern

```typescript
const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY)

// Listen to database changes
const channel = supabase
  .channel('conversations')
  .on('postgres_changes',
    { event: 'INSERT', schema: 'public', table: 'messages' },
    (payload) => {
      console.log('New message:', payload.new)
    }
  )
  .subscribe()

// Broadcast custom events
const channel = supabase.channel('room:1')
channel.send({
  type: 'broadcast',
  event: 'typing',
  payload: { user_id: 'abc', is_typing: true }
})

// Cleanup
supabase.removeChannel(channel)
```

## Quick Reference

| Event Type | Trigger | Use Case |
|------------|---------|----------|
| `postgres_changes` | DB row change | Live data sync |
| `broadcast` | Custom event | Typing indicators, notifications |
| `presence` | User state change | Online/offline status |

## Related

- [Auth Concept](../concepts/auth.md)
- [RLS Concept](../concepts/rls.md)
