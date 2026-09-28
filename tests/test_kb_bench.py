"""Tests for scripts/kb_bench — no Codex, no model, no network, no eval venv required.

Parser/isolation tests use JSONL recorded from codex-cli 0.157.0 (spikes,
2026-09-27) plus fixtures synthesised in the same shapes; loop/CLI tests drive
a fake ``codex`` (tests/fixtures/kb_bench/fake_codex.py) and a fake Context7
MCP server (fake_context7.py) that answers with recorded outputs.
"""
from __future__ import annotations

import dataclasses
import json
import os
import sys
from pathlib import Path

import pytest
from kb_bench import codex_runner, context7_probe, isolation, loop, setup_env, workspace
from kb_bench.cli import main as cli_main
from kb_bench.config import ARM_LETTERS, BENCH_DIR, BenchConfig, load_config
from kb_bench.evals import discriminates
from kb_bench.human_queue import HumanQueue
from kb_bench.report import ArmScore, recommend, render
from kb_bench.store import Record, RunStore
from kb_bench.tasks import Eval, Task, TaskError, load_task, load_tasks
from kb_bench.transcript import parse_jsonl

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "kb_bench"
PLUGIN_KB = Path("/Users/tester/.claude/plugins/cache/agentspec/agentspec/3.7.0/kb")
REPO = Path("/Users/tester/projetos/framework/agentspec")


def _jsonl(*events: dict) -> str:
    return "".join(json.dumps(e) + "\n" for e in events)


def _cmd(command: str, output: str, exit_code: int, status: str, iid: str = "c") -> dict:
    return {"type": "item.completed", "item": {"id": iid, "type": "command_execution", "command": command,
                                               "aggregated_output": output, "exit_code": exit_code,
                                               "status": status}}


@pytest.fixture
def state_dir(tmp_path, monkeypatch):
    path = tmp_path / "fake-state"
    monkeypatch.setenv("FAKE_STATE_DIR", str(path))
    return path


@pytest.fixture
def cfg(tmp_path, monkeypatch, state_dir):
    monkeypatch.setenv("KB_BENCH_HOME", str(tmp_path / "home"))
    user_codex = tmp_path / "user-codex"
    user_codex.mkdir()
    (user_codex / "auth.json").write_text('{"auth_mode": "chatgpt"}')
    monkeypatch.setenv("KB_BENCH_USER_CODEX_HOME", str(user_codex))
    monkeypatch.delenv("CONTEXT7_API_KEY", raising=False)
    monkeypatch.delenv("KB_BENCH_MODEL", raising=False)
    config = dataclasses.replace(load_config(), context7_command=sys.executable,
                                 context7_args=(str(FIXTURES / "fake_context7.py"),),
                                 context7_startup_timeout_s=20)
    for letter in ARM_LETTERS:
        config.arm_dir(letter).mkdir(parents=True, exist_ok=True)
    return config


@pytest.fixture
def fake_codex(tmp_path, monkeypatch):
    script = tmp_path / "bin" / "codex"
    script.parent.mkdir()
    script.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{FIXTURES / "fake_codex.py"}" "$@"\n')
    script.chmod(0o755)
    monkeypatch.setattr(codex_runner, "CODEX_BIN", str(script))
    return script


@pytest.fixture
def eval_venv(tmp_path, monkeypatch):
    """Hermetic stand-in for scripts/kb_bench/.venv (smoke only checks that python exists)."""
    bin_dir = tmp_path / "eval-venv" / "bin"
    bin_dir.mkdir(parents=True)
    (bin_dir / "python").symlink_to(sys.executable)
    monkeypatch.setattr(BenchConfig, "eval_venv_bin", property(lambda _self: bin_dir))
    return bin_dir


def _execs(state_dir: Path) -> list[dict]:
    log = state_dir / "exec.jsonl"
    return [json.loads(line) for line in log.read_text().splitlines()] if log.is_file() else []


def _task(evals=None, fixtures=None) -> Task:
    return Task(
        id="unit-01-hello", domain="dbt", stratum="library", origin="synthetic",
        authored_from="test", prompt="Write hello to out.txt",
        evals=tuple(evals or (Eval("out exists", ("test", "-f", "out.txt")),
                              Eval("says hello", ("grep", "-q", "hello", "out.txt")))),
        source=Path("unit.toml"), fixtures=fixtures,
    )


def _ctx(cfg) -> loop.RunContext:
    store = RunStore(cfg.results_root / "run-test")
    return loop.RunContext(cfg=cfg, store=store, queue=HumanQueue(store.root), cli_version="fake",
                           log=lambda _m: None)


# ── transcript ───────────────────────────────────────────────────────────────

class TestTranscript:
    def test_real_trivial_run_usage(self):
        t = parse_jsonl((FIXTURES / "codex_trivial.jsonl").read_text())
        assert t.ended and not t.failed and t.turns == 1 and t.text == "OK"
        assert (t.input_tokens, t.cached_input_tokens, t.output_tokens) == (10665, 8704, 5)
        assert t.total_tokens == 10670 and t.fresh_tokens == 1966

    def test_real_quota_spike_items(self):
        t = parse_jsonl((FIXTURES / "codex_context7_quota.jsonl").read_text())
        (c7,) = t.mcp_calls("context7__")
        assert c7.mcp_tool == "context7__resolve-library-id" and c7.status == "completed"
        assert "Monthly quota exceeded" in c7.output_text
        (cmd,) = [c for c in t.tool_calls if c.tool == "command_execution"]
        assert cmd.status == "completed" and cmd.exit_code == 0 and "notes.txt" in cmd.command

    def test_real_turn_failed(self):
        t = parse_jsonl((FIXTURES / "codex_turn_failed_401.jsonl").read_text())
        assert t.failed and not t.ended and "401 Unauthorized" in t.error_message
        assert any("Reconnecting" in e for e in t.errors) and t.total_tokens is None

    def test_started_item_is_superseded_by_completed(self):
        t = parse_jsonl((FIXTURES / "codex_denied_read.jsonl").read_text())
        cmds = [c for c in t.tool_calls if c.tool == "command_execution"]
        assert [c.status for c in cmds] == ["failed", "failed"]
        assert all(c.permission_denied for c in cmds)
        (change,) = [c for c in t.tool_calls if c.tool == "file_change"]
        assert change.paths == ("/Users/tester/.kb-bench/arms/d/models/orders.sql",)

    def test_unfinished_item_stays_in_progress(self):
        raw = _jsonl({"type": "item.started", "item": {"id": "x", "type": "command_execution",
                                                       "command": "sleep 99", "status": "in_progress"}})
        (call,) = parse_jsonl(raw).tool_calls
        assert call.status == "in_progress"

    def test_malformed_lines_are_counted_not_fatal(self):
        t = parse_jsonl('not json\n[1]\n{"type": "item.completed", "item": {"id": "a", '
                        '"type": "agent_message", "text": "hi"}}\n')
        assert t.malformed_lines == 2 and t.text == "hi" and not t.ended


# ── isolation ────────────────────────────────────────────────────────────────

class TestIsolation:
    def test_denied_reads_are_counted_not_contamination(self, tmp_path):
        t = parse_jsonl((FIXTURES / "codex_denied_read.jsonl").read_text())
        v = isolation.check(t, uses_context7=False, deny=(PLUGIN_KB, REPO), cwd=tmp_path)
        assert not v.contaminated and v.kb_access_denied == 2

    def test_declined_read_is_neither(self, tmp_path):
        t = parse_jsonl((FIXTURES / "codex_canary_declined.jsonl").read_text())
        v = isolation.check(t, uses_context7=False, deny=(Path("/private/tmp/kbspike/benchhome/canary"),),
                            cwd=tmp_path)
        assert not v.contaminated and v.kb_access_denied == 0 and not t.tool_calls

    def test_completed_read_under_deny_is_contamination(self, tmp_path):
        raw = _jsonl(_cmd(f"/bin/zsh -lc 'cat {PLUGIN_KB}/dbt/index.md'", "# dbt KB\n", 0, "completed"))
        v = isolation.check(parse_jsonl(raw), uses_context7=False, deny=(PLUGIN_KB,), cwd=tmp_path)
        assert v.contaminated and "denied path" in v.reasons[0]

    def test_completed_empty_search_under_deny_is_only_denied(self, tmp_path):
        raw = _jsonl(_cmd(f"/bin/zsh -lc 'rg -l incremental {REPO} 2>/dev/null'", "", 0, "completed"))
        v = isolation.check(parse_jsonl(raw), uses_context7=False, deny=(REPO,), cwd=tmp_path)
        assert not v.contaminated and v.kb_access_denied == 1

    def test_prefix_sibling_is_not_a_deny_hit(self, tmp_path):
        raw = _jsonl(_cmd(f"/bin/zsh -lc 'cat {REPO}-notes/a.md'", "notes\n", 0, "completed"))
        v = isolation.check(parse_jsonl(raw), uses_context7=False, deny=(REPO,), cwd=tmp_path)
        assert not v.contaminated and v.kb_access_denied == 0

    def test_file_change_under_deny_is_contamination(self, tmp_path):
        raw = _jsonl({"type": "item.completed", "item": {"id": "f", "type": "file_change", "status": "completed",
                                                         "changes": [{"path": str(REPO / "x.md"), "kind": "add"}]}})
        assert isolation.check(parse_jsonl(raw), uses_context7=False, deny=(REPO,), cwd=tmp_path).contaminated

    def test_context7_in_non_mcp_arm_is_contamination(self, tmp_path):
        t = parse_jsonl((FIXTURES / "codex_context7_calls.jsonl").read_text())
        assert isolation.check(t, uses_context7=False, deny=(), cwd=tmp_path).contaminated
        v = isolation.check(t, uses_context7=True, deny=(), cwd=tmp_path)
        assert not v.contaminated and v.context7_calls == 7

    def test_quota_answer_is_unavailable_not_a_call(self, tmp_path):
        t = parse_jsonl((FIXTURES / "codex_context7_quota.jsonl").read_text())
        v = isolation.check(t, uses_context7=True, deny=(), cwd=tmp_path)
        assert v.context7_calls == 0 and v.context7_failed == 1 and v.context7_unavailable

    def test_web_search_is_contamination(self, tmp_path):
        raw = _jsonl({"type": "item.completed", "item": {"id": "w", "type": "web_search", "query": "dbt"}})
        assert isolation.check(parse_jsonl(raw), uses_context7=True, deny=(), cwd=tmp_path).contaminated

    def test_mcp_start_failure_is_missing(self, tmp_path):
        raw = _jsonl({"type": "error", "message": "MCP client for `context7` failed to start: program not found"},
                     {"type": "turn.completed", "usage": {}})
        assert isolation.check(parse_jsonl(raw), uses_context7=True, deny=(), cwd=tmp_path).mcp_missing

    def test_private_tmp_alias_matches(self):
        assert isolation.under(Path("/tmp/x/kb/a.md"), (Path("/private/tmp/x"),))


def test_feedback_hides_evaluator_paths(tmp_path):
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
        task = Task(**{**_task().__dict__, "solution": sol})
        result = discriminates(task, cfg)
        assert result.ok and result.fails_on_fixtures and result.solution_passes


# ── Codex command line per arm ───────────────────────────────────────────────

def _overrides(argv: list[str]) -> dict[str, str]:
    return dict(argv[i + 1].split("=", 1) for i, a in enumerate(argv) if a == "-c")


class TestCodexArgv:
    def test_exec_flags_and_prompt_last(self, cfg):
        argv = codex_runner.build_argv("-starts with a dash", cfg, cfg.arms["D"], cfg.arm_dir("D"))
        assert argv[1:3] == ["exec", "--json"]
        assert {"--ephemeral", "--skip-git-repo-check", "--ignore-user-config"} <= set(argv)
        assert argv[-2:] == ["--", "-starts with a dash"]
        assert argv[argv.index("-m") + 1] == "gpt-6-astra"
        over = _overrides(argv)
        assert over["approval_policy"] == '"never"' and over["web_search"] == '"disabled"'
        assert over["default_permissions"] == '"kbbench"'
        assert [argv[i + 1] for i, a in enumerate(argv) if a == "--disable"] == list(cfg.disabled_features)

    def test_context7_only_in_b_and_c(self, cfg):
        for letter in ARM_LETTERS:
            over = _overrides(codex_runner.build_argv("p", cfg, cfg.arms[letter], cfg.arm_dir(letter)))
            assert ("mcp_servers.context7.command" in over) == (letter in {"B", "C"})
            assert not any(k.startswith("mcp_servers.") and "context7" not in k for k in over)

    def test_api_key_forwarded_by_name_only(self, cfg, monkeypatch):
        monkeypatch.setenv("CONTEXT7_API_KEY", "ctx7sk-secret-value")
        argv = codex_runner.build_argv("p", cfg, cfg.arms["B"], cfg.arm_dir("B"))
        assert _overrides(argv)["mcp_servers.context7.env_vars"] == '["CONTEXT7_API_KEY"]'
        assert not any("ctx7sk-secret-value" in a for a in argv)
        assert "CONTEXT7_API_KEY" not in codex_runner.agent_env(cfg, cfg.arms["D"])

    def test_filesystem_policy_is_toml_and_denies(self, cfg):
        import tomllib
        deny = cfg.deny_paths("D")
        policy = tomllib.loads("v = " + codex_runner.filesystem_policy(cfg, deny))["v"]
        assert policy[":root"] == "read" and policy[":project_roots"] == {".": "write"}
        assert policy[str(codex_runner.scratch_dir(cfg))] == "write"
        none = {p for p, mode in policy.items() if mode == "none"}
        assert str(BENCH_DIR.parent.parent) in none and str(cfg.canary_dir.resolve()) in none
        assert str(cfg.user_codex_home) in none and str(cfg.results_root.resolve()) in none
        assert {str(cfg.arm_dir(x).resolve()) for x in "ABC"} <= none
        assert str(cfg.arm_dir("D").resolve()) not in none

    def test_attempt_env_is_isolated(self, cfg):
        env = codex_runner.agent_env(cfg, cfg.arms["A"])
        assert env["HOME"] == str(cfg.agent_home) and env["CODEX_HOME"] == str(cfg.codex_home)
        assert env["TMPDIR"].startswith(str(cfg.agent_home)) and env["TMPPREFIX"].startswith(str(cfg.agent_home))


class TestAgentHome:
    def test_reset_keeps_only_the_auth_symlink(self, cfg):
        codex_runner.reset_agent_home(cfg)
        (cfg.codex_home / "logs_2.sqlite").write_text("previous attempt")
        (codex_runner.scratch_dir(cfg) / "notes.md").write_text("kb notes")
        (cfg.agent_home / ".zshrc").write_text("x")
        codex_runner.reset_agent_home(cfg)
        assert sorted(p.name for p in cfg.codex_home.iterdir()) == ["auth.json"]
        assert (cfg.codex_home / "auth.json").resolve() == cfg.user_auth_file.resolve()
        assert not any(codex_runner.scratch_dir(cfg).iterdir()) and not (cfg.agent_home / ".zshrc").exists()

    def test_refreshed_auth_moves_back_to_user(self, cfg):
        codex_runner.reset_agent_home(cfg)
        link = cfg.codex_home / "auth.json"
        link.unlink()
        link.write_text('{"refreshed": true}')   # Codex replaced the symlink atomically
        assert codex_runner.sync_auth_back(cfg)
        assert link.is_symlink() and json.loads(cfg.user_auth_file.read_text()) == {"refreshed": True}
        assert oct(cfg.user_auth_file.stat().st_mode & 0o777) == "0o600"

    def test_missing_login_is_reported(self, cfg):
        cfg.user_auth_file.unlink()
        with pytest.raises(codex_runner.CodexHomeError, match="codex login"):
            codex_runner.reset_agent_home(cfg)

    def test_teardown_removes_agent_home_only(self, cfg):
        codex_runner.reset_agent_home(cfg)
        store = RunStore(cfg.results_root / "old-run")
        assert setup_env.teardown(cfg, log=lambda _m: None)
        assert not cfg.agent_home.exists() and store.root.is_dir() and cfg.user_auth_file.is_file()


# ── workspace ────────────────────────────────────────────────────────────────

class TestWorkspace:
    def test_prepare_copies_kb_per_arm(self, cfg):
        task = Task(**{**_task().__dict__, "domain": "dbt"})
        a = workspace.prepare(cfg.arms["A"], task, cfg, fresh=True)
        assert (a / "kb" / "index.md").is_file()
        c = workspace.prepare(cfg.arms["C"], task, cfg, fresh=True)
        assert (c / "kb" / "anti-patterns.md").is_file()
        for letter in ("B", "D"):
            assert not (workspace.prepare(cfg.arms[letter], task, cfg, fresh=True) / "kb").exists()

    def test_nothing_bench_specific_in_the_arm_folder(self, cfg):
        arm_dir = workspace.prepare(cfg.arms["B"], _task(), cfg, fresh=True)
        assert not any(arm_dir.iterdir())

    def test_reset_refuses_outside_home(self, cfg, tmp_path):
        with pytest.raises(workspace.WorkspaceError):
            workspace.reset_arm_dir(tmp_path / "elsewhere", cfg)


# ── Context7 probe (no model) ────────────────────────────────────────────────

class TestContext7Probe:
    def test_handshake_lists_tools(self, cfg, tmp_path):
        res = context7_probe.probe(cfg, tmp_path)
        assert res.ok and set(res.tools) == {"resolve-library-id", "query-docs"}

    def test_server_down(self, cfg, tmp_path, monkeypatch):
        monkeypatch.setenv("FAKE_C7", "down")
        res = context7_probe.probe(cfg, tmp_path)
        assert not res.ok and "exited" in res.detail

    def test_quota_refusal_fails_the_probe(self, cfg, tmp_path, monkeypatch):
        monkeypatch.setenv("FAKE_C7", "quota")
        res = context7_probe.probe(cfg, tmp_path, resolve=("dbt",))
        assert not res.ok and "quota exceeded" in res.detail.lower()

    def test_coverage_from_recorded_outputs(self, cfg):
        res, cov = setup_env.coverage(cfg)
        assert res.ok
        assert cov["airflow"] == {"status": "covered", "library_id": "/apache/airflow", "title": "Apache Airflow"}
        assert cov["dbt"]["status"] == "covered" and cov["shadowtraffic"]["status"] == "covered"
        assert cov["medallion"]["status"] == "not_covered"

    def test_key_reaches_the_server_env_only(self, cfg, state_dir, monkeypatch):
        monkeypatch.setenv("CONTEXT7_API_KEY", "ctx7sk-secret-value")
        assert context7_probe.probe(cfg, cfg.arm_dir("B"), env=codex_runner.agent_env(cfg, cfg.arms["B"])).ok
        (start,) = [json.loads(x) for x in (state_dir / "c7.jsonl").read_text().splitlines()]
        assert start == {"has_key": True, "npm_cache": str(cfg.npm_cache_dir)}


# ── loop with fake codex (AT-003/004/005/009) ────────────────────────────────

class TestLoop:
    def _run(self, cfg, monkeypatch, scenario, arm="D", **env):
        monkeypatch.setenv("FAKE_SCENARIO", scenario)
        for k, v in env.items():
            monkeypatch.setenv(k, v)
        return loop.run_pair(_task(), cfg.arms[arm], _ctx(cfg))

    def test_pass_first_with_isolated_env(self, cfg, fake_codex, state_dir, monkeypatch):
        rec = self._run(cfg, monkeypatch, "solve")
        assert rec.outcome == "pass_first" and rec.attempts == 1
        assert rec.tokens == 1000 and rec.fresh_tokens == 600 and rec.model == "gpt-6-astra"
        (call,) = _execs(state_dir)
        assert call["stdin_devnull"] and call["auth_is_symlink"]
        assert call["home"] == str(cfg.agent_home) and call["codex_home"] == str(cfg.codex_home)
        transcript = cfg.results_root / "run-test" / "transcripts" / "unit-01-hello__D__1.jsonl"
        assert parse_jsonl(transcript.read_text()).ended

    def test_pass_retry_accumulates_tokens(self, cfg, fake_codex, monkeypatch):
        rec = self._run(cfg, monkeypatch, "fail_then_solve")
        assert rec.outcome == "pass_retry" and rec.attempts == 2 and rec.tokens == 2000

    def test_exhausted_retries_go_to_blind_human_queue(self, cfg, fake_codex, monkeypatch):
        rec = self._run(cfg, monkeypatch, "never")
        assert rec.outcome == "human" and rec.attempts == 3 and rec.human_id
        queue = HumanQueue(cfg.results_root / "run-test")
        item = (queue.dir / f"{rec.human_id}.md").read_text()
        assert "says hello" in item and "out.txt" in item
        assert "D — " not in item and "arm" not in item.lower()
        assert queue.mapping()[rec.human_id] == {"arm": "D", "task": "unit-01-hello"}

    def test_no_turn_completed_is_timeout(self, cfg, fake_codex, monkeypatch):
        rec = self._run(cfg, monkeypatch, "hang")
        assert rec.outcome == "timeout" and "no turn.completed" in rec.reason

    def test_failed_turn_is_timeout(self, cfg, fake_codex, monkeypatch):
        rec = self._run(cfg, monkeypatch, "turn_failed")
        assert rec.outcome == "timeout" and "turn failed" in rec.reason

    def test_usage_limit_stops_the_run(self, cfg, fake_codex, monkeypatch):
        with pytest.raises(loop.ExecutorStopped, match="usage limit"):
            self._run(cfg, monkeypatch, "usage_limit")

    def test_completed_read_of_deny_path_is_contaminated(self, cfg, fake_codex, monkeypatch):
        deny = str(cfg.canary_dir / "canary.txt")
        rec = self._run(cfg, monkeypatch, "leak", FAKE_DENY_PATH=deny)
        assert rec.outcome == "contaminated" and rec.contamination_reasons

    def test_read_of_other_arm_folder_is_contaminated(self, cfg, fake_codex, monkeypatch):
        rec = self._run(cfg, monkeypatch, "leak", FAKE_DENY_PATH=str(cfg.arm_dir("A") / "kb" / "index.md"))
        assert rec.outcome == "contaminated"

    def test_context7_preflight_failure_is_unavailable(self, cfg, fake_codex, state_dir, monkeypatch):
        rec = self._run(cfg, monkeypatch, "solve", arm="B", FAKE_C7="down")
        assert rec.outcome == "unavailable" and rec.attempts == 0 and not _execs(state_dir)

    def test_context7_transport_failure_is_unavailable(self, cfg, fake_codex, monkeypatch):
        rec = self._run(cfg, monkeypatch, "c7_down", arm="B")
        assert rec.outcome == "unavailable"

    def test_context7_quota_in_session_is_unavailable(self, cfg, fake_codex, monkeypatch):
        rec = self._run(cfg, monkeypatch, "c7_quota", arm="C")
        assert rec.outcome == "unavailable" and rec.context7_calls == 0

    def test_context7_missing_in_session_is_unavailable(self, cfg, fake_codex, monkeypatch):
        rec = self._run(cfg, monkeypatch, "mcp_missing", arm="B")
        assert rec.outcome == "unavailable" and "not available" in rec.reason

    def test_context7_arm_counts_calls(self, cfg, fake_codex, monkeypatch):
        rec = self._run(cfg, monkeypatch, "c7", arm="C")
        assert rec.outcome == "pass_first" and rec.context7_calls == 1

    def test_budget_is_fresh_tokens(self, cfg, fake_codex, monkeypatch):
        monkeypatch.setenv("FAKE_SCENARIO", "solve")
        ctx = _ctx(dataclasses.replace(cfg, budget_tokens=500))
        tasks = [_task(), Task(**{**_task().__dict__, "id": "unit-02-x"})]
        with pytest.raises(loop.BudgetExceeded, match="600"):
            loop.run_plan(tasks, ["D"], ctx)
        assert len(ctx.store.records()) == 1

    def test_plan_is_seeded(self):
        tasks = [_task(), Task(**{**_task().__dict__, "id": "unit-02-x"})]
        assert loop.plan(tasks, list(ARM_LETTERS), 7) == loop.plan(tasks, list(ARM_LETTERS), 7)
        assert len(loop.plan(tasks, list(ARM_LETTERS), 7)) == 8

    def test_prompt_differs_only_by_arm_preamble(self):
        t = _task()
        assert loop.build_prompt(t, load_config().arms["D"]).startswith(t.prompt)
        assert "./kb/" in loop.build_prompt(t, load_config().arms["A"])
        assert "context7" in loop.build_prompt(t, load_config().arms["B"])


# ── smoke / dry-run preflight (AT-008) ───────────────────────────────────────

class TestSmoke:
    """The preflight passes on a fake codex + fake Context7: no account, no model call."""

    def test_preflight_without_model_calls(self, cfg, fake_codex, eval_venv, state_dir):
        res = setup_env.smoke(cfg, model_calls=False, log=lambda _m: None)
        assert res.ok, [(c.name, c.detail) for c in res.checks if not c.ok]
        names = {c.name for c in res.checks}
        assert {"arm B has context7", "arm C has context7", "arm A has no context7", "arm D has no context7",
                "arm B context7 starts", "sandbox canary", "codex login (isolated home)"} <= names
        assert not _execs(state_dir), "a prompt was sent to codex"
        assert not res.coverage and res.warnings  # no CONTEXT7_API_KEY → loud warning

    def test_full_smoke_probes_quota_and_runs_one_canary(self, cfg, fake_codex, eval_venv, state_dir):
        res = setup_env.smoke(cfg, model_calls=True, log=lambda _m: None)
        assert res.ok, [(c.name, c.detail) for c in res.checks if not c.ok]
        assert res.coverage["airflow"]["status"] == "covered"
        assert len(_execs(state_dir)) == 1
        assert "declined" in next(c.detail for c in res.checks if c.name == "exec canary")

    def test_quota_exceeded_fails_smoke_before_the_model_call(self, cfg, fake_codex, eval_venv, state_dir,
                                                               monkeypatch):
        monkeypatch.setenv("FAKE_C7", "quota")
        res = setup_env.smoke(cfg, model_calls=True, log=lambda _m: None)
        assert [c.name for c in res.checks if not c.ok] == ["context7 quota available"]
        assert not _execs(state_dir)

    def test_exec_canary_sees_the_denial(self, cfg, fake_codex, monkeypatch):
        monkeypatch.setenv("FAKE_SCENARIO", "canary_denied")
        check = setup_env.exec_canary(cfg)
        assert check.ok and "Operation not permitted" in check.detail

    def test_unknown_feature_fails_smoke(self, cfg, fake_codex, eval_venv):
        bad = dataclasses.replace(cfg, disabled_features=("no_such_feature",))
        res = setup_env.smoke(bad, model_calls=False, log=lambda _m: None)
        assert [c.name for c in res.checks if not c.ok] == ["disabled features accepted"]

    def test_missing_login_fails_smoke(self, cfg, fake_codex, eval_venv):
        cfg.user_auth_file.unlink()
        res = setup_env.smoke(cfg, model_calls=False, log=lambda _m: None)
        assert not res.ok and "codex login" in res.checks[-1].detail

    def test_cli_dry_run_makes_no_model_call(self, cfg, fake_codex, eval_venv, state_dir, monkeypatch, capsys):
        monkeypatch.setattr("kb_bench.cli.load_config", lambda _p=None: cfg)
        monkeypatch.setattr("kb_bench.cli._validate", lambda *_a, **_k: 0)
        assert cli_main(["run", "--dry-run", "--task", "dbt-01-incremental-orders"]) == 0
        assert "4 (task, arm) pairs planned" in capsys.readouterr().out
        assert not _execs(state_dir)

    def test_setup_creates_home_without_consent_prompt(self, cfg):
        setup_env.setup(cfg, skip_venv=True, log=lambda _m: None)
        assert (cfg.codex_home / "auth.json").is_symlink()
        assert os.readlink(cfg.codex_home / "auth.json") == str(cfg.user_auth_file)


# ── report ───────────────────────────────────────────────────────────────────

class TestReport:
    def test_report_renders_recommendation_and_caveat(self, cfg):
        store = RunStore(cfg.results_root / "run-report")
        for arm, outcome in (("A", "pass_first"), ("B", "pass_first"), ("C", "human"), ("D", "human")):
            store.append(Record(run_id="run-report", task="dbt-01", domain="dbt", stratum="library",
                                origin="synthetic", arm=arm, outcome=outcome, attempts=1, tokens=10,
                                fresh_tokens=4))
        text = render(store, cfg)
        assert "substituir por B" in text
        assert "Indicativo, não estatístico" in text
        assert "Só tarefas sintéticas" in text
        assert "amostra de 1 execução" in text
        assert "40 / 16" in text and "US$ não medido" in text

    def test_old_records_still_load(self):
        old = {"run_id": "r", "task": "t", "domain": "dbt", "stratum": "library", "origin": "synthetic",
               "arm": "A", "outcome": "pass_first", "attempts": 1, "cost_usd": 0.4, "tokens": 9}
        assert Record.from_dict(old).tokens == 9

    def test_unknown_outcome_rejected(self):
        with pytest.raises(ValueError):
            Record(run_id="r", task="t", domain="dbt", stratum="library", origin="synthetic",
                   arm="A", outcome="maybe", attempts=1)
