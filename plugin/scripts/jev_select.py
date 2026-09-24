#!/usr/bin/env python3
"""JEV agent selection — pick the phase variant and specialists from a spec.

Asks TypeSafe's JEV decision model (via OpenRouter) two typed questions about
a spec summary: which variant a phase should run (``single`` or
``multiagent``) and which pre-filtered specialists materially matter. When JEV
cannot decide (no key, network error, timeout, uncertain answer, bad response)
the deterministic heuristic that AgentSpec used before this script takes over.

The ``select`` mode NEVER fails the phase: it always prints a JSON result on
stdout and exits 0. The ``--eval`` mode compares JEV against the heuristic on a
labeled set of specs.

Usage:
  python3 scripts/jev_select.py < input.json
  python3 scripts/jev_select.py --input input.json
  python3 scripts/jev_select.py --eval labels.json [--json]

Input JSON:
  {"phase": "define|design", "summary": "...", "kb_domains": ["dbt", "`tailwind`", "sql/postgres"],
   "variant_locked": null | "multiagent"}
  kb_domains may be copied verbatim from the spec; they are normalized to KB names.

Environment:
  OPENROUTER_API_KEY   Key used for the JEV call (same key as the Judge Layer)
  JEV_API_KEY          Optional; takes precedence over OPENROUTER_API_KEY
  JEV_URL              Default: https://openrouter.ai/api/alpha/decisions
  JEV_MODEL            Default: typesafe/jev-1.13
  JEV_SINGLE_THRESHOLD Default: 0.5  (p(single) at or above → single variant)
  JEV_UNCERTAIN_BAND   Default: 0.1  (|p(single) - threshold| below this → fallback)
  JEV_FIT_THRESHOLD    Default: 0.5  (specialist Noul gate)
  JEV_TIMEOUT_MS       Default: 4000 (total wall-clock budget for the call)
  JEV_DISABLE          Set to 1 to never send the spec anywhere (always fallback)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import threading
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent

DEFAULT_URL = "https://openrouter.ai/api/alpha/decisions"
DEFAULT_MODEL = "typesafe/jev-1.13"
DEFAULT_SINGLE_THRESHOLD = 0.5
DEFAULT_UNCERTAIN_BAND = 0.1
DEFAULT_FIT_THRESHOLD = 0.5
DEFAULT_TIMEOUT_MS = 4000

SUMMARY_MAX_CHARS = 4000
MAX_CANDIDATES = 12
MAX_SPECIALISTS = 4
MULTIAGENT_DOMAIN_THRESHOLD = 3

VARIANTS: frozenset[str] = frozenset({"single", "multiagent"})
PHASES: frozenset[str] = frozenset({"define", "design"})
EXCLUDED_CATEGORIES: frozenset[str] = frozenset({"workflow"})
# General implementers the overlap pre-filter tends to hide; JEV still decides whether they fit.
ALWAYS_CANDIDATES: tuple[str, ...] = ("python-developer", "react-developer")

# Free-text domain spellings seen in real specs → KB domain names.
KB_ALIASES: dict[str, str] = {
    "tailwind": "tailwind-css", "css": "tailwind-css", "a11y": "accessibility",
    "sql": "sql-patterns", "postgres": "sql-patterns", "postgresql": "sql-patterns",
    "fastapi": "python", "pytest": "testing", "tests": "testing",
    "llm": "genai", "rag": "genai", "agents": "genai", "agent-orchestration": "genai", "llm-eval": "genai",
    "prompts": "prompt-engineering", "prompting": "prompt-engineering",
    "databricks": "lakeflow", "dlt": "lakeflow", "iac": "terraform",
    "frontend": "frontend-patterns", "typescript": "frontend-patterns", "dataviz": "frontend-patterns",
    "next.js": "nextjs", "next": "nextjs", "reactjs": "react",
    "modelagem de dados": "data-modeling", "data modeling": "data-modeling",
}
_DOMAIN_SPLIT = re.compile(r"[,/;|]|\s+e\s+|\s+and\s+")

ROUTING_CANDIDATES: tuple[Path, ...] = (
    SCRIPT_DIR.parent / ".claude" / "skills" / "agent-router" / "routing.json",  # source repo
    SCRIPT_DIR.parent / "skills" / "agent-router" / "routing.json",              # installed plugin
)


# ── Typed values ─────────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class Settings:
    """Runtime knobs, resolved once from the environment."""

    api_key: str | None
    url: str
    model: str
    single_threshold: float
    uncertain_band: float
    fit_threshold: float
    timeout_s: float
    disabled: bool

    @classmethod
    def from_env(cls, env: Mapping[str, str]) -> Settings:
        return cls(
            api_key=env.get("JEV_API_KEY") or env.get("OPENROUTER_API_KEY") or None,
            url=env.get("JEV_URL") or DEFAULT_URL,
            model=env.get("JEV_MODEL") or DEFAULT_MODEL,
            single_threshold=_env_float(env, "JEV_SINGLE_THRESHOLD", DEFAULT_SINGLE_THRESHOLD),
            uncertain_band=_env_float(env, "JEV_UNCERTAIN_BAND", DEFAULT_UNCERTAIN_BAND),
            fit_threshold=_env_float(env, "JEV_FIT_THRESHOLD", DEFAULT_FIT_THRESHOLD),
            timeout_s=_env_float(env, "JEV_TIMEOUT_MS", DEFAULT_TIMEOUT_MS) / 1000.0,
            disabled=env.get("JEV_DISABLE", "").strip() in {"1", "true", "yes"},
        )


@dataclass(frozen=True, slots=True)
class Candidate:
    name: str
    category: str
    description: str
    kb_domains: tuple[str, ...]
    overlap: int


@dataclass(frozen=True, slots=True)
class SelectionInput:
    phase: str
    summary: str
    kb_domains: tuple[str, ...]
    variant_locked: str | None = None


@dataclass(frozen=True, slots=True)
class Decision:
    """One gated decision. ``value`` is a variant name or a tuple of agent names."""

    value: str | tuple[str, ...]
    source: str                          # "jev" | "fallback" | "locked"
    fallback_reason: str | None = None
    confidence: float | None = None
    probabilities: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        value = list(self.value) if isinstance(self.value, tuple) else self.value
        return {
            "value": value,
            "source": self.source,
            "fallback_reason": self.fallback_reason,
            "confidence": self.confidence,
            "probabilities": self.probabilities,
        }


class TransportError(RuntimeError):
    """Raised by ``post_decisions`` with a short, loggable reason code."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


Transport = Callable[[dict[str, object], Settings], dict[str, object]]


def _env_float(env: Mapping[str, str], key: str, default: float) -> float:
    try:
        return float(env[key])
    except (KeyError, ValueError):
        return default


# ── Catalog + deterministic heuristic ────────────────────────────────────────

def resolve_routing_path(explicit: str | None = None) -> Path | None:
    candidates = (Path(explicit).expanduser(),) if explicit else ROUTING_CANDIDATES
    return next((p for p in candidates if p.is_file()), None)


def load_routing(path: Path | None) -> list[dict[str, object]]:
    if path is None:
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    agents = data.get("agents", []) if isinstance(data, dict) else []
    return [a for a in agents if isinstance(a, dict) and a.get("name")]


def normalize_domains(domains: Iterable[object]) -> tuple[str, ...]:
    seen: dict[str, None] = {}
    for d in domains:
        key = str(d).strip().lower()
        if key:
            seen.setdefault(key, None)
    return tuple(seen)


def known_domains(agents: Iterable[Mapping[str, object]]) -> frozenset[str]:
    return frozenset(d for a in agents for d in normalize_domains(a.get("kb_domains") or ()))


def normalize_kb_domains(raw: Iterable[str], known: frozenset[str]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Map free-text domain mentions to KB names; return (kept, dropped).

    Handles backticks, parenthetical notes and compound entries such as
    ``frontend/nextjs`` or ``genai (rag, guardrails)``. With an empty ``known``
    set (no routing.json) every normalized token is kept.
    """
    kept: dict[str, None] = {}
    dropped: dict[str, None] = {}
    for entry in raw:
        text = re.sub(r"\([^)]*\)", " ", str(entry).replace("`", " "))
        for token in _DOMAIN_SPLIT.split(text.lower()):
            name = token.strip(" .:-")
            if not name:
                continue
            name = KB_ALIASES.get(name, name)
            if not known or name in known:
                kept.setdefault(name, None)
            else:
                dropped.setdefault(name, None)
    return tuple(kept), tuple(d for d in dropped if d not in kept)


def prefilter_candidates(
    agents: Iterable[Mapping[str, object]],
    domains: Iterable[str],
    limit: int = MAX_CANDIDATES,
) -> list[Candidate]:
    """Agents sharing at least one KB domain with the spec, best overlap first."""
    wanted = set(domains)
    found: list[Candidate] = []
    for agent in agents:
        category = str(agent.get("category", ""))
        if category in EXCLUDED_CATEGORIES:
            continue
        agent_domains = normalize_domains(agent.get("kb_domains") or ())
        overlap = len(wanted.intersection(agent_domains))
        if overlap == 0:
            continue
        found.append(Candidate(
            name=str(agent["name"]),
            category=category,
            description=str(agent.get("description", "")).strip(),
            kb_domains=agent_domains,
            overlap=overlap,
        ))
    found.sort(key=lambda c: (-c.overlap, c.name))
    return found[:limit]


def with_always_candidates(
    agents: Iterable[Mapping[str, object]],
    overlap: list[Candidate],
    domains: Iterable[str],
    limit: int = MAX_CANDIDATES,
) -> list[Candidate]:
    """Overlap candidates plus ALWAYS_CANDIDATES, still within ``limit``."""
    present = {c.name for c in overlap}
    wanted = set(domains)
    extra: list[Candidate] = []
    for agent in agents:
        name = str(agent.get("name"))
        if name in ALWAYS_CANDIDATES and name not in present:
            agent_domains = normalize_domains(agent.get("kb_domains") or ())
            extra.append(Candidate(
                name=name,
                category=str(agent.get("category", "")),
                description=str(agent.get("description", "")).strip(),
                kb_domains=agent_domains,
                overlap=len(wanted.intersection(agent_domains)),
            ))
    extra.sort(key=lambda c: ALWAYS_CANDIDATES.index(c.name))
    return overlap[: max(limit - len(extra), 0)] + extra


def heuristic(domains: tuple[str, ...], candidates: list[Candidate]) -> tuple[str, tuple[str, ...]]:
    """The pre-JEV rule: 3+ domains → multiagent; top 4 by kb_domains overlap."""
    variant = "multiagent" if len(domains) >= MULTIAGENT_DOMAIN_THRESHOLD else "single"
    return variant, tuple(c.name for c in candidates[:MAX_SPECIALISTS])


# ── JEV request / response ───────────────────────────────────────────────────

def build_request(inp: SelectionInput, candidates: list[Candidate], model: str) -> dict[str, object]:
    """State carries only the phase and the spec summary; every instruction lives in a question.

    KB domains stay out of the state: listing 3+ domains next to the variant
    question made JEV answer "multiagent" for every spec (literal reading).
    """
    questions: dict[str, object] = {}
    if inp.variant_locked is None:
        questions["single_area"] = {
            "type": "noul",
            "instructions": (
                "Is the implementation work in this spec confined to ONE technical area "
                "(for example: only frontend screens with mock data, only infrastructure or "
                "configuration changes, only a written document)?"
            ),
            "criteria": {
                "true": "One area does all the real work; other technologies are mocked, unchanged or only mentioned",
                "false": "Two or more areas (for example frontend AND backend/database AND AI) each need real new implementation",
            },
        }
    for i, cand in enumerate(candidates):
        questions[f"fit_{i}"] = {
            "type": "noul",
            "instructions": (
                f"Would the specialist '{cand.name}' ({cand.description}) materially "
                f"change the quality of the {inp.phase} phase for this spec?"
            ),
            "criteria": {
                "true": "The spec needs this specialist's domain expertise to avoid mistakes",
                "false": "The domain is absent, incidental, or already covered by another specialist",
            },
        }
    return {
        "model": model,
        "state": {
            "phase": inp.phase,
            "spec_summary": inp.summary[:SUMMARY_MAX_CHARS],
        },
        "questions": questions,
    }


def post_decisions(payload: dict[str, object], settings: Settings) -> dict[str, object]:
    """The only function that touches the network.

    Runs the request on a daemon thread so the wall-clock budget holds even
    when DNS/connect/read each stall (urllib's timeout is per socket op). An
    abandoned request dies with the process instead of delaying exit.
    """
    box: dict[str, object] = {}

    def _run() -> None:
        req = urllib.request.Request(
            settings.url,
            data=json.dumps(payload).encode(),
            method="POST",
            headers={
                "Authorization": f"Bearer {settings.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/marcoleloam/agentspec",
                "X-Title": "AgentSpec JEV Agent Selection",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=settings.timeout_s) as resp:
                box["raw"] = resp.read().decode()
        except urllib.error.HTTPError as e:
            box["error"] = f"http_{e.code}"
        except TimeoutError:
            box["error"] = "timeout"
        except urllib.error.URLError as e:
            box["error"] = "timeout" if isinstance(e.reason, TimeoutError) else "network"
        except OSError:
            box["error"] = "network"

    worker = threading.Thread(target=_run, daemon=True)
    worker.start()
    worker.join(settings.timeout_s)
    if worker.is_alive():
        raise TransportError("timeout")
    if "error" in box:
        raise TransportError(str(box["error"]))
    try:
        parsed = json.loads(str(box.get("raw", "")))
    except json.JSONDecodeError as e:
        raise TransportError("invalid_response") from e
    if not isinstance(parsed, dict):
        raise TransportError("invalid_response")
    return parsed


def noul_value(answer: object) -> float | None:
    if not isinstance(answer, Mapping):
        return None
    value = answer.get("noul")
    if not _is_number(value):
        return None
    number = float(value)
    return number if 0.0 <= number <= 1.0 else None


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


# ── Gates ────────────────────────────────────────────────────────────────────

def gate_variant(answer: object, fallback_variant: str, threshold: float, band: float) -> Decision:
    """p(single) decides the variant; answers too close to the threshold fall back."""
    p = noul_value(answer)
    if p is None:
        return Decision(fallback_variant, "fallback", "invalid_response")
    distance = round(abs(p - threshold), 9)   # rounding keeps the band open: 0.6 is not "uncertain"
    probabilities = {"single": p, "multiagent": round(1.0 - p, 6)}
    confidence = round(min(distance * 2, 1.0), 6)
    if distance < band:
        return Decision(fallback_variant, "fallback", "uncertain", confidence, probabilities)
    return Decision("single" if p >= threshold else "multiagent", "jev", None, confidence, probabilities)


def gate_specialists(
    answers: Mapping[str, object],
    candidates: list[Candidate],
    fallback_specialists: tuple[str, ...],
    fit_threshold: float,
) -> Decision:
    nouls: dict[str, float] = {}
    for i, cand in enumerate(candidates):
        value = noul_value(answers.get(f"fit_{i}"))
        if value is not None:
            nouls[cand.name] = value
    if not nouls:
        return Decision(fallback_specialists, "fallback", "invalid_response")
    fit = sorted(((n, p) for n, p in nouls.items() if p >= fit_threshold), key=lambda t: (-t[1], t[0]))
    if not fit:
        return Decision(fallback_specialists, "fallback", "no_fit_above_threshold", probabilities=nouls)
    return Decision(tuple(n for n, _ in fit[:MAX_SPECIALISTS]), "jev", probabilities=nouls)


# ── Selection ────────────────────────────────────────────────────────────────

def parse_input(raw: str) -> SelectionInput:
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise TypeError("input must be a JSON object")
    phase = str(data.get("phase", "")).strip().lower()
    if phase not in PHASES:
        raise ValueError(f"phase must be one of {sorted(PHASES)}")
    locked = data.get("variant_locked")
    if locked is not None and locked not in VARIANTS:
        raise ValueError(f"variant_locked must be null or one of {sorted(VARIANTS)}")
    domains = data.get("kb_domains") or []
    if not isinstance(domains, list):
        raise TypeError("kb_domains must be a list")
    return SelectionInput(
        phase=phase,
        summary=str(data.get("summary", ""))[:SUMMARY_MAX_CHARS],
        kb_domains=normalize_domains(domains),
        variant_locked=locked,
    )


def select(
    inp: SelectionInput,
    settings: Settings,
    agents: list[dict[str, object]],
    transport: Transport = post_decisions,
    routing_found: bool = True,
) -> dict[str, object]:
    domains, dropped = normalize_kb_domains(inp.kb_domains, known_domains(agents))
    overlap = prefilter_candidates(agents, domains)
    candidates = with_always_candidates(agents, overlap, domains)
    h_variant, h_specialists = heuristic(domains, overlap)

    locked = inp.variant_locked is not None
    if not candidates:
        no_cand_reason = "no_routing" if not routing_found else "no_candidates"
    else:
        no_cand_reason = None

    answers: Mapping[str, object] = {}
    transport_reason: str | None = None
    latency_ms: int | None = None
    usage: object = None

    needs_call = not locked or bool(candidates)
    if settings.disabled:
        transport_reason = "disabled"
    elif not settings.api_key:
        transport_reason = "missing_key"
    elif needs_call:
        started = time.monotonic()
        try:
            response = transport(build_request(inp, candidates, settings.model), settings)
            raw_answers = response.get("answers")
            if isinstance(raw_answers, Mapping):
                answers = raw_answers
                usage = response.get("usage")
            else:
                transport_reason = "invalid_response"
        except TransportError as err:
            transport_reason = err.reason
        latency_ms = int((time.monotonic() - started) * 1000)

    if locked:
        variant = Decision(str(inp.variant_locked), "locked")
    elif transport_reason:
        variant = Decision(h_variant, "fallback", transport_reason)
    else:
        variant = gate_variant(answers.get("single_area"), h_variant,
                               settings.single_threshold, settings.uncertain_band)

    if no_cand_reason:
        specialists = Decision((), "fallback", no_cand_reason)
    elif transport_reason:
        specialists = Decision(h_specialists, "fallback", transport_reason)
    else:
        specialists = gate_specialists(answers, candidates, h_specialists, settings.fit_threshold)

    primary = specialists if locked else variant
    first_reason = variant.fallback_reason or specialists.fallback_reason
    return {
        "version": 1,
        "phase": inp.phase,
        "source": primary.source,
        "fallback_reason": first_reason,
        "model": settings.model,
        "latency_ms": latency_ms,
        "kb_domains": list(domains),
        "kb_domains_dropped": list(dropped),
        "variant": variant.to_dict(),
        "specialists": {**specialists.to_dict(), "applies": variant.value == "multiagent"},
        "candidates": [{"name": c.name, "overlap": c.overlap} for c in candidates],
        "heuristic": {"variant": h_variant, "specialists": list(h_specialists)},
        "usage": usage,
    }


def fallback_result(reason: str) -> dict[str, object]:
    """Result for unusable input: nothing to decide on, but the phase must not break."""
    empty = Decision((), "fallback", reason)
    return {
        "version": 1,
        "phase": None,
        "source": "fallback",
        "fallback_reason": reason,
        "model": None,
        "latency_ms": None,
        "kb_domains": [],
        "kb_domains_dropped": [],
        "variant": Decision("single", "fallback", reason).to_dict(),
        "specialists": {**empty.to_dict(), "applies": False},
        "candidates": [],
        "heuristic": {"variant": "single", "specialists": []},
        "usage": None,
    }


# ── Offline evaluation ───────────────────────────────────────────────────────

def f1(predicted: Iterable[str], expected: Iterable[str]) -> float:
    pred, exp = set(predicted), set(expected)
    if not pred and not exp:
        return 1.0
    hit = len(pred & exp)
    if hit == 0:
        return 0.0
    precision, recall = hit / len(pred), hit / len(exp)
    return 2 * precision * recall / (precision + recall)


def load_labels(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    cases = data.get("cases") if isinstance(data, dict) else None
    if not isinstance(cases, list) or not cases:
        raise ValueError("labels file must contain a non-empty 'cases' list")
    for case in cases:
        if not isinstance(case, dict):
            raise TypeError("every case must be an object")
        missing = {"id", "phase", "summary", "kb_domains", "expected_variant", "expected_specialists"} - case.keys()
        if missing:
            raise ValueError(f"case {case.get('id', '?')} is missing {sorted(missing)}")
        if case["expected_variant"] not in VARIANTS:
            raise ValueError(f"case {case['id']}: expected_variant must be one of {sorted(VARIANTS)}")
    return cases


def run_eval(
    cases: list[dict[str, Any]],
    settings: Settings,
    agents: list[dict[str, object]],
    transport: Transport = post_decisions,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for case in cases:
        inp = parse_input(json.dumps({
            "phase": case["phase"], "summary": case["summary"], "kb_domains": case["kb_domains"],
        }))
        result: dict[str, Any] = select(inp, settings, agents, transport)
        expected_specs = [str(s) for s in case["expected_specialists"]]
        rows.append({
            "id": case["id"],
            "expected_variant": case["expected_variant"],
            "system_variant": result["variant"]["value"],
            "system_confidence": result["variant"]["confidence"],
            "p_single": result["variant"]["probabilities"].get("single"),
            "heuristic_variant": result["heuristic"]["variant"],
            "system_specialists": result["specialists"]["value"],
            "heuristic_specialists": result["heuristic"]["specialists"],
            "expected_specialists": expected_specs,
            "source": result["source"],
            "fallback_reason": result["fallback_reason"],
        })

    def accuracy(key: str) -> float:
        return sum(r[key] == r["expected_variant"] for r in rows) / len(rows)

    multi = [r for r in rows if r["expected_variant"] == "multiagent"]

    def mean_f1(key: str) -> float | None:
        if not multi:
            return None
        return sum(f1(r[key], r["expected_specialists"]) for r in multi) / len(multi)

    fallbacks: dict[str, int] = {}
    for r in rows:
        if r["fallback_reason"]:
            reason = str(r["fallback_reason"])
            fallbacks[reason] = fallbacks.get(reason, 0) + 1

    system_acc, heuristic_acc = accuracy("system_variant"), accuracy("heuristic_variant")
    system_f1, heuristic_f1 = mean_f1("system_specialists"), mean_f1("heuristic_specialists")
    variant_ok = system_acc >= 0.85 and system_acc >= heuristic_acc + 0.10
    specialists_ok = (
        system_f1 is not None and heuristic_f1 is not None and system_f1 >= heuristic_f1 + 0.10
    )
    return {
        "cases": len(rows),
        "multiagent_cases": len(multi),
        "variant_accuracy": {"system": system_acc, "heuristic": heuristic_acc},
        "specialists_f1": {"system": system_f1, "heuristic": heuristic_f1},
        "fallbacks": fallbacks,
        "success": {"variant": variant_ok, "specialists": specialists_ok},
        "rows": rows,
    }


def render_eval(report: Mapping[str, Any]) -> str:
    acc, f1s, ok = report["variant_accuracy"], report["specialists_f1"], report["success"]

    def num(value: float | None) -> str:
        return "n/a" if value is None else f"{value:.2f}"

    variant_verdict = "PASS" if ok["variant"] else "FAIL"
    specialists_verdict = "PASS" if ok["specialists"] else "FAIL"
    lines = [
        f"cases: {report['cases']}  (multiagent: {report['multiagent_cases']})",
        (
            f"variant accuracy   system={num(acc['system'])}  heuristic={num(acc['heuristic'])}  "
            f"-> {variant_verdict} (>= 0.85 and >= heuristic + 0.10)"
        ),
        (
            f"specialists F1     system={num(f1s['system'])}  heuristic={num(f1s['heuristic'])}  "
            f"-> {specialists_verdict} (>= heuristic + 0.10)"
        ),
        f"fallbacks: {json.dumps(report['fallbacks'], sort_keys=True)}",
    ]
    for row in report["rows"]:
        mark = "ok " if row["system_variant"] == row["expected_variant"] else "ERR"
        lines.append(
            f"  [{mark}] {row['id']}: expected={row['expected_variant']} "
            f"system={row['system_variant']} (p_single={num(row['p_single'])}) "
            f"heuristic={row['heuristic_variant']} source={row['source']}"
        )
    return "\n".join(lines)


# ── CLI ──────────────────────────────────────────────────────────────────────

def _log(result: Mapping[str, object]) -> None:
    print(
        f"[jev_select] source={result['source']} reason={result['fallback_reason']} "
        f"latency_ms={result['latency_ms']}",
        file=sys.stderr,
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="JEV agent selection (variant + specialists)")
    ap.add_argument("--input", help="Input JSON file (default: stdin)")
    ap.add_argument("--routing", help="Path to routing.json (default: auto-detect repo/plugin layout)")
    ap.add_argument("--eval", dest="eval_path", help="Labels JSON: compare JEV against the heuristic")
    ap.add_argument("--json", action="store_true", help="With --eval, print the full report as JSON")
    args = ap.parse_args(argv)

    settings = Settings.from_env(os.environ)
    routing_path = resolve_routing_path(args.routing)
    agents = load_routing(routing_path)

    if args.eval_path:
        try:
            cases = load_labels(Path(args.eval_path).expanduser())
        except (OSError, ValueError, TypeError) as err:
            print(f"[ERROR] invalid labels file: {err}", file=sys.stderr)
            return 2
        report = run_eval(cases, settings, agents)
        print(json.dumps(report, indent=2) if args.json else render_eval(report))
        return 0

    try:
        raw = Path(args.input).read_text(encoding="utf-8") if args.input else sys.stdin.read()
        inp = parse_input(raw)
    except (OSError, ValueError, TypeError):
        result = fallback_result("invalid_input")
    else:
        result = select(inp, settings, agents, routing_found=routing_path is not None and bool(agents))
    _log(result)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
