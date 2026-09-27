"""Assert that a regex matches (or does not match) a file's contents.

Usage:
  python -m kb_bench.checks.regex_check FILE PATTERN [--absent] [--ignore-case] [--min-count N]
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from kb_bench.checks import finish, run


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="regex_check")
    ap.add_argument("file")
    ap.add_argument("pattern")
    ap.add_argument("--absent", action="store_true", help="pass only if the pattern does NOT match")
    ap.add_argument("--ignore-case", action="store_true")
    ap.add_argument("--min-count", type=int, default=1)
    args = ap.parse_args(argv)

    path = Path(args.file)
    if not path.is_file():
        return finish([f"{args.file} does not exist"])
    flags = re.MULTILINE | (re.IGNORECASE if args.ignore_case else 0)
    count = len(re.findall(args.pattern, path.read_text(encoding="utf-8", errors="replace"), flags))
    if args.absent:
        return finish([f"{args.file} matches forbidden /{args.pattern}/ ({count}x)"] if count else [])
    if count < args.min_count:
        return finish([f"{args.file} matches /{args.pattern}/ {count}x, expected >= {args.min_count}"])
    return 0


if __name__ == "__main__":
    run(main)
