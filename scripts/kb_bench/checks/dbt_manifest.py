"""Assertions over a dbt ``target/manifest.json`` produced by ``dbt parse``.

Usage:
  python -m kb_bench.checks.dbt_manifest MANIFEST --model NAME [--materialized M]
      [--unique-key KEY] [--incremental-strategy S] [--config KEY=VALUE]...
      [--has-test TEST_NAME]... [--column-test COL:TEST]... [--depends-on NAME]...
      [--min-models N] [--has-source SOURCE.TABLE]... [--has-snapshot NAME]...
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from kb_bench.checks import finish, run


def _nodes(manifest: dict[str, Any], resource_type: str) -> list[dict[str, Any]]:
    return [n for n in manifest.get("nodes", {}).values() if n.get("resource_type") == resource_type]


def _tests_for(manifest: dict[str, Any], unique_id: str) -> list[dict[str, Any]]:
    return [
        t for t in _nodes(manifest, "test")
        if unique_id in (t.get("depends_on") or {}).get("nodes", [])
    ]


def _test_name(test: dict[str, Any]) -> str:
    meta = test.get("test_metadata") or {}
    return meta.get("name") or test.get("name", "")


def _unique_key(config: dict[str, Any]) -> list[str]:
    key = config.get("unique_key")
    if key is None:
        return []
    return [key] if isinstance(key, str) else list(key)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="dbt_manifest")
    ap.add_argument("manifest")
    ap.add_argument("--model")
    ap.add_argument("--materialized")
    ap.add_argument("--unique-key")
    ap.add_argument("--incremental-strategy")
    ap.add_argument("--config", action="append", default=[])
    ap.add_argument("--has-test", action="append", default=[])
    ap.add_argument("--column-test", action="append", default=[])
    ap.add_argument("--depends-on", action="append", default=[])
    ap.add_argument("--min-models", type=int, default=0)
    ap.add_argument("--has-source", action="append", default=[])
    ap.add_argument("--has-snapshot", action="append", default=[])
    args = ap.parse_args(argv)

    path = Path(args.manifest)
    if not path.is_file():
        return finish([f"{args.manifest} does not exist (did `dbt parse` run?)"])
    manifest = json.loads(path.read_text(encoding="utf-8"))
    failures: list[str] = []

    models = _nodes(manifest, "model")
    if len(models) < args.min_models:
        failures.append(f"{len(models)} model(s), expected >= {args.min_models}")
    snapshots = {n.get("name") for n in _nodes(manifest, "snapshot")}
    failures += [f"missing snapshot {s}" for s in args.has_snapshot if s not in snapshots]
    sources = {f"{s.get('source_name')}.{s.get('name')}" for s in manifest.get("sources", {}).values()}
    failures += [f"missing source {s}" for s in args.has_source if s not in sources]

    if args.model:
        model = next((m for m in models if m.get("name") == args.model), None)
        if model is None:
            return finish(failures + [f"model {args.model} not in manifest"])
        config = model.get("config") or {}
        if args.materialized and config.get("materialized") != args.materialized:
            failures.append(f"{args.model} materialized={config.get('materialized')}, expected {args.materialized}")
        if args.unique_key and args.unique_key not in _unique_key(config):
            failures.append(f"{args.model} unique_key={config.get('unique_key')}, expected {args.unique_key}")
        if args.incremental_strategy and config.get("incremental_strategy") != args.incremental_strategy:
            failures.append(
                f"{args.model} incremental_strategy={config.get('incremental_strategy')}, "
                f"expected {args.incremental_strategy}"
            )
        for spec in args.config:
            key, _, value = spec.partition("=")
            if str(config.get(key)).lower() != value.lower():
                failures.append(f"{args.model} config.{key}={config.get(key)}, expected {value}")
        tests = _tests_for(manifest, model["unique_id"])
        names = {_test_name(t) for t in tests}
        failures += [f"{args.model} has no {t} test" for t in args.has_test if t not in names]
        for spec in args.column_test:
            col, _, test = spec.partition(":")
            if not any(_test_name(t) == test and t.get("column_name") == col for t in tests):
                failures.append(f"{args.model}.{col} has no {test} test")
        deps = [d.rsplit(".", 1)[-1] for d in (model.get("depends_on") or {}).get("nodes", [])]
        failures += [f"{args.model} does not depend on {d}" for d in args.depends_on if d not in deps]
    return finish(failures)


if __name__ == "__main__":
    run(main)
