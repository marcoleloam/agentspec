# Animation Patterns — AIDE Slides

> All animation keyframes and timing patterns. The master easing curve is `cubic-bezier(0.16,1,0.3,1)`.

## Master Easing Curve

`cubic-bezier(0.16,1,0.3,1)` — snappy, modern bounce. Use for ALL entrance and transition animations.

## Shimmer (Text Highlight — Infinite Loop)

```css
@keyframes shimmer { 0%,100% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } }

.shimmer-text {
  background: linear-gradient(135deg, var(--accent) 0%, #fff 30%, var(--gold) 60%, var(--accent) 100%);
  background-size: 300% 300%;
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
  animation: shimmer 6s ease infinite;
}

.shimmer-gold {
  background: linear-gradient(135deg, var(--gold) 0%, #fff 30%, var(--accent) 60%, var(--gold) 100%);
  background-size: 300% 300%;
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
  animation: shimmer 8s ease infinite;
}
```

## Pulse Glow (Card/Node Emphasis — Infinite Loop)

```css
@keyframes pulse-glow {
  0%, 100% { box-shadow: 0 0 15px rgba(0,180,255,0.15), 0 0 30px rgba(0,180,255,0.05); }
  50% { box-shadow: 0 0 25px rgba(0,180,255,0.3), 0 0 50px rgba(0,180,255,0.1); }
}

@keyframes pulse-gold {
  0%, 100% { box-shadow: 0 0 15px rgba(212,175,55,0.15); }
  50% { box-shadow: 0 0 25px rgba(212,175,55,0.3); }
}
```

Usage: `animation: pulse-glow 4s ease-in-out infinite` on a highlighted card.

## Bar Fill (Progressive Reveal — One Shot)

```css
@keyframes bar-fill { from { width: 0; } }
/* Usage: animation: bar-fill 1.4s cubic-bezier(0.16,1,0.3,1) both; */
```

## Reveal Stagger (Entrance — Triggered by IntersectionObserver)

The `.reveal` class is the core entrance animation. Elements start invisible and slide up when the slide enters the viewport.

```css
.slide .reveal {
  opacity: 0; transform: translateY(24px);
  transition: opacity 0.5s cubic-bezier(0.16,1,0.3,1), transform 0.5s cubic-bezier(0.16,1,0.3,1);
}
.slide.visible .reveal { opacity: 1; transform: none; }
```

**Stagger delays:** Each nth-child gets +0.1s delay (0.1s, 0.2s, ... up to 1.0s for 10 children).

**Usage:** Add `class="reveal"` to each top-level content block in a slide. The first block appears at 0.1s, second at 0.2s, etc.

## Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  .slide, .slide .reveal { opacity: 1 !important; transform: none !important; transition: none !important; }
}
```
