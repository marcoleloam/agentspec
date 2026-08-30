# Langfuse Quick Reference

> Fast lookup tables. For code examples, see linked files.
> **MCP Validated:** 2026-02-17

## Observation Types

| Type | Purpose | Extra Fields |
|------|---------|-------------|
| `span` | Generic duration-based step | input, output, metadata |
| `generation` | LLM call tracking | model, usage_details, cost_details |
| `event` | Discrete point-in-time event | input, output, metadata |
| `tool` | Tool/function call | input, output |
| `retriever` | Vector store / DB retrieval | input, output |
| `embedding` | Embedding model call | model, usage_details, cost_details |

## Environment Variables

| Variable | Required | Example |
|----------|----------|---------|
| `LANGFUSE_SECRET_KEY` | Yes | `sk-lf-...` |
| `LANGFUSE_PUBLIC_KEY` | Yes | `pk-lf-...` |
| `LANGFUSE_BASE_URL` | Yes | `https://cloud.langfuse.com` |
| `LANGFUSE_TRACING_ENVIRONMENT` | No | `production` |

## SDK Quick Start

| Action | Code |
|--------|------|
| Install | `pip install langfuse` |
| Get client | `from langfuse import get_client` |
| Decorator | `@observe()` |
| Generation | `@observe(as_type="generation")` |
| Flush | `langfuse.flush()` |
| Auth check | `langfuse.auth_check()` |

## Score Data Types

| Type | Values | Example |
|------|--------|---------|
| `NUMERIC` | Any float | `0.95` |
| `CATEGORICAL` | String labels | `"correct"`, `"partial"` |
| `BOOLEAN` | 0 or 1 | `1` (true) |

## Cost Tracking Fields

| Field | Type | Description |
|-------|------|-------------|
| `usage_details.input` | int | Input tokens |
| `usage_details.output` | int | Output tokens |
| `usage_details.total` | int | Total tokens (auto-summed) |
| `cost_details.input` | float | Input cost in USD |
| `cost_details.output` | float | Output cost in USD |
| `cost_details.total` | float | Total cost in USD |

## Decision Matrix

| Use Case | Choose |
|----------|--------|
| Track LLM call with tokens | `generation` observation |
| Track non-LLM processing step | `span` observation |
| Log a discrete event | `event` observation |
| Version control prompts | Prompt management |
| Measure output quality | Scores (numeric/categorical/boolean) |
| Monitor spend per user/model | Cost tracking + dashboard |

## Common Pitfalls

| Don't | Do |
|-------|-----|
| Forget `flush()` in serverless | Always call `langfuse.flush()` before exit |
| Hardcode prompts in source | Use prompt management with labels |
| Skip `as_type="generation"` | Set it for LLM calls to get token tracking |
| Ignore cost_details | Ingest costs for accurate spend tracking |

## Related Documentation

| Topic | Path |
|-------|------|
| Trace hierarchy | `concepts/traces-spans.md` |
| Python SDK setup | `patterns/python-sdk-integration.md` |
| Full Index | `index.md` |
