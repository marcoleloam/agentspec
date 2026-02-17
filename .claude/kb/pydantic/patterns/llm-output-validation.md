# LLM Output Validation Pattern

> **Purpose**: Robust validation of JSON responses from LLMs
> **MCP Validated**: 2026-01-25

## When to Use

- Parsing structured JSON from LLM responses
- Validating extraction results from document processing
- Ensuring type safety before database insertion
- Handling malformed or partial LLM outputs

## Implementation

```python
from pydantic import BaseModel, Field, ValidationError, field_validator
from typing import Optional
from datetime import date
from decimal import Decimal
from enum import Enum
import json
import logging

logger = logging.getLogger(__name__)


class CategoryType(str, Enum):
    CATEGORY_A = "category_a"
    CATEGORY_B = "category_b"
    CATEGORY_C = "category_c"
    OTHER = "other"


class LineItem(BaseModel):
    description: str = Field(..., min_length=1)
    quantity: int = Field(default=1, ge=1)
    unit_price: Decimal = Field(..., ge=0)
    amount: Decimal = Field(..., ge=0)


class OrderExtraction(BaseModel):
    """Schema for LLM order extraction output."""

    order_id: str
    supplier_name: str
    supplier_type: CategoryType = CategoryType.OTHER
    order_date: date
    due_date: Optional[date] = None
    subtotal: Decimal = Field(..., ge=0)
    tax_amount: Decimal = Field(default=Decimal("0"), ge=0)
    commission_rate: Optional[Decimal] = Field(default=None, ge=0, le=1)
    commission_amount: Optional[Decimal] = Field(default=None, ge=0)
    total_amount: Decimal = Field(..., ge=0)
    currency: str = Field(default="USD", max_length=3)
    line_items: list[LineItem] = Field(default_factory=list)

    @field_validator("currency", mode="after")
    @classmethod
    def normalize_currency(cls, v: str) -> str:
        return v.upper().strip()

    @field_validator("supplier_name", mode="before")
    @classmethod
    def clean_supplier_name(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v


def validate_llm_output(
    llm_response: str,
    strict: bool = True
) -> tuple[Optional[OrderExtraction], list[dict]]:
    """
    Validate LLM JSON output against order schema.

    Args:
        llm_response: Raw JSON string from LLM
        strict: If False, attempt recovery from partial data

    Returns:
        Tuple of (validated_model or None, list of errors)
    """
    errors = []

    # Step 1: Clean potential markdown formatting
    json_str = llm_response.strip()
    if json_str.startswith("```"):
        # Remove markdown code blocks
        lines = json_str.split("\n")
        json_str = "\n".join(
            line for line in lines
            if not line.startswith("```")
        )

    # Step 2: Parse JSON
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        errors.append({"type": "json_parse", "msg": str(e)})
        return None, errors

    # Step 3: Validate with Pydantic
    try:
        order = OrderExtraction.model_validate(data)
        return order, []
    except ValidationError as e:
        errors = e.errors()
        if strict:
            return None, errors

        # Attempt partial recovery with defaults
        logger.warning(f"Validation errors, attempting recovery: {errors}")
        return _attempt_recovery(data, errors), errors


def _attempt_recovery(data: dict, errors: list) -> Optional[OrderExtraction]:
    """Attempt to recover by applying defaults for missing/invalid fields."""
    # Set defaults for non-critical fields
    defaults = {
        "supplier_type": "other",
        "tax_amount": "0",
        "currency": "USD",
        "line_items": [],
    }

    for key, default in defaults.items():
        if key not in data or data[key] is None:
            data[key] = default

    try:
        return OrderExtraction.model_validate(data)
    except ValidationError:
        return None
```

## Configuration

| Setting          | Default   | Description                      |
| ---------------- | --------- | -------------------------------- |
| `strict`         | `True`    | Fail on any validation error     |
| `currency`       | `"USD"`   | Default currency if missing      |
| `supplier_type`  | `"other"` | Default supplier classification  |

## Example Usage

```python
# Raw LLM response (may include markdown)
llm_response = '''```json
{
    "order_id": "ORD-2026-001",
    "supplier_name": "Vendor Alpha",
    "supplier_type": "category_a",
    "order_date": "2026-01-15",
    "subtotal": 125.50,
    "tax_amount": 10.04,
    "total_amount": 135.54,
    "line_items": [
        {"description": "Product delivery", "quantity": 1, "unit_price": 125.50, "amount": 125.50}
    ]
}
```'''

order, errors = validate_llm_output(llm_response)

if order:
    print(f"Validated: {order.order_id} - ${order.total_amount}")
    # Safe to persist to storage
else:
    print(f"Validation failed: {errors}")
```

## See Also

- [extraction-schema.md](extraction-schema.md)
- [error-handling.md](error-handling.md)
- [validators.md](../concepts/validators.md)
