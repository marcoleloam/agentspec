# Trace Linking

> **Purpose**: Link traces across services for distributed tracing in multi-service architectures
> **MCP Validated**: 2026-02-17

## When to Use

- Multi-service architectures where a request spans several Cloud Run services
- Linking Pub/Sub-triggered processing back to the originating trace
- Correlating frontend requests with backend LLM pipeline traces
- Building end-to-end observability across microservices

## Implementation

```python
"""Cross-service trace linking with Langfuse."""

import json
import uuid
from langfuse import get_client, observe, propagate_attributes

langfuse = get_client()


# ── Service A: API Gateway ────────────────────────────────────
def handle_api_request(request_data: dict) -> dict:
    """First service: receives request, creates trace, forwards."""
    trace_id = str(uuid.uuid4())
    session_id = request_data.get("session_id", str(uuid.uuid4()))

    with langfuse.start_as_current_observation(
        as_type="span",
        name="api-gateway",
        trace_id=trace_id
    ) as span:
        with propagate_attributes(
            user_id=request_data.get("user_id"),
            session_id=session_id,
            tags=["api-gateway"]
        ):
            span.update(input=request_data)

            # Forward to downstream service with trace context
            message = {
                "data": request_data,
                "trace_context": {
                    "trace_id": trace_id,
                    "session_id": session_id,
                    "user_id": request_data.get("user_id"),
                    "parent_observation_id": span.id
                }
            }
            publish_to_pubsub("extraction-topic", message)

            span.update(output={"status": "forwarded"})

    langfuse.flush()
    return {"trace_id": trace_id, "status": "processing"}


# ── Service B: Extraction Worker ──────────────────────────────
def handle_extraction(pubsub_message: dict) -> dict:
    """Second service: picks up trace context, continues trace."""
    data = pubsub_message["data"]
    ctx = pubsub_message["trace_context"]

    # Continue the same trace from Service A
    with langfuse.start_as_current_observation(
        as_type="span",
        name="extraction-worker",
        trace_id=ctx["trace_id"]
    ) as span:
        with propagate_attributes(
            user_id=ctx.get("user_id"),
            session_id=ctx.get("session_id"),
            tags=["extraction-worker"],
            metadata={
                "parent_service": "api-gateway",
                "parent_observation_id": ctx.get(
                    "parent_observation_id"
                )
            }
        ):
            span.update(input=data)

            # LLM generation within linked trace
            with langfuse.start_as_current_observation(
                as_type="generation",
                name="extract-fields",
                model="gemini-2.0-flash"
            ) as gen:
                result = call_extraction_llm(data["text"])
                gen.update(
                    output=result,
                    usage_details={
                        "input": 400, "output": 100
                    }
                )

            # Forward trace context to next service
            forward_message = {
                "result": result,
                "trace_context": {
                    "trace_id": ctx["trace_id"],
                    "session_id": ctx["session_id"],
                    "user_id": ctx.get("user_id")
                }
            }
            publish_to_pubsub("validation-topic", forward_message)

            span.update(output=result)

    langfuse.flush()
    return result


# ── Service C: Validation Worker ──────────────────────────────
def handle_validation(pubsub_message: dict) -> dict:
    """Third service: validates and scores within same trace."""
    result = pubsub_message["result"]
    ctx = pubsub_message["trace_context"]

    with langfuse.start_as_current_observation(
        as_type="span",
        name="validation-worker",
        trace_id=ctx["trace_id"]
    ) as span:
        with propagate_attributes(
            user_id=ctx.get("user_id"),
            session_id=ctx.get("session_id"),
            tags=["validation-worker"]
        ):
            is_valid = validate_extraction(result)
            span.update(output={"valid": is_valid})

            # Score the entire trace
            langfuse.create_score(
                name="extraction_valid",
                value=1 if is_valid else 0,
                trace_id=ctx["trace_id"],
                data_type="BOOLEAN",
                comment="Cross-service validation result"
            )

    langfuse.flush()
    return {"valid": is_valid}
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `trace_id` | Auto-generated | Shared across services |
| `session_id` | Auto-generated | Groups related traces |
| Propagation method | Message payload | Pub/Sub, HTTP headers |

## Trace Context Propagation

| Transport | How to Propagate |
|-----------|-----------------|
| Pub/Sub message | Include `trace_context` in message data |
| HTTP request | Pass `trace_id` in `X-Langfuse-Trace-Id` header |
| gRPC metadata | Add `trace_id` to metadata |
| Cloud Tasks | Include in task payload |

## Architecture

```text
Service A (API Gateway)          trace_id=abc
    |
    | Pub/Sub message with trace_context
    v
Service B (Extraction Worker)    trace_id=abc (continued)
    |
    | Pub/Sub message with trace_context
    v
Service C (Validation Worker)    trace_id=abc (continued)
    |
    v
Langfuse Dashboard: Single trace with all 3 services
```

## See Also

- [Traces and Spans](../concepts/traces-spans.md)
- [Cloud Run Instrumentation](../patterns/cloud-run-instrumentation.md)
- [Dashboard Metrics](../patterns/dashboard-metrics.md)
