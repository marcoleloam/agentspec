# Component Library — AIDE Slides

> Every reusable CSS component extracted from the Kurv slides and AL-1 reference deck. Use these instead of writing custom styles.

---

## Tags (Color-Coded Badges)

The proven Kurv tag style: Fira Code mono, 0.68rem, soft rounded corners, tinted background. No borders, no glows, no glass effects — elegance through simplicity.

```css
.tag { font-family: var(--font-mono); font-size: 0.68rem; font-weight: 600; padding: 0.22rem 0.65rem; border-radius: 6px; letter-spacing: 0.05em; display: inline-flex; align-items: center; gap: 0.3rem; }
.tag-accent { background: var(--accent-dim); color: var(--accent); }
.tag-silver { background: var(--silver-dim); color: var(--silver); }
.tag-gold   { background: var(--gold-dim);   color: var(--gold); }
.tag-green  { background: var(--green-dim);  color: var(--green); }
.tag-blue   { background: var(--blue-dim);   color: var(--blue); }
.tag-purple { background: var(--purple-dim); color: var(--purple); }
.tag-red    { background: var(--red-dim);    color: var(--red); }
.tag-orange { background: var(--orange-dim); color: var(--orange); }
.tag-cyan   { background: var(--cyan-dim);   color: var(--cyan); }
```

**RULES:**
- NEVER add `border`, `box-shadow`, `backdrop-filter`, or `text-transform:uppercase` to tags
- NEVER use Inter, DM Sans, or any non-mono font for tags — always `var(--font-mono)` (Fira Code)
- NEVER add inline `style=""` overrides on tags for font-size, padding, or border-radius — let the class handle it
- Tags look best at 0.65–0.68rem. Going larger makes them compete with headings

## Stat Cards (3-column grid)

```css
.stats-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: clamp(10px,1.8vw,20px); margin-top: clamp(16px,3vh,32px); }
.stat-card { background: var(--surface); border: 1px solid var(--border); border-radius: 14px; text-align: center; padding: clamp(18px,3vh,32px) clamp(12px,2vw,20px); position: relative; overflow: hidden; }
.stat-card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px; background: var(--accent); }
.stat-val { font-size: clamp(36px,6vw,64px); font-weight: 800; line-height: 1; letter-spacing: -0.03em; }
.stat-lbl { font-family: var(--font-mono); font-size: clamp(9px,1.1vw,12px); color: var(--text-dim); margin-top: 0.4rem; text-transform: uppercase; letter-spacing: 1.5px; }
```

## Tier Cards (3-column comparison)

```css
.tier-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-top: clamp(16px,3vh,28px); }
.tier-card { background: var(--surface); border: 1px solid var(--border); border-radius: 16px; padding: clamp(20px,3vh,32px); position: relative; overflow: hidden; }
.tier-card h4 { font-family: var(--font-display); font-size: 1.5rem; font-style: italic; margin-bottom: 0.3rem; }
.tier-card .tier-sub { font-family: var(--font-mono); font-size: 0.7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 0.8rem; }
.tier-card p { font-size: 0.88rem; color: var(--text-dim); line-height: 1.5; }
```

## Phase Flow (Horizontal Pipeline)

```css
.phase-flow { display: flex; gap: 0; align-items: stretch; margin-top: clamp(16px,3vh,28px); width: 100%; }
.phase-card { flex: 1; padding: clamp(20px,3vh,32px) clamp(14px,2vw,24px); border-radius: 14px; background: var(--surface); border: 1px solid var(--border); margin: 0 6px; }
.phase-num { font-family: var(--font-mono); font-size: 0.72rem; font-weight: 600; letter-spacing: 0.12em; margin-bottom: 0.5rem; }
.phase-name { font-family: var(--font-display); font-size: 1.4rem; font-style: italic; margin-bottom: 0.5rem; }
.phase-desc { font-family: var(--font-editorial); font-size: 0.92rem; color: var(--text-dim); line-height: 1.5; font-style: italic; }
.phase-evidence { font-family: var(--font-mono); font-size: 0.72rem; color: var(--gold); margin-top: 0.8rem; padding: 0.4rem 0.7rem; background: var(--gold-dim); border-radius: 6px; display: inline-block; }
.phase-connector { display: flex; align-items: center; flex-shrink: 0; padding: 0 0.2rem; }
```

**SVG Arrow for phase connectors:**
```html
<div class="phase-connector">
  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2.5">
    <path d="M5 12h14M12 5l7 7-7 7"/>
  </svg>
</div>
```

## Timeline Grid (7-column)

```css
.timeline-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 0.6rem; margin-top: clamp(10px,1.5vh,16px); position: relative; }
.timeline-grid::before { content: ''; position: absolute; top: 20px; left: 4%; right: 4%; height: 3px; background: linear-gradient(90deg, var(--text-dim), var(--accent), var(--gold), var(--orange)); border-radius: 2px; }
.tl-col { text-align: center; position: relative; padding-top: 40px; }
.tl-dot { width: 14px; height: 14px; border-radius: 50%; border: 3px solid; position: absolute; top: 14px; left: 50%; transform: translateX(-50%); z-index: 1; background: var(--bg); }
.tl-col.major .tl-dot { width: 20px; height: 20px; top: 11px; }
.tl-year { font-family: var(--font-display); font-size: 1.5rem; font-style: italic; }
.tl-title { font-family: var(--font-display); font-size: 1.05rem; font-style: italic; }
.tl-desc { font-family: var(--font-editorial); font-size: 0.78rem; color: var(--text-dim); font-style: italic; }
.tl-detail { font-family: var(--font-body); font-size: 0.78rem; color: var(--text-dim); line-height: 1.55; padding-top: 0.4rem; border-top: 1px solid var(--border); text-align: left; }
.tl-stat { font-family: var(--font-mono); font-size: 0.62rem; color: var(--gold); background: var(--gold-dim); padding: 0.2rem 0.5rem; border-radius: 4px; display: inline-block; margin-top: 0.5rem; }
```

## Bar Chart (Animated)

```css
@keyframes bar-fill { from { width: 0; } }
.bar-chart { display: flex; flex-direction: column; gap: 1rem; }
.bar-row { display: flex; align-items: center; gap: 1rem; }
.bar-label { font-family: var(--font-body); font-size: 0.92rem; font-weight: 600; color: var(--text); width: 140px; text-align: right; flex-shrink: 0; }
.bar-label span { display: block; font-family: var(--font-mono); font-size: 0.68rem; font-weight: 400; color: var(--text-dim); }
.bar-track { flex: 1; height: 44px; background: rgba(255,255,255,0.03); border-radius: 10px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 10px; display: flex; align-items: center; padding-left: 16px; font-family: var(--font-mono); font-size: 0.88rem; font-weight: 700; color: var(--text); animation: bar-fill 1.4s cubic-bezier(0.16,1,0.3,1) both; }
```

## Glass Card

```css
.glass-card { background: rgba(17, 24, 39, 0.6); border: 1px solid var(--border-bright); border-radius: 16px; padding: clamp(24px, 4vh, 40px); box-shadow: 0 8px 40px rgba(0,0,0,0.3); }
```

## Method Grid (2-column panels)

```css
.method-grid { display: grid; grid-template-columns: 1fr 1fr; gap: clamp(16px,2.5vw,32px); margin-top: clamp(16px,3vh,28px); }
.method-panel { background: var(--surface); border-radius: 16px; padding: clamp(20px,3vh,32px); }
.method-panel.panel-accent { border: 1px solid rgba(0,180,255,0.2); }
.method-panel.panel-gold { border: 1px solid rgba(212,175,55,0.2); }
.method-panel h3 { font-family: var(--font-mono); font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.15em; margin-bottom: 1rem; }
```

## Authors Table

```css
.authors-table { width: 100%; font-size: 0.95rem; margin-top: clamp(16px,3vh,24px); border-collapse: collapse; }
.authors-table th { font-family: var(--font-mono); font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.12em; color: var(--text-dim); text-align: left; padding: 0.8rem 1.2rem; border-bottom: 2px solid var(--border-bright); }
.authors-table td { padding: 0.7rem 1.2rem; border-bottom: 1px solid var(--border); }
.authors-table td:first-child { font-family: var(--font-display); font-size: 1.1rem; font-style: italic; }
```

## Code Block

```css
.code-block { background: var(--code-bg); border: 1px solid var(--border); border-radius: 10px; padding: 0.75rem 1rem; font-family: var(--font-mono); font-size: 0.82rem; line-height: 1.5; color: var(--code-text); }
.code-block .kw { color: var(--purple); }
.code-block .fn { color: var(--accent); }
.code-block .str { color: var(--green); }
.code-block .num { color: var(--gold); }
.code-block .dim { color: var(--text-dim); }
```

## Bottom Explanation Panel (use on every content slide)

```html
<div style="margin-top:auto; padding-top:clamp(8px,1.5vh,12px);">
  <div style="background:var(--surface); border:1px solid var(--border); border-radius:12px; padding:0.8rem 1.5rem;">
    <p style="font-family:var(--font-display); font-size:1rem; font-style:italic; color:var(--accent); margin-bottom:0.2rem;">Por que isso importa?</p>
    <p style="font-size:0.82rem; color:var(--text-dim); line-height:1.5;">Explanation of practical value for the AI Data Engineer...</p>
  </div>
</div>
```

## Numbered Step Badge

```html
<div style="width:40px; height:40px; border-radius:10px; background:var(--accent-dim); border:1px solid rgba(0,180,255,0.2); display:flex; align-items:center; justify-content:center; font-family:var(--font-mono); font-size:0.72rem; font-weight:700; color:var(--accent);">1</div>
```

## SVG Down Arrow (for vertical flows)

```html
<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--text-dim)" stroke-width="2"><path d="M12 5v14M5 12l7 7 7-7"/></svg>
```

## SVG Right Arrow (for horizontal flows)

```html
<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
```

## Practical Example Box (use inside cards)

```html
<div style="margin-top:auto; padding-top:0.6rem;">
  <p style="font-family:var(--font-mono); font-size:0.55rem; color:var(--text-dim); text-transform:uppercase; letter-spacing:0.08em; margin-bottom:0.3rem;">Na prática:</p>
  <div style="background:rgba(0,180,255,0.05); border:1px solid rgba(0,180,255,0.12); border-radius:8px; padding:0.5rem 0.6rem;">
    <p style="font-size:0.72rem; color:var(--text-dim); line-height:1.45;">Example content here</p>
  </div>
</div>
```
