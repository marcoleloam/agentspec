"""SQL assertions using sqlglot (installed in the kb_bench eval venv).

Jinja blocks (``{{ ... }}``, ``{% ... %}``) are neutralised before parsing so
dbt models can be checked too. All statements in the file are parsed.

Usage:
  python -m kb_bench.checks.sql_check FILE [--dialect duckdb] [--require-table NAME]...
      [--require-column TABLE.COL]... [--forbid-select-star] [--require-regex REGEX]...
      [--require-create] [--require-primary-key TABLE]...
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from kb_bench.checks import finish, run

_JINJA_EXPR = re.compile(r"\{\{.*?\}\}", re.DOTALL)
_JINJA_STMT = re.compile(r"\{%.*?%\}", re.DOTALL)
_JINJA_COMMENT = re.compile(r"\{#.*?#\}", re.DOTALL)


def strip_jinja(sql: str) -> str:
    sql = _JINJA_COMMENT.sub("", sql)
    sql = _JINJA_STMT.sub("", sql)
    return _JINJA_EXPR.sub("jinja_ref", sql)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="sql_check")
    ap.add_argument("file")
    ap.add_argument("--dialect", default="duckdb")
    ap.add_argument("--require-table", action="append", default=[],
                    help="table created (CREATE TABLE/VIEW) or referenced")
    ap.add_argument("--require-column", action="append", default=[],
                    help="TABLE.COL defined in a CREATE TABLE, or COL anywhere if no table")
    ap.add_argument("--forbid-select-star", action="store_true")
    ap.add_argument("--require-regex", action="append", default=[])
    ap.add_argument("--require-create", action="store_true")
    ap.add_argument("--require-primary-key", action="append", default=[])
    args = ap.parse_args(argv)

    try:
        import sqlglot
        from sqlglot import exp
    except ImportError:
        print("ERROR: sqlglot not installed — run `make kb-bench-setup`")
        return 2

    path = Path(args.file)
    if not path.is_file():
        return finish([f"{args.file} does not exist"])
    raw = path.read_text(encoding="utf-8", errors="replace")
    try:
        statements = [s for s in sqlglot.parse(strip_jinja(raw), read=args.dialect) if s is not None]
    except sqlglot.errors.ParseError as exc:
        return finish([f"{args.file} does not parse as {args.dialect} SQL: {str(exc)[:200]}"])
    if not statements:
        return finish([f"{args.file} has no SQL statements"])

    tables_created: dict[str, set[str]] = {}
    pk_tables: set[str] = set()
    referenced: set[str] = set()
    all_columns: set[str] = set()
    star = False
    for stmt in statements:
        for table in stmt.find_all(exp.Table):
            referenced.add(table.name.lower())
        for col in stmt.find_all(exp.Column):
            all_columns.add(col.name.lower())
        for alias in stmt.find_all(exp.Alias):
            all_columns.add(alias.alias.lower())
        for select in stmt.find_all(exp.Select):
            star = star or any(
                isinstance(e, exp.Star) or (isinstance(e, exp.Column) and isinstance(e.this, exp.Star))
                for e in select.expressions
            )
        if isinstance(stmt, exp.Create):
            target = stmt.this.find(exp.Table) if stmt.this else None
            name = target.name.lower() if target is not None else ""
            cols = {c.name.lower() for c in stmt.find_all(exp.ColumnDef)}
            tables_created.setdefault(name, set()).update(cols)
            all_columns.update(cols)
            if stmt.find(exp.PrimaryKey) or stmt.find(exp.PrimaryKeyColumnConstraint):
                pk_tables.add(name)

    failures: list[str] = []
    if args.require_create and not tables_created:
        failures.append("no CREATE statement")
    for name in args.require_table:
        if name.lower() not in referenced and name.lower() not in tables_created:
            failures.append(f"table {name} not created or referenced")
    for spec in args.require_column:
        table, _, col = spec.rpartition(".")
        pool = tables_created.get(table.lower(), set()) if table else all_columns
        if col.lower() not in pool:
            failures.append(f"column {spec} not found")
    for name in args.require_primary_key:
        if name.lower() not in pk_tables:
            failures.append(f"table {name} has no PRIMARY KEY")
    if args.forbid_select_star and star:
        failures.append("uses SELECT *")
    failures += [f"no match for /{rx}/" for rx in args.require_regex
                 if not re.search(rx, raw, re.IGNORECASE | re.MULTILINE)]
    return finish(failures)


if __name__ == "__main__":
    run(main)
