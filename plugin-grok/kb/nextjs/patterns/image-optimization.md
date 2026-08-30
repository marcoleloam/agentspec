# Image Optimization

> **Purpose**: next/image for automatic optimization, responsive sizes, blur placeholder
> **MCP Validated**: 2026-03-29

## When to Use

- Displaying images with automatic WebP/AVIF conversion
- Responsive images that serve correct size per viewport
- LCP optimization with priority loading
- Blur-up placeholder for perceived performance

## Implementation

```tsx
import Image from "next/image";

// Fixed dimensions — known width/height
function ProductCard({ product }: { product: Product }) {
  return (
    <Image
      src={product.imageUrl}
      alt={product.name}
      width={400}
      height={300}
      className="rounded-lg object-cover"
    />
  );
}

// Fill container — parent must have position: relative
function HeroBanner({ src }: { src: string }) {
  return (
    <div className="relative h-[400px] w-full">
      <Image
        src={src}
        alt="Hero banner"
        fill
        sizes="100vw"
        priority      // LCP image — preload
        className="object-cover"
      />
    </div>
  );
}

// Responsive sizes — serve correct size per viewport
function BlogImage({ src, alt }: { src: string; alt: string }) {
  return (
    <Image
      src={src}
      alt={alt}
      width={800}
      height={450}
      sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 800px"
      placeholder="blur"
      blurDataURL="data:image/png;base64,..." // tiny base64
    />
  );
}
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `priority` | `false` | Preload for LCP images |
| `sizes` | — | Responsive breakpoint hints |
| `placeholder` | `"empty"` | `"blur"` for blur-up effect |
| `quality` | `75` | Image quality 1-100 |
| `fill` | `false` | Fill parent container |

```tsx
// next.config.ts — remote image domains
const config = {
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "images.example.com" },
    ],
  },
};
```

## See Also

- [rendering-strategies.md](../concepts/rendering-strategies.md)
- [deployment.md](../patterns/deployment.md)
