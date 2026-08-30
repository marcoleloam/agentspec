# API Routes

> **Purpose**: Route handlers with validation, error handling, streaming
> **MCP Validated**: 2026-03-29

## When to Use

- Building REST API endpoints in Next.js
- Handling webhooks from external services
- Streaming large responses to the client

## Implementation

```tsx
// app/api/products/route.ts
import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";

const CreateProductSchema = z.object({
  name: z.string().min(1),
  price: z.number().positive(),
  category: z.string(),
});

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const category = searchParams.get("category");

  const products = await db.query(
    "SELECT * FROM products WHERE ($1::text IS NULL OR category = $1)",
    [category]
  );

  return NextResponse.json(products);
}

export async function POST(request: NextRequest) {
  const body = await request.json();
  const parsed = CreateProductSchema.safeParse(body);

  if (!parsed.success) {
    return NextResponse.json(
      { error: parsed.error.flatten() },
      { status: 400 }
    );
  }

  const product = await db.insert("products", parsed.data);
  return NextResponse.json(product, { status: 201 });
}
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `export const runtime` | `"nodejs"` | `"edge"` for edge runtime |
| `export const dynamic` | auto | `"force-dynamic"` for no cache |
| `export const maxDuration` | 10 | Max execution time in seconds |

## Example Usage

```tsx
// app/api/products/[id]/route.ts — dynamic segment
export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const product = await db.findOne("products", params.id);
  if (!product) {
    return NextResponse.json({ error: "Not found" }, { status: 404 });
  }
  return NextResponse.json(product);
}
```

## See Also

- [auth-patterns.md](../patterns/auth-patterns.md)
- [middleware.md](../concepts/middleware.md)
