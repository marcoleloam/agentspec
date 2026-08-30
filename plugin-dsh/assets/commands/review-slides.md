---
name: review-slides
description: |
  Review an AIDE slide deck for quality issues. Invokes aide-slide-reviewer for independent
  validation against 8 rule categories. Optionally auto-fixes with aide-slide-fixer.
---

# Review Slides Command

> Independent quality review for AIDE HTML slide decks

## Usage

```bash
/review-slides                        # Review most recently modified deck in presentation/
/review-slides d1-ingest              # Review specific deck
/review-slides d2-context.html        # Review by filename
/review-slides --fix                  # Review + auto-fix (invokes fixer)
/review-slides d1-ingest --fix        # Review specific deck + auto-fix
```

---

## Overview

This command invokes the **aide-slide-reviewer** agent for independent, read-only validation of any slide deck against the AIDE quality KB. Optionally pairs with **aide-slide-fixer** for automated corrections.

```text
┌─────────────────────────────────────────────────────────────────┐
│                 /review-slides PIPELINE                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌───────────────────────┐                                     │
│   │  aide-slide-reviewer  │  READ-ONLY                          │
│   │  (sonnet, orange)     │  8 validation categories            │
│   └───────────┬───────────┘                                     │
│               │                                                  │
│       ┌───────▼───────┐                                         │
│       │  REVIEW       │                                         │
│       │  REPORT       │                                         │
│       └───────┬───────┘                                         │
│               │                                                  │
│        --fix flag?                                               │
│        ┌──────┴──────┐                                          │
│        │ YES         │ NO                                       │
│        ▼             ▼                                          │
│   ┌──────────┐  Report only                                    │
│   │  aide-   │  (done)                                          │
│   │  slide-  │                                                  │
│   │  fixer   │                                                  │
│   │ (sonnet) │                                                  │
│   └────┬─────┘                                                  │
│        │                                                         │
│   ┌────▼──────┐                                                 │
│   │ RE-REVIEW │  Confirm fixes                                  │
│   └───────────┘                                                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Process

### Step 1: Locate Deck

```text
IF user provides deck name (e.g., "d1-ingest"):
  → Look for presentation/d1-ingest.html
  → If not found, look for presentation/**/d1-ingest*.html

IF user provides filename (e.g., "d2-context.html"):
  → Look for presentation/d2-context.html

IF no deck specified:
  → Find most recently modified .html file in presentation/

VERIFY: File exists and contains 'class="slide"'
```

### Step 2: Run aide-slide-reviewer

Spawn the **aide-slide-reviewer** agent with this prompt:

```text
Review the slide deck at {deck_path}.

Read these KB files first:
- .claude/kb/aide-slides/quality-rules.md
- .claude/kb/aide-slides/component-library.md
- .claude/kb/aide-slides/design-system.md
- .claude/kb/aide-slides/semana-palette.md (if deck is d1-d4)

Run all 8 validation categories:
1. Screen filling
2. Bottom bar pattern
3. Typography
4. SVG positioning
5. Portuguese accents
6. Hover effects
7. Palette compliance
8. Component patterns

Produce a full review report with severity classification
(CRITICAL/ERROR/WARNING/INFO) and confidence scores.
```

### Step 3: Display Review Report

Show the review report to the user. Format:

```text
AIDE SLIDE REVIEW
━━━━━━━━━━━━━━━━━
Deck: {filename} | Slides: {count} | Lines: {line_count}
Palette: {Semana | AIDE}

CRITICAL:  {n}  {✓ if 0, else ✗}
ERROR:     {n}  {✓ if 0, else ✗}
WARNING:   {n}  ⚠
INFO:      {n}  ℹ

{List of CRITICAL findings with details}
{List of ERROR findings with details}
{List of WARNING findings, brief}
{Positive observations}

VERDICT: {PASS | BLOCK}
```

### Step 4: Auto-Fix (if --fix flag)

If the user passed `--fix` AND there are CRITICAL or ERROR findings:

1. Spawn **aide-slide-fixer** agent with the review report and deck path
2. Fixer applies surgical corrections for all CRITICAL + ERROR findings
3. Fixer applies WARNING fixes with confidence >= 0.85
4. After fixing, spawn **aide-slide-reviewer** again for confirmation pass
5. Display updated review report

```text
FIX CYCLE
━━━━━━━━━
Applied: {n} fixes ({critical} CRITICAL, {error} ERROR, {warning} WARNING)
Skipped: {n} (low confidence)
Escalated: {n} (too complex for surgical fix)

RE-REVIEW: {PASS | still BLOCK with remaining issues}
```

### Step 5: Final Summary

```text
━━━━━━━━━━━━━━━━━
MERGE STATUS: {✓ Ready to present | ⚠ Fix warnings | ✗ Fix critical/errors}
```

---

## Error Handling

### Deck Not Found

```text
IF no HTML file found at specified path:
  1. List available .html files in presentation/
  2. Suggest: "Did you mean one of these?"
  3. Wait for user clarification
```

### Very Large Deck (100+ slides)

```text
IF slide count > 100:
  1. Note: "Large deck detected ({n} slides). Review may take longer."
  2. Proceed with full review (do not skip categories)
```

### No Issues Found

```text
IF all categories pass with 0 CRITICAL, 0 ERROR:
  1. Celebrate: "Deck meets AIDE production quality bar"
  2. Still list any WARNINGS as recommendations
  3. Include positive observations
```

---

## Examples

### Example 1: Standard Review

```bash
/review-slides d1-ingest

# Output:
AIDE SLIDE REVIEW
━━━━━━━━━━━━━━━━━
Deck: d1-ingest.html | Slides: 140 | Lines: 4715
Palette: Semana (black/silver/blue)

CRITICAL:  0  ✓
ERROR:     0  ✓
WARNING:   3  ⚠
INFO:      1  ℹ

WARNINGS:
  [W1] Slide 23: SVG description text color #6b7fa0 → should be #c8d8e8
  [W2] Slide 45: stat card has 2 lines, expected 4
  [W3] Slide 67: "equacao" → "equação" in SVG text

VERDICT: ✓ PASS — Ready to present
```

### Example 2: Review + Auto-Fix

```bash
/review-slides d2-context --fix

# Output:
AIDE SLIDE REVIEW
━━━━━━━━━━━━━━━━━
CRITICAL: 0  ERROR: 2  WARNING: 5

ERRORS:
  [E1] Slide 8: <em> used for heading color → should be <span>
  [E2] Slide 14: onmouseover → should be onmouseenter

FIX CYCLE
━━━━━━━━━
Applied: 7 fixes (0C, 2E, 5W)
Skipped: 0
Escalated: 0

RE-REVIEW: ✓ PASS (0C, 0E, 0W)

VERDICT: ✓ PASS — Ready to present
```

---

## Integration

### Before Presenting

```bash
# Quick quality check before a live session
/review-slides d1-ingest
```

### After Manual Edits

```bash
# Verify manual changes didn't break anything
/review-slides d1-ingest --fix
```

### After Building a New Deck

```bash
# The /build-slides command includes review automatically,
# but you can re-review anytime
/review-slides d3-agent
```

---

## Agent Integration

| Agent | Role in Pipeline |
|-------|-----------------|
| **aide-slide-reviewer** | Independent read-only validator (always invoked) |
| **aide-slide-fixer** | Surgical corrections (only with --fix flag) |

---

## Related

- `/build-slides` — Full pipeline: plan + build + review + fix
- `aide-slide-reviewer` agent: `.claude/agents/domain/aide-slide-reviewer.md`
- `aide-slide-fixer` agent: `.claude/agents/domain/aide-slide-fixer.md`
- Quality rules KB: `.claude/kb/aide-slides/quality-rules.md`
