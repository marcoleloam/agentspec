# Design System — AIDE Slides

> The AIDE slide design system fuses the Kurv presentation framework (proven in production at Pythian) with the Formacao AI Data Engineer color palette.

## Color Palette (CSS Custom Properties)

```css
:root {
  /* BACKGROUNDS */
  --bg: #0a0f1a;              /* Deep space navy */
  --surface: #111827;          /* Card backgrounds */
  --surface2: #1a2236;         /* Elevated surfaces */
  --surface-elevated: #1e293b; /* Highest elevation */

  /* BORDERS */
  --border: rgba(0, 180, 255, 0.08);
  --border-bright: rgba(0, 180, 255, 0.20);

  /* TEXT */
  --text: #e8edf5;             /* Primary text */
  --text-dim: #6b7fa0;         /* Secondary/muted text */

  /* PRIMARY ACCENT */
  --accent: #00b4ff;           /* Cyan-blue (from PDF) */
  --accent-dim: rgba(0, 180, 255, 0.10);

  /* SEMANTIC COLORS (each with -dim variant at 0.10 opacity) */
  --gold: #d4af37;             /* Gold highlights, premium */
  --gold-dim: rgba(212, 175, 55, 0.10);
  --orange: #ef9000;           /* Warm orange */
  --orange-dim: rgba(239, 144, 0, 0.10);
  --green: #3fb950;            /* Success, positive */
  --green-dim: rgba(63, 185, 80, 0.10);
  --red: #f85149;              /* Alert, important */
  --red-dim: rgba(248, 81, 73, 0.10);
  --blue: #60a5fa;             /* Info, secondary */
  --blue-dim: rgba(96, 165, 250, 0.10);
  --purple: #a78bfa;           /* Feature, tertiary */
  --purple-dim: rgba(167, 139, 250, 0.10);
  --cyan: #22d3ee;             /* Bright emphasis */
  --cyan-dim: rgba(34, 211, 238, 0.10);

  /* CODE */
  --code-bg: #060b14;
  --code-text: #c8d8e8;
}
```

**NEVER use Kurv green** (`#b2f752`). The AIDE palette is navy/cyan/gold.

## Typography Stack (4 Fonts)

```html
<link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:wght@400;500;600;700;800&family=Fira+Code:wght@400;500;600;700&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;1,6..72,400;1,6..72,500&display=swap" rel="stylesheet">
```

| Variable | Font | Role | Usage |
|----------|------|------|-------|
| `--font-display` | Instrument Serif | Headlines, card titles | Always italic for drama |
| `--font-body` | DM Sans | Body paragraphs, descriptions | 400-800 weights |
| `--font-editorial` | Newsreader | Quotes, captions, editorial | Italic with optical sizing |
| `--font-mono` | Fira Code | Code, labels, stats, tags | 400-700 weights |

## Typography Scale

```css
.slide__display  { font-size: clamp(56px,12vw,140px); }  /* Hero title */
.slide__heading  { font-size: clamp(36px,7vw,72px); }    /* Section heading */
.slide__body     { font-size: clamp(19px,2.6vw,26px); }  /* Body copy */
.slide__subtitle { font-size: clamp(13px,1.7vw,18px); }  /* Mono label */
.slide__label    { font-size: clamp(12px,1.4vw,15px); }  /* Feature label */
```

## Film Grain Overlay

```css
body::after {
  content: '';
  position: fixed; inset: 0; z-index: 9999; pointer-events: none; opacity: 0.03;
  background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='300'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.75' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='300' height='300' filter='url(%23n)' opacity='1'/%3E%3C/svg%3E");
}
```

## AIDE Branding Bar

```html
<div class="aide-bar">
  <div class="aide-bar__left">
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg>
    FORMACAO AI DATA ENGINEER
  </div>
  <div class="aide-bar__center">De AI-Curious a AI-Native Engineer</div>
  <div class="aide-bar__right">
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
    Luan Moreno &middot; 2026
  </div>
</div>
```

```css
.aide-bar {
  position: fixed; top: 3px; left: 0; right: 0; height: 44px; z-index: 99;
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 clamp(20px,3vw,48px);
  background: rgba(10,15,26,0.85); border-bottom: 1px solid var(--border);
  font-family: var(--font-mono); font-size: 0.68rem; letter-spacing: 0.15em; text-transform: uppercase;
}
.aide-bar__left { color: var(--accent); font-weight: 600; display: flex; align-items: center; gap: 8px; }
.aide-bar__center { color: var(--gold); font-weight: 500; font-style: italic; letter-spacing: 0.08em; text-transform: none; font-family: var(--font-editorial); font-size: 0.82rem; }
.aide-bar__right { color: var(--text-dim); display: flex; align-items: center; gap: 6px; }
```

## Gradient Text Effects

```css
.gradient-text { background: linear-gradient(135deg, var(--accent) 0%, var(--cyan) 50%, #fff 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.gradient-gold { background: linear-gradient(135deg, var(--gold) 0%, #f0d060 50%, #fff 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.shimmer-text { /* cyan-white-gold animated */ animation: shimmer 6s ease infinite; }
.shimmer-gold { /* gold-white-cyan animated */ animation: shimmer 8s ease infinite; }
```

## Instructor Image

Always reference: `../../../images/luan-moreno.png` (relative to slide file in `presentation/l1-gen-ai/al-x/`)

```html
<div style="width:clamp(56px,7vw,80px); height:clamp(56px,7vw,80px); border-radius:50%; overflow:hidden; border:2px solid rgba(0,180,255,0.3);">
  <img src="../../../images/luan-moreno.png" alt="Luan Moreno" style="width:100%; height:100%; object-fit:cover; object-position:center -5%; transform:scale(1.3); transform-origin:center 3%;">
</div>
```
