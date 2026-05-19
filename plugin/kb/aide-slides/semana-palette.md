# Semana Palette — Black / Silver / Blue

> Alternative color palette for the Semana AI Data Engineer slide decks. Used instead of the AIDE navy/cyan/gold palette. Based on the Engenharia de Dados Academy blue brand color.

## When to Use

Use this palette for all **Semana AI Data Engineer** presentation decks (`presentation/d1-*.html` through `d4-*.html`). The standard AIDE navy palette is used for Formacao lesson decks (`presentation/l0-*/`, `presentation/l1-*/`).

## CSS Custom Properties

```css
:root {
  /* BACKGROUNDS — True black */
  --bg: #08080a;
  --surface: #111114;
  --surface2: #19191e;
  --surface-elevated: #222228;

  /* BORDERS — Blue-tinted */
  --border: rgba(120, 160, 220, 0.08);
  --border-bright: rgba(120, 160, 220, 0.18);

  /* TEXT */
  --text: #eaedf2;
  --text-dim: #6e7a8c;

  /* PRIMARY — Academy Blue */
  --accent: #4a9eff;
  --accent-dim: rgba(74, 158, 255, 0.10);
  --accent2: #3d8ae6;

  /* SILVER — The secondary hero */
  --silver: #b0bec5;
  --silver-bright: #cfd8dc;
  --silver-dim: rgba(176, 190, 197, 0.10);

  /* SEMANTIC COLORS (unchanged from AIDE) */
  --gold: #d4af37;    --gold-dim: rgba(212, 175, 55, 0.10);
  --orange: #ef9000;  --orange-dim: rgba(239, 144, 0, 0.10);
  --green: #3fb950;   --green-dim: rgba(63, 185, 80, 0.10);
  --red: #f85149;     --red-dim: rgba(248, 81, 73, 0.10);
  --blue: #60a5fa;    --blue-dim: rgba(96, 165, 250, 0.10);
  --purple: #a78bfa;  --purple-dim: rgba(167, 139, 250, 0.10);
  --cyan: #22d3ee;    --cyan-dim: rgba(34, 211, 238, 0.10);

  /* CODE */
  --code-bg: #060608;
  --code-text: #c8d0dc;
}
```

## Key Differences from AIDE Navy Palette

| Property | AIDE Navy | Semana Black |
|----------|-----------|-------------|
| `--bg` | `#0a0f1a` (deep navy) | `#08080a` (true black) |
| `--surface` | `#111827` (navy-gray) | `#111114` (charcoal) |
| `--accent` | `#00b4ff` (bright cyan) | `#4a9eff` (Academy blue) |
| `--text-dim` | `#6b7fa0` (blue-gray) | `#6e7a8c` (neutral gray) |
| `--border` | cyan-tinted | blue-tinted |
| Silver | not present | `#b0bec5` (secondary hero) |

## Gradient Text

```css
/* Blue-to-silver (replaces cyan-to-white) */
.gradient-text { background: linear-gradient(135deg, var(--accent) 0%, var(--silver-bright) 50%, #ffffff 100%); }

/* Blue shimmer (replaces cyan shimmer) */
.shimmer-text { background: linear-gradient(135deg, var(--accent) 0%, #ffffff 30%, var(--silver-bright) 60%, var(--accent) 100%); }
```

## Slide Backgrounds

Use subtle blue/silver radial gradients instead of green/navy:

```css
/* Title slide */
background-image: radial-gradient(ellipse at 50% 20%, rgba(74,158,255,0.08) 0%, transparent 50%),
                  radial-gradient(ellipse at 80% 80%, rgba(176,190,197,0.03) 0%, transparent 40%);

/* Content slide */
background-image: radial-gradient(ellipse at 30% 20%, rgba(74,158,255,0.05) 0%, transparent 50%),
                  radial-gradient(ellipse at 80% 70%, rgba(176,190,197,0.02) 0%, transparent 40%);
```

## Reference Deck

Golden reference: `presentation/d1-ingest.html` — the first Semana deck built with this palette.

## NEVER

- NEVER use Kurv green (`#b2f752`) in Semana decks
- NEVER use AIDE cyan (`#00b4ff`) — use Academy blue (`#4a9eff`) instead
- NEVER mix palettes — a deck is either AIDE navy OR Semana black, never both
