# Document Extraction Pattern

> **Purpose**: Extract structured data from document images using Gemini vision
> **MCP Validated**: 2026-01-25

## When to Use

- Processing TIFF/PNG/PDF document images
- Extracting vendor, line items, totals from documents
- Building automated document intelligence pipelines
- Replacing manual data entry workflows

## Implementation

```python
from google import genai
from google.genai import types
import base64
import json
from pathlib import Path


class DocumentExtractor:
    """Extract structured data from document images using Gemini."""

    DOCUMENT_SCHEMA = {
        "type": "object",
        "properties": {
            "document_id": {"type": "string", "description": "Unique document number"},
            "source_name": {"type": "string", "description": "Organization or entity name"},
            "vendor_address": {"type": "string"},
            "created_date": {"type": "string", "description": "Date in YYYY-MM-DD format"},
            "due_date": {"type": "string"},
            "subtotal": {"type": "number"},
            "tax_amount": {"type": "number"},
            "total_value": {"type": "number", "description": "Final amount due"},
            "currency": {"type": "string", "default": "USD"},
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "description": {"type": "string"},
                        "quantity": {"type": "number"},
                        "unit_price": {"type": "number"},
                        "total": {"type": "number"}
                    },
                    "required": ["description", "total"]
                }
            }
        },
        "required": ["document_id", "source_name", "created_date", "total_value"]
    }

    EXTRACTION_PROMPT = """Extract all document information from this document image.

Instructions:
- Extract the document number, source details, dates, and all line items
- Convert dates to YYYY-MM-DD format
- Extract numeric values without currency symbols
- If a field is not visible, omit it from the response
- For line items, include description, quantity, unit price, and line total"""

    def __init__(self, project_id: str, location: str = "us-central1"):
        self.client = genai.Client(
            vertexai=True,
            project=project_id,
            location=location
        )
        self.model = "gemini-2.5-flash"

    def extract(self, image_path: str) -> dict:
        """Extract document data from an image file."""
        # Load and encode image
        image_data = self._load_image(image_path)
        mime_type = self._get_mime_type(image_path)

        # Build request
        content = types.Content(
            parts=[
                types.Part(text=self.EXTRACTION_PROMPT),
                types.Part(
                    inline_data=types.Blob(
                        mime_type=mime_type,
                        data=image_data
                    )
                )
            ]
        )

        # Generate with structured output
        response = self.client.models.generate_content(
            model=self.model,
            contents=[content],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=self.DOCUMENT_SCHEMA,
                temperature=0.3,  # Low temp for accuracy
            )
        )

        return json.loads(response.text)

    def _load_image(self, path: str) -> str:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def _get_mime_type(self, path: str) -> str:
        suffix = Path(path).suffix.lower()
        return {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".tiff": "image/tiff",
            ".tif": "image/tiff",
            ".webp": "image/webp",
        }.get(suffix, "image/png")
```

## Configuration

| Setting | Default | Description |
| ------- | ------- | ----------- |
| `model` | `gemini-2.5-flash` | Best cost/quality for documents |
| `temperature` | `0.3` | Low for consistent extraction |
| `response_mime_type` | `application/json` | Enable structured output |

## Example Usage

```python
extractor = DocumentExtractor(project_id="your-project-id")

result = extractor.extract("documents/sample-vendor-001.pdf")
print(result)
# {
#   "document_id": "DOC-2026-001",
#   "source_name": "Example Corp",
#   "created_date": "2026-01-20",
#   "total_value": 45.99,
#   "items": [...]
# }
```

## See Also

- [structured-json-output.md](structured-json-output.md)
- [batch-processing.md](batch-processing.md)
- [../concepts/multimodal-prompting.md](../concepts/multimodal-prompting.md)
