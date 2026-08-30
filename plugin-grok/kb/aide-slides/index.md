# AIDE Slides — Knowledge Base

> Design system, component library, and quality rules for building HTML slide decks for the Formacao AI Data Engineer course.

## When to Use

Reference this KB when:
- Creating new slide decks for any lesson (AL-x, PR-x)
- Modifying existing slide decks
- Building new slide components or layouts
- Reviewing slides for quality

## Quality Standard

Follow the KB rules strictly. The first deck you generate becomes the golden reference for future decks.

## File Naming Convention (Per Lesson)

```
presentation/l1-gen-ai/{code}/
├── {code}-slide-spec.md      # INPUT: Slide generation spec (drives the agent)
├── {code}-slides.html        # OUTPUT: Generated slide deck
├── {code}-content-pt-br.md   # Full lesson content with code examples + quiz
├── {code}-excalidraw.md      # Visual briefs for Excalidraw diagrams
├── {code}.excalidraw          # Excalidraw diagram file
└── {code}.png                 # Rendered diagram PNG
```

**The slide-spec.md is the source of truth.** It contains: lesson metadata, slide map (every slide planned), evidence data (verified facts), practical examples, student questions, and visual asset references. The agent reads this file to generate the slides.

## Files in This Domain

| File | Purpose |
|------|---------|
| [design-system.md](design-system.md) | AIDE color palette, CSS variables, 4-font stack, branding bar |
| [component-library.md](component-library.md) | 20+ reusable CSS components with full code |
| [slide-types.md](slide-types.md) | 10+ slide type layouts with structure rules |
| [quality-rules.md](quality-rules.md) | Hard-won rules: screen filling, accents, fonts, density |
| [slide-engine.md](slide-engine.md) | SlideEngine JS, navigation chrome, scroll-snap |
| [animation-patterns.md](animation-patterns.md) | Shimmer, pulse-glow, bar-fill, reveal stagger |
| [advanced-visuals.md](advanced-visuals.md) | **Killer visuals:** SVG architectures, pipelines, agent orchestration, glassmorphism, animated ribbons |
| [template.md](template.md) | Full HTML skeleton for starting new decks |
| [semana-palette.md](semana-palette.md) | **Semana palette:** Black/silver/blue alternative for Semana AI Data Engineer decks |

## Agent

The `aide-slide-builder` agent reads this KB automatically when creating slides.

## Color Palette Quick Reference

| Token | Hex | Usage |
|-------|-----|-------|
| `--accent` | `#00b4ff` | Primary cyan-blue |
| `--gold` | `#d4af37` | Gold highlights |
| `--bg` | `#0a0f1a` | Deep navy background |
| `--text` | `#e8edf5` | Primary text |
| `--text-dim` | `#6b7fa0` | Secondary text |
