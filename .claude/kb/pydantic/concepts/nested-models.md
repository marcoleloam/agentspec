# Nested Models

> **Purpose**: Composing BaseModel classes for complex, hierarchical data structures
> **Confidence**: 0.95
> **MCP Validated**: 2026-01-25

## Overview

Pydantic supports nested models where one BaseModel contains another as a field type.
This enables validation of complex structures like orders with line items. Nested
models are validated recursively, and JSON Schema generation includes all nested definitions.

## The Pattern

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date
from decimal import Decimal
from enum import Enum

class CategoryType(str, Enum):
    CATEGORY_A = "category_a"
    CATEGORY_B = "category_b"
    OTHER = "other"

class LineItem(BaseModel):
    description: str = Field(..., min_length=1)
    quantity: int = Field(..., ge=1)
    unit_price: Decimal = Field(..., ge=0)
    amount: Decimal = Field(..., ge=0)

class Order(BaseModel):
    order_id: str
    supplier_type: CategoryType
    order_date: date
    line_items: list[LineItem] = Field(default_factory=list)
    total_amount: Decimal
```

## Quick Reference

| Input | Output | Notes |
|-------|--------|-------|
| `{"line_items": [{"..."}]}` | `Order(line_items=[LineItem(...)])` | Dict to nested |
| `order.line_items[0].amount` | `Decimal` | Access list item |

## Instantiation

```python
data = {
    "order_id": "ORD-001",
    "supplier_type": "category_a",
    "order_date": "2026-01-15",
    "line_items": [
        {"description": "Delivery", "quantity": 1, "unit_price": "2.99", "amount": "2.99"}
    ],
    "total_amount": "3.24"
}
order = Order.model_validate(data)

# From JSON string
order = Order.model_validate_json(json_string)
```

## Lists of Nested Models

```python
line_items: list[LineItem]  # Type hint

for item in order.line_items:
    print(f"{item.description}: {item.amount}")

# Default empty list
line_items: list[LineItem] = Field(default_factory=list)
```

## Common Mistakes

### Wrong

```python
class Order(BaseModel):
    line_items: list[dict]  # No validation inside!
```

### Correct

```python
class Order(BaseModel):
    line_items: list[LineItem]  # Full validation
```

## Validation Cascade

```python
try:
    Order.model_validate({"line_items": [{"quantity": -1}]})
except ValidationError as e:
    # Error location: "line_items.0.quantity"
    for error in e.errors():
        print(error["loc"], error["msg"])
```

## Related

- [base-model.md](base-model.md)
- [field-types.md](field-types.md)
- [extraction-schema.md](../patterns/extraction-schema.md)
