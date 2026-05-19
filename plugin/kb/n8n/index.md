# n8n Knowledge Base

> **Purpose**: Workflow automation patterns, node configuration, and integration design for n8n
> **MCP Validated**: 2026-04-14 | n8n v1.x
> **MCP Tools**: `mcp__n8n-mcp__search_nodes`, `mcp__n8n-mcp__get_node`, `mcp__n8n-mcp__validate_workflow`

## Quick Navigation

### Concepts (< 150 lines each)

| File | Purpose |
|------|---------|
| [workflow-fundamentals](concepts/workflow-fundamentals.md) | Triggers, nodes, connections, data flow, execution |
| [node-types](concepts/node-types.md) | Trigger, action, transformation, helper nodes |
| [expressions-data](concepts/expressions-data.md) | Expression syntax, data mapping, transformations |
| [credentials-auth](concepts/credentials-auth.md) | Authentication patterns, credential management |

### Patterns (< 200 lines each)

| File | Purpose |
|------|---------|
| [webhook-processing](patterns/webhook-processing.md) | Receive HTTP → Validate → Process → Respond |
| [api-integration](patterns/api-integration.md) | REST API calls, pagination, rate limiting |
| [database-operations](patterns/database-operations.md) | Read/Write/Sync with Postgres, MySQL |
| [error-handling](patterns/error-handling.md) | Error triggers, retry logic, alerting |
| [ai-agent-workflow](patterns/ai-agent-workflow.md) | AI Agent nodes with tools, memory, vector stores |
| [scheduled-automation](patterns/scheduled-automation.md) | Cron triggers, batch processing, idempotency |

## Quick Reference

- [quick-reference.md](quick-reference.md)

## Key Concepts

| Concept | Description |
|---------|-------------|
| Workflow | Directed graph of nodes connected by edges |
| Node | Single unit of work (trigger, action, transformation) |
| Item | One JSON object flowing through the workflow |
| Expression | `{{ }}` syntax for dynamic data access |
| Credential | Stored authentication for external services |
| Execution | Single run of a workflow |

## Learning Path

| Level | Files |
|-------|-------|
| Beginner | workflow-fundamentals → node-types → quick-reference |
| Intermediate | expressions-data → webhook-processing → api-integration |
| Advanced | ai-agent-workflow → error-handling → scheduled-automation |

## Agent Usage

| Agent | Primary Files | Use Case |
|-------|---------------|----------|
| n8n-specialist | All | Workflow design, node configuration, integrations |
| streaming-engineer | webhook-processing, api-integration | Real-time event processing |
| ai-data-engineer | ai-agent-workflow | RAG pipelines, AI agent design |
