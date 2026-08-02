#!/usr/bin/env python3
"""Generate this repo's live Codex CLI config from .claude/ (single source of truth).

Codex CLI reached subagent GA in March 2026: custom agents are TOML files under
`.codex/agents/` (project-scoped) or `~/.codex/agents/` (personal). This script
translates each Claude Code agent (`.claude/agents/**/*.md`) into the equivalent
Codex agent TOML, so both targets stay derived from one source.

Output goes to the real Codex locations (`.codex/agents/`, `.codex/skills/`,
`AGENTS.md`) rather than
a staging folder: AgentSpec dogfoods its own Codex agents, and consumers copy from
the repo. See docs/reference/codex-cli.md.

Codex 0.146.0 migrates Claude plugin commands to skills during installation, but
silently skips generated skills larger than 4 KiB. This script therefore emits a
native skill for every command. Native skills take precedence over migrated command
skills with the same name, so command availability no longer depends on file size.

Field mapping (Claude frontmatter -> Codex TOML):
  name                 -> name
  description          -> description  (first line; Codex shows it when selecting)
  <markdown body>      -> developer_instructions
  model: opus|sonnet   -> model_reasoning_effort: high|medium
  tools: [...]         -> sandbox_mode: read-only | workspace-write
  kb_domains: [...]    -> appended as a reference note in developer_instructions

Deliberately NOT emitted:
  model  - Codex model ids (gpt-5.x) drift and are account-dependent; omitting it
           makes each agent inherit the parent/session model, which is the
           documented default and avoids pinning ids we cannot verify here.

Outputs:
  .codex/agents/*.toml   - fully generated, do not hand-edit
  .codex/skills/*/SKILL.md - native Codex wrappers for Claude commands
  AGENTS.md              - only the region between the AgentSpec markers is
                           regenerated; text outside it is preserved

Run:
  python3 scripts/generate-codex-plugin.py
  python3 scripts/generate-codex-plugin.py --check   # fail if outputs drift
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
AGENTS_DIR = REPO_ROOT / ".claude" / "agents"
COMMANDS_DIR = REPO_ROOT / ".claude" / "commands"
OUT_DIR = REPO_ROOT / ".codex"
OUT_AGENTS = OUT_DIR / "agents"
OUT_SKILLS = OUT_DIR / "skills"
AGENTS_MD_PATH = REPO_ROOT / "AGENTS.md"

# Only the text between these markers is regenerated in AGENTS.md; anything a
# human writes outside them survives `make codex` and does not trip `--check`.
MARKER_START = "<!-- agentspec:start -->"
MARKER_END = "<!-- agentspec:end -->"

SKIP_FILES: frozenset[str] = frozenset({"README.md", "_template.md"})

_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)

# Claude model tier -> Codex reasoning effort. Codex accepts low|medium|high.
EFFORT_BY_MODEL = {"opus": "high", "sonnet": "medium", "haiku": "low"}

# Tools that imply the agent mutates the workspace.
WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}


def parse_frontmatter(text: str) -> dict:
    """Extract the frontmatter keys we need. Mirrors generate-agent-router.py."""
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}
    body = match.group(1)
    fm: dict = {}

    for key in ("name", "tier", "model"):
        m = re.search(rf"^{key}:\s*(.+)$", body, re.MULTILINE)
        if m:
            fm[key] = m.group(1).strip()

    # description: block scalar `|` or single line
    m = re.search(r"^description:\s*\|\s*\n((?:[ \t]+.*\n?)+)", body, re.MULTILINE)
    if m:
        fm["description"] = m.group(1)
    else:
        m = re.search(r"^description:\s*(.+)$", body, re.MULTILINE)
        if m:
            fm["description"] = m.group(1).strip()

    for key in ("kb_domains", "tools"):
        m = re.search(rf"^{key}:\s*\[([^\]]*)\]", body, re.MULTILINE)
        if m:
            fm[key] = [s.strip() for s in m.group(1).split(",") if s.strip()]

    return fm


def strip_frontmatter(text: str) -> str:
    return _FRONTMATTER_RE.sub("", text, count=1).strip()


def one_line_description(raw: str) -> str:
    """Codex shows `description` when picking an agent - keep it to one sentence."""
    for line in (raw or "").strip().splitlines():
        line = line.strip()
        if line:
            return line
    return ""


def toml_escape_multiline(s: str) -> str:
    r"""Escape a string for a TOML multi-line basic string (\"\"\"...\"\"\")."""
    s = s.replace("\\", "\\\\")
    # A literal `"""` would close the string early.
    s = s.replace('"""', '\\"\\"\\"')
    return s


def toml_escape_basic(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def build_agent_toml(fm: dict, body: str, category: str) -> str:
    name = fm["name"]
    desc = one_line_description(fm.get("description", ""))

    instructions = body
    kb = fm.get("kb_domains") or []
    if kb:
        domains = ", ".join(kb)
        instructions += (
            f"\n\n## Knowledge Base\n\n"
            f"Consult these AgentSpec KB domains before acting: {domains}.\n"
            f"Each lives at `kb/{{domain}}/` with `index.md`, `quick-reference.md`, "
            f"`concepts/` and `patterns/`.\n"
        )

    tools = fm.get("tools") or []
    mutates = bool(WRITE_TOOLS & set(tools)) if tools else True
    sandbox = "workspace-write" if mutates else "read-only"

    effort = EFFORT_BY_MODEL.get((fm.get("model") or "").strip())

    lines = [
        "# Generated by scripts/generate-codex-plugin.py - do not edit by hand.",
        f"# Source: .claude/agents/{category}/{name}.md",
        "",
        f'name = "{toml_escape_basic(name)}"',
        f'description = "{toml_escape_basic(desc)}"',
    ]
    if effort:
        lines.append(f'model_reasoning_effort = "{effort}"')
    lines.append(f'sandbox_mode = "{sandbox}"')
    lines += [
        "",
        'developer_instructions = """',
        toml_escape_multiline(instructions),
        '"""',
        "",
    ]
    return "\n".join(lines)


def command_skill_name(command: Path) -> str:
    """Match the name used by Codex's built-in Claude-command migration."""
    relative = command.relative_to(COMMANDS_DIR).with_suffix("")
    return "source-command-" + "-".join(relative.parts)


def build_command_skill(fm: dict, body: str, command: Path) -> str:
    """Render a Claude command as a native Codex skill without the 4 KiB cap."""
    skill_name = command_skill_name(command)
    command_id = "-".join(command.relative_to(COMMANDS_DIR).with_suffix("").parts)
    description = one_line_description(fm.get("description", ""))
    if not description:
        description = f"Run the AgentSpec {command.stem} command"
    return (
        "---\n"
        f'name: "{toml_escape_basic(skill_name)}"\n'
        f'description: "{toml_escape_basic(description)}"\n'
        "---\n\n"
        f"# {skill_name}\n\n"
        f"Use this skill when the user asks to run the migrated source command "
        f"`{command_id}`.\n\n"
        "## Command Template\n\n"
        f"{body}\n"
    )


GENERATED_BLOCK = """This project uses AgentSpec's Spec-Driven Development workflow: 5 phases, one markdown
document per phase, all under `.claude/sdd/`.

```text
Phase 0: brainstorm -> .claude/sdd/features/BRAINSTORM_{FEATURE}.md
Phase 1: define     -> .claude/sdd/features/DEFINE_{FEATURE}.md
Phase 2: design     -> .claude/sdd/features/DESIGN_{FEATURE}.md
Phase 3: build      -> .claude/sdd/reports/BUILD_REPORT_{FEATURE}.md
Phase 4: ship       -> .claude/sdd/archive/{FEATURE}/
```

Rules:
- `{FEATURE}` is a short UPPER_SNAKE_CASE slug (e.g. `JUDGE_LAYER`).
- Each phase reads the previous phase's document before writing its own.
- Do not jump to build without a `DESIGN_{FEATURE}.md` unless explicitly asked.
- Generated SDD documents are written in pt-BR; code, paths, commands and technical
  terms (MUST/SHOULD/COULD, MoSCoW) stay in English.

## Specialist agents

{AGENT_COUNT} specialist agents live under `.codex/agents/`. Codex loads them as
subagents - delegate explicitly ("use the dbt-specialist agent", "spawn two agents in
parallel") and Codex will spawn them. They are grouped by category:

{CATEGORY_TABLE}"""


AGENTS_MD_SCAFFOLD = f"""# AgentSpec - SDD Workflow (Codex CLI)

> The block between the `agentspec:start` / `agentspec:end` markers is generated by
> `scripts/generate-codex-plugin.py` from `.claude/`. Notes written outside the markers
> are preserved across `make codex`.

{MARKER_START}

{{BLOCK}}

{MARKER_END}
"""


def render_agents_md(block: str) -> str:
    """Splice `block` into AGENTS.md between the markers, preserving the rest."""
    if not AGENTS_MD_PATH.exists():
        return AGENTS_MD_SCAFFOLD.replace("{BLOCK}", block)

    current = AGENTS_MD_PATH.read_text(encoding="utf-8")
    start = current.find(MARKER_START)
    end = current.find(MARKER_END)
    if start == -1 or end == -1 or end < start:
        raise SystemExit(
            f"ERROR: AGENTS.md exists but has no {MARKER_START} / {MARKER_END} region.\n"
            f"Add the markers around the AgentSpec section, or delete the file and rerun."
        )
    head = current[: start + len(MARKER_START)]
    tail = current[end:]
    return f"{head}\n\n{block}\n\n{tail}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="fail if outputs drift")
    args = ap.parse_args()

    if not AGENTS_DIR.is_dir():
        print(f"ERROR: {AGENTS_DIR} not found", file=sys.stderr)
        return 1
    if not COMMANDS_DIR.is_dir():
        print(f"ERROR: {COMMANDS_DIR} not found", file=sys.stderr)
        return 1

    generated: dict[Path, str] = {}
    by_category: dict[str, list[str]] = {}

    for md in sorted(AGENTS_DIR.glob("*/*.md")):
        if md.name in SKIP_FILES:
            continue
        fm = parse_frontmatter(md.read_text(encoding="utf-8"))
        if not fm.get("name"):
            print(f"[WARN] skipping {md.relative_to(REPO_ROOT)} - no parseable name", file=sys.stderr)
            continue
        category = md.parent.name
        body = strip_frontmatter(md.read_text(encoding="utf-8"))
        generated[OUT_AGENTS / f"{fm['name']}.toml"] = build_agent_toml(fm, body, category)
        by_category.setdefault(category, []).append(fm["name"])

    command_count = 0
    for md in sorted(COMMANDS_DIR.glob("*/*.md")):
        if md.name in SKIP_FILES:
            continue
        text = md.read_text(encoding="utf-8")
        fm = parse_frontmatter(text)
        body = strip_frontmatter(text)
        generated[OUT_SKILLS / command_skill_name(md) / "SKILL.md"] = (
            build_command_skill(fm, body, md)
        )
        command_count += 1

    agent_count = sum(map(len, by_category.values()))
    rows = ["| Category | Agents |", "|---|---|"]
    for cat in sorted(by_category):
        rows.append(f"| `{cat}` | {len(by_category[cat])} |")
    block = (
        GENERATED_BLOCK
        .replace("{AGENT_COUNT}", str(agent_count))
        .replace("{CATEGORY_TABLE}", "\n".join(rows))
    )
    generated[AGENTS_MD_PATH] = render_agents_md(block)

    if args.check:
        drift = [
            p for p, content in generated.items()
            if not p.exists() or p.read_text(encoding="utf-8") != content
        ]
        if drift:
            print("Codex config is out of date. Run: make codex", file=sys.stderr)
            for p in drift:
                print(f"  drift: {p.relative_to(REPO_ROOT)}", file=sys.stderr)
            return 1
        print(
            f"OK - .codex/ + AGENTS.md up to date "
            f"({agent_count} agents, "
            f"{command_count} command skills)"
        )
        return 0

    if OUT_AGENTS.exists():
        shutil.rmtree(OUT_AGENTS)
    if OUT_SKILLS.exists():
        shutil.rmtree(OUT_SKILLS)
    OUT_AGENTS.mkdir(parents=True, exist_ok=True)
    for path, content in generated.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    print(
        f"Generated .codex/ + AGENTS.md - {agent_count} agents in "
        f"{len(by_category)} categories, {command_count} command skills"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
