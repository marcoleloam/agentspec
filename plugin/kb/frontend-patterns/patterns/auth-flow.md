# Auth Flow

> **Purpose**: Login, session management, protected routes, role-based access
> **MCP Validated**: 2026-03-29

## When to Use

- Implementing authentication in the app
- Protecting routes from unauthenticated users
- Role-based UI rendering

## Implementation

```tsx
// 1. Protected route — Server Component
import { auth } from "@/lib/auth";
import { redirect } from "next/navigation";

async function DashboardPage() {
  const session = await auth();
  if (!session) redirect("/login");
  return <Dashboard user={session.user} />;
}

// 2. Role-based access
async function AdminPage() {
  const session = await auth();
  if (!session) redirect("/login");
  if (session.user.role !== "admin") redirect("/unauthorized");
  return <AdminPanel />;
}

// 3. Client-side session hook
"use client";
import { useSession } from "next-auth/react";

function UserMenu() {
  const { data: session, status } = useSession();

  if (status === "loading") return <Skeleton className="h-8 w-8 rounded-full" />;
  if (!session) return <LoginButton />;

  return (
    <div className="flex items-center gap-2">
      <span>{session.user.name}</span>
      <SignOutButton />
    </div>
  );
}

// 4. Login page with form
"use client";
import { signIn } from "next-auth/react";

function LoginPage() {
  async function handleSubmit(formData: FormData) {
    const result = await signIn("credentials", {
      email: formData.get("email"),
      password: formData.get("password"),
      redirect: false,
    });

    if (result?.error) {
      toast.error("Invalid credentials");
    } else {
      router.push("/dashboard");
    }
  }

  return (
    <form action={handleSubmit}>
      <input name="email" type="email" required />
      <input name="password" type="password" required />
      <button type="submit">Sign in</button>
    </form>
  );
}
```

## Configuration

| Pattern | Where | Implementation |
|---------|-------|----------------|
| Route protection | middleware.ts | Redirect if no session |
| Server session | Server Component | `auth()` from NextAuth |
| Client session | Client Component | `useSession()` hook |
| Role check | Server or Client | Check `session.user.role` |

## See Also

- [auth-patterns.md](../../nextjs/patterns/auth-patterns.md)
- [error-handling.md](../concepts/error-handling.md)
