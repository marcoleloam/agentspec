---
name: build-slides
description: |
  Full pipeline for building AIDE slide decks: plan → build (chunked) → review → fix → assemble.
  Orchestrates 4 agents (planner, builder, reviewer, fixer) for 90%+ first-pass quality.
---

# Build Slides Command

> Full pipeline: Plan → Build (chunked) → Review → Fix → Assemble

## Usage

```bash
/build-slides d2-context                    # Full pipeline from prompt file
/build-slides d2-context --plan-only        # Only run planner (inspect map before building)
/build-slides d2-context --skip-plan        # Skip planner, build from content directly
/build-slides d2-context --no-fix           # Review but don't auto-fix (report only)
/build-slides d2-context --chunks 5         # Override chunk size (default: auto 5-7)
```

---

## Overview

This command orchestrates the **full 4-agent slide production pipeline**. The user provides a deck name and content source — the pipeline handles everything else.

```text
┌──────────────────────────────────────────────────────────────────┐
│                    /build-slides PIPELINE                          │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Step 0: RESOLVE INPUT                                           │
│  ├─ Parse deck name → locate content + determine palette          │
│  └─ Set output path                                              │
│                                                                   │
│  Step 1: PLAN (aide-slide-planner)                               │
│  ├─ Reads content + KB → structured slide-map                     │
│  └─ Defines: types, visuals, chunks, accent words                │
│                                                                   │
│  Step 2: BUILD + REVIEW LOOP (per chunk)                         │
│  ├─ aide-slide-builder generates 5-7 slides                      │
│  ├─ aide-slide-reviewer validates chunk                          │
│  ├─ aide-slide-fixer corrects if needed                          │
│  └─ Loop: max 2 fix cycles per chunk                             │
│                                                                   │
│  Step 3: ASSEMBLE                                                │
│  ├─ Combine validated chunks → single HTML file                  │
│  └─ Add head, CSS, SlideEngine JS                                │
│                                                                   │
│  Step 4: FINAL REVIEW                                            │
│  ├─ Full-deck review for cross-chunk issues                      │
│  └─ Final quality report                                         │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## Process

### Step 0: Resolve Input

```text
PARSE deck name:
  "d1-ingest"   → presentation/d1-ingest.html
  "d2-context"  → presentation/d2-context.html
  "d3-agent"    → presentation/d3-agent.html
  "d4-multi"    → presentation/d4-multi-agent.html

LOCATE content source (in priority order):
  1. User provides content directly in the message
  2. prompts/day{N}-{theme}.md (e.g., prompts/day2-context.md)
  3. docs/agenda.md (search for relevant day section)
  4. Ask user for content if none found

DETERMINE palette:
  d1-d4 decks → Semana (black/silver/blue) — read semana-palette.md
  l0/l1 decks → AIDE (navy/cyan/gold) — read design-system.md

SET output path:
  presentation/{deck-name}.html
```

### Step 1: Plan (aide-slide-planner)

**Skip if `--skip-plan` flag is set.**

Spawn the **aide-slide-planner** agent:

```text
"You are the slide planner for deck '{deck-name}'.

Read the lesson content at: {content_path}

Read these KB files:
- .claude/kb/aide-slides/quality-rules.md
- .claude/kb/aide-slides/slide-types.md
- .claude/kb/aide-slides/advanced-visuals.md
- .claude/kb/aide-slides/{palette_file}

Produce a slide-map with:
- Every content item mapped to a slide type
- Visual pattern assigned per slide
- SVG needed (yes/no) with viewBox width
- Bottom panel content per slide
- Portuguese accent words per slide
- Chunk boundaries (5-7 slides per chunk, dividers start new chunks)
- Minimum 15 slides total

Output the slide-map as structured markdown."
```

**Display to user:**

```text
PLAN
  ✓ Content read: {content_path} ({line_count} lines)
  ✓ Palette: {Semana | AIDE}
  ✓ Slide map: {N} slides in {M} chunks
```

**If `--plan-only`:** Display the slide-map and stop here. User can review before continuing.

### Step 2: Build + Review Loop

For each chunk defined in the slide-map:

#### 2a. Build Chunk

Spawn **aide-slide-builder** agent:

```text
"You are building chunk {i} of {M} for deck '{deck-name}'.

SLIDE MAP (your contract):
{paste the relevant chunk section from the slide-map}

READ ONLY THESE KB FILES for this chunk:
{list KB files based on visual types in this chunk:}
- SVG slides → .claude/kb/aide-slides/advanced-visuals.md
- Card/stat slides → .claude/kb/aide-slides/component-library.md
- All chunks → .claude/kb/aide-slides/quality-rules.md
- All chunks → .claude/kb/aide-slides/{palette_file}
- Chunk 1 only → .claude/kb/aide-slides/template.md (for <head> and structure)
- Chunk 1 only → .claude/kb/aide-slides/slide-engine.md (for JS)

GENERATE HTML for slides {start} through {end} ONLY.
Follow the slide-map exactly — types, visuals, and accent words are already decided.
Write Portuguese words with correct accents from the start.

Do NOT validate your output — the reviewer handles that.

{For chunk 1: include full <head>, CSS, branding bar, and opening <div class="deck">}
{For middle chunks: generate only <section class="slide"> elements}
{For last chunk: include closing </div>, SlideEngine JS, and closing tags}
"
```

#### 2b. Review Chunk

Spawn **aide-slide-reviewer** agent:

```text
"Review the HTML just generated for chunk {i} of deck '{deck-name}'.

The generated HTML is:
{paste chunk HTML or reference the file}

Read KB files:
- .claude/kb/aide-slides/quality-rules.md
- .claude/kb/aide-slides/component-library.md
- .claude/kb/aide-slides/design-system.md
- .claude/kb/aide-slides/{palette_file}

Run all 8 validation categories. Produce a review report with
CRITICAL/ERROR/WARNING/INFO severity and confidence scores.
Focus on this chunk only ({slide_count} slides)."
```

#### 2c. Fix (if needed)

**Skip if `--no-fix` flag is set or if review verdict is PASS.**

If review has CRITICAL or ERROR findings, spawn **aide-slide-fixer** agent:

```text
"Fix the issues found in chunk {i} of deck '{deck-name}'.

REVIEW REPORT:
{paste review findings — CRITICAL and ERROR only, plus WARNING >= 0.85}

HTML TO FIX:
{reference the chunk HTML}

Read KB:
- .claude/kb/aide-slides/quality-rules.md
- .claude/kb/aide-slides/component-library.md

Apply targeted fixes. One Edit per finding. Do not change anything
not mentioned in the review report."
```

#### 2d. Re-Review (after fix)

Spawn reviewer again on the fixed chunk. If still failing after 2 fix cycles → **ESCALATE**.

#### 2e. Display Progress

After each chunk:

```text
  Chunk {i}/{M} (slides {start}-{end}): BUILD ✓  REVIEW {✓|✗}  {FIX ✓ if needed}  ({nC}C {nE}E {nW}W)
```

### Step 3: Assemble

After all chunks pass review:

1. Combine all chunk HTML into a single file
2. Ensure `<head>`, CSS variables, Google Fonts link are present (from chunk 1)
3. Ensure SlideEngine JS is at the bottom (from last chunk)
4. Write the assembled file to `presentation/{deck-name}.html`

```text
ASSEMBLE
  ✓ Combined {M} chunks → {N} slides
  ✓ Added <head>, CSS, SlideEngine JS
  ✓ Output: presentation/{deck-name}.html
```

### Step 4: Final Full-Deck Review

Spawn **aide-slide-reviewer** one final time on the complete assembled file:

```text
"Final review of the complete assembled deck at presentation/{deck-name}.html.

This is the post-assembly check. Look for:
- Cross-chunk issues (duplicate CSS definitions, mismatched variables)
- Slide count matching navigation dots
- Consistent styling across all sections
- Any issues introduced during assembly

Run all 8 validation categories on the full deck.
Produce the final review report."
```

### Step 5: Report

```text
BUILD-SLIDES: {deck-name}
━━━━━━━━━━━━━━━━━━━━━━━━

PLAN
  ✓ Content: {source} ({lines} lines)
  ✓ Palette: {palette}
  ✓ Map: {N} slides in {M} chunks

BUILD + REVIEW
  Chunk 1/{M} (slides 1-{n}):     BUILD ✓  REVIEW ✓  (0C 0E 1W)
  Chunk 2/{M} (slides {n+1}-{m}): BUILD ✓  REVIEW ✗  → FIX ✓  RE-REVIEW ✓
  ...
  Chunk {M}/{M} (slides {x}-{N}): BUILD ✓  REVIEW ✓  (0C 0E 0W)

ASSEMBLE
  ✓ Combined {M} chunks → {N} slides
  ✓ Output: presentation/{deck-name}.html

FINAL REVIEW
  ✓ Full deck: {nC} CRITICAL, {nE} ERROR, {nW} WARNING

━━━━━━━━━━━━━━━━━━━━━━━━
QUALITY: {percentage}% ({total_warnings} warnings, {blocking} blocking)
OUTPUT:  presentation/{deck-name}.html
FIX CYCLES: {count} (chunks {list})
```

---

## Escalation Rules

| Condition | Action |
|-----------|--------|
| Chunk passes review first try | Continue to next chunk |
| Chunk fails, fixer corrects, re-review passes | Continue (log 1 fix cycle) |
| Chunk fails after 2 fix cycles | **ESCALATE:** show report, ask user for guidance |
| Planner produces < 15 slides | **WARN:** "Content may be insufficient — proceed anyway?" |
| Content source not found | **ASK:** "Where is the lesson content?" |
| Builder errors during generation | **RETRY** once, then escalate |

---

## Flags

| Flag | Description | Effect |
|------|-------------|--------|
| `--plan-only` | Run planner only | Produces slide-map, stops before building |
| `--skip-plan` | Skip planner | Builds directly from content (no slide-map) |
| `--no-fix` | Review but don't fix | Shows review report without invoking fixer |
| `--chunks N` | Override chunk size | Sets max slides per chunk (default: auto 5-7) |

---

## Agent Roles

| Agent | Phase | Model | Role |
|-------|-------|-------|------|
| **aide-slide-planner** | Step 1 | Sonnet | Content architecture → slide-map |
| **aide-slide-builder** | Step 2a | Opus | HTML generation per chunk |
| **aide-slide-reviewer** | Step 2b, 4 | Sonnet | Independent validation (read-only) |
| **aide-slide-fixer** | Step 2c | Sonnet | Surgical corrections |

---

## Related

- `/review-slides` — Review-only (no build) for existing decks
- Quality rules KB: `.claude/kb/aide-slides/quality-rules.md`
- Golden reference: `presentation/d1-ingest.html`
