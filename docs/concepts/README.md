# Core Concepts

Understanding the mental model behind Spec-Driven Development.

## The Problem

AI-assisted development without structure leads to:

- **Lost decisions** — requirements discussed but never captured
- **Spec drift** — implementation diverges from intent
- **Repeated mistakes** — no institutional memory between sessions
- **No audit trail** — can't trace why something was built a certain way

## The SDD Mental Model

AgentSpec solves this with a **5-phase pipeline** where each phase produces a traceable artifact:

```text
  Idea                                                    Shipped Feature
   │                                                            ▲
   ▼                                                            │
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────┐   ┌──────────┐
│BRAINSTORM│──▶│  DEFINE  │──▶│  DESIGN  │──▶│BUILD │──▶│   SHIP   │
│ explore  │   │ capture  │   │architect │   │execute│   │ archive  │
└──────────┘   └──────────┘   └──────────┘   └──────┘   └──────────┘
  Optional      Score≥12/15    Manifest+ADRs   Agents     Lessons
```

**Each arrow is a quality gate.** You can't proceed without meeting measurable criteria.

## The Three Pillars

### 1. Phases (the workflow)

Five phases that structure how features move from idea to production:

| Phase          | What Happens                       | Quality Gate                     |
|----------------|------------------------------------|---------------------------------:|
| **Brainstorm** | Explore approaches, ask questions  | Min 3 questions, 2+ approaches   |
| **Define**     | Capture requirements formally      | Clarity Score >= 12/15           |
| **Design**     | Create architecture, assign agents | Complete manifest, ADRs          |
| **Build**      | Execute implementation with agents | All tests pass                   |
| **Ship**       | Archive with lessons learned       | Acceptance tests verified        |

Brainstorm is optional. You can start directly with `/define` if requirements are clear.

### 2. Agents (the specialists)

16 specialized agents, each with a specific domain:

| Category          | Count | What They Do                                     |
|-------------------|-------|--------------------------------------------------|
| **Workflow**      | 6     | Drive each SDD phase (brainstorm through ship)   |
| **Code Quality**  | 4     | Review, clean, document, and test code           |
| **Communication** | 4     | Explain, plan, manage projects, analyze meetings |
| **Exploration**   | 2     | Navigate codebases and manage knowledge bases    |

During `/build`, the design-agent scans `.claude/agents/**/*.md` and matches agents to tasks based on the DESIGN file manifest. Each task gets the best-fit specialist.

### 3. Knowledge Base (the memory)

KB domains ground agent responses in verified patterns instead of hallucinated ones:

```text
.claude/kb/
├── _templates/          # Templates for creating domains
├── _index.yaml          # Domain registry
└── your-domain/         # Your custom domain
    ├── index.md         # Overview
    ├── quick-reference.md  # Cheat sheet
    ├── concepts/        # Core concepts (max 150 lines each)
    └── patterns/        # Implementation patterns (max 200 lines each)
```

Create a domain with `/create-kb redis` and agents will consult it during `/design` and `/build`.

## How Phases Connect

Context flows forward through the pipeline:

1. **BRAINSTORM** explores approaches, produces draft requirements
2. **DEFINE** formalizes those into scored requirements with acceptance tests
3. **DESIGN** reads DEFINE, creates architecture + file manifest + agent assignments
4. **BUILD** reads DESIGN, delegates tasks to matched agents, verifies results
5. **SHIP** reads BUILD_REPORT, archives everything with lessons learned

If requirements change mid-stream, use `/iterate` to update any phase document with automatic cascade detection.

## When to Use Each Phase

| Situation                           | Start With     |
|-------------------------------------|----------------|
| Vague idea, need to explore         | `/brainstorm`  |
| Clear requirements, ready to spec   | `/define`      |
| Small bug fix or tweak              | Direct coding  |
| Requirements changed after design   | `/iterate`     |
| Feature complete, ready to archive  | `/ship`        |

## Key Design Decisions

- **YAML contracts** enforce phase transitions (not human discipline)
- **Clarity scoring** prevents vague specs from reaching design
- **Agent matching** is automatic, not manual assignment
- **Lessons learned** are structured, not freeform — they feed future decisions
- **KB domains** have line limits to stay focused and maintainable
