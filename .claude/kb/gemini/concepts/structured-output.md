# Structured Output

> **Purpose**: Generate guaranteed JSON responses with schema validation
> **Confidence**: 0.95
> **MCP Validated**: 2026-01-25

## Overview

Gemini's Structured Outputs feature guarantees responses adhere to a specified JSON schema. This is essential for document extraction where consistent field names and types are required for downstream processing.

## The Pattern

```python
from google import genai
from google.genai import types

client = genai.Client(vertexai=True, project="your-project-id", location="us-central1")

# Define the schema
document_schema = {
    "type": "object",
    "properties": {
        "document_id": {"type": "string"},
        "source_name": {"type": "string"},
        "created_date": {"type": "string", "format": "date"},
        "total_value": {"type": "number"},
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "description": {"type": "string"},
                    "quantity": {"type": "integer"},
                    "unit_price": {"type": "number"},
                    "total": {"type": "number"}
                }
            }
        }
    },
    "required": ["document_id", "source_name", "total_value"]
}

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=[image_content],
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=document_schema
    )
)

# Response is guaranteed valid JSON matching schema
import json
data = json.loads(response.text)
```

## Quick Reference

| Config Key | Value | Purpose |
| ---------- | ----- | ------- |
| `response_mime_type` | `"application/json"` | Enable JSON mode |
| `response_schema` | JSON Schema object | Define structure |

## Supported JSON Schema Features (Gemini 2.5+)

| Feature | Support | Example |
| ------- | ------- | ------- |
| Basic types | Yes | `string`, `number`, `integer`, `boolean` |
| Arrays | Yes | `{"type": "array", "items": {...}}` |
| Nested objects | Yes | `{"type": "object", "properties": {...}}` |
| Required fields | Yes | `"required": ["field1", "field2"]` |
| anyOf | Yes | Union types |
| $ref | Yes | Schema references |
| Enums | Yes | `{"enum": ["a", "b", "c"]}` |

## Best Practices

| Practice | Reason |
| -------- | ------ |
| Match schema order in prompts | Improves output quality |
| Use required fields | Ensures critical data extracted |
| Keep schemas focused | One document type per schema |
| Include descriptions | Helps model understand intent |

## Common Mistakes

### Wrong

```python
# Duplicating schema in prompt
prompt = """
Extract document data as JSON:
{"document_id": "...", "total": "..."}  # DON'T repeat schema here
"""
```

### Correct

```python
# Schema only in config, clear instruction in prompt
prompt = "Extract all document information from this file."
config = types.GenerateContentConfig(
    response_mime_type="application/json",
    response_schema=document_schema  # Schema here only
)
```

## Related

- [multimodal-prompting.md](multimodal-prompting.md)
- [../patterns/structured-json-output.md](../patterns/structured-json-output.md)
