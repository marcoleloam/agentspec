"""Unit tests for scripts/jev_client.py — the Jev (TypeSafe) client.

Everything here runs offline: `opener` is injected so no test ever touches
the network. The only exception is `test_live_decide`, which is skipped
unless `OPENROUTER_API_KEY` is present in the environment.

Fixtures under tests/fixtures/evals/jev/*.json are real Jev responses
captured on 2026-09-23 (see DEFINE_POST_BUILD_EVALS.md, "Evidência do teste
do JEV"), plus one synthetic confident-fail case.
"""
from __future__ import annotations

import io
import json
import os
import urllib.error
from pathlib import Path

import pytest

import jev_client

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "evals" / "jev"


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


# ── Fake transport ───────────────────────────────────────────────────────────

class _FakeResponse:
    """Minimal stand-in for the context manager `urlopen` returns."""

    def __init__(self, payload: dict) -> None:
        self._data = json.dumps(payload).encode()

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *exc: object) -> bool:
        return False

    def read(self) -> bytes:
        return self._data


def _http_error(url: str, code: int, body: bytes = b"") -> urllib.error.HTTPError:
    return urllib.error.HTTPError(url, code, "error", None, io.BytesIO(body))


def _opener_sequence(*steps):
    """Build an opener that returns/raises ``steps`` in order, one per call.

    Each step is either a dict (successful JSON payload) or an Exception
    instance to raise. Also records the URL of every call on ``.calls``.
    """
    calls: list[str] = []

    def opener(request, timeout=None):
        calls.append(request.full_url)
        step = steps[len(calls) - 1]
        if isinstance(step, BaseException):
            raise step
        return _FakeResponse(step)

    opener.calls = calls  # type: ignore[attr-defined]
    return opener


def _question(qid: str = "consistent", qtype: str = "noul", **kw) -> jev_client.Question:
    return jev_client.Question(id=qid, type=qtype, instructions="does it hold?", **kw)


# ── build_body / truncate_state ──────────────────────────────────────────────

class TestBuildBody:
    def test_no_truncation_when_state_is_small(self):
        state = {"report": "short report", "evidence": "short evidence"}
        body, truncated = jev_client.build_body(state, [_question()], "typesafe/jev-1.13")
        assert truncated is False
        assert body["state"] == state
        assert body["model"] == "typesafe/jev-1.13"
        assert body["questions"]["consistent"]["type"] == "noul"

    def test_truncates_large_state_proportionally(self):
        state = {"a": "x" * 100_000, "b": "y" * 100_000}
        body, truncated = jev_client.build_body(state, [_question()], "typesafe/jev-1.13", limit=10_000)
        assert truncated is True
        total = sum(len(v) for v in body["state"].values())
        assert total <= 10_000
        assert body["state"]["a"].endswith(jev_client.TRUNCATION_MARKER)
        assert body["state"]["b"].endswith(jev_client.TRUNCATION_MARKER)
        # Proportional: both fields started the same size, so both should
        # end up roughly the same size after shrinking.
        assert abs(len(body["state"]["a"]) - len(body["state"]["b"])) < 5

    def test_requires_at_least_one_question(self):
        with pytest.raises(jev_client.JevError) as excinfo:
            jev_client.build_body({"a": "x"}, [], "typesafe/jev-1.13")
        assert excinfo.value.code == "CONFIG"

    def test_rejects_duplicate_question_ids(self):
        with pytest.raises(jev_client.JevError) as excinfo:
            jev_client.build_body({"a": "x"}, [_question("dup"), _question("dup")], "typesafe/jev-1.13")
        assert excinfo.value.code == "CONFIG"

    def test_score_question_includes_criteria_in_payload(self):
        q = _question("quality", "score", criteria=("weak", "strong"))
        body, _ = jev_client.build_body({"a": "x"}, [q], "typesafe/jev-1.13")
        assert body["questions"]["quality"]["criteria"] == ["weak", "strong"]


class TestTruncateState:
    def test_noop_under_limit(self):
        state = {"a": "short"}
        shrunk, truncated = jev_client.truncate_state(state, limit=1000)
        assert shrunk == state
        assert truncated is False

    def test_shrinks_and_marks_truncated_over_limit(self):
        state = {"a": "z" * 500}
        shrunk, truncated = jev_client.truncate_state(state, limit=100)
        assert truncated is True
        assert len(shrunk["a"]) <= 100
        assert shrunk["a"].endswith(jev_client.TRUNCATION_MARKER)


# ── parse_response / load_answers ────────────────────────────────────────────

class TestParseResponse:
    def test_pass_fixture(self):
        result = jev_client.parse_response(_load_fixture("pass.json"))
        assert result.model == "typesafe/jev-1.13-20260917"
        assert result.answers["consistent"].noul == pytest.approx(0.94)
        assert result.answers["quality"].confidence == pytest.approx(0.97)
        assert result.answers["quality"].probabilities == {"0": 0.0, "1": 0.0, "2": 0.03, "3": 0.97}
        assert result.cost_usd == pytest.approx(1.6296e-05)
        assert result.truncated is False

    def test_fail_fixture_is_a_confident_contradiction(self):
        result = jev_client.parse_response(_load_fixture("fail.json"))
        assert result.answers["consistent"].noul == pytest.approx(0.21)
        assert result.answers["quality"].confidence == pytest.approx(0.65)

    def test_pending_ambiguous_fixture_has_zero_confidence(self):
        result = jev_client.parse_response(_load_fixture("pending_ambiguous.json"))
        assert result.answers["consistent"].noul == pytest.approx(0.70)
        assert result.answers["quality"].confidence == pytest.approx(0.0)

    def test_fail_confident_fixture(self):
        result = jev_client.parse_response(_load_fixture("fail_confident.json"))
        assert result.answers["consistent"].noul == pytest.approx(0.05)
        assert result.answers["quality"].confidence == pytest.approx(0.9)

    def test_missing_answers_raises_parse_error(self):
        with pytest.raises(jev_client.JevError) as excinfo:
            jev_client.parse_response({"model": "x"})
        assert excinfo.value.code == "PARSE"

    def test_answers_not_a_mapping_raises_parse_error(self):
        with pytest.raises(jev_client.JevError) as excinfo:
            jev_client.parse_response({"answers": "not-a-dict"})
        assert excinfo.value.code == "PARSE"


class TestLoadAnswers:
    def test_builds_typed_answers(self):
        answers = jev_client.load_answers({"q1": {"type": "noul", "noul": 0.5}})
        assert answers["q1"].id == "q1"
        assert answers["q1"].type == "noul"
        assert answers["q1"].noul == 0.5

    def test_malformed_answer_raises_parse_error(self):
        with pytest.raises(jev_client.JevError) as excinfo:
            jev_client.load_answers({"q1": "not-a-mapping"})
        assert excinfo.value.code == "PARSE"

    def test_answer_missing_type_raises_parse_error(self):
        with pytest.raises(jev_client.JevError) as excinfo:
            jev_client.load_answers({"q1": {"noul": 0.5}})
        assert excinfo.value.code == "PARSE"


# ── decide(): endpoint fallback and typed errors ─────────────────────────────

class TestDecideEndpointFallback:
    def test_primary_endpoint_success_no_fallback(self):
        opener = _opener_sequence(_load_fixture("pass.json"))
        result = jev_client.decide(
            {"report": "x"}, [_question()], api_key="k", opener=opener,
        )
        assert len(opener.calls) == 1
        assert opener.calls[0] == jev_client.ENDPOINTS[0]
        assert result.endpoint == jev_client.ENDPOINTS[0]

    def test_falls_back_to_second_endpoint_on_not_found(self):
        opener = _opener_sequence(_http_error(jev_client.ENDPOINTS[0], 404), _load_fixture("pass.json"))
        result = jev_client.decide({"report": "x"}, [_question()], api_key="k", opener=opener)
        assert len(opener.calls) == 2
        assert result.endpoint == jev_client.ENDPOINTS[1]

    def test_falls_back_to_second_endpoint_on_unavailable(self):
        opener = _opener_sequence(_http_error(jev_client.ENDPOINTS[0], 503), _load_fixture("pass.json"))
        result = jev_client.decide({"report": "x"}, [_question()], api_key="k", opener=opener)
        assert len(opener.calls) == 2
        assert result.endpoint == jev_client.ENDPOINTS[1]

    def test_falls_back_on_network_error(self):
        opener = _opener_sequence(urllib.error.URLError("timed out"), _load_fixture("pass.json"))
        result = jev_client.decide({"report": "x"}, [_question()], api_key="k", opener=opener)
        assert len(opener.calls) == 2
        assert result.model

    def test_auth_error_raises_immediately_without_fallback(self):
        opener = _opener_sequence(_http_error(jev_client.ENDPOINTS[0], 401), _load_fixture("pass.json"))
        with pytest.raises(jev_client.JevError) as excinfo:
            jev_client.decide({"report": "x"}, [_question()], api_key="k", opener=opener)
        assert excinfo.value.code == "AUTH"
        assert len(opener.calls) == 1

    def test_bad_request_raises_immediately_without_fallback(self):
        opener = _opener_sequence(_http_error(jev_client.ENDPOINTS[0], 400), _load_fixture("pass.json"))
        with pytest.raises(jev_client.JevError) as excinfo:
            jev_client.decide({"report": "x"}, [_question()], api_key="k", opener=opener)
        assert excinfo.value.code == "BAD_REQUEST"
        assert len(opener.calls) == 1

    def test_decide_at014_both_endpoints_unavailable_raises_and_never_returns_a_result(self):
        """AT-014: Jev unavailable on both endpoints must never produce a decision."""
        opener = _opener_sequence(
            _http_error(jev_client.ENDPOINTS[0], 503),
            _http_error(jev_client.ENDPOINTS[1], 503),
        )
        with pytest.raises(jev_client.JevError) as excinfo:
            jev_client.decide({"report": "x"}, [_question()], api_key="k", opener=opener)
        assert excinfo.value.code == "UNAVAILABLE"
        assert len(opener.calls) == 2

    def test_decide_at014_timeout_on_both_endpoints(self):
        opener = _opener_sequence(TimeoutError("timed out"), TimeoutError("timed out"))
        with pytest.raises(jev_client.JevError) as excinfo:
            jev_client.decide({"report": "x"}, [_question()], api_key="k", opener=opener)
        assert excinfo.value.code == "UNAVAILABLE"

    def test_decide_requires_api_key(self):
        with pytest.raises(jev_client.JevError) as excinfo:
            jev_client.decide({"report": "x"}, [_question()], api_key="", opener=_opener_sequence())
        assert excinfo.value.code == "CONFIG"

    def test_decide_non_json_response_raises_parse_error(self):
        def opener(request, timeout=None):
            class _Bad:
                def __enter__(self_inner):
                    return self_inner

                def __exit__(self_inner, *exc):
                    return False

                def read(self_inner):
                    return b"not json"
            return _Bad()

        with pytest.raises(jev_client.JevError) as excinfo:
            jev_client.decide({"report": "x"}, [_question()], api_key="k", opener=opener)
        assert excinfo.value.code == "PARSE"


# ── Budget / ledger ──────────────────────────────────────────────────────────

class TestBudget:
    def test_jev_calls_today_counts_only_typesafe_prefix_and_today(self, tmp_path):
        ledger = tmp_path / "judge-ledger.jsonl"
        today = jev_client.today_utc()
        rows = [
            {"date": today, "model": "typesafe/jev-1.13", "verdict": "pass"},
            {"date": today, "model": "typesafe/jev-1.13", "verdict": "fail"},
            {"date": today, "model": "openai/gpt-4o-mini", "verdict": "PASS"},  # /judge row, not counted
            {"date": "1999-01-01", "model": "typesafe/jev-1.13", "verdict": "pass"},  # not today
        ]
        ledger.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
        assert jev_client.jev_calls_today(ledger) == 2

    def test_jev_calls_today_missing_ledger_is_zero(self, tmp_path):
        assert jev_client.jev_calls_today(tmp_path / "does-not-exist.jsonl") == 0

    def test_jev_calls_today_skips_malformed_lines(self, tmp_path):
        ledger = tmp_path / "judge-ledger.jsonl"
        today = jev_client.today_utc()
        ledger.write_text(
            json.dumps({"date": today, "model": "typesafe/jev-1.13", "verdict": "pass"}) + "\nnot json\n",
            encoding="utf-8",
        )
        assert jev_client.jev_calls_today(ledger) == 1

    def test_budget_remaining_uses_explicit_budget(self, tmp_path):
        ledger = tmp_path / "judge-ledger.jsonl"
        assert jev_client.budget_remaining(ledger, budget=5) == 5

    def test_budget_remaining_uses_env_var(self, tmp_path, monkeypatch):
        ledger = tmp_path / "judge-ledger.jsonl"
        monkeypatch.setenv("JEV_BUDGET", "3")
        assert jev_client.budget_remaining(ledger) == 3

    def test_budget_remaining_never_negative(self, tmp_path):
        ledger = tmp_path / "judge-ledger.jsonl"
        today = jev_client.today_utc()
        rows = [{"date": today, "model": "typesafe/jev-1.13", "verdict": "pass"} for _ in range(5)]
        ledger.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
        assert jev_client.budget_remaining(ledger, budget=2) == 0

    def test_append_ledger_schema(self, tmp_path):
        ledger = tmp_path / "judge-ledger.jsonl"
        jev_client.append_ledger(ledger, "typesafe/jev-1.13", "DEMO:eval_1", "pass", 1.6e-05)
        line = ledger.read_text(encoding="utf-8").strip().splitlines()[-1]
        row = json.loads(line)
        assert set(row.keys()) == {"date", "ts", "model", "target", "verdict", "cost_usd"}
        assert row["model"] == "typesafe/jev-1.13"
        assert row["target"] == "DEMO:eval_1"
        assert row["verdict"] == "pass"
        assert row["cost_usd"] == pytest.approx(1.6e-05)
        assert row["date"] == jev_client.today_utc()

    def test_append_ledger_creates_parent_directory(self, tmp_path):
        ledger = tmp_path / "nested" / "storage" / "judge-ledger.jsonl"
        jev_client.append_ledger(ledger, "typesafe/jev-1.13", "DEMO:eval_1", "pass", None)
        assert ledger.exists()


# ── Cross-referenced by the AT-012 contract eval ─────────────────────────────

def test_at012_load_answers_matches_pass_fixture():
    """AT-012: a calibrated, confident graded eval reads its answers straight
    from the Jev response — this is the parsing half of that path."""
    result = jev_client.parse_response(_load_fixture("pass.json"))
    assert result.answers["consistent"].type == "noul"
    assert result.answers["quality"].type == "score"
    assert result.answers["consistent"].noul is not None and result.answers["consistent"].noul >= 0.85


# ── Live (optional) ──────────────────────────────────────────────────────────

@pytest.mark.skipif(not os.environ.get("OPENROUTER_API_KEY"), reason="requires a real OPENROUTER_API_KEY")
def test_live_decide():
    result = jev_client.decide(
        {"report": "The build passed all 3 tests.", "evidence": "pytest exit code 0."},
        [_question("consistent", "noul")],
        api_key=os.environ["OPENROUTER_API_KEY"],
    )
    assert "consistent" in result.answers
