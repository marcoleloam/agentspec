# BaseModel

> **Purpose**: Core class for creating validated data models in Pydantic
> **Confidence**: 0.95
> **MCP Validated**: 2026-01-25

## Overview

BaseModel is the foundation of Pydantic. All models inherit from it to get automatic
validation, type coercion, and serialization. Define fields using Python type hints,
and Pydantic handles validation at instantiation.

## The Pattern

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date

class Order(BaseModel):
    """Order extraction model for LLM output validation."""

    order_id: str = Field(..., description="Unique order identifier")
    supplier_name: str = Field(..., min_length=1)
    order_date: date
    total_amount: float = Field(..., ge=0)
    currency: str = Field(default="USD", max_length=3)
    notes: Optional[str] = None

    model_config = {
        "str_strip_whitespace": True,
        "validate_default": True,
    }
```

## Quick Reference

| Input | Output | Notes |
|-------|--------|-------|
| `{"order_id": "ORD-001", ...}` | `Order(...)` | Dict to model |
| `'{"order_id": "ORD-001"}'` | `Order(...)` | JSON via `model_validate_json` |
| `order.model_dump()` | `dict` | Model to dict |
| `order.model_dump_json()` | `str` | Model to JSON string |

## Field Configuration

```python
from pydantic import Field

# Required field with description
order_id: str = Field(..., description="Unique ID")

# Optional with default
currency: str = Field(default="USD")

# Numeric constraints
amount: float = Field(..., ge=0, le=1000000)

# String constraints
name: str = Field(..., min_length=1, max_length=100)

# Alias for JSON key mapping
supplier: str = Field(..., alias="supplierName")
```

## Common Mistakes

### Wrong

```python
class Order(BaseModel):
    # Missing type hints - no validation!
    order_id = ""
    amount = 0.0
```

### Correct

```python
class Order(BaseModel):
    # Type hints enable validation
    order_id: str
    amount: float = Field(..., ge=0)
```

## Model Methods

```python
# Instantiation
order = Order(order_id="ORD-001", supplier_name="Example Corp", ...)

# From dict
order = Order.model_validate({"order_id": "ORD-001", ...})

# From JSON string (for LLM output)
order = Order.model_validate_json('{"order_id": "ORD-001", ...}')

# To dict
data = order.model_dump()
data = order.model_dump(exclude_none=True)  # Skip None fields

# To JSON
json_str = order.model_dump_json(indent=2)

# JSON Schema (for LLM prompts)
schema = Order.model_json_schema()
```

## Related

- [field-types.md](field-types.md)
- [validators.md](validators.md)
- [extraction-schema.md](../patterns/extraction-schema.md)
