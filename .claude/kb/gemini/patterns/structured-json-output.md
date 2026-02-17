# Structured JSON Output Pattern

> **Purpose**: Guarantee valid JSON responses matching a defined schema
> **MCP Validated**: 2026-01-25

## When to Use

- Extracting data that feeds into databases
- Building APIs that return structured responses
- Ensuring consistent output format across requests
- Validating extracted data at API level

## Implementation

```python
from google import genai
from google.genai import types
import json
from typing import TypedDict, List, Optional
from pydantic import BaseModel


class LineItem(BaseModel):
    """Pydantic model for line item validation."""
    description: str
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    total: float


class Document(BaseModel):
    """Pydantic model for document validation."""
    document_id: str
    source_name: str
    created_date: str
    total_value: float
    items: List[LineItem] = []


def create_json_schema_from_pydantic(model: type[BaseModel]) -> dict:
    """Convert Pydantic model to JSON Schema for Gemini."""
    return model.model_json_schema()


class StructuredExtractor:
    """Extract data with guaranteed JSON schema compliance."""

    def __init__(self, project_id: str, location: str = "us-central1"):
        self.client = genai.Client(
            vertexai=True,
            project=project_id,
            location=location
        )

    def extract_with_schema(
        self,
        prompt: str,
        content: types.Content,
        schema: dict,
        model: str = "gemini-2.5-flash"
    ) -> dict:
        """Extract data matching the provided JSON schema."""

        response = self.client.models.generate_content(
            model=model,
            contents=[
                types.Content(parts=[types.Part(text=prompt)]),
                content
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=schema,
                temperature=0.2,
            )
        )

        # Parse and return
        return json.loads(response.text)

    def extract_document(self, image_content: types.Content) -> Document:
        """Extract document data with Pydantic validation."""
        schema = create_json_schema_from_pydantic(Document)

        raw_data = self.extract_with_schema(
            prompt="Extract all document information from this file.",
            content=image_content,
            schema=schema
        )

        # Validate with Pydantic
        return Document(**raw_data)


# Using with Pydantic models (recommended)
def extract_validated(extractor: StructuredExtractor, image_path: str) -> Document:
    """Extract and validate document data."""
    import base64

    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    content = types.Content(
        parts=[
            types.Part(
                inline_data=types.Blob(mime_type="image/png", data=image_data)
            )
        ]
    )

    return extractor.extract_document(content)
```

## Configuration

| Setting | Default | Description |
| ------- | ------- | ----------- |
| `response_mime_type` | `"application/json"` | Required for JSON mode |
| `response_schema` | JSON Schema dict | Defines output structure |
| `temperature` | `0.2` | Low for consistent structure |

## Schema Best Practices

```python
# DO: Use required fields for critical data
good_schema = {
    "type": "object",
    "properties": {
        "document_id": {"type": "string"},
        "total": {"type": "number"}
    },
    "required": ["document_id", "total"]  # Ensures these are always present
}

# DO: Add descriptions for clarity
better_schema = {
    "type": "object",
    "properties": {
        "created_date": {
            "type": "string",
            "description": "Document date in YYYY-MM-DD format"
        }
    }
}

# DON'T: Duplicate schema in prompt
# The schema should only be in response_schema, not repeated in text
```

## Example Usage

```python
extractor = StructuredExtractor(project_id="your-project-id")

# With Pydantic validation
document = extract_validated(extractor, "document.png")
print(f"Source: {document.source_name}")
print(f"Total: ${document.total_value:.2f}")

# Direct schema usage
custom_schema = {
    "type": "object",
    "properties": {"total": {"type": "number"}},
    "required": ["total"]
}
result = extractor.extract_with_schema(
    prompt="Extract the total amount.",
    content=image_content,
    schema=custom_schema
)
```

## See Also

- [document-extraction.md](document-extraction.md)
- [../concepts/structured-output.md](../concepts/structured-output.md)
