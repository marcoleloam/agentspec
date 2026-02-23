# Knowledge Base (KB) Framework

The KB framework grounds agent responses in your actual codebase patterns.

## Structure

```
kb/
├── _templates/           # Templates for new domains
│   ├── concept.md.template
│   ├── pattern.md.template
│   ├── index.md.template
│   ├── quick-reference.md.template
│   ├── domain-manifest.yaml.template
│   ├── spec.yaml.template
│   └── test-case.json.template
│
├── _index.yaml           # Domain registry (machine-readable)
│
└── {domain}/             # Your KB domains
    ├── index.md          # Domain overview
    ├── quick-reference.md # Cheat sheet
    ├── concepts/         # Core concepts (< 150 lines each)
    │   ├── concept-1.md
    │   └── concept-2.md
    └── patterns/         # Implementation patterns (< 200 lines each)
        ├── pattern-1.md
        └── pattern-2.md
```

## Creating a KB Domain

Use the `/create-kb` command:

```bash
claude> /create-kb redis
claude> /create-kb pandas
claude> /create-kb authentication
```

Or manually:

1. Create the domain directory: `mkdir -p .claude/kb/{domain}/{concepts,patterns}`
2. Copy templates from `_templates/` and fill in domain-specific content
3. Register the domain in `_index.yaml` under the `domains:` key
4. Include code examples from your actual codebase

## Domain Structure

Each KB domain follows this standard layout:

- **`index.md`** — Domain overview and navigation
- **`quick-reference.md`** — Fast lookup tables and cheat sheet (100 lines max)
- **`concepts/*.md`** — Core concepts with examples (150 lines each)
- **`patterns/*.md`** — Implementation patterns with production code (200 lines each)
- **`specs/*.yaml`** — Machine-readable specifications (optional)

## How KBs Integrate with AgentSpec

KBs are referenced during the SDD workflow:

1. **Define Phase** — Technical Context specifies which KB domains apply
2. **Design Phase** — Agent matching pulls relevant patterns from KB
3. **Build Phase** — Agents consult KB patterns for implementation guidance

```text
DEFINE                    DESIGN                    BUILD
──────                    ──────                    ─────

KB Domains:          →    Read patterns:       →    Agents consult:
• {domain-1}              • pattern-a               • KB/{domain-1}/patterns/
• {domain-2}              • pattern-b               • KB/{domain-2}/patterns/
```

## Best Practices

1. **Be specific** — Reference actual code from your project
2. **Include examples** — Working code snippets, not pseudocode
3. **Keep updated** — Mark stale content, record freshness dates
4. **Cite sources** — Link to official docs
5. **Stay within limits** — Respect the line limits in `_index.yaml`
