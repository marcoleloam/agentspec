"""Tests for scripts/kb_bench — no Grok, no network, no eval venv required.

Parser/isolation tests use transcripts recorded from grok 1.0.41 (anonymised);
loop/CLI tests drive a fake ``grok`` (tests/fixtures/kb_bench/fake_grok.py).
"""
from __future__ import annotations

import json
import stat
from pathlib import Path

import pytest
import tomllib
from kb_bench import grok_runner, isolation, loop, setup_env, workspace
from kb_bench.config import ARM_LETTERS, BENCH_DIR, load_config
from kb_bench.evals import discriminates
from kb_bench.human_queue import HumanQueue
from kb_bench.report import ArmScore, recommend, render
from kb_bench.store import Record, RunStore
from kb_bench.tasks import Eval, Task, TaskError, load_task, load_tasks
from kb_bench.transcript import parse_ndjson

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "kb_bench"
PLUGIN_KB = Path("/Users/tester/.grok/installed-plugins/plugin-grok-efb5f966/kb")


@pytest.fixture
def cfg(tmp_path, monkeypatch):
    monkeypatch.setenv("KB_BENCH_HOME", str(tmp_path / "home"))
    config = load_config()
    for letter in ARM_LETTERS:
        config.arm_dir(letter).mkdir(parents=True, exist_ok=True)
    return config


@pytest.fixture
def fake_grok(tmp_path, monkeypatch):
    script = tmp_path / "grok"
    script.write_text((FIXTURES / "fake_grok.py").read_text())
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setattr(grok_runner, "GROK_BIN", str(script))
    return script


def _task(evals=None, fixtures=None) -> Task:
    return Task(
        id="unit-01-hello", domain="dbt", stratum="library", origin="synthetic",
        authored_from="test", prompt="Write hello to out.txt",
        evals=tuple(evals or (Eval("out exists", ("test", "-f", "out.txt")),
                              Eval("says hello", ("grep", "-q", "hello", "out.txt")))),
        source=Path("unit.toml"), fixtures=fixtures,
    )


def _ctx(cfg, tmp_path) -> loop.RunContext:
    store = RunStore(cfg.results_root / "run-test")
    return loop.RunContext(cfg=cfg, store=store, queue=HumanQueue(store.root), grok_version="fake",
                           log=lambda _m: None)


# ── transcript ───────────────────────────────────────────────────────────────

class TestTranscript:
    def test_denied_read_recorded(self):
        t = parse_ndjson((FIXTURES / "denied_read.ndjson").read_text())
        denied = [c for c in t.tool_calls if c.permission_denied]
        assert len(denied) == 1
        assert denied[0].status == "failed"
        assert any(str(PLUGIN_KB) in p for p in denied[0].paths)
        assert t.ended and t.total_tokens == 53036 and t.model == "grok-4.7-build"

    def test_context7_calls_and_mcp_output(self):
        t = parse_ndjson((FIXTURES / "context7_calls.ndjson").read_text())
        resolves = t.mcp_calls("context7__resolve-library-id")
        assert len(resolves) == 6
        assert all(c.status == "completed" for c in resolves)
        assert "/apache/airflow" in " ".join(c.output_text for c in resolves)

    def test_malformed_lines_are_counted_not_fatal(self):
        t = parse_ndjson('not json\n{"type": "text", "data": "hi"}\n')
        assert t.malformed_lines == 1 and t.text == "hi" and not t.ended


# ── isolation ────────────────────────────────────────────────────────────────

class TestIsolation:
    def test_denied_read_is_counted_not_contamination(self, tmp_path):
        t = parse_ndjson((FIXTURES / "denied_read.ndjson").read_text())
        v = isolation.check(t, uses_context7=False, deny=(PLUGIN_KB,), cwd=tmp_path)
        assert not v.contaminated and v.kb_access_denied == 1

    def test_grep_blocked_by_sandbox_is_not_contamination(self, tmp_path):
        # grok marks the rg call "completed" (0 matches) and hides the EPERM in byte-list stdout
        t = parse_ndjson((FIXTURES / "denied_grep.ndjson").read_text())
        greps = [c for c in t.tool_calls if c.tool == "grep"]
        assert greps and all(c.status == "completed" and c.permission_denied for c in greps)
        v = isolation.check(t, uses_context7=False, deny=(Path("/Users/tester/agentspec"),), cwd=tmp_path)
        assert not v.contaminated and v.kb_access_denied == len(greps)

    def test_grep_with_matches_under_deny_is_contamination(self, tmp_path):
        raw = "\n".join(json.dumps(e) for e in (
            {"type": "tool_call", "toolCallId": "g", "toolName": "grep",
             "rawInput": {"pattern": "x", "path": str(PLUGIN_KB)}},
            {"type": "tool_call_update", "toolCallId": "g", "status": "completed",
             "rawOutput": {"type": "GrepSearch", "match_count": 3, "file_matches": ["a.md"]}},
        ))
        assert isolation.check(parse_ndjson(raw), uses_context7=False, deny=(PLUGIN_KB,), cwd=tmp_path).contaminated

    def test_completed_read_under_deny_is_contamination(self, tmp_path):
        raw = "\n".join(json.dumps(e) for e in (
            {"type": "tool_call", "toolCallId": "x", "toolName": "read_file",
             "rawInput": {"target_file": str(PLUGIN_KB / "dbt/index.md")}},
            {"type": "tool_call_update", "toolCallId": "x", "status": "completed", "rawOutput": {}},
        ))
        v = isolation.check(parse_ndjson(raw), uses_context7=False, deny=(PLUGIN_KB,), cwd=tmp_path)
        assert v.contaminated and "denied path" in v.reasons[0]

    def test_bash_command_touching_deny_is_contamination(self, tmp_path):
        raw = "\n".join(json.dumps(e) for e in (
            {"type": "tool_call", "toolCallId": "b", "toolName": "bash",
             "rawInput": {"command": f"cat {PLUGIN_KB}/dbt/index.md"}},
            {"type": "tool_call_update", "toolCallId": "b", "status": "completed", "rawOutput": {}},
        ))
        v = isolation.check(parse_ndjson(raw), uses_context7=False, deny=(PLUGIN_KB,), cwd=tmp_path)
        assert v.contaminated

    def test_context7_in_non_mcp_arm_is_contamination(self, tmp_path):
        t = parse_ndjson((FIXTURES / "context7_calls.ndjson").read_text())
        assert isolation.check(t, uses_context7=False, deny=(), cwd=tmp_path).contaminated
        v = isolation.check(t, uses_context7=True, deny=(), cwd=tmp_path)
        assert not v.contaminated and v.context7_calls == 7

    def test_web_tool_is_contamination(self, tmp_path):
        raw = "\n".join(json.dumps(e) for e in (
            {"type": "tool_call", "toolCallId": "w", "toolName": "web_search", "rawInput": {"query": "dbt"}},
            {"type": "tool_call_update", "toolCallId": "w", "status": "completed", "rawOutput": {}},
        ))
        assert isolation.check(parse_ndjson(raw), uses_context7=True, deny=(), cwd=tmp_path).contaminated

    def test_private_tmp_alias_matches(self):
        assert isolation.under(Path("/tmp/x/kb/a.md"), (Path("/private/tmp/x"),))


def test_feedback_hides_evaluator_paths(tmp_path):
    from kb_bench.config import BENCH_DIR
    from kb_bench.evals import EvalResult, feedback
    work = tmp_path / "evalws" / "t__D__1.run"
    out = f"{BENCH_DIR}/.venv/lib/python3.12/site-packages/dbt/x.py warn; model at {work}/models/a.sql"
    text = feedback([EvalResult("parse", False, 1, out)], 4096, workdir=work)
    assert str(BENCH_DIR) not in text and str(work) not in text
    assert "<evaluator>/.venv" in text and "./models/a.sql" in text


# ── decision rule (AT-007) ───────────────────────────────────────────────────

def _scores(**kw) -> dict[str, ArmScore]:
    base = {k: ArmScore(total=6, excluded=0, resolved=4, human=2) for k in ARM_LETTERS}
    base.update(kw)
    return base


class TestDecisionRule:
    def test_d_matching_a_retires_kb(self):
        assert recommend(_scores()) == "aposentar KB"

    def test_b_matching_a_replaces(self):
        worse = ArmScore(6, 0, 2, 4)
        assert recommend(_scores(D=worse)) == "substituir por B"

    def test_c_only_slims(self):
        worse = ArmScore(6, 0, 2, 4)
        assert recommend(_scores(D=worse, B=worse)) == "enxugar (C)"

    def test_none_keeps_a(self):
        worse = ArmScore(6, 0, 2, 4)
        assert recommend(_scores(D=worse, B=worse, C=worse)) == "manter A"

    def test_more_human_fails_even_with_same_resolved(self):
        worse = ArmScore(6, 0, 2, 4)
        noisy = ArmScore(6, 0, 4, 3)  # same resolved, one more to human than A
        assert recommend(_scores(D=worse, B=noisy, C=worse)) == "manter A"

    def test_rates_not_counts_with_exclusions(self):
        worse = ArmScore(6, 0, 2, 4)
        b = ArmScore(6, 2, 3, 1)  # 3/4 resolved beats A's 4/6
        assert recommend(_scores(D=worse, B=b)) == "substituir por B"

    def test_more_than_a_third_excluded_is_inconclusive(self):
        assert recommend(_scores(B=ArmScore(6, 3, 3, 0))) == "inconclusivo"

    def test_missing_arm_is_inconclusive(self):
        s = _scores()
        del s["C"]
        assert recommend(s) == "inconclusivo"


# ── tasks & discrimination (AT-002) ──────────────────────────────────────────

class TestTasks:
    def test_bundled_tasks_load(self):
        tasks = load_tasks(BENCH_DIR / "tasks")
        assert len(tasks) == 18
        per_domain = {}
        for t in tasks:
            per_domain[t.domain] = per_domain.get(t.domain, 0) + 1
            assert t.solution is not None, f"{t.id} has no reference solution"
        assert set(per_domain.values()) == {3} and len(per_domain) == 6

    def test_rejects_wrong_stratum(self, tmp_path):
        p = tmp_path / "dbt" / "dbt-99-x.toml"
        p.parent.mkdir()
        p.write_text('id="dbt-99-x"\ndomain="dbt"\nstratum="niche"\norigin="synthetic"\nauthored_from="t"\n'
                     'prompt="p"\n[[evals]]\nname="e"\ncmd=["true"]\n')
        with pytest.raises(TaskError, match="stratum"):
            load_task(p, base=tmp_path)

    def test_rejects_filename_id_mismatch(self, tmp_path):
        p = tmp_path / "dbt-98-y.toml"
        p.write_text('id="dbt-98-z"\ndomain="dbt"\nstratum="library"\norigin="synthetic"\nauthored_from="t"\n'
                     'prompt="p"\n[[evals]]\nname="e"\ncmd=["true"]\n')
        with pytest.raises(TaskError, match="file name"):
            load_task(p, base=tmp_path)

    def test_non_discriminating_task_is_rejected(self, cfg):
        always = _task(evals=(Eval("trivially true", ("true",)),))
        assert not discriminates(always, cfg).ok

    def test_discriminating_task_with_solution(self, cfg, tmp_path):
        sol = tmp_path / "sol"
        sol.mkdir()
        (sol / "out.txt").write_text("hello\n")
        task = _task()
        task = Task(**{**task.__dict__, "solution": sol})
        result = discriminates(task, cfg)
        assert result.ok and result.fails_on_fixtures and result.solution_passes


# ── workspace config per arm ─────────────────────────────────────────────────

class TestWorkspace:
    def test_context7_only_in_b_and_c(self, cfg):
        for letter in ARM_LETTERS:
            text = workspace.grok_config_toml(cfg.arms[letter], cfg)
            data = tomllib.loads(text)
            assert ("context7" in data["mcp_servers"]) == (letter in {"B", "C"})
            for name in cfg.disabled_global_mcps:
                assert data["mcp_servers"][name]["enabled"] is False

    def test_sandbox_denies_repo_and_canary(self, cfg):
        data = tomllib.loads(workspace.sandbox_toml(cfg))
        assert data["profiles"][cfg.sandbox_profile]["read_write"] == [str(cfg.npm_cache_dir)]
        deny = data["profiles"][cfg.sandbox_profile]["deny"]
        assert data["profiles"][cfg.sandbox_profile]["extends"] == "workspace"
        assert str(BENCH_DIR.parent.parent) in deny
        assert str(cfg.canary_dir.resolve()) in deny

    def test_prepare_copies_kb_per_arm(self, cfg):
        task = Task(**{**_task().__dict__, "domain": "dbt"})
        a = workspace.prepare(cfg.arms["A"], task, cfg, fresh=True)
        assert (a / "kb" / "index.md").is_file()
        c = workspace.prepare(cfg.arms["C"], task, cfg, fresh=True)
        assert (c / "kb" / "anti-patterns.md").is_file()
        for letter in ("B", "D"):
            assert not (workspace.prepare(cfg.arms[letter], task, cfg, fresh=True) / "kb").exists()

    def test_reset_refuses_outside_home(self, cfg, tmp_path):
        with pytest.raises(workspace.WorkspaceError):
            workspace.reset_arm_dir(tmp_path / "elsewhere", cfg)


# ── loop with fake grok (AT-003/004/005/009) ─────────────────────────────────

class TestLoop:
    def _run(self, cfg, tmp_path, monkeypatch, scenario, arm="D", **env):
        monkeypatch.setenv("FAKE_SCENARIO", scenario)
        for k, v in env.items():
            monkeypatch.setenv(k, v)
        return loop.run_pair(_task(), cfg.arms[arm], _ctx(cfg, tmp_path))

    def test_pass_first(self, cfg, fake_grok, tmp_path, monkeypatch):
        rec = self._run(cfg, tmp_path, monkeypatch, "solve")
        assert rec.outcome == "pass_first" and rec.attempts == 1 and rec.tokens == 1000

    def test_pass_retry_accumulates_cost(self, cfg, fake_grok, tmp_path, monkeypatch):
        rec = self._run(cfg, tmp_path, monkeypatch, "fail_then_solve")
        assert rec.outcome == "pass_retry" and rec.attempts == 2 and rec.tokens == 2000

    def test_exhausted_retries_go_to_blind_human_queue(self, cfg, fake_grok, tmp_path, monkeypatch):
        rec = self._run(cfg, tmp_path, monkeypatch, "never")
        assert rec.outcome == "human" and rec.attempts == 3 and rec.human_id
        queue = HumanQueue(cfg.results_root / "run-test")
        item = (queue.dir / f"{rec.human_id}.md").read_text()
        assert "says hello" in item and "out.txt" in item
        assert "D — " not in item and "arm" not in item.lower()
        assert queue.mapping()[rec.human_id] == {"arm": "D", "task": "unit-01-hello"}

    def test_no_end_event_is_timeout(self, cfg, fake_grok, tmp_path, monkeypatch):
        rec = self._run(cfg, tmp_path, monkeypatch, "hang")
        assert rec.outcome == "timeout" and "no end event" in rec.reason

    def test_completed_read_of_deny_path_is_contaminated(self, cfg, fake_grok, tmp_path, monkeypatch):
        deny = str(cfg.canary_dir / "canary.txt")
        rec = self._run(cfg, tmp_path, monkeypatch, "leak", FAKE_DENY_PATH=deny)
        assert rec.outcome == "contaminated" and rec.contamination_reasons

    def test_context7_preflight_failure_is_unavailable(self, cfg, fake_grok, tmp_path, monkeypatch):
        rec = self._run(cfg, tmp_path, monkeypatch, "solve", arm="B", FAKE_DOCTOR="down")
        assert rec.outcome == "unavailable" and rec.attempts == 0

    def test_context7_transport_failure_is_unavailable(self, cfg, fake_grok, tmp_path, monkeypatch):
        rec = self._run(cfg, tmp_path, monkeypatch, "c7_down", arm="B")
        assert rec.outcome == "unavailable"

    def test_context7_missing_in_session_is_unavailable(self, cfg, fake_grok, tmp_path, monkeypatch):
        rec = self._run(cfg, tmp_path, monkeypatch, "mcp_missing", arm="B")
        assert rec.outcome == "unavailable" and "not available" in rec.reason

    def test_context7_arm_counts_calls(self, cfg, fake_grok, tmp_path, monkeypatch):
        rec = self._run(cfg, tmp_path, monkeypatch, "c7", arm="C")
        assert rec.outcome == "pass_first" and rec.context7_calls == 1

    def test_plan_is_seeded(self):
        tasks = [_task(), Task(**{**_task().__dict__, "id": "unit-02-x"})]
        assert loop.plan(tasks, list(ARM_LETTERS), 7) == loop.plan(tasks, list(ARM_LETTERS), 7)
        assert len(loop.plan(tasks, list(ARM_LETTERS), 7)) == 8

    def test_prompt_differs_only_by_arm_preamble(self):
        t = _task()
        assert loop.build_prompt(t, load_config().arms["D"]).startswith(t.prompt)
        assert "./kb/" in loop.build_prompt(t, load_config().arms["A"])
        assert "context7" in loop.build_prompt(t, load_config().arms["B"])


# ── trust file (setup/teardown) ──────────────────────────────────────────────

class TestTrust:
    def test_add_then_remove_preserves_other_entries(self, cfg, tmp_path, monkeypatch):
        trust = tmp_path / "trusted_folders.toml"
        trust.write_text('[folders."/keep/me"]\ntrusted = true\ndecided_at = 1\n')
        monkeypatch.setattr(setup_env, "TRUST_FILE", trust)
        targets = setup_env.trust_targets(cfg)
        assert [p.name for p in targets] == ["b", "c"]
        added = setup_env.add_trust(cfg, targets)
        assert set(setup_env.trusted_folders(trust)) == {"/keep/me", *added}
        assert setup_env.add_trust(cfg, targets) == []  # idempotent
        setup_env.remove_trust(added)
        assert setup_env.trusted_folders(trust) == {"/keep/me"}

    def test_setup_requires_consent(self, cfg, tmp_path, monkeypatch):
        trust = tmp_path / "trusted_folders.toml"
        monkeypatch.setattr(setup_env, "TRUST_FILE", trust)
        with pytest.raises(setup_env.SetupError, match="not granted"):
            setup_env.setup(cfg, assume_yes=False, skip_venv=True, log=lambda _m: None,
                            confirm=lambda _p: "n")
        assert not trust.exists() or not setup_env.trusted_folders(trust)

    def test_setup_then_teardown_roundtrip(self, cfg, tmp_path, monkeypatch):
        trust = tmp_path / "trusted_folders.toml"
        trust.write_text('[folders."/keep/me"]\ntrusted = true\ndecided_at = 1\n')
        monkeypatch.setattr(setup_env, "TRUST_FILE", trust)
        added = setup_env.setup(cfg, assume_yes=True, skip_venv=True, log=lambda _m: None)
        assert len(added) == 2
        assert list(cfg.backups_dir.glob("trusted_folders.*.toml"))
        setup_env.teardown(cfg, log=lambda _m: None)
        assert setup_env.trusted_folders(trust) == {"/keep/me"}


# ── dry-run preflight (AT-008) ───────────────────────────────────────────────

class TestDryRun:
    """The dry-run preflight passes on a fake grok: no account, no model call."""

    def test_preflight_without_model_calls(self, cfg, fake_grok, tmp_path, monkeypatch):
        trust = tmp_path / "trusted_folders.toml"
        monkeypatch.setattr(setup_env, "TRUST_FILE", trust)
        setup_env.add_trust(cfg, setup_env.trust_targets(cfg))
        monkeypatch.setattr(setup_env, "canary", lambda _cfg: pytest.fail("canary makes a model call"))
        res = setup_env.smoke(cfg, model_calls=False, log=lambda _m: None)
        assert res.ok, [(c.name, c.detail) for c in res.checks if not c.ok]
        names = {c.name for c in res.checks}
        assert {"arm B context7 healthy", "arm C context7 healthy",
                "arm A has no context7", "arm D has no context7"} <= names
        assert not any(cfg.arms_root.rglob("fake_attempts")), "a prompt was sent to grok"
        assert not res.coverage

    def test_preflight_fails_when_context7_arm_untrusted(self, cfg, fake_grok, tmp_path, monkeypatch):
        monkeypatch.setattr(setup_env, "TRUST_FILE", tmp_path / "trusted_folders.toml")
        res = setup_env.smoke(cfg, model_calls=False, log=lambda _m: None)
        assert not res.ok
        assert {c.name for c in res.checks if not c.ok} == {"arm B trusted", "arm C trusted"}


# ── report ───────────────────────────────────────────────────────────────────

class TestReport:
    def test_report_renders_recommendation_and_caveat(self, cfg):
        store = RunStore(cfg.results_root / "run-report")
        for arm, outcome in (("A", "pass_first"), ("B", "pass_first"), ("C", "human"), ("D", "human")):
            store.append(Record(run_id="run-report", task="dbt-01", domain="dbt", stratum="library",
                                origin="synthetic", arm=arm, outcome=outcome, attempts=1, tokens=10))
        text = render(store, cfg)
        assert "substituir por B" in text
        assert "Indicativo, não estatístico" in text
        assert "Só tarefas sintéticas" in text
        assert "amostra de 1 execução" in text

    def test_unknown_outcome_rejected(self):
        with pytest.raises(ValueError):
            Record(run_id="r", task="t", domain="dbt", stratum="library", origin="synthetic",
                   arm="A", outcome="maybe", attempts=1)
