"""Static assertions over a Python file (or a .ipynb notebook's code cells).

Never imports or executes the target. Names match on the dotted callee text,
so ``--require-call saveAsTable`` matches ``df.write.format("delta").saveAsTable(...)``.

Usage:
  python -m kb_bench.checks.py_ast FILE [--require-import MOD]... [--forbid-import MOD]...
      [--require-call NAME]... [--forbid-call NAME]... [--require-name NAME]... [--forbid-name NAME]...
      [--require-string REGEX]...
"""
from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path

from kb_bench.checks import finish, run


def load_source(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix != ".ipynb":
        return text
    notebook = json.loads(text)
    cells = [c for c in notebook.get("cells", []) if c.get("cell_type") == "code"]
    lines: list[str] = []
    for cell in cells:
        src = cell.get("source", "")
        body = "".join(src) if isinstance(src, list) else src
        lines.extend(ln for ln in body.splitlines() if not ln.lstrip().startswith(("%", "!")))
    return "\n".join(lines)


def dotted(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{dotted(node.value)}.{node.attr}"
    if isinstance(node, ast.Call):
        return dotted(node.func)
    return ""


class Facts:
    def __init__(self, tree: ast.AST) -> None:
        self.imports: set[str] = set()
        self.calls: set[str] = set()
        self.names: set[str] = set()
        self.strings: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                self.imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                self.imports.add(node.module)
                self.imports.update(f"{node.module}.{alias.name}" for alias in node.names)
                self.names.update(alias.asname or alias.name for alias in node.names)
            elif isinstance(node, ast.Call):
                self.calls.add(dotted(node.func))
                self.names.update(kw.arg for kw in node.keywords if kw.arg)
            elif isinstance(node, ast.Name):
                self.names.add(node.id)
            elif isinstance(node, ast.Attribute):
                self.names.add(node.attr)
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                self.strings.append(node.value)

    def has_import(self, mod: str) -> bool:
        return any(i == mod or i.startswith(f"{mod}.") for i in self.imports)

    def has_call(self, name: str) -> bool:
        return any(c == name or c.endswith(f".{name}") for c in self.calls)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="py_ast")
    ap.add_argument("file")
    for flag in ("require-import", "forbid-import", "require-call", "forbid-call",
                 "require-name", "forbid-name", "require-string"):
        ap.add_argument(f"--{flag}", action="append", default=[])
    args = ap.parse_args(argv)

    path = Path(args.file)
    if not path.is_file():
        return finish([f"{args.file} does not exist"])
    try:
        facts = Facts(ast.parse(load_source(path), filename=str(path)))
    except (SyntaxError, ValueError) as exc:
        return finish([f"{args.file} is not valid Python: {exc}"])

    failures = [f"missing import {m}" for m in args.require_import if not facts.has_import(m)]
    failures += [f"forbidden import {m}" for m in args.forbid_import if facts.has_import(m)]
    failures += [f"missing call {c}()" for c in args.require_call if not facts.has_call(c)]
    failures += [f"forbidden call {c}()" for c in args.forbid_call if facts.has_call(c)]
    failures += [f"missing name {n}" for n in args.require_name if n not in facts.names]
    failures += [f"forbidden name {n}" for n in args.forbid_name if n in facts.names]
    failures += [
        f"no string literal matches /{rx}/"
        for rx in args.require_string
        if not any(re.search(rx, s) for s in facts.strings)
    ]
    return finish(failures)


if __name__ == "__main__":
    run(main)
