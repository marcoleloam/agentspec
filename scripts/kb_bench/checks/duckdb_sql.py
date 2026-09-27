"""Execute SQL files in an in-memory DuckDB and assert on query results.

File access is confined to the current directory (the eval workspace copy)
via DuckDB's ``allowed_directories`` + ``enable_external_access = false``.
Jinja is not supported — use this for plain SQL deliverables.

Usage:
  python -m kb_bench.checks.duckdb_sql SQL_FILE [SQL_FILE ...]
      [--assert "QUERY" == VALUE]... [--assert-rows "QUERY" == N]... [--assert-empty "QUERY"]...

Each --assert takes the form ``"select count(*) from t" == 3`` (scalar result
compared as string, so ``== abc`` and ``== 3`` both work).
"""
from __future__ import annotations

import argparse
import os
import re
from pathlib import Path

from kb_bench.checks import finish, run

_ASSERT = re.compile(r"^(?P<query>.+?)\s*==\s*(?P<value>.*)$", re.DOTALL)


def _parse_assert(spec: str) -> tuple[str, str]:
    match = _ASSERT.match(spec.strip())
    if not match:
        raise argparse.ArgumentTypeError(f"expected 'QUERY == VALUE', got {spec!r}")
    return match["query"].strip().strip('"'), match["value"].strip().strip('"')


def _connect(workdir: Path):
    import duckdb

    con = duckdb.connect(":memory:")
    root = str(workdir.resolve())
    con.execute("SET TimeZone = 'UTC'")
    con.execute(f"SET allowed_directories = ['{root}']")
    con.execute("SET enable_external_access = false")
    con.execute("SET lock_configuration = true")
    return con


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="duckdb_sql")
    ap.add_argument("sql_files", nargs="+")
    ap.add_argument("--assert", dest="asserts", action="append", default=[], type=_parse_assert)
    ap.add_argument("--assert-rows", action="append", default=[], type=_parse_assert)
    ap.add_argument("--assert-empty", action="append", default=[])
    args = ap.parse_args(argv)

    try:
        import duckdb
    except ImportError:
        print("ERROR: duckdb not installed — run `make kb-bench-setup`")
        return 2

    missing = [f for f in args.sql_files if not Path(f).is_file()]
    if missing:
        return finish([f"{f} does not exist" for f in missing])

    con = _connect(Path(os.getcwd()))
    for sql_file in args.sql_files:
        try:
            con.execute(Path(sql_file).read_text(encoding="utf-8"))
        except duckdb.Error as exc:
            return finish([f"{sql_file} failed in DuckDB: {str(exc).splitlines()[0][:240]}"])

    failures: list[str] = []
    for query, expected in args.asserts:
        try:
            row = con.execute(query).fetchone()
        except duckdb.Error as exc:
            failures.append(f"query failed: {query!r}: {str(exc).splitlines()[0][:200]}")
            continue
        got = "" if row is None or row[0] is None else str(row[0])
        if got != expected:
            failures.append(f"{query!r} returned {got!r}, expected {expected!r}")
    for query, expected in args.assert_rows:
        try:
            got = len(con.execute(query).fetchall())
        except duckdb.Error as exc:
            failures.append(f"query failed: {query!r}: {str(exc).splitlines()[0][:200]}")
            continue
        if str(got) != expected:
            failures.append(f"{query!r} returned {got} rows, expected {expected}")
    for query in args.assert_empty:
        try:
            rows = con.execute(query).fetchall()
        except duckdb.Error as exc:
            failures.append(f"query failed: {query!r}: {str(exc).splitlines()[0][:200]}")
            continue
        if rows:
            failures.append(f"{query!r} returned {len(rows)} row(s), expected none")
    return finish(failures)


if __name__ == "__main__":
    run(main)
