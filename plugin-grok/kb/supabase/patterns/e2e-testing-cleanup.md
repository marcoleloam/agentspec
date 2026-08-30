# E2E Testing and Cleanup

> **Purpose**: Safe test data reset and E2E validation patterns for multi-project Supabase repos
> **MCP Validated**: 2026-03-12

## When to Use

- Resetting test data before E2E test runs
- Validating conversation state after webhook-driven tests
- Working in a multi-project Supabase repository where SQL targets differ per folder

## Implementation

### FK-Safe Test Data Cleanup

Always delete children before parents to respect foreign key constraints.

```sql
-- Order matters: children first, then parents
DELETE FROM messages;           -- FK to conversations
DELETE FROM processed_messages;  -- standalone dedup table
DELETE FROM conversations;       -- FK to customers
DELETE FROM dead_letter_queue;   -- standalone

-- Keep customers but reset transient fields
UPDATE customers SET
  last_contact_date = NULL,
  journey_score = NULL,
  journey_signals = NULL,
  is_processing = false,
  processing_started_at = NULL;
```

### E2E Validation via Supabase MCP

Use `mcp__claude_ai_Supabase__execute_sql` with the correct `project_id` for read queries.

```sql
-- Validate conversation state
SELECT current_stage, status, checkout_sent, message_count
FROM conversations
WHERE phone = '5511999990001';

-- Validate AI responses (check message flow)
SELECT role, content
FROM messages
WHERE conversation_id = 'uuid-here'
ORDER BY created_at ASC;

-- Check signal accumulation
SELECT stage_signals_json::text
FROM conversations
WHERE phone = '5511999990001';
```

### Multi-Project Supabase Repo

```text
Folder                        Project ID                  Name
src/ai-sdr-agent/             dohtlrjonwtobfeknvio        ask-ai-sdr
src/prg-data-ship/            gmpvkybsubyfadqjbdzm        data-ship
src/data-analytics-brain/     nvqlfhcojmcxzmkpytnw        data-analytics-brain
src/ai-intel-hub/             nvqlfhcojmcxzmkpytnw        data-analytics-brain (intel_hub schema)
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `project_id` | none | **Required** -- must match the folder you are working in |
| `schema` | `public` | Override with `Content-Profile` header for custom schemas |
| `on_conflict` | none | Add to upsert URLs, e.g. `?on_conflict=trans_cod` |

## Example Usage

```text
-- Step 1: Identify project from folder
Working in src/ai-sdr-agent/ → project_id = dohtlrjonwtobfeknvio

-- Step 2: Clean test data (FK-safe order)
mcp__claude_ai_Supabase__execute_sql(
  project_id: "dohtlrjonwtobfeknvio",
  query: "DELETE FROM messages; DELETE FROM processed_messages; DELETE FROM conversations;"
)

-- Step 3: Run E2E tests (send webhooks)

-- Step 4: Validate results
mcp__claude_ai_Supabase__execute_sql(
  project_id: "dohtlrjonwtobfeknvio",
  query: "SELECT current_stage, status, message_count FROM conversations WHERE phone = '5511999990001'"
)
```

## Gotchas

- **SubAgents do not read MEMORY.md** -- always pass project_id explicitly in task prompts
- **Generated columns** cannot appear in INSERT/UPDATE -- omit `payment_year`, `payment_month`, etc.
- **PostgREST schema routing**: tables in custom schemas need `Content-Profile: <schema>` header for writes; views in `public` work by default
- **FK constraint errors** are silent failures in batch deletes -- always verify row counts after cleanup

## See Also

- [Migration Patterns](../patterns/migration-patterns.md)
- [RLS Policies](../concepts/rls-policies.md)
