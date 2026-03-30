# Auth Patterns

> **Purpose**: NextAuth.js v5, middleware auth, session management, protected routes
> **MCP Validated**: 2026-03-29

## When to Use

- Implementing authentication in Next.js
- Protecting routes with middleware
- Managing sessions server-side and client-side

## Implementation

```tsx
// lib/auth.ts — NextAuth v5 (Auth.js) setup
import NextAuth from "next-auth";
import GitHub from "next-auth/providers/github";
import Credentials from "next-auth/providers/credentials";

export const { handlers, signIn, signOut, auth } = NextAuth({
  providers: [
    GitHub,
    Credentials({
      credentials: { email: {}, password: {} },
      authorize: async (credentials) => {
        const user = await verifyUser(credentials);
        return user ?? null;
      },
    }),
  ],
});

// app/api/auth/[...nextauth]/route.ts
import { handlers } from "@/lib/auth";
export const { GET, POST } = handlers;

// middleware.ts — protect routes
import { auth } from "@/lib/auth";

export default auth((req) => {
  if (!req.auth && req.nextUrl.pathname.startsWith("/dashboard")) {
    return Response.redirect(new URL("/login", req.nextUrl));
  }
});

// Server Component — read session
import { auth } from "@/lib/auth";
async function DashboardPage() {
  const session = await auth();
  if (!session) redirect("/login");
  return <Dashboard user={session.user} />;
}

// Client Component — useSession
"use client";
import { useSession } from "next-auth/react";
function UserMenu() {
  const { data: session } = useSession();
  if (!session) return <LoginButton />;
  return <span>{session.user.name}</span>;
}
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `session.strategy` | `"jwt"` | `"database"` for DB sessions |
| `pages.signIn` | `/api/auth/signin` | Custom sign-in page |
| `callbacks.jwt` | — | Customize JWT token content |
| `callbacks.session` | — | Customize session object |

## See Also

- [middleware.md](../concepts/middleware.md)
- [api-routes.md](../patterns/api-routes.md)
