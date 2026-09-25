#!/usr/bin/env python3
"""LLM baseline for JEV agent selection — same cases, same inputs, a coding-agent CLI decides.

Asks a subscription-backed coding-agent CLI (Codex or Grok, headless, structured
output) the question jev_select.py asks JEV: which variant a phase should run and
which specialists matter. The model sees exactly what JEV sees — phase, spec
summary and the wide specialist pool — and nothing else. Runs in an empty
scratch directory so the agent cannot read the label files.

Usage:
  python3 scripts/eval_llm_baseline.py --provider codex --labels a.json b.json
  python3 scripts/eval_llm_baseline.py --provider grok  --labels a.json --workers 4

Answers are cached per case in the scratch dir (``<provider>.jsonl``) so an
interrupted run resumes instead of re-asking.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import jev_select as js

SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["variant", "specialists"],
    "properties": {
        "variant": {"type": "string", "enum": ["single", "multiagent"]},
        "specialists": {"type": "array", "maxItems": js.MAX_SPECIALISTS, "items": {"type": "string"}},
    },
}
TIMEOUT_S = 360


def build_prompt(case: dict[str, Any], pool: list[js.Candidate]) -> str:
    catalog = "\n".join(f"- {c.name}: {c.description[: js.WIDE_DESCRIPTION_CHARS]}" for c in pool)
    return f"""You are choosing agents for the {case['phase']} phase of a spec-driven workflow.
Do not run commands or read files. Answer only from the text below.

VARIANT — pick exactly one:
- single: the implementation work is confined to ONE technical area (for example: only frontend screens
  with mock data, only infrastructure or configuration changes, only a written document); other
  technologies are mocked, unchanged or only mentioned.
- multiagent: two or more areas (for example frontend AND backend/database AND AI) each need real new
  implementation.

SPECIALISTS — list up to {js.MAX_SPECIALISTS} agent names from the catalog whose expertise would materially
change the quality of this phase for this spec (list them even when the variant is single; use [] if none).
Use names exactly as written in the catalog.

CATALOG:
{catalog}

SPEC SUMMARY:
{case['summary']}
"""


def ask_codex(prompt: str, scratch: Path) -> dict[str, Any]:
    out = scratch / f"codex-{time.monotonic_ns()}.json"
    subprocess.run(
        ["codex", "exec", "--ephemeral", "--skip-git-repo-check", "-s", "read-only",
         "--output-schema", str(scratch / "schema.json"), "-o", str(out), prompt],
        cwd=scratch, stdin=subprocess.DEVNULL, capture_output=True, timeout=TIMEOUT_S, check=True,
    )
    try:
        return json.loads(out.read_text())
    finally:
        out.unlink(missing_ok=True)


def ask_grok(prompt: str, scratch: Path) -> dict[str, Any]:
    proc = subprocess.run(
        ["grok", "-p", prompt, "--json-schema", json.dumps(SCHEMA), "--permission-mode", "plan"],
        cwd=scratch, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=TIMEOUT_S, check=True,
    )
    envelope = json.loads(proc.stdout)
    if isinstance(envelope.get("structuredOutput"), dict):
        return envelope["structuredOutput"]
    # Multi-turn runs can repeat the JSON in "text"; take the first object.
    return json.JSONDecoder().raw_decode(envelope["text"].strip())[0]


PROVIDERS = {"codex": ask_codex, "grok": ask_grok}


def run_case(provider: str, case: dict[str, Any], pool: list[js.Candidate], scratch: Path) -> dict[str, Any]:
    names = {c.name for c in pool}
    started = time.monotonic()
    for attempt in (1, 2):
        try:
            answer = PROVIDERS[provider](build_prompt(case, pool), scratch)
            break
        except (subprocess.SubprocessError, json.JSONDecodeError, KeyError, OSError) as err:
            if attempt == 2:
                return {"id": case["id"], "error": type(err).__name__, "latency_s": time.monotonic() - started}
    picked = [str(n) for n in answer.get("specialists", [])]
    return {
        "id": case["id"],
        "variant": answer.get("variant"),
        "specialists": [n for n in picked if n in names][: js.MAX_SPECIALISTS],
        "unknown_names": [n for n in picked if n not in names],
        "latency_s": round(time.monotonic() - started, 1),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Codex/Grok baseline for JEV agent selection")
    ap.add_argument("--provider", choices=sorted(PROVIDERS), required=True)
    ap.add_argument("--labels", nargs="+", required=True, help="Labels JSON files (jev_select --eval format)")
    ap.add_argument("--scratch", default="/tmp/llm-baseline", help="Empty working dir for the CLI (and answer cache)")
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args(argv)

    scratch = Path(args.scratch)
    scratch.mkdir(parents=True, exist_ok=True)
    (scratch / "schema.json").write_text(json.dumps(SCHEMA))
    cache_path = scratch / f"{args.provider}.jsonl"
    cached = {r["id"]: r for r in map(json.loads, cache_path.read_text().splitlines())} if cache_path.exists() else {}
    cached = {k: v for k, v in cached.items() if "error" not in v}

    pool = js.wide_pool(js.load_routing(js.resolve_routing_path()), [])
    cases = [c for path in args.labels for c in js.load_labels(Path(path))]
    todo = [c for c in cases if c["id"] not in cached]
    print(f"[baseline] provider={args.provider} cases={len(cases)} cached={len(cases) - len(todo)} pool={len(pool)}",
          file=sys.stderr)
    with ThreadPoolExecutor(max_workers=args.workers) as ex, cache_path.open("a") as cache:
        for row in ex.map(lambda c: run_case(args.provider, c, pool, scratch), todo):
            cache.write(json.dumps(row) + "\n")
            cache.flush()
            cached[row["id"]] = row
            print(f"  {row['id']}: {row.get('variant', row.get('error'))} {row.get('specialists', '')}", file=sys.stderr)

    print(json.dumps({c["id"]: cached.get(c["id"]) for c in cases}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
