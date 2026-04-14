# AI Agent Workflow Pattern

> **Purpose**: Configure AI Agent nodes with tools, memory, and vector stores
> **MCP Validated**: 2026-04-14

## When to Use

- Building chatbots or conversational interfaces
- Smart document processing with tool access
- RAG (Retrieval-Augmented Generation) pipelines
- AI-powered automation with external tool calls

## Implementation

```text
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Trigger    │────►│   AI Agent   │────►│   Output     │
│ (Webhook/    │     │  ┌────────┐  │     │ (HTTP/Slack/ │
│  Chat/Manual)│     │  │ Model  │  │     │  DB/Respond) │
│              │     │  ├────────┤  │     │              │
│              │     │  │ Tools  │  │     └──────────────┘
│              │     │  ├────────┤  │
│              │     │  │ Memory │  │
│              │     │  └────────┘  │
│              │     └──────────────┘
```

### AI Agent Node Config

```json
{
  "agent": "toolsAgent",
  "options": {
    "systemMessage": "You are a helpful assistant that processes TikTok video data.",
    "maxIterations": 5,
    "returnIntermediateSteps": false
  }
}
```

### Model Sub-Node

| Model | Use Case | Cost |
|-------|----------|------|
| OpenAI GPT-4o | Complex reasoning | $$$ |
| OpenAI GPT-4o-mini | Simple tasks | $ |
| Anthropic Claude | Long context | $$ |
| Ollama (local) | Privacy, no API cost | Free |

### Tool Sub-Nodes

| Tool | Purpose | Config |
|------|---------|--------|
| Calculator | Math operations | — |
| Code | Custom JS execution | code |
| HTTP Request | Call external APIs | url, method, auth |
| Vector Store | RAG retrieval | collection, topK |
| Postgres | Query database | query |
| Custom Tool | Any n8n workflow | workflowId, description |

### Custom Tool (Sub-Workflow)

```text
Main Agent Workflow:
  Webhook → AI Agent (with Custom Tool) → Respond

Custom Tool Sub-Workflow:
  Execute Workflow Trigger → Postgres (query) → Return results
```

```json
{
  "tool": "workflowTool",
  "name": "search_products",
  "description": "Search products in the database by name or category",
  "workflowId": "wf_abc123"
}
```

### Memory Sub-Nodes

| Memory Type | Persistence | Use Case |
|-------------|-------------|----------|
| Window Buffer | In-memory (session) | Simple chatbots |
| Postgres Chat Memory | Database | Persistent conversations |
| Zep | External service | Long-term memory |

```json
{
  "memory": "postgresMemory",
  "sessionId": "={{ $json.sessionId }}",
  "tableName": "chat_history"
}
```

### Vector Store (RAG)

```text
                    ┌─────────────────┐
                    │  Vector Store    │
                    │  (Qdrant/PG)     │
                    │                  │
                    │  topK: 5         │
┌──────────┐       │  similarity: 0.7 │       ┌──────────┐
│ AI Agent │◄──────│                  │◄──────│ Embeddings│
│          │ query │                  │ index  │ (OpenAI)  │
└──────────┘       └─────────────────┘       └──────────┘
```

## Agent Types

| Type | When to Use |
|------|-------------|
| Tools Agent | Need to call tools (HTTP, DB, code) |
| Conversational Agent | Multi-turn chat without tools |
| ReAct Agent | Complex reasoning with tool chains |
| Plan and Execute | Multi-step tasks with planning |

## Example: Product Q&A Bot

```text
Webhook (POST /chat)
  → AI Agent
    Model: GPT-4o-mini
    Memory: Postgres (session-based)
    Tools:
      - Vector Store (product knowledge base)
      - HTTP Request (check inventory API)
      - Custom Tool (search orders sub-workflow)
  → Respond to Webhook (answer)
```

## Common Mistakes

### Wrong: No system message
Agent responds inconsistently without clear instructions.

### Correct: Detailed system message
```
You are a customer support agent for ContentForge.
Only answer questions about products and orders.
If unsure, say "I'll connect you with a human agent."
Always cite the source document when using RAG results.
```

### Wrong: Too many tools
Agent gets confused with 10+ tools.

### Correct: 3-5 focused tools per agent

## See Also

- [webhook-processing](webhook-processing.md) — Chat webhook endpoints
- [error-handling](error-handling.md) — AI agent error recovery
- [credentials-auth](../concepts/credentials-auth.md) — API key management
