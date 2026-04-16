# Python SDK Integration

> **Purpose**: Complete setup guide for the Langfuse Python SDK with decorators and context managers
> **MCP Validated**: 2026-02-17

## When to Use

- Instrumenting any Python LLM application for observability
- Adding tracing, cost tracking, and scoring to existing pipelines
- Setting up Langfuse for the first time in a project

## Implementation

```python
"""Langfuse Python SDK integration - complete setup."""

import os
from langfuse import get_client, observe, propagate_attributes

# ── 1. Environment Variables ──────────────────────────────────
# Set in .env or deployment config:
# LANGFUSE_SECRET_KEY=sk-lf-...
# LANGFUSE_PUBLIC_KEY=pk-lf-...
# LANGFUSE_BASE_URL=https://cloud.langfuse.com

# ── 2. Client Initialization ─────────────────────────────────
langfuse = get_client()

# Verify connection
assert langfuse.auth_check(), "Langfuse authentication failed"


# ── 3. Decorator-Based Tracing ────────────────────────────────
@observe()
def preprocess_document(document: dict) -> dict:
    """Automatically traced as a span. Input/output captured."""
    cleaned = document.copy()
    cleaned["text"] = cleaned["text"].strip()
    return cleaned


@observe(as_type="generation")
def extract_fields(text: str, model: str = "gemini-2.0-flash") -> dict:
    """Traced as a generation. Captures model, tokens, cost."""
    # Your LLM call here
    response = llm_client.generate(
        prompt=f"Extract invoice fields from: {text}",
        model=model,
        temperature=0.0
    )
    return response


@observe()
def process_invoice(document: dict) -> dict:
    """Top-level function creates the trace. Nested calls auto-nest."""
    cleaned = preprocess_document(document)
    result = extract_fields(cleaned["text"])
    return result


# ── 4. Context Manager Tracing ────────────────────────────────
def process_with_context(document: dict) -> dict:
    """Manual tracing with context managers for fine-grained control."""
    with langfuse.start_as_current_observation(
        as_type="span",
        name="process-invoice"
    ) as root:
        root.update(
            input=document,
            metadata={"source": "api"}
        )

        with propagate_attributes(
            user_id=document.get("user_id", "unknown"),
            session_id=document.get("session_id"),
            tags=["invoice-extraction"]
        ):
            # Nested generation
            with langfuse.start_as_current_observation(
                as_type="generation",
                name="extract-fields",
                model="gemini-2.0-flash"
            ) as gen:
                result = llm_client.generate(document["text"])
                gen.update(
                    input=document["text"],
                    output=result,
                    usage_details={"input": 500, "output": 120},
                    cost_details={"total": 0.001}
                )

        root.update(output=result)

    langfuse.flush()
    return result


# ── 5. Scoring During Execution ───────────────────────────────
@observe(as_type="generation")
def extract_and_score(text: str) -> dict:
    """Extract fields and score the result inline."""
    with langfuse.start_as_current_observation(
        as_type="generation",
        name="scored-extraction",
        model="gemini-2.0-flash"
    ) as gen:
        result = llm_client.generate(text)
        gen.update(output=result)

        # Score this generation
        gen.score(
            name="has_required_fields",
            value=1 if all_fields_present(result) else 0,
            data_type="BOOLEAN"
        )
    return result
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `LANGFUSE_SECRET_KEY` | None | Server-side API key |
| `LANGFUSE_PUBLIC_KEY` | None | Client-side API key |
| `LANGFUSE_BASE_URL` | `https://cloud.langfuse.com` | API endpoint (EU) |
| `LANGFUSE_TRACING_ENVIRONMENT` | None | Environment label (production/staging) |
| `LANGFUSE_OBSERVE_DECORATOR_IO_CAPTURE_ENABLED` | `true` | Capture function I/O |

## Example Usage

```python
# Minimal setup - just decorate your functions
from langfuse import observe

@observe()
def my_pipeline(input_text: str) -> str:
    preprocessed = clean_text(input_text)
    result = call_llm(preprocessed)
    return result

@observe(as_type="generation")
def call_llm(text: str) -> str:
    return llm.generate(text)

# Run - traces are created automatically
output = my_pipeline("Extract fields from this invoice...")
```

## Disabling I/O Capture

```python
# For large inputs/outputs, disable capture to reduce overhead
@observe(capture_input=False, capture_output=False)
def process_large_document(large_text: str) -> dict:
    return extract(large_text)
```

## See Also

- [Traces and Spans](../concepts/traces-spans.md)
- [Generations](../concepts/generations.md)
- [Cloud Run Instrumentation](../patterns/cloud-run-instrumentation.md)
