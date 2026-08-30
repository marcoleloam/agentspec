#!/usr/bin/env python3
"""Generate the DeepSeek Harness (dsh) bundle distribution from .claude/ (single
source of truth), mirroring generate-codex-plugin.py.

Syncing content from .claude/ into plugin-dsh/assets/:
  - skills        plugin/skills/*            (merged SKILL.md set, incl. source-command-*)
  - sdd templates .claude/sdd/templates/*.md
  - contracts     .claude/sdd/architecture/{WORKFLOW_CONTRACTS.yaml, ARCHITECTURE.md}
  - commands      .claude/commands/**/*.md   (flattened to plugin-dsh/assets/commands/)
  - agents        .claude/agents/workflow/*.md

The bundle's JS plugins (plugin-dsh/lib/) read these assets at runtime through
import.meta.url, so the bundle is self-contained and needs no CLAUDE_PLUGIN_ROOT.

Usage:
  python3 scripts/generate-dsh-bundle.py          # write plugin-dsh/assets/
  python3 scripts/generate-dsh-bundle.py --check  # fail if plugin-dsh/assets/ is stale
"""
from __future__ import annotations

import argparse
import filecmp
import shutil
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT = REPO_ROOT / "plugin-dsh" / "assets"

# Source dirs -> destination under OUT.
SKILLS_SRC = REPO_ROOT / "plugin" / "skills"
SDD_TEMPLATES_SRC = REPO_ROOT / ".claude" / "sdd" / "templates"
ARCH_SRC = REPO_ROOT / ".claude" / "sdd" / "architecture"
COMMANDS_SRC = REPO_ROOT / ".claude" / "commands"
AGENTS_SRC = REPO_ROOT / ".claude" / "agents" / "workflow"

OUT_SKILLS = OUT / "skills"
OUT_TEMPLATES = OUT / "sdd" / "templates"
OUT_ARCH = OUT / "sdd" / "architecture"
OUT_COMMANDS = OUT / "commands"
OUT_AGENTS = OUT / "agents" / "workflow"

SKIP_NAMES = frozenset({"README.md", "_template.md"})


def sync_dir(src: Path, dst: Path, flatten: bool = False) -> list[Path]:
    """Copy every regular file under src into dst (tree or flattened)."""
    written: list[Path] = []
    if not src.is_dir():
        return written
    dst.mkdir(parents=True, exist_ok=True)
    for item in sorted(src.rglob("*")):
        if not item.is_file() or item.name in SKIP_NAMES:
            continue
        target = dst / item.name if flatten else dst / item.relative_to(src)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, target)
        written.append(target)
    return written


def render() -> dict[str, list[Path]]:
    """Return {section: files} produced by a full regenerate."""
    return {
        "skills": sync_dir(SKILLS_SRC, OUT_SKILLS),
        "sdd/templates": sync_dir(SDD_TEMPLATES_SRC, OUT_TEMPLATES),
        "sdd/architecture": sync_dir(ARCH_SRC, OUT_ARCH),
        "commands": sync_dir(COMMANDS_SRC, OUT_COMMANDS, flatten=True),
        "agents/workflow": sync_dir(AGENTS_SRC, OUT_AGENTS),
    }


def diff_trees(left: Path, right: Path) -> list[str]:
    """Line-oriented tree diff: '+' added in right, '~' changed, '-' removed."""
    diff: list[str] = []
    for lf in sorted(left.rglob("*")):
        if not lf.is_file():
            continue
        rel = lf.relative_to(left)
        rf = right / rel
        if not rf.is_file():
            diff.append(f"+ {rel}")
        elif not filecmp.cmp(lf, rf, shallow=False):
            diff.append(f"~ {rel}")
    for rf in sorted(right.rglob("*")):
        if rf.is_file() and not (left / rf.relative_to(right)).is_file():
            diff.append(f"- {rf.relative_to(right)}")
    return diff


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--check",
        action="store_true",
        help="verify plugin-dsh/assets/ matches the sources; exit 1 on drift",
    )
    args = ap.parse_args()

    if args.check:
        with tempfile.TemporaryDirectory() as tmp:
            backup = Path(tmp) / "assets"
            shutil.copytree(OUT, backup)
            shutil.rmtree(OUT)
            render()
            drift = diff_trees(backup, OUT)
            shutil.rmtree(OUT)
            shutil.copytree(backup, OUT)  # leave the committed assets untouched
            if drift:
                for line in drift:
                    print(f"[drift] {line}", file=sys.stderr)
                return 1
        return 0

    shutil.rmtree(OUT, ignore_errors=True)
    produced = render()
    total = sum(len(files) for files in produced.values())
    for section, files in produced.items():
        print(f"  {section}: {len(files)} files")
    print(f"plugin-dsh/assets regenerated ({total} files).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
