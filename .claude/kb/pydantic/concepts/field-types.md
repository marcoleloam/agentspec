# Field Types

> **Purpose**: Type hints, Enums, Literals, and Optional fields for schema definition
> **Confidence**: 0.95
> **MCP Validated**: 2026-01-25

## Overview

Pydantic uses Python type hints to define field types. It supports primitives,
complex types, Enums, Literals for constrained values, and Optional for nullable
fields. Type coercion happens automatically where possible.

## The Pattern

```python
from pydantic import BaseModel, Field
from typing import Optional, Literal
from enum import Enum
from datetime import date
from decimal import Decimal

class CategoryType(str, Enum):
    CATEGORY_A = "category_a"
    CATEGORY_B = "category_b"
    CATEGORY_C = "category_c"
    OTHER = "other"

class LineItem(BaseModel):
    description: str
    quantity: int = Field(..., ge=1)
    unit_price: Decimal = Field(..., ge=0)
    amount: Decimal = Field(..., ge=0)

class Order(BaseModel):
    order_id: str
    supplier_name: str
    supplier_type: CategoryType
    order_date: date
    due_date: Optional[date] = None
    currency: Literal["USD", "EUR", "GBP"] = "USD"
    line_items: list[LineItem] = Field(default_factory=list)
```

## Quick Reference

| Input | Output | Notes |
|-------|--------|-------|
| `"category_a"` | `CategoryType.CATEGORY_A` | Enum coercion |
| `"2026-01-15"` | `date(2026, 1, 15)` | ISO date string |
| `"123.45"` | `Decimal("123.45")` | String to Decimal |
| `None` | `None` | Optional field |

## Primitive Types

```python
name: str                    # Required string
count: int                   # Coerces "123" to 123
amount: float                # Coerces int and string
active: bool                 # Coerces 1/0, "true"/"false"
price: Decimal               # Precise decimal math
```

## Optional and Default

```python
from typing import Optional

# Optional with None default
notes: Optional[str] = None

# Optional with value default
currency: str = "USD"

# Required (no default)
order_id: str

# Factory default for mutable types
items: list[str] = Field(default_factory=list)
```

## Enum Types

```python
from enum import Enum

class CategoryType(str, Enum):
    """Inherit from str for JSON serialization."""
    CATEGORY_A = "category_a"
    CATEGORY_B = "category_b"
    OTHER = "other"

# Usage in model
supplier_type: CategoryType

# Accepts: "category_a", CategoryType.CATEGORY_A
```

## Literal Types

```python
from typing import Literal

# Constrained to specific values
status: Literal["pending", "paid", "cancelled"]
currency: Literal["USD", "EUR", "GBP"] = "USD"
```

## Common Mistakes

### Wrong

```python
# Mutable default - shared between instances!
items: list[str] = []
```

### Correct

```python
# Factory creates new list per instance
items: list[str] = Field(default_factory=list)
```

## Type Coercion Examples

```python
# All valid inputs for int field:
# 123 (int), "123" (str), 123.0 (float)

# All valid for date field:
# date(2026, 1, 15), "2026-01-15", datetime(2026, 1, 15)

# Enum accepts string value:
# "category_a" -> CategoryType.CATEGORY_A
```

## Related

- [base-model.md](base-model.md)
- [nested-models.md](nested-models.md)
- [extraction-schema.md](../patterns/extraction-schema.md)
