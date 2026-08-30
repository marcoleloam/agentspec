# Slide Types — AIDE Slides

> Every slide in the deck fits one of these types. Choose the right type for each content item.

---

## 1. Title Slide (`slide--title`)

**Purpose:** Opening slide for the lesson. Sets the tone.
**Layout:** Centered, instructor image, module/class badges
**Required elements:** Module label, AL-X pill, duration pill, Instrument Serif title with shimmer, subtitle in Newsreader italic, instructor avatar + name, tag row

```html
<section class="slide slide--title">
  <!-- SVG corner brackets (accent top-left, gold bottom-right) -->
  <!-- Module label: "MÓDULO 01 — GENAI FUNDAMENTALS" -->
  <!-- Class pills: AL-1 + 12 min -->
  <!-- Hero title with shimmer-text -->
  <!-- Subtitle in font-editorial italic -->
  <!-- Instructor: circular image + name + AIDE BRASIL -->
  <!-- Tags: Layer · Self-Paced · aide-brasil.ai -->
</section>
```

## 2. Hook Quote (`slide--quote`)

**Purpose:** Dramatic opening quote to grab attention.
**Layout:** Centered, giant quote mark, editorial blockquote
**Required elements:** Quote mark (opacity 0.05), blockquote with key phrase highlighted, cite with source

## 3. Context Slide (Bio/Explanation)

**Purpose:** Explain a person, concept, or background before diving in.
**Layout:** 2-column grid (1fr 1.2fr), bio left + cards right
**Required elements:** Editorial text paragraphs (0.95rem+), 4-5 contribution cards with colored left-borders, bottom quote panel
**Screen filling:** Cards use flex-column, bio fills with multiple paragraphs

## 4. Timeline Grid

**Purpose:** Show historical progression.
**Layout:** 7-column CSS grid, centered on slide
**Required elements per node:** Year (display 1.5rem), title (display 1.05rem), tagline (editorial italic), detail paragraph (body 0.78rem), stat pill (mono 0.62rem)
**Screen filling:** `justify-content: center` on slide, bottom row with quote + stat tags

## 5. Stat Cards

**Purpose:** Display 3-4 key metrics.
**Layout:** 3-column grid
**Required elements:** Large stat value (800 weight), mono label, description line, bottom explanation panel connecting stats to course

## 6. Divider (`slide--divider`)

**Purpose:** Visual break between sections.
**Layout:** Centered, ghost number background
**Required elements:** Giant number (200-500px, opacity 0.04, gradient text), section label, heading with shimmer, one-line description

## 7. Flow Architecture

**Purpose:** Show data/process flow left-to-right.
**Layout:** Flex row with SVG arrows between boxes
**Required elements:** Input box → [Content boxes with details] → Output box, numbered steps, practical examples in each card, bottom insight panel

## 8. Pipeline (Horizontal Steps)

**Purpose:** Show numbered sequential steps.
**Layout:** Flex row with numbered circles + SVG arrows
**Required elements:** Numbered badge (40px circle), title in font-display, description, formula/evidence if applicable

## 9. Phase Flow (Training/Process)

**Purpose:** Show 3-phase progression with details.
**Layout:** `.phase-flow` with `.phase-card` + `.phase-connector` SVG arrows
**Required elements:** Phase number (mono), phase name (display italic), description (editorial italic), evidence pill (gold-dim), sub-note, bottom example pipeline

## 10. Bar Chart

**Purpose:** Show comparative data with animated bars.
**Layout:** `.bar-chart` stacked rows
**Required elements:** Labels (body 0.92rem + mono year), track + fill with gradient, values inside bars

## 11. Method Grid (2-panel comparison)

**Purpose:** Compare two approaches side-by-side.
**Layout:** `.method-grid` 2-column
**Required elements:** Panel with colored border, mono heading, editorial description, body details

## 12. Tier Cards (3-column comparison)

**Purpose:** Compare 3 options/versions.
**Layout:** `.tier-row` 3-column grid
**Required elements:** Display italic title, mono subtitle, body description, code block example (optional), one card highlighted with pulse-glow

## 13. Table Slide

**Purpose:** Display structured data.
**Layout:** `.authors-table` full-width
**Required elements:** Mono uppercase headers, display italic first column, hover highlight, tag pills in status column

## 14. Closing Quote

**Purpose:** Epic closing + next lesson teaser.
**Layout:** `slide--quote` centered
**Required elements:** Gold quote mark, blockquote, editorial follow-up paragraph, "Próximo: AL-X" tag pill, AIDE BRASIL footer

---

## Slide Ordering Convention

1. **Title** (always first)
2. **Context** (optional: explain a person/concept)
3. **Hook Quote** (set up the lesson's central idea)
4. **Timeline/Stats** (historical or data context)
5. **Divider** → Content slides for each section block
6. **Closing Quote** (always last)

Each section block follows: **Divider → Flow/Architecture → Deep-dive → Practical → Insight panel**
