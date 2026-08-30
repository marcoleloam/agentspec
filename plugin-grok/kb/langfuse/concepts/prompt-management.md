# Prompt Management

> **Purpose**: Version, cache, and manage prompts centrally with labels and linking
> **Confidence**: 0.95
> **MCP Validated**: 2026-02-17

## Overview

Langfuse prompt management provides centralized storage, versioning, and retrieval of prompt templates. Prompts support two types (text and chat), use `{{variable}}` template syntax, and are cached client-side for zero-latency retrieval. Labels like "production" and "staging" control which version is served. Changes can be made via UI without redeployment.

## The Pattern

```python
from langfuse import get_client

langfuse = get_client()

# Create a text prompt
langfuse.create_prompt(
    name="invoice-extractor",
    type="text",
    prompt="Extract the following fields from this invoice:\n"
           "- vendor_name\n- total_amount\n- invoice_date\n\n"
           "Invoice text: {{invoice_text}}\n\n"
           "Return JSON with the extracted fields.",
    labels=["production"]
)

# Fetch and compile the prompt
prompt = langfuse.get_prompt("invoice-extractor")
compiled = prompt.compile(invoice_text="Invoice #1234 from Acme Corp...")
print(compiled)
# "Extract the following fields from this invoice:..."
```

## Prompt Types

| Type | Format | Template Syntax | Use Case |
|------|--------|----------------|----------|
| `text` | Single string | `{{variable}}` | Simple prompts, completions |
| `chat` | Array of messages | `{{variable}}` in content | Chat-based models, system/user roles |

## Chat Prompt Example

```python
langfuse.create_prompt(
    name="chat-extractor",
    type="chat",
    prompt=[
        {"role": "system", "content": "You are an invoice extraction assistant."},
        {"role": "user", "content": "Extract fields from: {{invoice_text}}"}
    ],
    labels=["staging"]
)

prompt = langfuse.get_prompt("chat-extractor", label="staging")
compiled = prompt.compile(invoice_text="Invoice #5678...")
# Returns list of message dicts with variables replaced
```

## Versioning and Labels

| Concept | Description |
|---------|-------------|
| **Version** | Auto-incremented on each create with same name |
| **Labels** | String tags to mark versions (e.g., "production", "staging") |
| **Default fetch** | Returns the version labeled "production" |
| **Specific label** | `get_prompt("name", label="staging")` |
| **Specific version** | `get_prompt("name", version=3)` |

## Caching

Prompts are cached client-side by the SDK. Retrieval after first fetch is as fast as reading from memory. No additional latency is added to your application from prompt management.

| Cache Behavior | Detail |
|----------------|--------|
| Client-side | SDK caches in-process |
| Server-side | Langfuse server also caches |
| TTL | Configurable; default refreshes periodically |
| Cache miss | Falls back to API call |

## Linking Prompts to Traces

When using a prompt in a generation, link it to the trace for version-based analytics:

```python
prompt = langfuse.get_prompt("invoice-extractor")
compiled = prompt.compile(invoice_text=text)

with langfuse.start_as_current_observation(
    as_type="generation",
    name="extract",
    model="gemini-2.0-flash",
    langfuse_prompt=prompt  # Links prompt version to this generation
) as gen:
    result = call_llm(compiled)
    gen.update(output=result)
```

## Common Mistakes

### Wrong

```python
# Hardcoding prompts in source code
PROMPT = "Extract invoice fields from: {text}"
```

### Correct

```python
# Use Langfuse prompt management for versioning and analytics
prompt = langfuse.get_prompt("invoice-extractor")
compiled = prompt.compile(invoice_text=text)
```

## Related

- [Generations](../concepts/generations.md)
- [Model Comparison](../concepts/model-comparison.md)
- [Quality Feedback Loops](../patterns/quality-feedback-loops.md)
