# Advanced Visual Patterns — AIDE Slides

> Killer visual patterns extracted from D1-D4 Kurv production presentations. Use these for architecture diagrams, pipelines, step flows, agent orchestration, and conceptual slides. These patterns ELEVATE slides beyond basic cards and text.

---

## When to Use Advanced Visuals

Use these patterns instead of basic text/card layouts when the slide shows:
- Architecture diagrams (system layers, data flow)
- Multi-stage pipelines (Bronze → Silver → Gold, ETL stages)
- Step-by-step processes (numbered flows, setup guides)
- Agent orchestration (multi-agent systems, crews)
- Conceptual reframes (before/after, paradigm shifts)
- Dual/converging strategies (parallel paths merging)

---

## Pattern 1: Multi-Stage Pipeline (Horizontal)

**Use for:** ETL pipelines, data flows, process stages (5-9 steps)

```html
<!-- Wrapper: flex row, each stage is flex:1 -->
<div style="display:flex;align-items:center;justify-content:center;gap:0;width:100%">
  <!-- Each stage -->
  <div style="flex:1;background:#0D0D0D;border:1.5px solid rgba(color,0.4);border-radius:16px;padding:clamp(18px,3vh,30px) clamp(12px,1.5vw,20px);text-align:center;position:relative;margin:0 clamp(4px,0.5vw,8px)">
    <!-- Floating stage number -->
    <div style="position:absolute;top:-10px;left:50%;transform:translateX(-50%);font-family:var(--font-mono);font-size:.65rem;font-weight:700;padding:2px 12px;border-radius:6px;background:rgba(color,0.15);color:var(--color)">STAGE 1</div>
    <!-- SVG icon (30x30) -->
    <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="var(--color)" stroke-width="1.8">...</svg>
    <!-- Title -->
    <p style="font-family:var(--font-display);font-size:clamp(1.05rem,1.5vw,1.25rem);font-style:italic;color:var(--color);margin-top:.4rem">Stage Name</p>
    <!-- Subtitle -->
    <p style="font-family:var(--font-mono);font-size:clamp(.58rem,.82vw,.68rem);color:var(--text-dim);margin-top:.2rem">Technical detail</p>
  </div>
  <!-- Arrow separator -->
  <div style="font-size:clamp(18px,2.5vw,26px);color:var(--text-dim);flex-shrink:0">→</div>
</div>
```

**Key rules:**
- Each stage: `flex:1`, `border-radius:16px`, `border:1.5px solid rgba(color,0.4)`
- Floating stage number: `position:absolute;top:-10px;left:50%;transform:translateX(-50%)`
- SVG icons: 30x30px, `stroke-width:1.8`
- Color-code by phase: AWS=blue, Databricks=red, Spark=orange, etc.
- For platform grouping, wrap stages in a container with `border:2px solid rgba(color,0.35);border-radius:20px;box-shadow:0 0 40px rgba(color,0.06)`

---

## Pattern 2: Architecture 360 (SVG Multi-Layer)

**Use for:** Complex systems showing layers, connections, agent orchestration

```html
<svg viewBox="0 0 1200 480" style="width:100%;max-height:clamp(360px,60vh,520px)">
  <defs>
    <filter id="arch-glow">
      <feGaussianBlur stdDeviation="4" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <linearGradient id="g1" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#22d3ee" stop-opacity="0.6"/>
      <stop offset="100%" stop-color="#60a5fa" stop-opacity="0.3"/>
    </linearGradient>
  </defs>
  
  <!-- Row label -->
  <text x="10" y="40" font-family="var(--font-mono)" font-size="9" fill="#7da88f" letter-spacing="1.5" text-transform="uppercase">COMMANDS</text>
  
  <!-- Node box -->
  <rect x="100" y="12" width="150" height="50" rx="12" fill="rgba(34,211,238,0.1)" stroke="#22d3ee" stroke-width="1.8"/>
  <text x="175" y="42" text-anchor="middle" font-family="var(--font-mono)" font-size="11" fill="#22d3ee">/command</text>
  
  <!-- Connector line -->
  <line x1="250" y1="37" x2="300" y2="37" stroke="#60a5fa" stroke-width="1.5" opacity="0.25"/>
</svg>
```

**Key rules:**
- Use SVG for complex diagrams — not CSS grid
- Apply `filter="url(#arch-glow)"` on key nodes for depth
- Connector lines: `opacity:0.25` to avoid visual clutter
- Row labels: monospace 9px, uppercase, letter-spacing 1.5px
- Node boxes: `rx="12"`, `fill="rgba(color,0.1)"`, `stroke-width:1.8`
- Use `<foreignObject>` to embed HTML pills/tags inside SVG

---

## Pattern 3: Animated Flow Ribbons (SVG)

**Use for:** Data flow between stages, pipeline convergence, agent communication

```css
@keyframes flow-right {
  from { stroke-dashoffset: 24; }
  to { stroke-dashoffset: 0; }
}
.flow-r {
  stroke-dasharray: 12 12;
  animation: flow-right 1.2s linear infinite;
}
```

```html
<svg>
  <defs>
    <linearGradient id="flow-g" x1="0%" x2="100%">
      <stop offset="0%" stop-color="#4ade80" stop-opacity="0.8"/>
      <stop offset="100%" stop-color="#ef9000" stop-opacity="0.6"/>
    </linearGradient>
  </defs>
  <path d="M50,50 C150,50 200,100 300,100" stroke="url(#flow-g)" stroke-width="3" class="flow-r" fill="none"/>
</svg>
```

**Key rules:**
- `stroke-dasharray: 12 12` with `stroke-width: 3` for visible flow
- Animation: `1.2s linear infinite` for smooth continuous flow
- Use `<linearGradient>` to blend source and destination colors
- Curved paths (`C` bezier) look more natural than straight lines
- Multiple ribbons at different opacities create depth

---

## Pattern 4: Dual Strategy Comparison

**Use for:** Before/after architectures, parallel pipelines merging, strategy comparisons

**Layout:** Two-column grid with a center convergence point

```html
<div style="display:grid;grid-template-columns:1fr 64px 1fr;gap:0;flex:1">
  <!-- Left strategy -->
  <div style="background:rgba(248,81,73,.03);border:1px solid rgba(248,81,73,.12);border-radius:16px;padding:clamp(16px,2.5vh,28px)">
    <!-- Content: steps, cards, flow -->
  </div>
  
  <!-- Center divider with gradient lines + circle -->
  <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;gap:.5rem">
    <div style="width:2px;flex:1;background:linear-gradient(180deg,transparent,rgba(212,175,55,.3),transparent);max-height:30%"></div>
    <div style="width:clamp(40px,5vh,56px);height:clamp(40px,5vh,56px);border-radius:50%;background:var(--gold-dim);border:2px solid rgba(212,175,55,.3);display:flex;align-items:center;justify-content:center">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--gold)" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
    </div>
    <div style="width:2px;flex:1;background:linear-gradient(180deg,transparent,rgba(212,175,55,.3),transparent);max-height:30%"></div>
  </div>
  
  <!-- Right strategy (enhanced with glow) -->
  <div style="background:rgba(0,180,255,.03);border:1px solid rgba(0,180,255,.12);border-radius:16px;padding:clamp(16px,2.5vh,28px);box-shadow:0 0 30px rgba(0,180,255,.04)">
    <!-- Content: steps, cards, flow -->
  </div>
</div>
```

**Key rules:**
- Center column: 64px with gradient vertical lines fading to transparent at top/bottom
- Gold circle as visual anchor — always use for "transformation" concepts
- Left (old/before): subtle red/dim background, no glow
- Right (new/after): subtle cyan background WITH `box-shadow` glow
- Step cards inside use icon badges (28-42px) with themed SVG icons

---

## Pattern 5: Card Anatomy (Colored Section Stack)

**Use for:** Framework breakdown, document anatomy, concept layers

```html
<div style="display:flex;flex-direction:column;gap:clamp(6px,1vh,10px)">
  <div style="background:linear-gradient(135deg,rgba(248,81,73,.15),rgba(248,81,73,.05));padding:clamp(10px,1.5vh,16px) clamp(12px,1.5vw,18px);border-radius:12px;display:flex;align-items:center;gap:.8rem">
    <span style="font-family:var(--font-mono);font-size:.72rem;font-weight:700;padding:4px 10px;background:rgba(0,0,0,.3);border-radius:6px;color:#fff;flex-shrink:0">01</span>
    <span style="font-family:var(--font-display);font-size:clamp(.92rem,1.2vw,1.08rem);font-style:italic;color:#fff">Section Name</span>
  </div>
  <!-- Repeat with different colors: gold, green, purple, blue, cyan -->
</div>
```

**Key rules:**
- 6 color rotation: red → gold → green → purple → blue → cyan
- Each section: `background:linear-gradient(135deg,rgba(color,.15),rgba(color,.05))`
- Numbered badge: monospace, `background:rgba(0,0,0,.3)`, white text
- Label: display font italic, white text
- Stack with `gap:clamp(6px,1vh,10px)` for tight grouping

---

## Pattern 6: Glassmorphism Emphasis Card

**Use for:** Hero concepts, key insights, featured metrics

```css
background: linear-gradient(135deg, var(--surface) 0%, rgba(color, 0.04) 100%);
border: 1.5px solid rgba(color, 0.2);
border-radius: 18px;
padding: clamp(20px, 3vh, 36px);
box-shadow: 0 8px 40px rgba(0,0,0,0.3), inset 0 1px 0 rgba(color, 0.05);
```

**Top accent bar:**
```html
<div style="height:3px;background:linear-gradient(90deg,var(--gold),var(--green));border-radius:2px;margin-bottom:clamp(12px,2vh,20px)"></div>
```

**Key rules:**
- `inset 0 1px 0` creates subtle light edge on top
- Gradient background fades from surface to themed color at 0.04 opacity
- Top accent bar uses gradient between two related colors
- Border radius 18px (larger than standard 14-16px) for premium feel

---

## Pattern 7: Icon Badge Row (Traits/Features)

**Use for:** Comparison traits, feature lists, capability displays

```html
<div style="display:flex;align-items:center;gap:.6rem">
  <!-- Icon badge -->
  <div style="width:clamp(28px,3.5vh,36px);height:clamp(28px,3.5vh,36px);border-radius:8px;background:rgba(color,.1);border:1px solid rgba(color,.2);display:flex;align-items:center;justify-content:center;flex-shrink:0">
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--color)" stroke-width="2">...</svg>
  </div>
  <!-- Text -->
  <div>
    <p style="font-family:var(--font-display);font-size:clamp(.92rem,1.2vw,1.08rem);font-style:italic;color:var(--color)">Title</p>
    <p style="font-size:clamp(.72rem,.9vw,.82rem);color:var(--text-dim)">Description</p>
  </div>
</div>
```

**Key rules:**
- Icon badge: rounded square (8px border-radius), NOT circle
- Size: `clamp(28px,3.5vh,36px)` — scales with viewport
- SVG icon: 16x16, `stroke-width:2`
- Each row gets its own themed SVG icon (clock, monitor, team, globe, etc.)

---

## Pattern 8: Variance/Progress Bars (Conceptual)

**Use for:** Showing reduction, improvement, comparison of quantities

```html
<div style="display:flex;align-items:center;gap:.8rem;margin-bottom:.6rem">
  <div style="width:clamp(80px,10vw,120px);text-align:right;font-family:var(--font-body);font-size:.88rem;font-weight:600;color:var(--color)">Label</div>
  <div style="flex:1;height:clamp(32px,4vh,44px);background:rgba(255,255,255,.03);border-radius:10px;overflow:hidden">
    <div style="height:100%;width:90%;background:linear-gradient(90deg,rgba(color,.5),rgba(color,.85));border-radius:10px;display:flex;align-items:center;padding-left:12px;font-family:var(--font-mono);font-size:.82rem;font-weight:700;color:var(--text)">90%</div>
  </div>
</div>
```

**Key rules:**
- Use decreasing bars (90% → 30% → ≈0%) to show convergence/improvement
- Color gradient: red for high variance, gold for medium, green for low
- `border-radius:10px` on both track and fill for rounded ends
- Value text INSIDE the bar for bars >30%; below/beside for smaller bars

---

## SVG Text Sizing Rules (CRITICAL — prevents "text too small" feedback)

**SVG `<text>` elements do NOT respect rem units — use explicit px sizes.**

| Element Type | Minimum Size | Preferred | Font Family |
|-------------|-------------|-----------|-------------|
| **Node titles** (stage names, agent labels) | 14px | 16-18px | `var(--font-display)` italic |
| **Node descriptions** (subtitles, details) | 10px | 11-13px | `var(--font-editorial)` italic |
| **Row/section labels** (COMMANDS, LAYER) | 10px | 11-12px | `var(--font-mono)` uppercase |
| **Badge numbers** (step 1, 2, 3) | 12px | 13-14px | `var(--font-mono)` bold |
| **Center/watermark text** | 18px | 20-24px | `var(--font-display)` italic |

**Rules:**
1. **NEVER use SVG text < 10px** — unreadable on all screens
2. **foreignObject text** uses HTML sizing (rem) — minimum 0.78rem for any text
3. **foreignObject width** MUST be explicit (never `auto`) — use 200-260 viewBox units
4. **Description text color**: use `#c8d8e8` (bright) or `#e8edf5` (white), NOT `#6b7fa0` (dim) — dim text in SVG is invisible

## SVG Positioning & Spacing Rules (CRITICAL — prevents overlapping elements)

1. **ViewBox sizing**: Use 900-1100 width for most diagrams. NEVER use < 700 for diagrams with 4+ nodes
2. **Node-to-node minimum gap**: 50+ viewBox units between any two node edges
3. **Text inside circles**: if text width > circle diameter × 0.7, split into 2 lines or use shorter label
4. **Badge-to-ribbon collision**: step number badges MUST be positioned at the OPPOSITE corner from where ribbons pass — if ribbons enter from the right, put badge top-left
5. **Description tags below/above circles**: position at circle-edge + 25-35 viewBox units (NOT edge + 5)
6. **Expand viewBox for edge elements**: if badges or tags extend beyond `0,0` origin, use negative viewBox values like `viewBox="-20 -60 1140 560"`
7. **Flow ribbon start/end**: ribbons MUST start from circle EDGE (offset by radius toward destination), NOT from circle center

## Mandatory Visual Elevation Rules

1. **Architectures and pipelines MUST use SVG** with glow filters, NOT plain CSS boxes
2. **Step-by-step flows MUST have floating numbered badges** (position:absolute, top:-10px)
3. **Comparison slides MUST use the center divider** with gradient lines + gold circle
4. **Agent/crew diagrams MUST show parallel vs sequential** organization with animated ribbons
5. **Every flow arrow MUST be SVG** — never plain text `→` (except inside pipeline stage separators)
6. **Emphasis cards MUST use glassmorphism** (inset shadow + gradient background + accent bar)
7. **Icon badges MUST use themed SVG icons** — never emoji or unicode symbols for professional slides
8. **All sizing MUST use clamp()** — never fixed px values for text or padding
9. **SVG viewBox width MUST be 900+** for any diagram with 4+ nodes — prevents cramped layouts
10. **SVG text MUST be 10px+** — see SVG Text Sizing Rules above
11. **Description tags MUST have 25+ units clearance** from circles/nodes — see SVG Positioning Rules above

---

## Pattern 9: Topology Map (Network Diagrams)

**Use for:** Comparing linear vs graph topologies, workflow vs agentic patterns, simple vs complex architectures

```html
<!-- Two side-by-side SVG network topologies -->
<div style="display:grid;grid-template-columns:1fr 80px 1fr;gap:0;flex:1">
  <!-- LEFT: Linear topology (Workflow) -->
  <div style="background:rgba(96,165,250,.03);border:1px solid rgba(96,165,250,.12);border-radius:16px;padding:clamp(16px,2.5vh,28px)">
    <p style="font-family:var(--font-mono);font-size:.65rem;color:var(--blue);text-transform:uppercase;letter-spacing:.15em;margin-bottom:.8rem">LINEAR TOPOLOGY</p>
    <svg viewBox="0 0 400 200" style="width:100%">
      <!-- Nodes in a straight line connected by arrows -->
      <rect x="10" y="75" width="80" height="50" rx="10" fill="rgba(96,165,250,.1)" stroke="#60a5fa" stroke-width="1.5"/>
      <text x="50" y="105" text-anchor="middle" font-size="11" fill="#60a5fa" font-family="var(--font-mono)">Node A</text>
      <path d="M95,100 L135,100" stroke="#60a5fa" stroke-width="2" class="flow-r" fill="none" marker-end="url(#arrowB)"/>
      <!-- Repeat for B, C, D nodes -->
    </svg>
  </div>
  <!-- CENTER DIVIDER (gold circle) -->
  <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;gap:.5rem">
    <div style="width:2px;flex:1;background:linear-gradient(180deg,transparent,rgba(212,175,55,.3),transparent);max-height:30%"></div>
    <div style="width:clamp(48px,5vh,60px);height:clamp(48px,5vh,60px);border-radius:50%;background:var(--gold-dim);border:2px solid rgba(212,175,55,.3);display:flex;align-items:center;justify-content:center">
      <span style="font-family:var(--font-display);font-style:italic;font-size:clamp(.82rem,1.2vw,1rem);color:var(--gold)">vs</span>
    </div>
    <div style="width:2px;flex:1;background:linear-gradient(180deg,transparent,rgba(212,175,55,.3),transparent);max-height:30%"></div>
  </div>
  <!-- RIGHT: Graph/mesh topology (Agentic) -->
  <div style="background:rgba(167,139,250,.03);border:1px solid rgba(167,139,250,.12);border-radius:16px;padding:clamp(16px,2.5vh,28px);box-shadow:0 0 30px rgba(167,139,250,.04)">
    <p style="font-family:var(--font-mono);font-size:.65rem;color:var(--purple);text-transform:uppercase;letter-spacing:.15em;margin-bottom:.8rem">GRAPH TOPOLOGY</p>
    <svg viewBox="0 0 400 200" style="width:100%">
      <!-- Nodes interconnected with bidirectional arrows, feedback loops -->
      <circle cx="200" cy="100" r="30" fill="rgba(167,139,250,.1)" stroke="#a78bfa" stroke-width="1.5"/>
      <!-- Add satellite nodes at 120-degree intervals with cross-connections -->
    </svg>
  </div>
</div>
```

**Key rules:**
- LEFT = simple/predictable pattern (blue theme), RIGHT = complex/adaptive (purple theme with glow)
- Use actual SVG network diagrams — NOT text descriptions
- Cross-connections in graph topology use curved bezier paths at varying opacities
- Feedback loops use animated `flow-r` class on curved paths

---

## Pattern 10: Quadrant Matrix (2×2 Decision Grid)

**Use for:** Comparing 4 options along 2 axes, paradigm selection, tool comparison

```html
<div style="display:grid;grid-template-columns:1fr 1fr;grid-template-rows:1fr 1fr;gap:clamp(8px,1.2vw,14px);flex:1">
  <!-- Each quadrant -->
  <div style="background:var(--surface);border:1.5px solid rgba(color,.2);border-radius:16px;padding:clamp(16px,2.5vh,28px);position:relative;transition:transform .3s ease" onmouseover="this.style.transform='translateY(-4px)'" onmouseout="this.style.transform='none'">
    <!-- Quadrant label badge -->
    <div style="position:absolute;top:-10px;left:clamp(12px,2vw,20px);font-family:var(--font-mono);font-size:.62rem;font-weight:700;padding:2px 10px;border-radius:6px;background:rgba(color,.15);color:var(--color)">QUADRANT 1</div>
    <!-- SVG icon (32x32) -->
    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--color)" stroke-width="1.8">...</svg>
    <!-- Title -->
    <p style="font-family:var(--font-display);font-size:clamp(1.1rem,1.5vw,1.3rem);font-style:italic;color:var(--color);margin:.4rem 0 .2rem">Name</p>
    <!-- Subtitle -->
    <p style="font-family:var(--font-editorial);font-size:clamp(.82rem,1vw,.92rem);color:var(--text-dim);font-style:italic">Description</p>
    <!-- Key trait badge -->
    <div style="margin-top:.5rem;display:inline-flex;padding:.2rem .6rem;background:rgba(color,.08);border-radius:6px;font-family:var(--font-mono);font-size:.62rem;color:var(--color)">KEY TRAIT</div>
  </div>
  <!-- Repeat for 4 quadrants with different colors: accent, gold, purple, green -->
</div>
<!-- Axis labels overlaid -->
<div style="position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);font-family:var(--font-mono);font-size:.58rem;color:var(--text-dim);letter-spacing:.12em">CENTER LABEL</div>
```

**Key rules:**
- 4 quadrants with 4 different accent colors (accent, gold, purple, green)
- Floating badges at top of each quadrant
- Hover effect on each quadrant: `translateY(-4px)`
- Axis labels placed at edges or center using absolute positioning
- Each quadrant gets an SVG icon + title + description + key trait badge

---

## Pattern 11: Balance Scales (Paradox Visualization)

**Use for:** Showing that two opposing concepts BOTH increase together (not zero-sum), paradoxes, dual growth

```html
<svg viewBox="0 0 900 400" style="width:100%;max-height:clamp(300px,50vh,420px)">
  <defs>
    <filter id="scale-glow"><feGaussianBlur stdDeviation="5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
    <linearGradient id="beam-g" x1="0%" x2="100%"><stop offset="0%" stop-color="#d4af37" stop-opacity=".6"/><stop offset="100%" stop-color="#00b4ff" stop-opacity=".6"/></linearGradient>
  </defs>
  <!-- Central fulcrum -->
  <polygon points="450,350 430,380 470,380" fill="rgba(212,175,55,.3)" stroke="var(--gold)" stroke-width="1.5"/>
  <!-- Balance beam (tilted to show BOTH sides rising) -->
  <line x1="150" y1="180" x2="750" y2="180" stroke="url(#beam-g)" stroke-width="3" filter="url(#scale-glow)"/>
  <!-- LEFT pan (delegation) — rising -->
  <rect x="100" y="120" width="200" height="100" rx="14" fill="rgba(0,180,255,.08)" stroke="var(--accent)" stroke-width="1.5"/>
  <text x="200" y="160" text-anchor="middle" font-size="16" fill="var(--accent)" font-family="var(--font-display)" font-style="italic">Delegação</text>
  <text x="200" y="185" text-anchor="middle" font-size="11" fill="#c8d8e8" font-family="var(--font-editorial)" font-style="italic">Mais poder para agentes</text>
  <!-- Arrow showing BOTH rise -->
  <path d="M200,115 L200,80" stroke="var(--accent)" stroke-width="2" marker-end="url(#arrowUp)"/>
  <!-- RIGHT pan (responsibility) — also rising -->
  <rect x="600" y="120" width="200" height="100" rx="14" fill="rgba(212,175,55,.08)" stroke="var(--gold)" stroke-width="1.5"/>
  <text x="700" y="160" text-anchor="middle" font-size="16" fill="var(--gold)" font-family="var(--font-display)" font-style="italic">Responsabilidade</text>
  <path d="M700,115 L700,80" stroke="var(--gold)" stroke-width="2" marker-end="url(#arrowUp)"/>
  <!-- Center label -->
  <text x="450" y="340" text-anchor="middle" font-size="13" fill="var(--text-dim)" font-family="var(--font-mono)" letter-spacing="2">AMBOS SOBEM JUNTOS</text>
</svg>
```

**Key rules:**
- The beam is LEVEL or both sides rise — NOT a traditional imbalanced scale
- Left pan = one concept (accent), Right pan = opposing concept (gold)
- Both have upward arrows showing growth
- Central fulcrum with gold theme
- Gradient beam with glow filter for visual depth
- Key message at center: both sides grow together

---

## Pattern 12: Iceberg Diagram (Visible vs Hidden)

**Use for:** Surface skills vs deep skills, visible vs hidden factors, tip-of-the-iceberg concepts

```html
<svg viewBox="0 0 900 500" style="width:100%;max-height:clamp(340px,55vh,480px)">
  <defs>
    <linearGradient id="water" x1="0%" y1="0%" x2="0%" y2="100%"><stop offset="0%" stop-color="rgba(0,180,255,.15)"/><stop offset="100%" stop-color="rgba(0,180,255,.02)"/></linearGradient>
    <filter id="ice-glow"><feGaussianBlur stdDeviation="4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  </defs>
  <!-- Waterline -->
  <line x1="0" y1="160" x2="900" y2="160" stroke="rgba(0,180,255,.3)" stroke-width="1.5" stroke-dasharray="8 8"/>
  <text x="870" y="155" text-anchor="end" font-size="10" fill="var(--accent)" font-family="var(--font-mono)" letter-spacing="1.5">WATERLINE</text>
  <!-- Water fill below -->
  <rect x="0" y="160" width="900" height="340" fill="url(#water)"/>
  <!-- Above water (visible skills) — small triangle tip -->
  <polygon points="450,40 380,155 520,155" fill="rgba(212,175,55,.12)" stroke="var(--gold)" stroke-width="1.5" filter="url(#ice-glow)"/>
  <text x="450" y="110" text-anchor="middle" font-size="14" fill="var(--gold)" font-family="var(--font-display)" font-style="italic">Visível</text>
  <!-- Below water (hidden skills) — large trapezoid body -->
  <polygon points="380,165 520,165 620,460 280,460" fill="rgba(0,180,255,.06)" stroke="var(--accent)" stroke-width="1.5"/>
  <!-- Labels inside iceberg body -->
  <text x="450" y="220" text-anchor="middle" font-size="14" fill="var(--accent)" font-family="var(--font-display)" font-style="italic">Oculto</text>
  <!-- Skill labels at different depths -->
  <foreignObject x="300" y="240" width="300" height="40">
    <div xmlns="http://www.w3.org/1999/xhtml" style="font-family:var(--font-editorial);font-size:.88rem;color:#c8d8e8;text-align:center;font-style:italic">Meta-skill label here</div>
  </foreignObject>
</svg>
```

**Key rules:**
- Waterline at ~30% from top (small visible portion, large hidden)
- Above water: gold theme (visible skills), Below: accent theme (hidden depth)
- Use dashed line for waterline with "WATERLINE" label
- Water fill uses subtle gradient
- Labels inside iceberg body use foreignObject for HTML text
- Ice tip has glow filter for emphasis

---

## Pattern 13: Portal/Threshold (Transformation Moment)

**Use for:** Identity transformation, ritual passages, before/after states, crossing a boundary

```html
<svg viewBox="0 0 1000 450" style="width:100%;max-height:clamp(320px,52vh,440px)">
  <defs>
    <linearGradient id="portal-g" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="rgba(248,81,73,.3)"/>
      <stop offset="40%" stop-color="rgba(212,175,55,.5)"/>
      <stop offset="100%" stop-color="rgba(0,180,255,.3)"/>
    </linearGradient>
    <filter id="portal-glow"><feGaussianBlur stdDeviation="8" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  </defs>
  <!-- LEFT zone (Before) — dim, red-tinted -->
  <rect x="0" y="0" width="400" height="450" fill="rgba(248,81,73,.02)"/>
  <text x="200" y="40" text-anchor="middle" font-size="14" fill="var(--red)" font-family="var(--font-mono)" letter-spacing="2">BEFORE</text>
  <!-- PORTAL arch (center) -->
  <path d="M430,400 L430,100 Q500,20 570,100 L570,400" stroke="url(#portal-g)" stroke-width="4" fill="none" filter="url(#portal-glow)"/>
  <!-- Animated particles flowing through portal -->
  <circle cx="500" cy="200" r="3" fill="var(--gold)" opacity=".6"><animate attributeName="cy" values="350;100" dur="2s" repeatCount="indefinite"/></circle>
  <!-- RIGHT zone (After) — bright, cyan-tinted, glow -->
  <rect x="600" y="0" width="400" height="450" fill="rgba(0,180,255,.03)"/>
  <text x="800" y="40" text-anchor="middle" font-size="14" fill="var(--accent)" font-family="var(--font-mono)" letter-spacing="2">AFTER</text>
  <!-- Identity labels on each side -->
  <foreignObject x="50" y="180" width="300" height="80">
    <div xmlns="http://www.w3.org/1999/xhtml" style="font-family:var(--font-display);font-size:1.3rem;color:var(--text-dim);font-style:italic;text-align:center">AI-Curious</div>
  </foreignObject>
  <foreignObject x="650" y="180" width="300" height="80">
    <div xmlns="http://www.w3.org/1999/xhtml" style="font-family:var(--font-display);font-size:1.3rem;color:var(--accent);font-style:italic;text-align:center">AI-Native Engineer</div>
  </foreignObject>
</svg>
```

**Key rules:**
- Portal arch at center using quadratic bezier curve with gradient stroke
- LEFT zone: dim, red-tinted (before state)
- RIGHT zone: bright, cyan-tinted with glow (after state)
- Animated particles flowing through the portal (SVG `<animate>`)
- Portal glow filter for dramatic emphasis
- Identity labels on each side using foreignObject

---

## Pattern 14: Journey Path (Winding Road with Waypoints)

**Use for:** Course maps, learning journeys, multi-stage progressions with stops

```html
<svg viewBox="0 0 1100 400" style="width:100%;max-height:clamp(300px,50vh,420px)">
  <defs>
    <linearGradient id="path-g" x1="0%" x2="100%"><stop offset="0%" stop-color="#f85149" stop-opacity=".6"/><stop offset="33%" stop-color="#d4af37" stop-opacity=".6"/><stop offset="66%" stop-color="#a78bfa" stop-opacity=".6"/><stop offset="100%" stop-color="#00b4ff" stop-opacity=".6"/></linearGradient>
  </defs>
  <!-- Winding path -->
  <path d="M50,350 C150,350 200,100 350,100 C500,100 500,300 650,300 C800,300 800,80 1050,80" stroke="url(#path-g)" stroke-width="4" fill="none" class="flow-r" stroke-dasharray="12 8"/>
  <!-- Waypoint 1 -->
  <circle cx="50" cy="350" r="18" fill="rgba(248,81,73,.15)" stroke="var(--red)" stroke-width="2"/>
  <text x="50" y="354" text-anchor="middle" font-size="12" fill="var(--red)" font-family="var(--font-mono)" font-weight="700">01</text>
  <foreignObject x="-20" y="375" width="140" height="40">
    <div xmlns="http://www.w3.org/1999/xhtml" style="font-family:var(--font-display);font-size:.88rem;color:var(--red);font-style:italic;text-align:center">MindSet</div>
  </foreignObject>
  <!-- Waypoint 2 at curve peak -->
  <circle cx="350" cy="100" r="18" fill="rgba(212,175,55,.15)" stroke="var(--gold)" stroke-width="2"/>
  <text x="350" y="104" text-anchor="middle" font-size="12" fill="var(--gold)" font-family="var(--font-mono)" font-weight="700">02</text>
  <!-- Continue for waypoints 3, 4 at different curve positions -->
  <!-- Final destination with pulse-glow -->
  <circle cx="1050" cy="80" r="22" fill="rgba(0,180,255,.15)" stroke="var(--accent)" stroke-width="2" style="animation:pulse-glow 3s ease-in-out infinite"/>
</svg>
```

**Key rules:**
- Winding bezier path (not straight line) — curves add visual interest
- Path uses gradient stroke that transitions through colors per stage
- Animated flow using `flow-r` class on the path
- Waypoint circles at curve peaks/valleys with numbered badges
- Final destination gets `pulse-glow` animation
- foreignObject labels below/above waypoints

---

## Pattern 15: Tectonic Shift (Paradigm Change)

**Use for:** Dramatic paradigm shifts, before/after eras, market disruption

```html
<svg viewBox="0 0 1000 400" style="width:100%;max-height:clamp(300px,52vh,440px)">
  <defs>
    <filter id="crack-glow"><feGaussianBlur stdDeviation="6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
    <linearGradient id="crack-g" x1="0%" y1="0%" x2="0%" y2="100%"><stop offset="0%" stop-color="#d4af37"/><stop offset="100%" stop-color="#ef9000"/></linearGradient>
  </defs>
  <!-- LEFT plate (old paradigm) — sinking slightly -->
  <polygon points="0,120 480,140 480,400 0,400" fill="rgba(248,81,73,.05)" stroke="rgba(248,81,73,.2)" stroke-width="1"/>
  <text x="240" y="200" text-anchor="middle" font-size="18" fill="var(--red)" font-family="var(--font-display)" font-style="italic" opacity=".7">Paradigma Antigo</text>
  <!-- RIGHT plate (new paradigm) — rising -->
  <polygon points="520,100 1000,80 1000,400 520,400" fill="rgba(0,180,255,.05)" stroke="rgba(0,180,255,.2)" stroke-width="1"/>
  <text x="760" y="180" text-anchor="middle" font-size="18" fill="var(--accent)" font-family="var(--font-display)" font-style="italic">Novo Paradigma</text>
  <!-- CRACK/fault line between plates -->
  <path d="M490,0 L500,80 L485,160 L510,240 L480,320 L505,400" stroke="url(#crack-g)" stroke-width="5" fill="none" filter="url(#crack-glow)"/>
  <!-- Energy particles at crack -->
  <circle cx="500" cy="120" r="4" fill="var(--gold)" opacity=".8"><animate attributeName="opacity" values=".3;1;.3" dur="1.5s" repeatCount="indefinite"/></circle>
  <circle cx="490" cy="200" r="3" fill="var(--orange)" opacity=".6"><animate attributeName="opacity" values=".5;1;.5" dur="2s" repeatCount="indefinite"/></circle>
</svg>
```

**Key rules:**
- Two polygonal plates with slight angle (old sinks, new rises)
- Jagged crack/fault line down the center with gold/orange gradient + glow
- Animated energy particles along the crack
- LEFT plate: red-tinted (old, fading), RIGHT: cyan-tinted (new, glowing)
- Labels inside each plate using display font italic
- Crack conveys urgency and irreversibility of the shift
