#!/usr/bin/env python3
"""Generate the Grok Build TUI plugin distribution from .claude/ (single source of truth).

Mirrors generate-codex-plugin.py and generate-dsh-bundle.py. Grok's plugin layout is
close to Claude Code (skills/, commands/, agents/, hooks/) but three things need a
native bundle:

  1. Slash commands are discovered from *flat* ``commands/*.md`` files (stem = name).
     AgentSpec's nested ``commands/{category}/{name}.md`` would not register as
     ``/brainstorm``.
  2. Plugin agents are discovered from ``agents/*.md``. Nested category folders are
     flattened so ``spawn_subagent(subagent_type="dbt-specialist")`` resolves.
  3. Command/agent bodies tell the model to use Claude tool names (Read, Task, …).
     Those are rewritten to Grok tool names (read_file, spawn_subagent, …).

Outputs:
  plugin-grok/          distributable Grok plugin (marketplace source)
  .grok/agents/*.md     project-scoped dogfood agents (this repo)
  .grok/commands/*.md   project-scoped dogfood slash commands (this repo)

plugin-grok/ rewrites content paths to ``${GROK_PLUGIN_ROOT}`` and vendors kb/ + sdd/.
.grok/ keeps workspace ``.claude/sdd/{features,reports,archive}`` and source
``.claude/kb/`` paths — this repository already has them.

Static files kept across regenerations: plugin-grok/{plugin.json, README.md}.

Run:
  python3 scripts/generate-grok-plugin.py
  python3 scripts/generate-grok-plugin.py --check   # fail if outputs drift
"""
from __future__ import annotations

import argparse
import filecmp
import re
import shutil
import stat
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
AGENTS_DIR = REPO_ROOT / ".claude" / "agents"
COMMANDS_DIR = REPO_ROOT / ".claude" / "commands"
SKILLS_DIR = REPO_ROOT / ".claude" / "skills"
EXTRAS_SKILLS = REPO_ROOT / "plugin-extras" / "skills"
EXTRAS_SCRIPTS = REPO_ROOT / "plugin-extras" / "scripts"
KB_DIR = REPO_ROOT / ".claude" / "kb"
SDD_TEMPLATES = REPO_ROOT / ".claude" / "sdd" / "templates"
SDD_ARCH = REPO_ROOT / ".claude" / "sdd" / "architecture"
SDD_INDEX = REPO_ROOT / ".claude" / "sdd" / "_index.md"
SDD_README = REPO_ROOT / ".claude" / "sdd" / "README.md"
JUDGE_PY = REPO_ROOT / "scripts" / "judge.py"
LICENSE = REPO_ROOT / "LICENSE"

PLUGIN_OUT = REPO_ROOT / "plugin-grok"
PROJECT_OUT = REPO_ROOT / ".grok"

SKIP_FILES = frozenset({"README.md", "_template.md"})
REPO_LOCAL_SKILLS = frozenset(
    {"meeting-analysis", "standup-report", "create-skill", "create-agent"}
)
TEXT_SUFFIXES = frozenset(
    {".md", ".yaml", ".yml", ".json", ".py", ".sh", ".html", ".txt", ".toml"}
)

_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)

# Claude tool id -> Grok tool id. Unmapped names are left as-is.
TOOL_MAP = {
    "Read": "read_file",
    "Write": "write",
    "Edit": "search_replace",
    "MultiEdit": "search_replace",
    "NotebookEdit": "search_replace",
    "NotebookRead": "read_file",
    "Grep": "grep",
    "Glob": "list_dir",
    "LS": "list_dir",
    "Bash": "run_terminal_command",
    "TodoWrite": "todo_write",
    "AskUserQuestion": "ask_user_question",
    "Task": "spawn_subagent",
    "WebSearch": "web_search",
    "WebFetch": "web_fetch",
    "KillShell": "kill_command_or_subagent",
    "BashOutput": "get_command_or_subagent_output",
}

WRITE_TOOLS = {
    "Write",
    "Edit",
    "MultiEdit",
    "NotebookEdit",
    "write",
    "search_replace",
}

# Longer phrases first so "Task tool" is not partially eaten by "Task(".
_BODY_TOOL_RES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bAskUserQuestion\b"), "ask_user_question"),
    (re.compile(r"\bTodoWrite\b"), "todo_write"),
    (re.compile(r"\bMultiEdit\b"), "search_replace"),
    (re.compile(r"\bNotebookEdit\b"), "search_replace"),
    (re.compile(r"\bNotebookRead\b"), "read_file"),
    (re.compile(r"\bWebSearch\b"), "web_search"),
    (re.compile(r"\bWebFetch\b"), "web_fetch"),
    (re.compile(r"\bBashOutput\b"), "get_command_or_subagent_output"),
    (re.compile(r"\bKillShell\b"), "kill_command_or_subagent"),
    (re.compile(r"\bTask tool\b"), "spawn_subagent tool"),
    (re.compile(r"via Task\b"), "via spawn_subagent"),
    (re.compile(r"\bTask\("), "spawn_subagent("),
    (re.compile(r"\bRead\("), "read_file("),
    (re.compile(r"\bWrite\("), "write("),
    (re.compile(r"\bEdit\("), "search_replace("),
    (re.compile(r"\bGrep\("), "grep("),
    (re.compile(r"\bGlob\("), "list_dir("),
    (re.compile(r"\bBash\("), "run_terminal_command("),
    (re.compile(r"\bLS\("), "list_dir("),
]

_AGENT_PATH_RE = re.compile(r"\.claude/agents/[^/\s]+/([^/\s]+)")
_COMMAND_PATH_RE = re.compile(r"\.claude/commands/[^/\s]+/([^/\s]+)")

# Same preserve-list as build-plugin.sh: workspace SDD dirs stay project-relative.
_PLUGIN_PATHS: list[tuple[str, str]] = [
    (".claude/sdd/templates/", "${GROK_PLUGIN_ROOT}/sdd/templates/"),
    (".claude/sdd/architecture/", "${GROK_PLUGIN_ROOT}/sdd/architecture/"),
    (".claude/sdd/_index.md", "${GROK_PLUGIN_ROOT}/sdd/_index.md"),
    (".claude/sdd/README.md", "${GROK_PLUGIN_ROOT}/sdd/README.md"),
    (".claude/kb/", "${GROK_PLUGIN_ROOT}/kb/"),
    (".claude/skills/", "${GROK_PLUGIN_ROOT}/skills/"),
    ("${CLAUDE_PLUGIN_ROOT}", "${GROK_PLUGIN_ROOT}"),
]


def parse_frontmatter(text: str) -> dict:
    """Extract the frontmatter keys we need. Mirrors generate-codex-plugin.py."""
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}
    body = match.group(1)
    fm: dict = {}

    for key in ("name", "tier", "model"):
        m = re.search(rf"^{key}:\s*(.+)$", body, re.MULTILINE)
        if m:
            fm[key] = m.group(1).strip()

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
    for line in (raw or "").strip().splitlines():
        line = line.strip()
        if line:
            return line
    return ""


def remap_tool(name: str) -> str:
    return TOOL_MAP.get(name, name)


def remap_tools_csv(csv: str) -> str:
    parts = [s.strip() for s in csv.split(",") if s.strip()]
    # Preserve order, drop duplicates introduced by Edit+MultiEdit -> search_replace.
    seen: set[str] = set()
    out: list[str] = []
    for part in parts:
        mapped = remap_tool(part)
        if mapped not in seen:
            seen.add(mapped)
            out.append(mapped)
    return ", ".join(out)


def rewrite_tools_in_body(text: str) -> str:
    for pattern, repl in _BODY_TOOL_RES:
        text = pattern.sub(repl, text)
    return text


def rewrite_plugin_paths(text: str) -> str:
    """Point bundled content at GROK_PLUGIN_ROOT; keep workspace SDD dirs."""
    text = _AGENT_PATH_RE.sub(r"${GROK_PLUGIN_ROOT}/agents/\1", text)
    text = _COMMAND_PATH_RE.sub(r"${GROK_PLUGIN_ROOT}/commands/\1", text)
    # Any leftover category-less agent/command refs.
    text = text.replace(".claude/agents/", "${GROK_PLUGIN_ROOT}/agents/")
    text = text.replace(".claude/commands/", "${GROK_PLUGIN_ROOT}/commands/")
    for src, dst in _PLUGIN_PATHS:
        text = text.replace(src, dst)
    return text


def mutates_workspace(tools: list[str] | None) -> bool:
    if not tools:
        return True
    return bool(WRITE_TOOLS & set(tools))


def _strip_mcp_servers(fm_raw: str) -> str:
    return re.sub(r"^mcp_servers:\n(?:^[ \t].*\n?)*", "", fm_raw, flags=re.MULTILINE)


def adapt_agent(text: str, source: Path, *, plugin: bool) -> str:
    """Rewrite a Claude agent markdown file into a Grok agent definition."""
    fm = parse_frontmatter(text)
    match = _FRONTMATTER_RE.match(text)
    if not match:
        body = rewrite_tools_in_body(text)
        return rewrite_plugin_paths(body) if plugin else body

    fm_raw = match.group(1)
    body = text[match.end() :]

    def _tools_sub(m: re.Match[str]) -> str:
        return f"tools: [{remap_tools_csv(m.group(1))}]"

    fm_raw = re.sub(r"^tools:\s*\[([^\]]*)\]", _tools_sub, fm_raw, flags=re.MULTILINE)
    fm_raw = re.sub(r"^model:\s*.+\n?", "", fm_raw, flags=re.MULTILINE)
    fm_raw = _strip_mcp_servers(fm_raw)
    permission = "default" if mutates_workspace(fm.get("tools")) else "plan"
    grok_fields = (
        f"prompt_mode: full\n"
        f"agents_md: true\n"
        f"permission_mode: {permission}\n"
    )
    if re.search(r"^name:\s*.+$", fm_raw, re.MULTILINE):
        fm_raw = re.sub(
            r"^(name:\s*.+)$",
            r"\1\n" + grok_fields,
            fm_raw,
            count=1,
            flags=re.MULTILINE,
        )
    else:
        fm_raw = grok_fields + fm_raw

    body = rewrite_tools_in_body(body)
    if plugin:
        body = rewrite_plugin_paths(body)
        fm_raw = rewrite_plugin_paths(fm_raw)

    rel = source.relative_to(REPO_ROOT).as_posix()
    header = (
        f"<!-- Generated by scripts/generate-grok-plugin.py — do not edit by hand. -->\n"
        f"<!-- Source: {rel} -->\n\n"
    )
    fm_raw = fm_raw.strip("\n")
    body = body.lstrip("\n")
    return f"---\n{fm_raw}\n---\n\n{header}{body}"


def adapt_command(text: str, source: Path, *, plugin: bool) -> str:
    body_match = _FRONTMATTER_RE.match(text)
    if body_match:
        fm_raw = body_match.group(1)
        body = rewrite_tools_in_body(text[body_match.end() :])
        if plugin:
            fm_raw = rewrite_plugin_paths(fm_raw)
            body = rewrite_plugin_paths(body)
        rel = source.relative_to(REPO_ROOT).as_posix()
        header = (
            f"<!-- Generated by scripts/generate-grok-plugin.py — do not edit by hand. -->\n"
            f"<!-- Source: {rel} -->\n\n"
        )
        fm_raw = fm_raw.strip("\n")
        body = body.lstrip("\n")
        return f"---\n{fm_raw}\n---\n\n{header}{body}"
    body = rewrite_tools_in_body(text)
    return rewrite_plugin_paths(body) if plugin else body


def _iter_md(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return [
        p
        for p in sorted(root.glob("*/*.md"))
        if p.is_file() and p.name not in SKIP_FILES
    ]


def _copy_tree(src: Path, dst: Path) -> list[Path]:
    written: list[Path] = []
    if not src.exists():
        return written
    dst.mkdir(parents=True, exist_ok=True)
    if src.is_file():
        target = dst / src.name if dst.is_dir() else dst
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, target)
        return [target]
    for item in sorted(src.rglob("*")):
        if not item.is_file():
            continue
        target = dst / item.relative_to(src)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, target)
        written.append(target)
    return written


def _rewrite_text_file(path: Path, *, tools: bool = False) -> None:
    if path.suffix.lower() not in TEXT_SUFFIXES:
        return
    try:
        original = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return
    updated = rewrite_plugin_paths(original)
    if tools:
        updated = rewrite_tools_in_body(updated)
    if updated != original:
        path.write_text(updated, encoding="utf-8")


def _chmod_scripts(root: Path) -> None:
    for path in root.rglob("*.sh"):
        if path.is_file():
            path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def render_plugin(out: Path) -> dict[str, int]:
    """Write the distributable Grok plugin into `out`."""
    counts = {
        "agents": 0,
        "commands": 0,
        "skills": 0,
        "kb": 0,
        "sdd": 0,
        "scripts": 0,
    }

    agents_out = out / "agents"
    commands_out = out / "commands"
    skills_out = out / "skills"
    kb_out = out / "kb"
    sdd_out = out / "sdd"
    scripts_out = out / "scripts"
    hooks_out = out / "hooks"

    for d in (agents_out, commands_out, skills_out, kb_out, sdd_out, scripts_out, hooks_out):
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True)

    for md in _iter_md(AGENTS_DIR):
        text = adapt_agent(md.read_text(encoding="utf-8"), md, plugin=True)
        (agents_out / md.name).write_text(text, encoding="utf-8")
        counts["agents"] += 1

    for md in _iter_md(COMMANDS_DIR):
        text = adapt_command(md.read_text(encoding="utf-8"), md, plugin=True)
        (commands_out / md.name).write_text(text, encoding="utf-8")
        counts["commands"] += 1

    skill_sources = []
    if SKILLS_DIR.is_dir():
        skill_sources.extend(sorted(p for p in SKILLS_DIR.iterdir() if p.is_dir()))
    if EXTRAS_SKILLS.is_dir():
        skill_sources.extend(sorted(p for p in EXTRAS_SKILLS.iterdir() if p.is_dir()))
    for skill_dir in skill_sources:
        if skill_dir.name in REPO_LOCAL_SKILLS:
            continue
        dest = skills_out / skill_dir.name
        _copy_tree(skill_dir, dest)
        for path in dest.rglob("*"):
            if path.is_file():
                _rewrite_text_file(path)
        counts["skills"] += 1

    kb_files = _copy_tree(KB_DIR, kb_out)
    for path in kb_files:
        _rewrite_text_file(path)
    counts["kb"] = len(kb_files)

    sdd_files = _copy_tree(SDD_TEMPLATES, sdd_out / "templates")
    sdd_files += _copy_tree(SDD_ARCH, sdd_out / "architecture")
    for src, name in ((SDD_INDEX, "_index.md"), (SDD_README, "README.md")):
        if src.is_file():
            target = sdd_out / name
            shutil.copy2(src, target)
            sdd_files.append(target)
    for path in sdd_files:
        # Templates mention the Claude Task tool in the build legend; remap those
        # without touching kb/ (CrewAI's Task() class must stay).
        _rewrite_text_file(path, tools=True)
    counts["sdd"] = len(sdd_files)

    if EXTRAS_SCRIPTS.is_dir():
        for item in EXTRAS_SCRIPTS.iterdir():
            if item.is_file():
                shutil.copy2(item, scripts_out / item.name)
                counts["scripts"] += 1
    if JUDGE_PY.is_file():
        shutil.copy2(JUDGE_PY, scripts_out / JUDGE_PY.name)
        counts["scripts"] += 1
    for path in scripts_out.rglob("*"):
        if path.is_file():
            _rewrite_text_file(path)
    _chmod_scripts(out)

    if LICENSE.is_file():
        shutil.copy2(LICENSE, out / "LICENSE")

    (hooks_out / "hooks.json").write_text(
        """{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "${GROK_PLUGIN_ROOT}/scripts/init-workspace.sh"
          }
        ]
      }
    ]
  }
}
""",
        encoding="utf-8",
    )
    return counts


def render_project(out: Path) -> dict[str, int]:
    """Write project-scoped Grok agents + commands for dogfooding this repo."""
    agents_out = out / "agents"
    commands_out = out / "commands"
    if agents_out.exists():
        shutil.rmtree(agents_out)
    if commands_out.exists():
        shutil.rmtree(commands_out)
    agents_out.mkdir(parents=True)
    commands_out.mkdir(parents=True)

    counts = {"agents": 0, "commands": 0}
    for md in _iter_md(AGENTS_DIR):
        text = adapt_agent(md.read_text(encoding="utf-8"), md, plugin=False)
        (agents_out / md.name).write_text(text, encoding="utf-8")
        counts["agents"] += 1
    for md in _iter_md(COMMANDS_DIR):
        text = adapt_command(md.read_text(encoding="utf-8"), md, plugin=False)
        (commands_out / md.name).write_text(text, encoding="utf-8")
        counts["commands"] += 1
    return counts


def _generated_plugin_dirs(root: Path) -> tuple[Path, ...]:
    return (
        root / "agents",
        root / "commands",
        root / "skills",
        root / "kb",
        root / "sdd",
        root / "scripts",
        root / "hooks",
        root / "LICENSE",
    )


def diff_trees(left: Path, right: Path) -> list[str]:
    """Line-oriented tree diff: '+' added in right, '~' changed, '-' removed."""
    diff: list[str] = []
    left_files = {p.relative_to(left) for p in left.rglob("*") if p.is_file()} if left.exists() else set()
    right_files = {p.relative_to(right) for p in right.rglob("*") if p.is_file()} if right.exists() else set()
    for rel in sorted(right_files - left_files):
        diff.append(f"+ {rel}")
    for rel in sorted(left_files - right_files):
        diff.append(f"- {rel}")
    for rel in sorted(left_files & right_files):
        lf = left / rel
        rf = right / rel
        if not filecmp.cmp(lf, rf, shallow=False):
            diff.append(f"~ {rel}")
    return diff


def snapshot_generated(plugin_root: Path, project_root: Path, dest: Path) -> None:
    """Copy only generator-owned paths so --check ignores static README/plugin.json."""
    dest_plugin = dest / "plugin-grok"
    dest_project = dest / "dot-grok"
    dest_plugin.mkdir(parents=True)
    dest_project.mkdir(parents=True)
    for item in _generated_plugin_dirs(plugin_root):
        if not item.exists():
            continue
        target = dest_plugin / item.name
        if item.is_dir():
            shutil.copytree(item, target)
        else:
            shutil.copy2(item, target)
    for name in ("agents", "commands"):
        src = project_root / name
        if src.exists():
            shutil.copytree(src, dest_project / name)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--check",
        action="store_true",
        help="verify plugin-grok/ and .grok/{agents,commands} match sources; exit 1 on drift",
    )
    args = ap.parse_args()

    if not AGENTS_DIR.is_dir():
        print(f"ERROR: {AGENTS_DIR} not found", file=sys.stderr)
        return 1
    if not COMMANDS_DIR.is_dir():
        print(f"ERROR: {COMMANDS_DIR} not found", file=sys.stderr)
        return 1

    if args.check:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            before = tmp_path / "before"
            after = tmp_path / "after"
            snapshot_generated(PLUGIN_OUT, PROJECT_OUT, before)
            render_plugin(tmp_path / "plugin-grok")
            render_project(tmp_path / "dot-grok")
            snapshot_generated(tmp_path / "plugin-grok", tmp_path / "dot-grok", after)
            drift = diff_trees(before, after)
            if drift:
                print("Grok plugin is out of date. Run: make grok", file=sys.stderr)
                for line in drift[:80]:
                    print(f"  [drift] {line}", file=sys.stderr)
                if len(drift) > 80:
                    print(f"  ... {len(drift) - 80} more", file=sys.stderr)
                return 1
        print("OK - plugin-grok/ + .grok/{agents,commands} up to date")
        return 0

    PLUGIN_OUT.mkdir(parents=True, exist_ok=True)
    plugin_counts = render_plugin(PLUGIN_OUT)
    project_counts = render_project(PROJECT_OUT)
    print(
        "Generated plugin-grok/ - "
        f"{plugin_counts['agents']} agents, "
        f"{plugin_counts['commands']} commands, "
        f"{plugin_counts['skills']} skills, "
        f"{plugin_counts['kb']} kb files, "
        f"{plugin_counts['sdd']} sdd files, "
        f"{plugin_counts['scripts']} scripts"
    )
    print(
        "Generated .grok/ - "
        f"{project_counts['agents']} agents, "
        f"{project_counts['commands']} commands"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
