# Getting Started with AgentSpec

Get from zero to your first spec-driven feature in 10 minutes.

## Prerequisites

- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) installed
- Git

## Installation

Clone the AgentSpec framework into your project:

```bash
# Clone the repository
git clone https://github.com/luanmorenommaciel/agentspec.git

# Copy the .claude directory into your project
cp -r agentspec/.claude your-project/.claude
```

Or add it directly to an existing project:

```bash
cd your-project
git clone https://github.com/luanmorenommaciel/agentspec.git /tmp/agentspec
cp -r /tmp/agentspec/.claude .claude
```

## Initialize Your Project

The SDD directory structure is already set up:

```text
your-project/.claude/
├── agents/         # 16 specialized agents (ready to use)
├── commands/       # 12 slash commands (ready to use)
├── sdd/
│   ├── features/   # Your active feature documents go here
│   ├── reports/    # Build reports land here
│   └── archive/    # Shipped features archived here
└── kb/             # Add domain knowledge here
```

## Your First Feature (5 minutes)

Let's build a user authentication feature using the full SDD workflow.

### Step 1: Brainstorm (Optional)

Explore your idea through guided dialogue:

```bash
claude> /brainstorm "I want to add user authentication with JWT"
```

AgentSpec asks targeted questions, compares approaches, and helps you scope the work. Output: `BRAINSTORM_USER_AUTH.md`

### Step 2: Define Requirements

Capture formal requirements with a clarity score:

```bash
claude> /define USER_AUTH
```

Output: `DEFINE_USER_AUTH.md` with:

- Problem statement and users
- Functional and non-functional requirements
- Acceptance criteria (Given/When/Then)
- Clarity Score (must reach 12/15 to proceed)

### Step 3: Design Architecture

Create the technical architecture:

```bash
claude> /design USER_AUTH
```

Output: `DESIGN_USER_AUTH.md` with:

- Architecture diagram
- File manifest with agent assignments
- Key decisions (inline ADRs)
- Code patterns (copy-paste ready)

### Step 4: Build

Execute the implementation with agent matching:

```bash
claude> /build USER_AUTH
```

AgentSpec reads the DESIGN, matches specialized agents to each task, builds the code, and verifies it. Output: `BUILD_REPORT_USER_AUTH.md`

### Step 5: Ship

Archive everything with lessons learned:

```bash
claude> /ship USER_AUTH
```

Moves all artifacts to `.claude/sdd/archive/USER_AUTH/` with a SHIPPED document capturing what worked, what didn't, and recommendations.

## What's Next

- [Core Concepts](../concepts/) — understand how phases, agents, and KB work together
- [Tutorials](../tutorials/) — step-by-step walkthroughs for common workflows
- [Reference](../reference/) — full command and agent catalog

## Troubleshooting

**Commands not recognized?**
Ensure `.claude/skills/` exists in your project root with the skill directories (each containing a `SKILL.md`).

**Agent not matching?**
Check that `.claude/agents/` contains the agent `.md` files. Agents are discovered via glob pattern.

**Clarity score too low?**
The `/define` phase requires 12/15 to proceed. Add more detail to Problem, Users, Goals, Success criteria, and Scope sections.
