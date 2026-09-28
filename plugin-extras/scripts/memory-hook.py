#!/usr/bin/env python3
"""AgentSpec Living Memory — Claude Code hook adapter for memory-index.py.

The E2E run (Q-009) showed agents write the blackboard when told to, but skip the
script calls. These hooks make the calls deterministic:

    prompt      UserPromptSubmit  phase command → inject the ≤15-line brief as context
    pre-write   PreToolUse        creating DESIGN_{F}.md → run the gate; exit 2 blocks
    post-write  PostToolUse       Write/Edit of BLACKBOARD_*.md → rebuild MEMORY_INDEX.md;
                                  exit 2 feeds unreadable-row warnings back to the agent

The project root is the nearest ancestor holding .claude/sdd/features — of the tool's
file_path for the write hooks, of the event cwd for the prompt hook — so a session
started in a subdirectory is still gated.

Reads the hook JSON on stdin. Never fails the session: any unexpected error → exit 0
with no output (the only non-zero exits are the intentional gate block and the
unreadable-row feedback). Zero dependencies.
"""
from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PHASE_OF = {
    "brainstorm": "brainstorm", "define": "define", "define-m": "define",
    "design": "design", "design-m": "design", "build": "build",
    "continue": "build", "continuar": "build", "iterate": "iterate", "ship": "ship",
}
# Commands that act on the active feature when called without one (see /work, /continuar).
USES_ACTIVE = {"build", "continue", "continuar"}
NAMESPACES = {"agentspec", "workflow"}
SKILL_PREFIX = "source-command-workflow-"
COMMAND_RE = re.compile(r"^\s*/([a-z][a-z:-]*)(?![\w:-])(.*)$", re.DOTALL)
DOC_RE = re.compile(r"(?:BRAINSTORM|DEFINE|DESIGN|BLACKBOARD|BUILD_REPORT)_([A-Za-z0-9][A-Za-z0-9_]*?)\.md")
NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]{2,}$")


def load_index():
    spec = importlib.util.spec_from_file_location("agentspec_memory_index", HERE / "memory-index.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


Result = tuple[int, str, str]  # exit code, stdout, stderr
QUIET: Result = (0, "", "")


def find_root(start: Path) -> Path | None:
    """.claude/sdd/ of the nearest ancestor of start (inclusive) that has .claude/sdd/features.
    Stops at the enclosing git repository root, so it never picks up an unrelated project."""
    for d in (start, *start.parents):
        if (d / ".claude" / "sdd" / "features").is_dir():
            return d / ".claude" / "sdd"
        if (d / ".git").exists():
            return None
    return None


def command_of(prompt: str) -> tuple[str, str] | None:
    """'/agentspec:workflow:design X' | '/agentspec:source-command-workflow-design X' → ('design', ' X')."""
    m = COMMAND_RE.match(prompt)
    if not m:
        return None
    *spaces, name = m.group(1).split(":")
    if any(s not in NAMESPACES for s in spaces):
        return None
    name = name.removeprefix(SKILL_PREFIX)
    return (name, m.group(2)) if name in PHASE_OF else None


def known_features(root: Path) -> dict[str, str]:
    """Folded name → on-disk name of every feature with a document or an archive folder."""
    names = [p.name for p in (root / "archive").glob("*") if p.is_dir()]
    names += [m.group(1) for p in (root / "features").glob("*_*.md") if (m := DOC_RE.fullmatch(p.name))]
    return {n.lower(): n for n in names}


def feature_from_args(args: str, root: Path) -> str:
    doc = DOC_RE.search(args)
    token = doc.group(1) if doc else (args.split()[0].strip("\"'`") if args.strip() else "")
    if not NAME_RE.match(token):
        return ""
    known = known_features(root).get(token.lower())
    if known:
        return known
    # Unknown name: only a feature-shaped token (FEATURE_NAME, orders_etl) — not a word of prose.
    return token.upper() if token.isupper() or "_" in token else ""


def on_prompt(event: dict) -> Result:
    cmd = command_of(event.get("prompt", ""))
    if not cmd:
        return QUIET
    root = find_root(Path(event.get("cwd") or ".").resolve())
    if root is None:
        return QUIET
    name, args = cmd
    mi = load_index()
    feature = feature_from_args(args, root)
    if not feature and name in USES_ACTIVE:
        feature = mi.active_feature(root)
    if not feature:
        return QUIET
    lines = mi.brief(mi.collect(root), feature, PHASE_OF[name])
    if any("(sem memória registrada" in line for line in lines) and not any("⚠" in line for line in lines):
        return QUIET
    header = "=== Living Memory (injected by the AgentSpec hook — no need to run `brief` again) ==="
    return 0, "\n".join([header, *lines]) + "\n", ""


def target_path(event: dict) -> Path | None:
    value = (event.get("tool_input") or {}).get("file_path", "")
    if not value:
        return None
    path = Path(value)
    return path if path.is_absolute() else Path(event.get("cwd") or ".") / path


def on_pre_write(event: dict) -> Result:
    path = target_path(event)
    if path is None or path.exists():
        return QUIET
    m = re.match(r"^DESIGN_(.+)\.md$", path.name)
    if not m or path.parent.name != "features":
        return QUIET
    folder = path.parent.resolve()
    root = find_root(folder)
    if root is None or folder != (root / "features").resolve():
        return QUIET
    mi = load_index()
    code, lines = mi.gate_report(mi.collect(root), m.group(1), "design")
    if code == 0:
        return QUIET
    advice = ("DESIGN not written. Ask the user; close each 🔴 only with their answer (or /iterate), "
              "never with your own assumption — then write it again.")
    return 2, "", "\n".join([*lines, advice]) + "\n"


def on_post_write(event: dict) -> Result:
    path = target_path(event)
    if path is None or not re.match(r"^BLACKBOARD_.+\.md$", path.name):
        return QUIET
    root = find_root(path.parent.resolve())
    if root is None:
        return QUIET
    mi = load_index()
    _, warnings = mi.write_index(root, mi.collect(root))
    if not warnings:
        return QUIET
    advice = "MEMORY_INDEX.md rebuilt, but the rows above are invisible to brief/gate — fix them now."
    return 2, "", "\n".join([*warnings, advice]) + "\n"


HANDLERS = {"prompt": on_prompt, "pre-write": on_pre_write, "post-write": on_post_write}


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1 or argv[0] not in HANDLERS:
        print(f"usage: memory-hook.py {{{'|'.join(HANDLERS)}}} < hook-event.json", file=sys.stderr)
        return 0
    try:
        event = json.load(sys.stdin)
        code, out, err = HANDLERS[argv[0]](event if isinstance(event, dict) else {})
    except Exception:  # a memory hook must never break the session: no output, exit 0
        return 0
    sys.stdout.write(out)
    sys.stderr.write(err)
    return code


if __name__ == "__main__":
    sys.exit(main())
