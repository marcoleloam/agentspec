# Quality Rules — AIDE Slides

> Hard-won rules from 8+ iterations on AL-1. Every rule here exists because it was a repeated mistake. Read BEFORE generating any slide.

---

## Screen Filling Rules

1. Every slide MUST fill **90%+ of viewport height** — no large empty gaps
2. Use `justify-content: center` as default — NEVER `flex-start` unless the slide truly needs top-alignment AND has enough content to fill
3. Every content slide MUST have a **bottom explanation panel** using `margin-top: auto` that fills remaining space
4. Bottom panels explain **WHY this matters** for the AI Data Engineer — connect technical content to practical value
5. If a slide has a grid/timeline/flow, the content block itself should be vertically centered — NOT pushed to the top
6. Use `padding-top: clamp(48px,7vh,68px)` — never more than 90px top padding
7. Use `padding-bottom: clamp(24px,3vh,40px)` to balance top padding

## Horizontal Width Rules (CRITICAL — prevents narrow/cramped content)

1. **SVG diagrams** MUST use `width:100%` and `max-height:clamp(300px,55vh,500px)` — never set a restrictive `max-width` below 90vw
2. **ViewBox width** MUST be 900+ for architecture/flow diagrams (not 600). Use 1000-1200 for complex diagrams with 5+ nodes
3. **Card grids** MUST fill available width — use `flex:1` on grid containers, never set `max-width` on cards
4. **Stage cards** MUST use `display:grid;grid-template-columns:1fr 1fr` to fill width with LEFT (content) + RIGHT (evidence) columns
5. **Comparison slides** (vs/split-screen) MUST use `grid-template-columns:1fr 64px 1fr` with `gap:0` — columns fill full width
6. **Node boxes** in SVG diagrams: minimum `width:200` viewBox units (renders ~200px). Preferred: 220-260

## Bottom Bar Pattern (GOLDEN REFERENCE — from d1-ingest.html slides 1-9)

**DO NOT use `.bottom-panel` class or `.content-center-wrap` wrapper.**

The production-proven pattern is an **inline flex bar** with `margin-top:auto` and `border-top`:

```html
<div class="reveal" style="margin-top:auto; padding-top:clamp(12px,2vh,20px); border-top:1px solid var(--border); display:flex; align-items:center; justify-content:space-between; gap:clamp(16px,3vw,32px);">
  <p style="font-family:var(--font-editorial); font-size:clamp(1rem,1.7vw,1.25rem); font-style:italic; color:var(--text-dim); line-height:1.5; flex:1;">
    Message text with <strong style="color:var(--accent);">key highlights</strong> in bold accent color.
  </p>
  <div style="display:flex; gap:0.5rem; flex-shrink:0;">
    <span class="tag tag-accent">TAG 1</span>
    <span class="tag tag-silver">TAG 2</span>
    <span class="tag tag-gold">TAG 3</span>
  </div>
</div>
```

**Rules:**
1. **3+ tags minimum** in the right-side tag row — never just 1-2
2. **2+ sentences** in the editorial italic text — never a fragment
3. Use `<strong style="color:var(--accent);">` to highlight key phrases
4. For key architecture slides, use the **enriched glassmorphism variant**:
```html
<div class="reveal" style="padding:clamp(10px,1.5vh,16px) clamp(16px,2vw,24px); background:linear-gradient(135deg, var(--surface) 0%, rgba(COLOR,0.03) 100%); border:1px solid var(--border-bright); border-radius:14px; display:flex; align-items:center; justify-content:space-between; gap:1rem; box-shadow:0 4px 24px rgba(0,0,0,0.2);">
```
5. The enriched variant can include a small SVG icon before the text (like slide 4's lightning bolt)

## Circular Element Spacing Rules

1. **Minimum clearance** from circle edge to description tag: circle radius + 25px (in viewBox units)
2. **Agent circles** in orbital diagrams: radius 46-48 viewBox units, description tags placed radius+30 units away
3. **Spectrum markers**: node radius 8-10, label box placed 20+ units below/above the node
4. **Concentric circles with text**: split long labels into 2 lines using separate `<text>` elements, never overflow the circle diameter
5. **Step number badges**: position OUTSIDE the flow ribbon path — if ribbons pass near (x,y), move badge to opposite corner of the node box

## Portuguese Language Rules

1. **ALWAYS use proper accents** — this is Brazilian Portuguese, not ASCII:
   - ã, õ (nasal): Formação, não, atenção, computação, revolução
   - ç (cedilha): informação, publicação, classificação
   - é, ê (acute/circumflex): é, você, também, ciência
   - á, â: prática, parâmetro, matemático
   - ó, ô: lógica, próximo, módulo
   - ú: único, conteúdo, público
   - í: possível, específico, estatístico
2. Common words that MUST have accents: Formação, não, é, também, está, você, módulo, próximo, prática, atenção, página, código, número, único, índice, conteúdo, informação, classificação, tradução
3. Use `&ldquo;` and `&rdquo;` for smart quotes, `&mdash;` for em-dash

## Portuguese Accent Validation Checklist (MANDATORY before delivery)

Run this search-and-replace on EVERY generated deck before considering it complete:

| Wrong | Correct | Context |
|-------|---------|---------|
| ESTAGIO | ESTÁGIO | Stage labels in SVG and HTML |
| Estagio | Estágio | Mixed case |
| voce | você | All occurrences |
| vocêestá | você está | Missing space (common bug) |
| esta (as verb) | está | "onde você está" |
| sao | são | "universos diferentes" |
| nao | não | Negation |
| equacao | equação | Math/formula context |
| decisao | decisão | Decision context |
| presenca | presença | Presence context |
| nivel | nível | Level references |
| especifico | específico | Specific context |
| formacao | formação | Course name |
| FORMACAO | FORMAÇÃO | Uppercase in branding bar |
| codigo | código | Code references |
| pratica | prática | "Na prática" sections |
| diferenca | diferença | Difference context |
| comeca | começa | "starts" context |
| cirurgiao | cirurgião | Surgeon metaphor |
| construcao | construção | Construction metaphor |
| producao | produção | Production context |
| autonomos | autônomos | Autonomous agents |
| rapido | rápido | Fast/speed context |

**Also check for:** `maioriaestá` → `maioria está`, `oportunidadeestá` → `oportunidade está` (merged words)

## Typography Rules (Updated from d1-ingest.html production session)

1. **Minimum body text:** 0.88rem — never below 0.78rem for any readable content
2. **Minimum detail/description text:** 0.78rem — never below 0.68rem for decorative mono labels
3. **Headings:** ALWAYS use `font-family: var(--font-display)` (Instrument Serif) with `font-style: italic`
4. **Heading highlights:** Use `<span style="color:var(--accent);">` NOT `<em>` tags — `<em>` is for semantics, `<span>` is for visual coloring
5. **Card titles:** `font-display` at `clamp(1.3rem,2.2vw,1.7rem)` italic — NOT DM Sans bold
6. **Comparison card titles:** `clamp(1.6rem,2.8vw,2.2rem)` for 2-panel slides (bigger for visual weight)
7. **Mono labels:** `font-family: var(--font-mono)` (Fira Code) at 0.62-0.78rem for uppercase labels
8. **Body text / bullet points:** `font-family: var(--font-editorial)` (Newsreader) italic for ALL descriptive content — quotes, card descriptions, bullet points, editorial text. NEVER use `var(--font-body)` (DM Sans) for bullet point descriptions.
9. **Stat values:** Use `font-display` italic (Instrument Serif) at `clamp(42px,7vw,72px)`, letter-spacing -0.03em — NOT `.stat-val` class (which uses DM Sans 800)
10. Never use DM Sans for headings or stat numbers — it's for UI labels only
11. **SVG text MUST use inline font strings** — CSS variables don't resolve in SVG attributes:
    - `font-family="'Instrument Serif',serif"` (NOT `var(--font-display)`)
    - `font-family="'Fira Code',monospace"` (NOT `var(--font-mono)`)
    - `font-family="'Newsreader',serif"` (NOT `var(--font-editorial)`)

## Content Density Rules

1. Every card/container MUST have a **practical example** ("Na prática:" section with tinted background)
2. Timeline nodes MUST have ALL of: year + title + tagline + detail paragraph + stat pill (5 elements)
3. Flow architectures MUST have **numbered steps** with SVG arrow icons between them
4. Tables MUST use `font-display italic` for the first column (names/titles)
5. Training pipeline MUST show a **concrete example** pipeline (e.g., Internet → Pre-Training → SFT → RLHF → ChatGPT)
6. Divider slides MUST have a ghost number (200-500px, opacity 0.04) + section label + heading + description
7. Q/K/V and attention slides MUST show both the metaphor AND the mathematical flow diagram

## Layout Rules

1. **2-column grids:** `grid-template-columns: 1fr 1.2fr` (slightly wider right for cards/flows)
2. **Cards in a column:** `display: flex; flex-direction: column` with `margin-top: auto` to push bottom content
3. **Timeline grid:** `grid-template-columns: repeat(7, 1fr)` with `justify-content: center` on the slide
4. **Phase flows:** SVG arrow `<svg>` icons between cards — NEVER plain text `→`
5. **Bottom explanation panels:** `background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 0.8rem 1.5rem`
6. **Flow step numbering:** Circular badges (18-40px, border-radius: 50% or 10px, accent-dim background)
7. **Tag pills:** `font-family: var(--font-mono); font-size: 0.58-0.68rem; padding: 0.2-0.25rem 0.5-0.65rem; border-radius: 4-6px`

## Slide Structure Rules

1. **Title slide (slide 1):** MUST include Luan Moreno image (`../../../images/luan-moreno.png`), module badge, class code pill, duration pill, course subtitle, instructor info, tag row
2. **Hook quote (slide 2-3):** Giant quote mark (opacity 0.05), editorial italic blockquote, cite line with source
3. **Every section MUST start with a divider slide** with ghost number + heading + one-line description
4. **Closing slide:** Quote + "Próximo: AL-X" tag + AIDE BRASIL footer

## Card Hover Effects (GOLDEN REFERENCE)

**NEVER use CSS-only `:hover`.** Use inline `onmouseenter`/`onmouseleave` JS for ALL interactive cards:

```html
<div style="background:var(--surface); border:1px solid rgba(COLOR,0.12); border-radius:16px; padding:clamp(22px,3.5vh,36px) clamp(18px,2.5vw,28px); display:flex; flex-direction:column; transition:transform 0.3s, box-shadow 0.3s, border-color 0.3s;"
  onmouseenter="this.style.borderColor='rgba(COLOR,0.3)';this.style.transform='translateY(-3px)';this.style.boxShadow='0 8px 28px rgba(COLOR,0.06)'"
  onmouseleave="this.style.borderColor='rgba(COLOR,0.12)';this.style.transform='none';this.style.boxShadow='none'">
```

**RGB values by color:**
- accent: `74,158,255` | gold: `212,175,55` | silver: `176,190,197`
- orange: `239,144,0` | green: `63,185,80` | purple: `167,139,250`
- red: `248,81,73` | cyan: `34,211,238` | blue: `96,165,250`

**Rules:**
1. NEVER mix `onmouseover`/`onmouseout` with `onmouseenter`/`onmouseleave` — they conflict
2. NEVER have duplicate `style=""` attributes on the same element — merge into one
3. NEVER have duplicate `flex:1` in the same style string

## Stat Card Pattern (GOLDEN REFERENCE)

Stat cards should have **4 lines** (not 2):

```html
<div class="stat-card" style="border-top:2px solid var(--gold); padding:clamp(22px,3.5vh,36px) clamp(18px,2.5vw,28px);">
  <!-- 1. Big number — Instrument Serif italic, NOT .stat-val -->
  <div style="font-family:var(--font-display); font-size:clamp(42px,7vw,72px); font-style:italic; color:var(--gold); line-height:1; letter-spacing:-0.03em;">$3–5T</div>
  <!-- 2. Mono label -->
  <div class="stat-lbl" style="margin-top:clamp(6px,1vh,10px);">MCKINSEY 2026</div>
  <!-- 3. Trend line (NEW — from Kurv template) -->
  <p style="font-family:var(--font-mono); font-size:clamp(0.72rem,0.95vw,0.82rem); margin-top:clamp(4px,0.6vh,6px); color:var(--green);">▲ Crescimento acelerado</p>
  <!-- 4. Editorial description -->
  <p style="font-family:var(--font-editorial); font-size:clamp(0.92rem,1.3vw,1.08rem); font-style:italic; color:var(--text-dim); margin-top:clamp(8px,1.2vh,14px); line-height:1.55;">Valor gerado por agentes de IA no comércio global.</p>
</div>
```

## Comparison Card Pattern (Before/After — GOLDEN REFERENCE)

For 2-panel slides, use glassmorphism cards with Instrument Serif titles, **bold key phrases**, SVG icons or tag badges, and a nested stat section:

```html
<!-- LEFT panel (old/before) — subtle border, no glow -->
<div style="background:var(--surface); border:1px solid rgba(248,81,73,0.12); border-radius:16px; padding:clamp(30px,5vh,52px) clamp(28px,4vw,44px); display:flex; flex-direction:column;">
  <p style="font-family:var(--font-display); font-size:clamp(1.6rem,2.8vw,2.2rem); font-style:italic;">O Funil <span style="color:var(--red);">Tradicional</span></p>
  <p style="font-family:var(--font-editorial); font-size:clamp(1rem,1.5vw,1.2rem); font-style:italic; color:var(--text-dim);">Description with <strong style="color:var(--text);">bold key phrases</strong>.</p>
  <!-- Bullet items with SVG X icons -->
  <!-- Nested stat section at bottom -->
  <div style="margin-top:auto; padding-top:clamp(14px,2vh,20px); border-top:1px solid var(--border);">
    <p style="font-family:var(--font-display); font-size:clamp(2.4rem,4.5vw,3.6rem); font-style:italic; color:var(--red);">7 etapas</p>
  </div>
</div>

<!-- RIGHT panel (new/after) — accent tint + pulse-glow -->
<div style="background:linear-gradient(135deg, var(--surface) 0%, rgba(74,158,255,0.04) 100%); border:1px solid rgba(74,158,255,0.18); animation:pulse-glow 4s ease-in-out infinite;">
  <!-- Same structure but with colored tag badges instead of X icons -->
</div>
```

**Key rules for comparison cards:**
1. Bullet items on LEFT use SVG X icons (stroke red)
2. Bullet items on RIGHT use colored `<span class="tag tag-{color}">` badges
3. Body text uses `var(--font-editorial)` italic with `<strong>` highlights
4. Big stat number at bottom uses Instrument Serif at `clamp(2.4rem,4.5vw,3.6rem)`
5. Card padding: `clamp(30px,5vh,52px) clamp(28px,4vw,44px)` — generous

## Performance Bars Pattern

Animated horizontal bars showing progression (from Kurv `.perf-bar` pattern):

```html
<div style="display:flex; align-items:center; gap:clamp(8px,1.2vw,14px);">
  <span style="font-family:var(--font-mono); font-size:clamp(0.72rem,1vw,0.82rem); color:var(--COLOR); width:clamp(90px,11vw,120px); text-align:right; flex-shrink:0;">Label</span>
  <div style="flex:1; height:clamp(26px,3.8vh,34px); border-radius:8px; background:var(--surface); overflow:hidden;">
    <div style="width:75%; height:100%; border-radius:8px; background:linear-gradient(90deg, rgba(COLOR,0.3), rgba(COLOR,0.5)); display:flex; align-items:center; padding-left:clamp(8px,1vw,12px); font-family:var(--font-mono); font-size:clamp(0.72rem,0.95vw,0.82rem); font-weight:600; color:var(--COLOR); animation:bar-fill 1.4s cubic-bezier(0.16,1,0.3,1) both;">Text</div>
  </div>
</div>
```

## The Brain + The Hands Pattern (LLM vs Agent comparison)

Two glassmorphism panels with a center connector circle:
- LEFT: `border-radius:18px 0 0 18px` (silver glass, `rgba(176,190,197,0.06)`)
- CENTER: gradient line + circle with `+` symbol + gradient line
- RIGHT: `border-radius:0 18px 18px 0` (accent glass, `rgba(74,158,255,0.08)`)
- Each panel has 4 capability rows: icon badge (36x36 rounded square) + title (editorial bold) + description (editorial italic dim)
- Use `backdrop-filter:blur(12px)` for glassmorphism depth

## Semana Deck Rules (d1-d4 files)

1. **Palette:** Black/Silver/Blue — `--accent: #4a9eff`, `--silver: #b0bec5`, `--bg: #08080a`
2. NEVER use Kurv green (`#b2f752`) or AIDE cyan (`#00b4ff`)
3. Use `color-mix(in srgb, var(--bg) 60%, transparent 40%)` for dot nav background
4. Portuguese text uses **direct UTF-8 characters** (ã, ç, é) — NOT HTML entities (`&atilde;`)
5. Structural entities (`&mdash;`, `&middot;`, `&rarr;`, `&ndash;`, `&ldquo;`, `&rdquo;`) are OK

## AIDE Branding

1. **Top bar:** Fixed, 44px height, background rgba(10,15,26,0.85), shows "FORMAÇÃO AI DATA ENGINEER" left, "De AI-Curious a AI-Native Engineer" center, "Luan Moreno · 2026" right
2. **Color palette:** Navy/Cyan/Gold — NEVER use Kurv green (#b2f752)
3. **Footer on closing slide:** "FORMAÇÃO AI DATA ENGINEER · AIDE BRASIL · aide-brasil.ai · 2026"
