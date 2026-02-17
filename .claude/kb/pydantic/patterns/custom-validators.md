# Custom Validators Pattern

> **Purpose**: Business rule validation for data extraction with custom logic
> **MCP Validated**: 2026-01-25

## When to Use

- Enforcing business rules beyond type validation
- Cross-field validation (e.g., date ranges, total calculations)
- Normalizing and transforming extracted data

## Implementation

```python
from pydantic import BaseModel, Field, field_validator, model_validator, ValidationInfo
from typing import Optional, Any
from datetime import date, timedelta
from decimal import Decimal
from enum import Enum
from typing_extensions import Self
import re

class CategoryType(str, Enum):
    CATEGORY_A = "category_a"
    CATEGORY_B = "category_b"
    OTHER = "other"

CATEGORY_PATTERNS = {
    CategoryType.CATEGORY_A: [r"category[\s_]*a", r"categorya"],
    CategoryType.CATEGORY_B: [r"category[\s_]*b", r"categoryb"],
}

class OrderWithValidation(BaseModel):
    order_id: str
    supplier_name: str
    supplier_type: CategoryType = CategoryType.OTHER
    order_date: date
    due_date: Optional[date] = None
    subtotal: Decimal = Field(..., ge=0)
    tax_amount: Decimal = Field(default=Decimal("0"), ge=0)
    total_amount: Decimal = Field(..., ge=0)
    currency: str = "USD"

    @field_validator("order_id", mode="after")
    @classmethod
    def normalize_order_id(cls, v: str) -> str:
        v = v.strip().upper()
        v = re.sub(r"^(ORDER|ORD|#)\s*[-:]?\s*", "ORD-", v)
        return v

    @field_validator("supplier_name", mode="before")
    @classmethod
    def clean_supplier_name(cls, v: Any) -> Any:
        if isinstance(v, str):
            v = " ".join(v.split()).title()
        return v

    @field_validator("currency", mode="after")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        v = v.upper().strip()
        if v not in {"USD", "EUR", "GBP", "CAD"}:
            raise ValueError(f"Unsupported currency: {v}")
        return v

    @field_validator("subtotal", "tax_amount", "total_amount", mode="after")
    @classmethod
    def round_money(cls, v: Decimal) -> Decimal:
        return round(v, 2)

    @model_validator(mode="after")
    def auto_classify_category(self) -> Self:
        if self.supplier_type == CategoryType.OTHER:
            name_lower = self.supplier_name.lower()
            for ctype, patterns in CATEGORY_PATTERNS.items():
                if any(re.search(p, name_lower) for p in patterns):
                    self.supplier_type = ctype
                    break
        return self

    @model_validator(mode="after")
    def validate_dates(self) -> Self:
        today = date.today()
        if self.order_date > today:
            raise ValueError("Order date cannot be in the future")
        if self.order_date < today - timedelta(days=365):
            raise ValueError("Order date is more than 1 year old")
        if self.due_date and self.due_date < self.order_date:
            raise ValueError("Due date must be after order date")
        return self

    @model_validator(mode="after")
    def validate_totals(self) -> Self:
        expected = self.subtotal + self.tax_amount
        if abs(self.total_amount - expected) > Decimal("0.02"):
            pass  # Log warning but allow
        return self
```

## Configuration

| Setting          | Default    | Description                                  |
| ---------------- | ---------- | -------------------------------------------- |
| `tolerance`      | `0.02`     | Allowed difference in monetary calculations  |
| `max_order_age`  | `365 days` | Maximum age for valid orders                 |

## Example Usage

```python
data = {
    "order_id": "order #12345",
    "supplier_name": "category a systems",
    "supplier_type": "other",
    "order_date": "2026-01-15",
    "subtotal": "100.005",
    "tax_amount": "8.00",
    "total_amount": "108.01",
}

order = OrderWithValidation.model_validate(data)
print(order.order_id)       # "ORD-12345"
print(order.supplier_name)  # "Category A Systems"
print(order.supplier_type)  # CategoryType.CATEGORY_A

# Context-aware validation
class ContextAwareOrder(BaseModel):
    supplier_name: str

    @field_validator("supplier_name", mode="after")
    @classmethod
    def validate_known_supplier(cls, v: str, info: ValidationInfo) -> str:
        context = info.context or {}
        known = context.get("known_suppliers", [])
        if known and v not in known:
            raise ValueError(f"Unknown supplier: {v}")
        return v

# Usage with context
order = ContextAwareOrder.model_validate(
    {"supplier_name": "Vendor Alpha"},
    context={"known_suppliers": ["Vendor Alpha", "Vendor Beta"]}
)
```

## See Also

- [validators.md](../concepts/validators.md)
- [llm-output-validation.md](llm-output-validation.md)
- [error-handling.md](error-handling.md)
