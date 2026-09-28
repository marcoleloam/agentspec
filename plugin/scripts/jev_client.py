#!/usr/bin/env python3
"""JEV client — typed decisions from TypeSafe's Jev model via OpenRouter.

Jev is a "System One" model: it does not generate text. It answers typed
questions (``noul`` = yes/no probability, ``score`` = ordered rubric level)
about a ``state``. The eval runner uses it to grade subjective criteria.

This module is stdlib-only and network access is injectable (``opener``) so
the whole surface is testable offline.

Endpoints (both verified live on 2026-09-23, same response schema):
  primary   https://openrouter.ai/api/v1/systemone
  fallback  https://openrouter.ai/api/alpha/decisions

Environment:
  OPENROUTER_API_KEY   Required for live calls.
  JEV_MODEL            Optional. Default: typesafe/jev-1.13
  JEV_BUDGET           Optional. Max Jev calls per UTC day. Default: 200
                       (a non-integer value falls back to the default; a
                       negative one means no calls)
"""
from __future__ import annotations

import datetime as dt
import json
import os
import socket
import threading
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

DEFAULT_MODEL = "typesafe/jev-1.13"
ENDPOINTS: tuple[str, ...] = (
    "https://openrouter.ai/api/v1/systemone",
    "https://openrouter.ai/api/alpha/decisions",
)
DEFAULT_BUDGET = 200
MAX_STATE_CHARS = 96_000
TRUNCATION_MARKER = "…[truncated]"
MODEL_PREFIX = "typesafe/"

QuestionType = Literal["noul", "score"]


class JevError(RuntimeError):
    """Typed failure. ``code`` is one of AUTH, BAD_REQUEST, NOT_FOUND,
    UNAVAILABLE, BUDGET, CONFIG, PARSE."""

    def __init__(self, message: str, code: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class Question:
    id: str
    type: QuestionType
    instructions: str
    criteria: tuple[str, ...] = ()

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"type": self.type, "instructions": self.instructions}
        if self.type == "score":
            payload["criteria"] = list(self.criteria)
        return payload


@dataclass(frozen=True, slots=True)
class Answer:
    id: str
    type: str
    noul: float | None = None
    score: float | None = None
    probabilities: dict[str, float] | None = None
    confidence: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in (
            ("type", self.type),
            ("noul", self.noul),
            ("score", self.score),
            ("probabilities", self.probabilities),
            ("confidence", self.confidence),
        ) if v is not None}


@dataclass(frozen=True, slots=True)
class DecisionResult:
    model: str
    answers: dict[str, Answer]
    cost_usd: float | None = None
    request_id: str | None = None
    truncated: bool = False
    endpoint: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


# ── Request building ────────────────────────────────────────────────────────

def truncate_state(state: Mapping[str, str], limit: int = MAX_STATE_CHARS) -> tuple[dict[str, str], bool]:
    """Shrink every field proportionally so the total stays under ``limit``.

    Each field gets a share of ``limit`` proportional to its length; the
    marker is paid out of that share, and skipped when the share is too small
    to hold it — so truncation can never make a field (or the state) grow."""
    total = sum(len(v) for v in state.values())
    if total <= limit:
        return dict(state), False
    ratio = limit / total
    shrunk: dict[str, str] = {}
    for key, value in state.items():
        share = int(len(value) * ratio)
        if len(value) <= share:
            shrunk[key] = value
        elif share > len(TRUNCATION_MARKER):
            shrunk[key] = value[:share - len(TRUNCATION_MARKER)] + TRUNCATION_MARKER
        else:
            shrunk[key] = value[:share]
    return shrunk, True


def build_body(
    state: Mapping[str, str],
    questions: Sequence[Question],
    model: str,
    limit: int = MAX_STATE_CHARS,
) -> tuple[dict[str, Any], bool]:
    if not questions:
        raise JevError("at least one question is required", "CONFIG")
    ids = [q.id for q in questions]
    if len(set(ids)) != len(ids):
        raise JevError(f"duplicate question ids: {ids}", "CONFIG")
    shrunk, truncated = truncate_state(state, limit)
    body = {
        "model": model,
        "state": shrunk,
        "questions": {q.id: q.to_payload() for q in questions},
    }
    return body, truncated


# ── Response parsing ────────────────────────────────────────────────────────

def load_answers(raw_answers: Mapping[str, Any]) -> dict[str, Answer]:
    """Every shape problem — a ``None`` probability, a non-numeric rubric
    level, a missing field — surfaces as ``JevError(PARSE)``, never as a raw
    ``TypeError``/``ValueError`` that would escape the caller's handler."""
    answers: dict[str, Answer] = {}
    for qid, raw in raw_answers.items():
        if not isinstance(raw, Mapping) or "type" not in raw:
            raise JevError(f"malformed answer for {qid!r}: {raw!r}", "PARSE")
        try:
            answers[qid] = Answer(
                id=str(qid),
                type=str(raw["type"]),
                noul=_as_float(raw.get("noul")),
                score=_as_float(raw.get("score")),
                probabilities=_probabilities(raw.get("probabilities")),
                confidence=_as_float(raw.get("confidence")),
            )
        except (TypeError, ValueError, KeyError, AttributeError) as err:
            raise JevError(f"malformed answer for {qid!r}: {type(err).__name__}: {err}"[:300], "PARSE") from err
    return answers


def _probabilities(raw: Any) -> dict[str, float] | None:
    if raw is None:
        return None
    if not isinstance(raw, Mapping):
        raise TypeError(f"probabilities must be an object, got {type(raw).__name__}")
    parsed: dict[str, float] = {}
    for level, value in raw.items():
        int(str(level))  # rubric levels are ordinal indices; the classifier relies on it
        if value is None or isinstance(value, bool):
            raise TypeError(f"probability for level {level!r} is {value!r}")
        parsed[str(level)] = float(value)
    return parsed


def parse_response(payload: Mapping[str, Any], truncated: bool = False, endpoint: str | None = None) -> DecisionResult:
    if "answers" not in payload or not isinstance(payload["answers"], Mapping):
        raise JevError(f"response has no answers: {str(payload)[:300]}", "PARSE")
    usage = payload.get("usage") if isinstance(payload.get("usage"), Mapping) else {}
    return DecisionResult(
        model=str(payload.get("model", "")),
        answers=load_answers(payload["answers"]),
        cost_usd=_as_float(usage.get("cost")),
        request_id=payload.get("id"),
        truncated=truncated,
        endpoint=endpoint,
    )


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# ── Transport ───────────────────────────────────────────────────────────────

def _post(url: str, body: Mapping[str, Any], api_key: str, timeout: float, opener: Callable[..., Any]) -> dict[str, Any]:
    """POST with a wall-clock ceiling of ``timeout`` seconds.

    urllib's ``timeout`` applies per socket operation, so a slow DNS lookup,
    connect and trickling read can each take ``timeout``. The request runs on a
    daemon thread and is abandoned (``UNAVAILABLE``) once the ceiling passes,
    the same approach as ``jev_select.post_decisions``."""
    box: dict[str, Any] = {}

    def _run() -> None:
        try:
            box["value"] = _post_blocking(url, body, api_key, timeout, opener)
        except BaseException as err:  # re-raised on the caller's thread
            box["error"] = err

    worker = threading.Thread(target=_run, name="jev-post", daemon=True)
    worker.start()
    worker.join(timeout)
    if worker.is_alive():
        raise JevError(f"wall-clock timeout ({timeout:g}s) calling {url}", "UNAVAILABLE")
    if "error" in box:
        raise box["error"]
    return box["value"]


def _post_blocking(url: str, body: Mapping[str, Any], api_key: str, timeout: float, opener: Callable[..., Any]) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/marcoleloam/agentspec",
            "X-Title": "AgentSpec Eval Runner",
        },
        method="POST",
    )
    try:
        with opener(request, timeout=timeout) as response:
            raw = response.read().decode()
    except urllib.error.HTTPError as err:
        detail = (err.read().decode(errors="replace") if err.fp else "")[:300]
        raise JevError(f"HTTP {err.code} from {url}: {detail}", _code_for_status(err.code)) from err
    except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError) as err:
        raise JevError(f"network error calling {url}: {err}", "UNAVAILABLE") from err
    try:
        decoded = json.loads(raw)
    except json.JSONDecodeError as err:
        raise JevError(f"non-JSON response from {url}: {raw[:200]}", "PARSE") from err
    if not isinstance(decoded, dict):
        raise JevError(f"unexpected response shape from {url}: {raw[:200]}", "PARSE")
    return decoded


def _code_for_status(status: int) -> str:
    if status in (401, 403):
        return "AUTH"
    if status == 404:
        return "NOT_FOUND"
    if status == 429 or status >= 500:
        return "UNAVAILABLE"
    return "BAD_REQUEST"


def decide(
    state: Mapping[str, str],
    questions: Sequence[Question],
    *,
    api_key: str,
    model: str = DEFAULT_MODEL,
    endpoints: Sequence[str] = ENDPOINTS,
    timeout: float = 30.0,
    opener: Callable[..., Any] = urllib.request.urlopen,
) -> DecisionResult:
    """Ask Jev ``questions`` about ``state``; fall back across ``endpoints``
    only on NOT_FOUND / UNAVAILABLE."""
    if not api_key:
        raise JevError("OPENROUTER_API_KEY not set", "CONFIG")
    body, truncated = build_body(state, questions, model)
    last_error: JevError | None = None
    for url in endpoints:
        try:
            return parse_response(_post(url, body, api_key, timeout, opener), truncated, url)
        except JevError as err:
            if err.code not in {"NOT_FOUND", "UNAVAILABLE"}:
                raise
            last_error = err
    raise last_error or JevError("no endpoint configured", "CONFIG")


# ── Ledger (same row schema as scripts/judge.py) ────────────────────────────

def today_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")


def jev_calls_today(ledger: Path) -> int:
    if not ledger.exists():
        return 0
    today = today_utc()
    count = 0
    for line in ledger.read_text(encoding="utf-8").splitlines():
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if row.get("date") == today and str(row.get("model", "")).startswith(MODEL_PREFIX):
            count += 1
    return count


def configured_budget() -> int:
    raw = os.environ.get("JEV_BUDGET", "").strip()
    if not raw:
        return DEFAULT_BUDGET
    try:
        return int(raw)
    except ValueError:
        return DEFAULT_BUDGET


def budget_remaining(ledger: Path, budget: int | None = None) -> int:
    limit = budget if budget is not None else configured_budget()
    return max(0, limit - jev_calls_today(ledger))


def append_ledger(ledger: Path, model: str, target: str, verdict: str, cost_usd: float | None) -> None:
    ledger.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "date": today_utc(),
        "ts": dt.datetime.now(dt.timezone.utc).isoformat(),
        "model": model,
        "target": target,
        "verdict": verdict,
        "cost_usd": cost_usd,
    }
    with ledger.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row) + "\n")
