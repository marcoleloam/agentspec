"""Assertions over a JSON (or .ipynb) document using dotted paths.

Path syntax: ``a.b.0.c`` (integers index lists); ``*`` matches every element
of a list or every value of an object, and the assertion passes if ANY match
satisfies it.

Usage:
  python -m kb_bench.checks.json_check FILE [--has PATH]... [--eq PATH=VALUE]...
      [--min-len PATH=N]... [--contains PATH=SUBSTRING]... [--any-key PATH=REGEX]...
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from kb_bench.checks import finish, run

_MISSING = object()


def resolve(doc: Any, path: str) -> list[Any]:
    nodes: list[Any] = [doc]
    for part in (p for p in path.split(".") if p):
        nxt: list[Any] = []
        for node in nodes:
            if part == "*":
                if isinstance(node, list):
                    nxt.extend(node)
                elif isinstance(node, dict):
                    nxt.extend(node.values())
            elif isinstance(node, list) and part.isdigit() and int(part) < len(node):
                nxt.append(node[int(part)])
            elif isinstance(node, dict) and part in node:
                nxt.append(node[part])
        nodes = nxt
    return nodes


def _split(spec: str) -> tuple[str, str]:
    path, _, value = spec.partition("=")
    return path, value


def _coerce(value: str) -> Any:
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="json_check")
    ap.add_argument("file")
    ap.add_argument("--has", action="append", default=[])
    ap.add_argument("--eq", action="append", default=[])
    ap.add_argument("--min-len", action="append", default=[])
    ap.add_argument("--contains", action="append", default=[])
    ap.add_argument("--any-key", action="append", default=[],
                    help="PATH=REGEX: an object at PATH has a key matching REGEX")
    args = ap.parse_args(argv)

    path = Path(args.file)
    if not path.is_file():
        return finish([f"{args.file} does not exist"])
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return finish([f"{args.file} is not valid JSON: {exc}"])

    failures = [f"missing {p}" for p in args.has if not resolve(doc, p)]
    for spec in args.eq:
        p, v = _split(spec)
        if _coerce(v) not in resolve(doc, p):
            failures.append(f"{p} != {v}")
    for spec in args.min_len:
        p, n = _split(spec)
        if not any(isinstance(x, (list, dict, str)) and len(x) >= int(n) for x in resolve(doc, p)):
            failures.append(f"{p} has fewer than {n} items")
    for spec in args.contains:
        p, s = _split(spec)
        if not any(s in json.dumps(x) for x in resolve(doc, p)):
            failures.append(f"{p} does not contain {s!r}")
    for spec in args.any_key:
        p, rx = _split(spec)
        objs = [x for x in resolve(doc, p) if isinstance(x, dict)]
        if not any(re.search(rx, k) for o in objs for k in o):
            failures.append(f"no key under {p} matches /{rx}/")
    return finish(failures)


if __name__ == "__main__":
    run(main)
