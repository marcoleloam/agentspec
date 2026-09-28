#!/usr/bin/env python3
"""LLM baseline for JEV agent selection — same cases, same inputs, a coding-agent CLI decides.

Asks a subscription-backed coding-agent CLI (Codex or Claude Code, headless,
structured output) the question jev_select.py asks JEV: which variant a phase
should run and which specialists matter. The model sees exactly what JEV sees —
phase, spec summary and the wide specialist pool — and nothing else. The rubric
text comes from .claude/sdd/architecture/AGENT_SELECTION_RUBRIC.md, the same
block the phase commands apply.

Label isolation does not rely on the prompt's "do not read files":

* codex — ``--ignore-user-config`` plus a permission profile (``-c
  permissions.agentsel.filesystem=…``, ``-c default_permissions="agentsel"``)
  that reads the disk but denies (``none``) the repo, the label files' folders
  and the agent transcripts that quote the labels (``~/.claude``,
  ``~/.codex/sessions``, ``~/.omp``, ``~/.grok``) to every shell command.
* claude — ``claude -p`` with no tools at all (``--tools ""``), no MCP
  (``--strict-mcp-config``), no user/project settings, plugins or hooks
  (``--setting-sources local``), no slash commands and no session on disk.

Both run in the scratch directory with stdin closed.

Usage:
  python3 scripts/eval_llm_baseline.py --provider codex --labels a.json b.json
  python3 scripts/eval_llm_baseline.py --provider claude --labels a.json --scratch /tmp/run2 --workers 4

Answers are cached per case in the scratch dir (``<provider>.jsonl``) so an
interrupted run resumes instead of re-asking. Override the binaries with
AGENTSPEC_BASELINE_CODEX / AGENTSPEC_BASELINE_CLAUDE.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from dataclasses import dataclass, field
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
REPO_ROOT = Path(__file__).resolve().parent.parent
CODEX_BIN = os.environ.get("AGENTSPEC_BASELINE_CODEX", "codex")
CLAUDE_BIN = os.environ.get("AGENTSPEC_BASELINE_CLAUDE", "claude")
PERMISSION_PROFILE = "agentsel"
# Transcripts and caches that quote the labels (the build agent that wrote them was Claude).
DEFAULT_DENY = ("~/.claude", "~/.codex/sessions", "~/.omp", "~/.grok")
# Env that would make a nested `claude -p` think it runs inside the caller's session.
_NESTED_ENV = ("CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT", "CLAUDE_CODE_SSE_PORT")


@dataclass(frozen=True)
class Options:
    deny: tuple[Path, ...] = ()
    model: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


RUBRIC_CANDIDATES: tuple[Path, ...] = (
    REPO_ROOT / ".claude" / "sdd" / "architecture" / "AGENT_SELECTION_RUBRIC.md",
    REPO_ROOT / "sdd" / "architecture" / "AGENT_SELECTION_RUBRIC.md",
)


def load_rubric() -> str:
    """The rubric block shipped to the phase commands — the exact text that gets measured."""
    path = next(p for p in RUBRIC_CANDIDATES if p.is_file())
    text = path.read_text(encoding="utf-8")
    start, end = text.index("<!-- rubric:start -->\n"), text.index("\n<!-- rubric:end -->")
    return text[start + len("<!-- rubric:start -->\n"):end]


def build_prompt(case: dict[str, Any], pool: list[js.Candidate]) -> str:
    catalog = "\n".join(f"- {c.name}: {c.description[: js.WIDE_DESCRIPTION_CHARS]}" for c in pool)
    return f"""You are choosing agents for the {case['phase']} phase of a spec-driven workflow.
Do not run commands or read files. Answer only from the text below.

{load_rubric()}

CATALOG:
{catalog}

SPEC SUMMARY:
{case['summary']}
"""


def _toml_str(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def deny_roots(label_paths: list[Path], extra: tuple[str, ...] = ()) -> tuple[Path, ...]:
    """Folders every shell command of the Codex baseline must not read."""
    roots = {REPO_ROOT.resolve()}
    roots.update(p.resolve().parent for p in label_paths)
    for raw in (*DEFAULT_DENY, *extra):
        path = Path(os.path.expanduser(raw))
        if path.exists():
            roots.add(path.resolve())
    return tuple(sorted(roots))


def codex_argv(prompt: str, scratch: Path, out: Path, opts: Options) -> list[str]:
    entries = [('":root"', '"read"'), ('":project_roots"', '{"." = "read"}')]
    entries += [(_toml_str(str(p)), '"none"') for p in opts.deny]
    policy = "{" + ", ".join(f"{k} = {v}" for k, v in entries) + "}"
    return [
        CODEX_BIN, "exec", "--ephemeral", "--skip-git-repo-check", "--ignore-user-config",
        "-C", str(scratch), *(["-m", opts.model] if opts.model else []),
        "-c", 'approval_policy="never"', "-c", 'web_search="disabled"',
        "-c", f"permissions.{PERMISSION_PROFILE}.filesystem={policy}",
        "-c", f"default_permissions={_toml_str(PERMISSION_PROFILE)}",
        "--output-schema", str(scratch / "schema.json"), "-o", str(out), "--", prompt,
    ]


def ask_codex(prompt: str, scratch: Path, opts: Options | None = None) -> dict[str, Any]:
    opts = opts or Options()
    out = scratch / f"codex-{time.monotonic_ns()}.json"
    proc = subprocess.run(
        codex_argv(prompt, scratch, out, opts),
        cwd=scratch, stdin=subprocess.DEVNULL, capture_output=True, timeout=TIMEOUT_S, check=True,
    )
    try:
        answer = json.loads(out.read_text())
        model = re.search(r"^model:\s*(\S+)", proc.stderr.decode(errors="replace"), re.MULTILINE)
        answer["_provider_model"] = model.group(1) if model else "unknown"
        return answer
    finally:
        out.unlink(missing_ok=True)


def claude_argv(prompt: str, opts: Options) -> list[str]:
    # --tools and --mcp-config are variadic: the prompt goes after "--" so they can't swallow it.
    return [
        CLAUDE_BIN, "-p", "--output-format", "json", "--json-schema", json.dumps(SCHEMA),
        "--tools", "", "--strict-mcp-config", "--mcp-config", '{"mcpServers": {}}',
        "--setting-sources", "local", "--disable-slash-commands", "--no-session-persistence",
        *(["--model", opts.model] if opts.model else []), "--", prompt,
    ]


def _claude_answer(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("is_error") or payload.get("subtype", "success") != "success":
        raise subprocess.SubprocessError(f"claude -p failed: {str(payload.get('result', payload))[:200]}")
    structured = payload.get("structured_output")
    if isinstance(structured, dict):
        return dict(structured)
    text = str(payload.get("result", "")).strip()
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    answer = json.loads(fenced.group(1) if fenced else text)
    if not isinstance(answer, dict):
        raise json.JSONDecodeError("answer is not an object", text, 0)
    return answer


def ask_claude(prompt: str, scratch: Path, opts: Options | None = None) -> dict[str, Any]:
    opts = opts or Options()
    env = {k: v for k, v in os.environ.items() if k not in _NESTED_ENV}
    proc = subprocess.run(
        claude_argv(prompt, opts), cwd=scratch, env=env, stdin=subprocess.DEVNULL,
        capture_output=True, timeout=TIMEOUT_S, check=True,
    )
    payload = json.loads(proc.stdout.decode(errors="replace"))
    answer = _claude_answer(payload)
    usage = payload.get("modelUsage")
    models = sorted(usage) if isinstance(usage, dict) else []
    answer["_provider_model"] = ",".join(models) or str(payload.get("model", "unknown"))
    return answer


PROVIDERS = {"codex": ask_codex, "claude": ask_claude}


def run_case(provider: str, case: dict[str, Any], pool: list[js.Candidate], scratch: Path,
             opts: Options | None = None) -> dict[str, Any]:
    names = {c.name for c in pool}
    started = time.monotonic()
    for attempt in (1, 2):
        try:
            answer = PROVIDERS[provider](build_prompt(case, pool), scratch, opts)
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
        "provider_model": answer.get("_provider_model", "unknown"),
        "latency_s": round(time.monotonic() - started, 1),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Coding-agent CLI baseline for JEV agent selection")
    ap.add_argument("--provider", choices=sorted(PROVIDERS), required=True)
    ap.add_argument("--labels", nargs="+", required=True, help="Labels JSON files (jev_select --eval format)")
    ap.add_argument("--scratch", default="/tmp/llm-baseline", help="Empty working dir for the CLI (and answer cache)")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--model", default=None, help="Model passed to the CLI (default: the account default)")
    ap.add_argument("--deny", action="append", default=[],
                    help="Extra folder the Codex sandbox must not read (repeatable)")
    args = ap.parse_args(argv)

    scratch = Path(args.scratch)
    label_paths = [Path(path) for path in args.labels]
    cases = [c for path in label_paths for c in js.load_labels(path)]
    opts = Options(deny=deny_roots(label_paths, tuple(args.deny)), model=args.model)
    target = scratch.resolve()
    inside = [d for d in opts.deny if target == d or d in target.parents]
    if args.provider == "codex" and inside:
        ap.error(f"--scratch {scratch} is inside a denied folder ({inside[0]}); pick a scratch dir outside it")
    scratch.mkdir(parents=True, exist_ok=True)
    (scratch / "schema.json").write_text(json.dumps(SCHEMA))
    cache_path = scratch / f"{args.provider}.jsonl"
    cached = {r["id"]: r for r in map(json.loads, cache_path.read_text().splitlines())} if cache_path.exists() else {}
    cached = {k: v for k, v in cached.items() if "error" not in v}

    pool = js.wide_pool(js.load_routing(js.resolve_routing_path()), [])
    todo = [c for c in cases if c["id"] not in cached]
    print(f"[baseline] provider={args.provider} cases={len(cases)} cached={len(cases) - len(todo)} pool={len(pool)}",
          file=sys.stderr)
    with ThreadPoolExecutor(max_workers=args.workers) as ex, cache_path.open("a") as cache:
        for row in ex.map(lambda c: run_case(args.provider, c, pool, scratch, opts), todo):
            cache.write(json.dumps(row) + "\n")
            cache.flush()
            cached[row["id"]] = row
            print(f"  {row['id']}: {row.get('variant', row.get('error'))} {row.get('specialists', '')}", file=sys.stderr)

    print(json.dumps({c["id"]: cached.get(c["id"]) for c in cases}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
