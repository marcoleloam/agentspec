# Deployment

> **Purpose**: Vercel, Docker standalone, static export, environment variables
> **MCP Validated**: 2026-03-29

## When to Use

- Deploying Next.js to production
- Choosing between Vercel, Docker, or static hosting
- Managing environment variables across environments

## Implementation

```tsx
// 1. Vercel — zero config (recommended)
// Push to GitHub → Vercel auto-deploys
// next.config.ts — no changes needed

// 2. Docker — standalone output
// next.config.ts
const config = {
  output: "standalone", // Produces minimal Node.js server
};

// Dockerfile
// FROM node:20-alpine AS builder
// WORKDIR /app
// COPY . .
// RUN npm ci && npm run build
//
// FROM node:20-alpine AS runner
// WORKDIR /app
// COPY --from=builder /app/.next/standalone ./
// COPY --from=builder /app/.next/static ./.next/static
// COPY --from=builder /app/public ./public
// EXPOSE 3000
// CMD ["node", "server.js"]

// 3. Static export — no server needed
// next.config.ts
const config = {
  output: "export", // Generates static HTML in /out
};
// Limitations: no SSR, no API routes, no middleware
```

## Configuration

```bash
# Environment variables

# .env.local — local dev (gitignored)
DATABASE_URL=postgres://localhost:5432/mydb
NEXTAUTH_SECRET=dev-secret

# Server-only (no prefix) — NOT exposed to browser
DATABASE_URL=postgres://...

# Client-exposed (NEXT_PUBLIC_ prefix) — included in JS bundle
NEXT_PUBLIC_API_URL=https://api.example.com

# Runtime env — read at request time (not build time)
# Access via process.env in Server Components
```

| Platform | Output | Server | Best For |
|----------|--------|--------|----------|
| Vercel | Auto | Managed | Fastest deploy, edge functions |
| Docker | `standalone` | Self-hosted | Kubernetes, custom infra |
| Static | `export` | None (CDN) | Marketing sites, docs |

## See Also

- [rendering-strategies.md](../concepts/rendering-strategies.md)
- [image-optimization.md](../patterns/image-optimization.md)
