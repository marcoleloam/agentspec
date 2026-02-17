# Multimodal Prompting

> **Purpose**: Combine text and images in Gemini requests
> **Confidence**: 0.95
> **MCP Validated**: 2026-01-25

## Overview

Gemini's native multimodal capabilities allow processing text and images simultaneously. For document extraction, this eliminates the need for separate OCR preprocessing. Each image consumes 258-1290 tokens depending on resolution.

## The Pattern

```python
from google import genai
from google.genai import types
import base64

client = genai.Client(vertexai=True, project="your-project-id", location="us-central1")

# Load image
with open("document.png", "rb") as f:
    image_data = base64.b64encode(f.read()).decode("utf-8")

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=[
        types.Content(
            parts=[
                types.Part(text="Extract all line items from this document as JSON."),
                types.Part(
                    inline_data=types.Blob(
                        mime_type="image/png",
                        data=image_data
                    )
                )
            ]
        )
    ]
)
print(response.text)
```

## Image from GCS

```python
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=[
        types.Content(
            parts=[
                types.Part(text="Extract the document total."),
                types.Part(
                    file_data=types.FileData(
                        mime_type="application/pdf",
                        file_uri="gs://bucket/documents/sample-001.pdf"
                    )
                )
            ]
        )
    ]
)
```

## Quick Reference

| Input Type | Tokens | Notes |
| ---------- | ------ | ----- |
| Image (any size) | 258-1290 | Higher res = more tokens |
| PDF page | ~258 per page | Native understanding |
| Video (per second) | 258 | 1 fps sample rate |

## Best Practices for Documents

| Practice | Reason |
| -------- | ------ |
| Use PNG over JPEG | Better text clarity |
| Resize to 1024px max | Reduces token cost |
| Put text prompt first | Better instruction following |
| Be specific about output | "Extract as JSON with fields..." |

## Common Mistakes

### Wrong

```python
# Image after text without structure
contents = "Extract data" + image  # Won't work
```

### Correct

```python
# Properly structured multimodal content
contents = [
    types.Content(
        parts=[
            types.Part(text="Extract data as JSON."),
            types.Part(inline_data=types.Blob(mime_type="image/png", data=img))
        ]
    )
]
```

## Related

- [structured-output.md](structured-output.md)
- [../patterns/document-extraction.md](../patterns/document-extraction.md)
