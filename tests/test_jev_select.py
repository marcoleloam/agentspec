"""Tests for scripts/jev_select.py — JEV agent selection with deterministic fallback.

No test touches the real network: the selection logic takes an injectable
transport, and the transport itself is exercised against a local HTTP server.
Acceptance test ids (AT-xxx) refer to DEFINE_JEV_AGENT_SELECTION.md.
"""
from __future__ import annotations

import importlib.util
import io
import json
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import ClassVar

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _load_module():
    spec_path = REPO_ROOT / "scripts" / "jev_select.py"
    spec = importlib.util.spec_from_file_location("jev_select_mod", spec_path)
    assert spec and spec.loader, "could not locate scripts/jev_select.py"
    module = importlib.util.module_from_spec(spec)
    sys.modules["jev_select_mod"] = module   # required for dataclass resolution
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def js():
    return _load_module()


AGENTS = [
    {"name": "dbt-specialist", "category": "data-engineering", "description": "dbt models and tests",
     "kb_domains": ["dbt", "data-quality", "sql-patterns"]},
    {"name": "spark-engineer", "category": "data-engineering", "description": "PySpark jobs",
     "kb_domains": ["spark", "sql-patterns", "streaming"]},
    {"name": "sql-optimizer", "category": "data-engineering", "description": "SQL tuning",
     "kb_domains": ["sql-patterns", "data-modeling", "dbt"]},
    {"name": "design-agent", "category": "workflow", "description": "Phase 2", "kb_domains": ["dbt"]},
    {"name": "react-developer", "category": "frontend", "description": "React", "kb_domains": ["react"]},
]
DOMAINS = ["dbt", "spark", "sql-patterns"]
NO_IMPLEMENTERS = [a for a in AGENTS if a["name"] not in {"python-developer", "react-developer"}]


def fixture(name: str) -> dict:
    return json.loads((FIXTURES / "jev" / name).read_text())


class FakeTransport:
    def __init__(self, response: dict | None = None, error: str | None = None) -> None:
        self.response = response
        self.error = error
        self.payloads: list[dict] = []

    def __call__(self, payload, settings):
        self.payloads.append(payload)
        if self.error:
            raise sys.modules["jev_select_mod"].TransportError(self.error)
        return self.response


def settings(js, **env):
    base = {"OPENROUTER_API_KEY": "sk-test"}
    base.update(env)
    return js.Settings.from_env({k: v for k, v in base.items() if v is not None})


def make_input(js, domains=DOMAINS, locked=None, phase="design", summary="Daily orders ETL with dbt and Spark"):
    return js.SelectionInput(phase=phase, summary=summary, kb_domains=tuple(domains), variant_locked=locked)


# ── Settings ─────────────────────────────────────────────────────────────────

class TestSettings:
    def test_defaults(self, js):
        s = js.Settings.from_env({})
        assert s.api_key is None
        assert s.url == "https://openrouter.ai/api/alpha/decisions"
        assert s.model == "typesafe/jev-1.13"
        assert s.single_threshold == 0.5
        assert s.uncertain_band == 0.1
        assert s.fit_threshold == 0.5
        assert s.timeout_s == 4.0
        assert s.disabled is False

    def test_jev_api_key_takes_precedence(self, js):
        s = js.Settings.from_env({"OPENROUTER_API_KEY": "or", "JEV_API_KEY": "jev"})
        assert s.api_key == "jev"

    def test_bad_float_falls_back_to_default(self, js):
        s = js.Settings.from_env({"JEV_SINGLE_THRESHOLD": "high", "JEV_TIMEOUT_MS": "500"})
        assert s.single_threshold == 0.5
        assert s.timeout_s == 0.5

    def test_disable_flag(self, js):
        assert js.Settings.from_env({"JEV_DISABLE": "1"}).disabled is True


# ── Catalog + heuristic ──────────────────────────────────────────────────────

class TestPrefilterAndHeuristic:
    def test_excludes_workflow_and_non_overlapping(self, js):
        names = [c.name for c in js.prefilter_candidates(AGENTS, DOMAINS)]
        assert names == ["dbt-specialist", "spark-engineer", "sql-optimizer"]

    def test_orders_by_overlap_then_name(self, js):
        cands = js.prefilter_candidates(AGENTS, ["dbt", "data-quality"])
        assert [(c.name, c.overlap) for c in cands] == [("dbt-specialist", 2), ("sql-optimizer", 1)]

    def test_caps_candidates(self, js):
        many = [{"name": f"a{i:02d}", "category": "python", "kb_domains": ["python"]} for i in range(20)]
        assert len(js.prefilter_candidates(many, ["python"])) == js.MAX_CANDIDATES

    def test_heuristic_rule(self, js):
        cands = js.prefilter_candidates(AGENTS, DOMAINS)
        assert js.heuristic(tuple(DOMAINS), cands) == (
            "multiagent", ("dbt-specialist", "spark-engineer", "sql-optimizer"))
        assert js.heuristic(("dbt", "spark"), cands)[0] == "single"

    def test_normalize_domains_dedupes_case(self, js):
        assert js.normalize_domains(["DBT", " dbt ", "", "Spark"]) == ("dbt", "spark")

    def test_real_routing_json_loads(self, js):
        path = js.resolve_routing_path()
        assert path is not None and path.name == "routing.json"
        agents = js.load_routing(path)
        assert len(agents) > 50
        assert all(c.category != "workflow" for c in js.prefilter_candidates(agents, ["dbt", "spark"]))


# ── Request shape ────────────────────────────────────────────────────────────

class TestBuildRequest:
    def test_state_holds_only_phase_and_summary(self, js):
        cands = js.prefilter_candidates(AGENTS, DOMAINS)
        req = js.build_request(make_input(js), cands, "typesafe/jev-1.13")
        assert set(req["state"]) == {"phase", "spec_summary"}   # no kb_domains (v1.1)
        assert req["questions"]["single_area"]["type"] == "noul"
        assert set(req["questions"]["single_area"]["criteria"]) == {"true", "false"}
        assert [k for k in req["questions"] if k.startswith("fit_")] == ["fit_0", "fit_1", "fit_2"]
        assert req["questions"]["fit_0"]["type"] == "noul"
        assert "dbt-specialist" in req["questions"]["fit_0"]["instructions"]

    def test_locked_variant_omits_variant_question(self, js):
        cands = js.prefilter_candidates(AGENTS, DOMAINS)
        req = js.build_request(make_input(js, locked="multiagent"), cands, "m")
        assert "single_area" not in req["questions"]

    def test_summary_truncated(self, js):
        long = make_input(js, summary="x" * 10_000)
        req = js.build_request(long, [], "m")
        assert len(req["state"]["spec_summary"]) == js.SUMMARY_MAX_CHARS


# ── Normalization ────────────────────────────────────────────────────────────

class TestNormalization:
    def test_free_text_domains_are_mapped(self, js):
        known = js.known_domains(js.load_routing(js.resolve_routing_path()))
        kept, dropped = js.normalize_kb_domains(
            ["`tailwind`", "a11y", "sql/postgres", "golang", "genai (rag, guardrails)",
             "frontend/nextjs", "modelagem de dados/Postgres", "DBT"], known)
        assert kept == ("tailwind-css", "accessibility", "sql-patterns", "genai",
                        "frontend-patterns", "nextjs", "data-modeling", "dbt")
        assert dropped == ("golang",)

    def test_unknown_catalog_keeps_everything(self, js):
        assert js.normalize_kb_domains(["a11y", "golang"], frozenset()) == (("accessibility", "golang"), ())

    @pytest.mark.parametrize("p,value,reason", [
        (0.95, "single", None), (0.6, "single", None), (0.05, "multiagent", None),
        (0.4, "multiagent", None), (0.55, "multiagent", "uncertain"), (0.45, "multiagent", "uncertain"),
    ])
    def test_gate_variant_threshold_and_band(self, js, p, value, reason):
        d = js.gate_variant({"noul": p}, "multiagent", 0.5, 0.1)
        assert (d.value, d.fallback_reason) == (value, reason)
        assert d.probabilities["single"] == p

    def test_gate_variant_rejects_non_noul(self, js):
        assert js.gate_variant({"choice": "single"}, "single", 0.5, 0.1).fallback_reason == "invalid_response"

    def test_always_candidates_are_added_within_cap(self, js):
        many = [{"name": f"a{i:02d}", "category": "python", "kb_domains": ["dbt"]} for i in range(20)]
        catalog = [*many, {"name": "python-developer", "category": "python", "kb_domains": ["python"]},
                   {"name": "react-developer", "category": "frontend", "kb_domains": ["react"]}]
        overlap = js.prefilter_candidates(catalog, ["dbt"])
        cands = js.with_always_candidates(catalog, overlap, ["dbt"])
        assert len(cands) == js.MAX_CANDIDATES
        assert [c.name for c in cands[-2:]] == ["python-developer", "react-developer"]

    def test_always_candidates_not_duplicated(self, js):
        overlap = js.prefilter_candidates(AGENTS, ["react"])
        assert [c.name for c in js.with_always_candidates(AGENTS, overlap, ["react"])] == ["react-developer"]

    @pytest.mark.parametrize("raw,expected", [
        ({"noul": 0.3}, 0.3), ({"noul": 1}, 1.0), ({"noul": 1.7}, None),
        ({"noul": "x"}, None), ({"noul": True}, None), ("nope", None),
    ])
    def test_noul_value(self, js, raw, expected):
        assert js.noul_value(raw) == expected


# ── select(): acceptance tests ───────────────────────────────────────────────

class TestSelect:
    def test_at001_multiagent_happy_path(self, js):
        t = FakeTransport(fixture("multiagent_happy.json"))
        r = js.select(make_input(js), settings(js), AGENTS, t)
        assert r["source"] == "jev" and r["fallback_reason"] is None
        assert r["variant"]["value"] == "multiagent" and r["variant"]["confidence"] == pytest.approx(0.9)
        assert r["variant"]["probabilities"] == {"single": 0.05, "multiagent": 0.95}
        assert r["specialists"]["value"] == ["dbt-specialist", "spark-engineer"]
        assert r["specialists"]["applies"] is True
        assert r["specialists"]["probabilities"]["sql-optimizer"] == 0.2
        assert r["usage"] == {"input_tokens": 812, "output_tokens": 21}

    def test_at002_single_happy_path(self, js):
        r = js.select(make_input(js), settings(js), AGENTS, FakeTransport(fixture("single_happy.json")))
        assert r["variant"] == {**r["variant"], "value": "single", "source": "jev"}
        assert r["specialists"]["applies"] is False

    def test_at003_missing_key_never_calls(self, js):
        t = FakeTransport(fixture("multiagent_happy.json"))
        r = js.select(make_input(js), settings(js, OPENROUTER_API_KEY=None), AGENTS, t)
        assert t.payloads == []
        assert r["source"] == "fallback" and r["fallback_reason"] == "missing_key"
        assert r["variant"]["value"] == "multiagent"   # 3 domains → heuristic multiagent
        assert r["specialists"]["value"] == ["dbt-specialist", "spark-engineer", "sql-optimizer"]

    @pytest.mark.parametrize("reason", ["timeout", "http_404", "http_500", "network", "invalid_response"])
    def test_at004_at005_transport_errors_fall_back(self, js, reason):
        r = js.select(make_input(js), settings(js), AGENTS, FakeTransport(error=reason))
        assert r["source"] == "fallback"
        assert r["variant"]["fallback_reason"] == reason
        assert r["specialists"]["fallback_reason"] == reason
        assert r["latency_ms"] is not None

    def test_at006_uncertain_keeps_probabilities(self, js):
        r = js.select(make_input(js), settings(js), AGENTS, FakeTransport(fixture("uncertain.json")))
        assert r["variant"]["source"] == "fallback"
        assert r["variant"]["fallback_reason"] == "uncertain"
        assert r["variant"]["value"] == "multiagent"      # heuristic (3 domains), not JEV's lean to single
        assert r["variant"]["probabilities"] == {"single": 0.55, "multiagent": 0.45}
        assert r["variant"]["confidence"] == pytest.approx(0.1)

    def test_at007_free_text_domains_normalized(self, js):
        inp = make_input(js, domains=["DBT", "sql/postgres", "golang", "`spark`"])
        r = js.select(inp, settings(js), AGENTS, FakeTransport(fixture("multiagent_happy.json")))
        assert r["kb_domains"] == ["dbt", "sql-patterns", "spark"]
        assert r["kb_domains_dropped"] == ["golang"]
        assert r["heuristic"]["variant"] == "multiagent"

    def test_at008_no_fit_above_threshold(self, js):
        r = js.select(make_input(js), settings(js), AGENTS, FakeTransport(fixture("all_below_threshold.json")))
        assert r["variant"]["source"] == "jev"
        assert r["specialists"]["source"] == "fallback"
        assert r["specialists"]["fallback_reason"] == "no_fit_above_threshold"
        assert r["specialists"]["value"] == ["dbt-specialist", "spark-engineer", "sql-optimizer"]
        assert r["source"] == "jev" and r["fallback_reason"] == "no_fit_above_threshold"

    def test_at009_locked_variant(self, js):
        t = FakeTransport(fixture("single_happy.json"))
        r = js.select(make_input(js, locked="multiagent"), settings(js), AGENTS, t)
        assert "single_area" not in t.payloads[0]["questions"]
        assert r["variant"]["value"] == "multiagent" and r["variant"]["source"] == "locked"
        assert r["specialists"]["source"] == "jev" and r["specialists"]["value"] == ["dbt-specialist"]
        assert r["source"] == "jev"

    def test_at010_at_most_four_specialists(self, js):
        agents = [{"name": f"s{i}", "category": "python", "kb_domains": ["python"]} for i in range(6)]
        answers = {"single_area": {"noul": 0.05}}
        answers.update({f"fit_{i}": {"noul": 0.5 + i / 20} for i in range(6)})
        r = js.select(make_input(js, domains=["python"]), settings(js), agents, FakeTransport({"answers": answers}))
        assert r["specialists"]["value"] == ["s5", "s4", "s3", "s2"]

    def test_at013_disabled_never_calls(self, js):
        t = FakeTransport(fixture("multiagent_happy.json"))
        r = js.select(make_input(js), settings(js, JEV_DISABLE="1"), AGENTS, t)
        assert t.payloads == [] and r["fallback_reason"] == "disabled"

    def test_invalid_nouls_fall_back(self, js):
        r = js.select(make_input(js), settings(js), AGENTS, FakeTransport(fixture("invalid_nouls.json")))
        assert r["variant"]["source"] == "jev"
        assert r["specialists"]["fallback_reason"] == "invalid_response"

    def test_response_without_answers(self, js):
        r = js.select(make_input(js), settings(js), AGENTS, FakeTransport({"error": "weird"}))
        assert r["fallback_reason"] == "invalid_response"

    def test_variant_answer_must_be_noul(self, js):
        resp = {"answers": {"single_area": {"choice": "single", "confidence": 0.99}}}
        r = js.select(make_input(js), settings(js), AGENTS, FakeTransport(resp))
        assert r["variant"]["fallback_reason"] == "invalid_response"

    def test_implementers_are_candidates_without_overlap(self, js):
        t = FakeTransport(fixture("single_happy.json"))
        r = js.select(make_input(js, domains=["terraform"]), settings(js), AGENTS, t)
        assert [c["name"] for c in r["candidates"]] == ["react-developer"]
        assert r["specialists"]["value"] == ["react-developer"] and r["specialists"]["source"] == "jev"
        assert r["heuristic"]["specialists"] == []          # heuristic keeps the overlap-only rule

    def test_no_candidates(self, js):
        r = js.select(make_input(js, domains=["terraform"]), settings(js), NO_IMPLEMENTERS,
                      FakeTransport(fixture("single_happy.json")))
        assert r["specialists"]["value"] == [] and r["specialists"]["fallback_reason"] == "no_candidates"
        assert r["variant"]["source"] == "jev"

    def test_no_routing(self, js):
        r = js.select(make_input(js), settings(js), [], FakeTransport(fixture("single_happy.json")),
                      routing_found=False)
        assert r["specialists"]["fallback_reason"] == "no_routing"

    def test_locked_without_candidates_skips_call(self, js):
        t = FakeTransport(fixture("single_happy.json"))
        r = js.select(make_input(js, domains=["terraform"], locked="multiagent"), settings(js), NO_IMPLEMENTERS, t)
        assert t.payloads == [] and r["specialists"]["fallback_reason"] == "no_candidates"


# ── Transport against a local server ─────────────────────────────────────────

class _Handler(BaseHTTPRequestHandler):
    mode = "ok"
    seen_auth: ClassVar[list[str]] = []

    def do_POST(self):
        self.seen_auth.append(self.headers.get("Authorization", ""))
        length = int(self.headers.get("Content-Length", 0))
        self.rfile.read(length)
        if self.mode == "slow":
            time.sleep(3)
        if self.mode == "http_500":
            self.send_response(500)
            self.end_headers()
            return
        body = b"not json" if self.mode == "garbage" else json.dumps(fixture("single_happy.json")).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


@pytest.fixture
def server():
    srv = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    srv.daemon_threads = True
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    yield srv
    srv.shutdown()
    srv.server_close()
    _Handler.mode = "ok"


def _local(js, srv, timeout_ms="2000"):
    return settings(js, JEV_URL=f"http://127.0.0.1:{srv.server_port}/", JEV_TIMEOUT_MS=timeout_ms)


class TestPostDecisions:
    def test_success_sends_bearer(self, js, server):
        _Handler.seen_auth = []
        out = js.post_decisions({"model": "m", "state": "s", "questions": {}}, _local(js, server))
        assert out["answers"]["single_area"]["noul"] == 0.95
        assert _Handler.seen_auth == ["Bearer sk-test"]

    def test_at004_total_timeout_is_enforced(self, js, server):
        _Handler.mode = "slow"
        started = time.monotonic()
        with pytest.raises(js.TransportError) as err:
            js.post_decisions({}, _local(js, server, timeout_ms="500"))
        assert err.value.reason == "timeout"
        assert time.monotonic() - started < 1.5

    def test_at005_http_error_code(self, js, server):
        _Handler.mode = "http_500"
        with pytest.raises(js.TransportError) as err:
            js.post_decisions({}, _local(js, server))
        assert err.value.reason == "http_500"

    def test_non_json_body(self, js, server):
        _Handler.mode = "garbage"
        with pytest.raises(js.TransportError) as err:
            js.post_decisions({}, _local(js, server))
        assert err.value.reason == "invalid_response"

    def test_unreachable_host(self, js):
        s = settings(js, JEV_URL="http://127.0.0.1:9/", JEV_TIMEOUT_MS="2000")
        with pytest.raises(js.TransportError) as err:
            js.post_decisions({}, s)
        assert err.value.reason in {"network", "timeout"}


# ── Eval ─────────────────────────────────────────────────────────────────────

class TestEval:
    @pytest.mark.parametrize("pred,exp,expected", [
        ([], [], 1.0), (["a"], [], 0.0), (["a", "b"], ["a"], 2 / 3), (["a"], ["a"], 1.0), (["x"], ["y"], 0.0),
    ])
    def test_f1(self, js, pred, exp, expected):
        assert js.f1(pred, exp) == pytest.approx(expected)

    def test_at011_eval_on_sample_labels(self, js):
        cases = js.load_labels(FIXTURES / "agent_selection" / "labels_sample.json")
        agents = js.load_routing(js.resolve_routing_path())

        def transport(payload, _settings):
            is_frontend = "frontend" in payload["state"]["spec_summary"].lower()
            fits = [k for k in payload["questions"] if k.startswith("fit_")]
            answers = {"single_area": {"noul": 0.1 if is_frontend else 0.9}}
            answers.update({k: {"noul": 0.9 if is_frontend else 0.1} for k in fits})
            return {"answers": answers}

        report = js.run_eval(cases, settings(js), agents, transport)
        assert report["cases"] == 2 and report["multiagent_cases"] == 1
        assert report["variant_accuracy"] == {"system": 1.0, "heuristic": 0.5}
        assert report["success"]["variant"] is True
        text = js.render_eval(report)
        assert "variant accuracy" in text and "PASS" in text
        assert all("system_confidence" in row for row in report["rows"])
        assert "(p_single=0.10)" in text

    def test_load_labels_rejects_bad_variant(self, js, tmp_path):
        bad = tmp_path / "labels.json"
        bad.write_text(json.dumps({"cases": [{
            "id": "x", "phase": "design", "summary": "s", "kb_domains": [],
            "expected_variant": "many", "expected_specialists": [],
        }]}))
        with pytest.raises(ValueError):
            js.load_labels(bad)


# ── CLI ──────────────────────────────────────────────────────────────────────

class TestCli:
    def test_invalid_input_still_exits_zero(self, js, monkeypatch, capsys):
        monkeypatch.setattr(sys, "stdin", io.StringIO("not json"))
        assert js.main([]) == 0
        out = json.loads(capsys.readouterr().out)
        assert out["source"] == "fallback" and out["fallback_reason"] == "invalid_input"

    @pytest.mark.parametrize("payload", [
        {"phase": "ship", "summary": "s", "kb_domains": []},
        {"phase": "design", "summary": "s", "kb_domains": "dbt"},
        {"phase": "design", "summary": "s", "kb_domains": [], "variant_locked": "both"},
        ["not", "an", "object"],
    ])
    def test_rejected_inputs_fall_back(self, js, monkeypatch, capsys, payload):
        monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))
        assert js.main([]) == 0
        assert json.loads(capsys.readouterr().out)["fallback_reason"] == "invalid_input"

    def test_missing_key_end_to_end(self, js, monkeypatch, capsys):
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.delenv("JEV_API_KEY", raising=False)
        monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(
            {"phase": "define", "summary": "s", "kb_domains": ["dbt", "spark", "airflow"]})))
        assert js.main([]) == 0
        captured = capsys.readouterr()
        out = json.loads(captured.out)
        assert out["fallback_reason"] == "missing_key" and out["variant"]["value"] == "multiagent"
        assert "[jev_select] source=fallback" in captured.err

    def test_eval_bad_labels_exit_2(self, js, tmp_path):
        bad = tmp_path / "labels.json"
        bad.write_text("{}")
        assert js.main(["--eval", str(bad)]) == 2
