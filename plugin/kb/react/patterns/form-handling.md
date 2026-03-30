# Form Handling

> **Purpose**: React Hook Form + Zod validation, Server Actions for submission
> **MCP Validated**: 2026-03-29

## When to Use

- Forms with validation (login, signup, settings)
- Multi-step forms with complex state
- Server-side form submission in Next.js

## Implementation

```tsx
"use client";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

const schema = z.object({
  email: z.string().email("Invalid email"),
  password: z.string().min(8, "At least 8 characters"),
});

type FormData = z.infer<typeof schema>;

function LoginForm() {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  async function onSubmit(data: FormData) {
    const res = await fetch("/api/auth/login", {
      method: "POST",
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Login failed");
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div>
        <label htmlFor="email">Email</label>
        <input id="email" type="email" {...register("email")} />
        {errors.email && (
          <p role="alert" className="text-red-500 text-sm">
            {errors.email.message}
          </p>
        )}
      </div>
      <div>
        <label htmlFor="password">Password</label>
        <input id="password" type="password" {...register("password")} />
        {errors.password && (
          <p role="alert" className="text-red-500 text-sm">
            {errors.password.message}
          </p>
        )}
      </div>
      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Signing in..." : "Sign in"}
      </button>
    </form>
  );
}
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `mode` | `"onSubmit"` | When to validate: onSubmit, onChange, onBlur |
| `resolver` | — | Zod, Yup, or custom validation resolver |
| `defaultValues` | `{}` | Pre-fill form fields |

## See Also

- [hooks-patterns.md](../concepts/hooks-patterns.md)
- [component-composition.md](../patterns/component-composition.md)
