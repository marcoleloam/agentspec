#!/usr/bin/env python3
"""AgentSpec Living Memory — Claude Code hook adapter for memory-index.py.

The E2E run (Q-009) showed agents write the blackboard when told to, but skip the
script calls. These hooks make the calls deterministic:

    prompt      UserPromptSubmit  phase command → inject the ≤15-line brief as context
    pre-write   PreToolUse        creating DESIGN_{F}.md → run the gate; exit 2 blocks
    post-write  PostToolUse       Write/Edit of BLACKBOARD_*.md → rebuild MEMORY_INDEX.md;
                                  exit 2 feeds unreadable-row warnings back to the agent

Reads the hook JSON on stdin. Never fails the session: any unexpected error → exit 0.
Zero dependencies.
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PHASE_OF = {
    "brainstorm": "brainstorm", "define": "define", "define-m": "define",
    "design": "design", "design-m": "design", "build": "build", "continue": "build",
    "iterate": "iterate", "ship": "ship",
}
COMMAND_RE = re.compile(r"^\s*/(?:agentspec:)?(?:workflow:)?([a-z-]+)\b(.*)$", re.DOTALL)
DOC_RE = re.compile(r"(?:BRAINSTORM|DEFINE|DESIGN|BLACKBOARD|BUILD_REPORT)_([A-Z0-9][A-Z0-9_]*?)\.md")
NAME_RE = re.compile(r"^[A-Z][A-Z0-9_]{2,}$")


def load_index():
    spec = importlib.util.spec_from_file_location("agentspec_memory_index", HERE / "memory-index.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def feature_from_args(args: str) -> str:
    doc = DOC_RE.search(args)
    if doc:
        return doc.group(1)
    first = args.strip().split()[0] if args.strip() else ""
    return first if NAME_RE.match(first) else ""


def run(mi, argv: list[str]) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = mi.main(argv)
    return code, out.getvalue(), err.getvalue()


def on_prompt(event: dict, root: Path) -> int:
    m = COMMAND_RE.match(event.get("prompt", ""))
    if not m or m.group(1) not in PHASE_OF:
        return 0
    feature = feature_from_args(m.group(2))
    if not feature:
        return 0
    _, out, _ = run(load_index(), ["--root", str(root), "brief", feature, "--phase", PHASE_OF[m.group(1)]])
    if "(sem memória registrada" in out and "⚠" not in out:
        return 0
    print("=== Living Memory (injected by the AgentSpec hook — no need to run `brief` again) ===")
    print(out.rstrip())
    return 0


def target_path(event: dict) -> Path | None:
    value = (event.get("tool_input") or {}).get("file_path", "")
    return Path(value) if value else None


def on_pre_write(event: dict, root: Path) -> int:
    path = target_path(event)
    if path is None or path.exists():
        return 0
    m = re.match(r"^DESIGN_(.+)\.md$", path.name)
    if not m or path.parent.name != "features":
        return 0
    code, out, _ = run(load_index(), ["--root", str(root), "gate", m.group(1), "--to", "design"])
    if code == 0:
        return 0
    print(out.rstrip(), file=sys.stderr)
    print("DESIGN not written. Ask the user; close each 🔴 only with their answer (or /iterate), "
          "never with your own assumption — then write it again.", file=sys.stderr)
    return 2


def on_post_write(event: dict, root: Path) -> int:
    path = target_path(event)
    if path is None or not re.match(r"^BLACKBOARD_.+\.md$", path.name):
        return 0
    code, _, err = run(load_index(), ["--root", str(root), "build"])
    if code != 2:
        return 0
    print(err.rstrip(), file=sys.stderr)
    print("MEMORY_INDEX.md rebuilt, but the rows above are invisible to brief/gate — fix them now.",
          file=sys.stderr)
    return 2


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    handlers = {"prompt": on_prompt, "pre-write": on_pre_write, "post-write": on_post_write}
    if len(argv) != 1 or argv[0] not in handlers:
        print(f"usage: memory-hook.py {{{'|'.join(handlers)}}} < hook-event.json", file=sys.stderr)
        return 0
    try:
        event = json.load(sys.stdin)
        root = Path(event.get("cwd") or ".") / ".claude" / "sdd"
        if not root.is_dir():
            return 0
        return handlers[argv[0]](event, root)
    except Exception:  # a memory hook must never break the session
        return 0


if __name__ == "__main__":
    sys.exit(main())
