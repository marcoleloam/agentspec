# Langfuse Knowledge Base

> **Purpose**: LLMOps observability platform for tracking LLM calls, costs, latency, and quality
> **MCP Validated**: 2026-02-17

## Quick Navigation

### Concepts (< 150 lines each)

| File | Purpose |
|------|---------|
| [concepts/traces-spans.md](concepts/traces-spans.md) | Trace hierarchy, sessions, observation nesting |
| [concepts/generations.md](concepts/generations.md) | LLM call tracking with model, tokens, cost |
| [concepts/cost-tracking.md](concepts/cost-tracking.md) | Usage details, cost details, model definitions |
| [concepts/scoring.md](concepts/scoring.md) | Numeric, categorical, boolean quality scores |
| [concepts/prompt-management.md](concepts/prompt-management.md) | Prompt versioning, labels, caching |
| [concepts/model-comparison.md](concepts/model-comparison.md) | A/B testing models, prompt versions |

### Patterns (< 200 lines each)

| File | Purpose |
|------|---------|
| [patterns/python-sdk-integration.md](patterns/python-sdk-integration.md) | Python SDK setup, decorators, context managers |
| [patterns/cloud-run-instrumentation.md](patterns/cloud-run-instrumentation.md) | Cloud Run tracing with flush on shutdown |
| [patterns/quality-feedback-loops.md](patterns/quality-feedback-loops.md) | Scoring, evaluation, LLM-as-a-Judge |
| [patterns/cost-alerting.md](patterns/cost-alerting.md) | Cost monitoring and budget alerts |
| [patterns/trace-linking.md](patterns/trace-linking.md) | Cross-service distributed tracing |
| [patterns/dashboard-metrics.md](patterns/dashboard-metrics.md) | Dashboard setup and metric exports |

### Specs (Machine-Readable)

| File | Purpose |
|------|---------|
| [specs/langfuse-config.yaml](specs/langfuse-config.yaml) | Configuration spec for environment variables |

---

## Quick Reference

- [quick-reference.md](quick-reference.md) - Fast lookup tables

---

## Key Concepts

| Concept | Description |
|---------|-------------|
| **Trace** | Top-level container for a single request/operation |
| **Span** | Duration-based observation for non-LLM work |
| **Generation** | Specialized span for LLM calls with token/cost tracking |
| **Score** | Quality metric (numeric, categorical, or boolean) |
| **Prompt** | Versioned, cached prompt template with labels |

---

## Learning Path

| Level | Files |
|-------|-------|
| **Beginner** | concepts/traces-spans.md, concepts/generations.md |
| **Intermediate** | patterns/python-sdk-integration.md, concepts/cost-tracking.md |
| **Advanced** | patterns/cloud-run-instrumentation.md, patterns/quality-feedback-loops.md |

---

## Agent Usage

| Agent | Primary Files | Use Case |
|-------|---------------|----------|
| ai-data-engineer | patterns/python-sdk-integration.md, concepts/generations.md | Instrument LLM pipelines with observability |
