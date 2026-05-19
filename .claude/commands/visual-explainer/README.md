# Visual Explainer Commands

> **8 slash commands** for generating self-contained HTML pages — diagrams, slides, plans, reviews, and live sharing

## Command Catalog

| Command | Purpose |
|---------|---------|
| `/generate-web-diagram` | Generate a standalone HTML diagram for any topic |
| `/generate-slides` | Magazine-quality slide deck as HTML |
| `/generate-visual-plan` | Visual implementation plan with flow diagrams |
| `/diff-review` | Before/after architecture comparison with code review |
| `/plan-review` | Current codebase vs. proposed plan with risk assessment |
| `/project-recap` | Project state, decisions, and cognitive debt snapshot |
| `/fact-check` | Verify document accuracy against actual codebase |
| `/share` | Deploy an HTML page to Vercel and get a live URL |

## Quick Start

```bash
# Generate a diagram
/generate-web-diagram "Data pipeline architecture"

# Create a slide deck
/generate-slides "AgentSpec overview for stakeholders"

# Review a diff visually
/diff-review main

# Share a generated page
/share ~/.agent/diagrams/my-diagram.html
```

## How Commands Work

Each command delegates to the `visual-explainer` skill, which:

1. Reads reference templates and CSS patterns from `.claude/skills/visual-explainer/`
2. Generates a self-contained `.html` file with no external dependencies
3. Opens the result in the browser automatically
4. Writes output to `~/.agent/diagrams/` for persistence across sessions

Output files are single HTML files — no build step, no server required. Share them with `/share`.
