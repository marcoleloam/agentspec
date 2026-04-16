# Traces and Spans

> **Purpose**: Understand the Langfuse trace hierarchy and observation nesting model
> **Confidence**: 0.95
> **MCP Validated**: 2026-02-17

## Overview

A Langfuse trace represents a single request or operation in your LLM application. Traces contain observations (spans, generations, events) that can be nested to form a tree structure. Sessions group related traces from the same user interaction. The hierarchy is: Session > Trace > Observations (nested).

## The Pattern

```python
from langfuse import get_client

langfuse = get_client()

# Create a trace with context manager
with langfuse.start_as_current_observation(
    as_type="span",
    name="process-document"
) as root_span:
    root_span.update(
        input={"document_id": "doc-123"},
        metadata={"pipeline": "extraction"}
    )

    # Nested span for a sub-step
    with langfuse.start_as_current_observation(
        as_type="span",
        name="preprocess"
    ) as child_span:
        child_span.update(output={"pages": 5, "status": "cleaned"})

    # Nested generation for an LLM call
    with langfuse.start_as_current_observation(
        as_type="generation",
        name="extract-fields",
        model="gemini-2.0-flash"
    ) as gen:
        gen.update(
            input={"prompt": "Extract invoice fields..."},
            output={"vendor": "Acme Corp", "total": 1500.00},
            usage_details={"input": 250, "output": 80}
        )

    root_span.update(output={"status": "completed"})

langfuse.flush()
```

## Data Model

| Level | Description | Key Attributes |
|-------|-------------|----------------|
| **Session** | Groups related traces | `session_id` |
| **Trace** | Single request/operation | `trace_id`, `user_id`, `tags`, `release` |
| **Span** | Duration-based sub-step | `name`, `input`, `output`, `metadata` |
| **Generation** | LLM call observation | `model`, `usage_details`, `cost_details` |
| **Event** | Point-in-time marker | `name`, `input`, `metadata` |

## Trace Attributes

| Attribute | Type | Purpose |
|-----------|------|---------|
| `name` | string | Identify the trace type (e.g., "invoice-extraction") |
| `user_id` | string | Associate trace with a user |
| `session_id` | string | Group traces into sessions |
| `tags` | list | Filterable labels (e.g., ["production", "v2"]) |
| `release` | string | Application version |
| `metadata` | dict | Arbitrary key-value data |
| `input` | any | Trace input payload |
| `output` | any | Trace output payload |

## Propagating Attributes

```python
from langfuse import observe, propagate_attributes

@observe()
def my_pipeline(user_id: str, session_id: str):
    with propagate_attributes(
        user_id=user_id,
        session_id=session_id,
        tags=["production"],
        metadata={"pipeline": "extraction"}
    ):
        result = process_step()
    return result
```

## Common Mistakes

### Wrong

```python
# Missing flush - data lost in serverless environments
with langfuse.start_as_current_observation(as_type="span", name="task") as span:
    span.update(output="done")
# Application exits without sending buffered traces
```

### Correct

```python
with langfuse.start_as_current_observation(as_type="span", name="task") as span:
    span.update(output="done")
langfuse.flush()  # Always flush in short-lived / serverless apps
```

## Related

- [Generations](../concepts/generations.md)
- [Python SDK Integration](../patterns/python-sdk-integration.md)
- [Trace Linking](../patterns/trace-linking.md)
