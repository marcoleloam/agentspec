# Middleware

> **Purpose**: Request interception for auth, redirects, headers, geolocation
> **Confidence**: 0.90
> **MCP Validated**: 2026-03-29

## Overview

Middleware runs before every matched request at the edge. Use for authentication redirects, geolocation-based routing, A/B testing, and request headers. Defined in `middleware.ts` at the project root.

## The Concept

```tsx
// middleware.ts — at project root
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  // Auth check
  const token = request.cookies.get("session")?.value;

  if (!token && request.nextUrl.pathname.startsWith("/dashboard")) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  // Add custom headers
  const response = NextResponse.next();
  response.headers.set("x-request-id", crypto.randomUUID());
  return response;
}

// Only run on matched paths
export const config = {
  matcher: [
    "/dashboard/:path*",
    "/api/:path*",
    // Skip static files and images
    "/((?!_next/static|_next/image|favicon.ico).*)",
  ],
};
```

## Quick Reference

| Action | Method |
|--------|--------|
| Continue | `NextResponse.next()` |
| Redirect | `NextResponse.redirect(url)` |
| Rewrite | `NextResponse.rewrite(url)` |
| Add headers | `response.headers.set(key, value)` |
| Read cookies | `request.cookies.get(name)` |
| Read geo | `request.geo?.country` |

## Common Mistakes

### Wrong

```tsx
// Heavy computation in middleware — runs on EVERY request
export function middleware(req) {
  const data = await fetch("https://slow-api.com/validate"); // slow!
}
```

### Correct

```tsx
// Keep middleware fast — only check cookies/headers
export function middleware(req) {
  const token = req.cookies.get("session"); // fast
  if (!token) return NextResponse.redirect("/login");
}
```

## Related

- [auth-patterns.md](../patterns/auth-patterns.md)
- [app-router.md](../concepts/app-router.md)
