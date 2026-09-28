"""eval_llm_baseline.py and check_agent_selection_quality.py — no model call, fake CLI binaries only.

The fake ``codex``/``claude`` record argv, cwd and stdin kind to a JSON file and
print canned output in the shape the real CLIs emit.
"""
from __future__ import annotations

import importlib.util
import json
import sys
import tomllib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / "scripts"
SAMPLE_LABELS = REPO_ROOT / "tests" / "fixtures" / "agent_selection" / "labels_sample.json"

FAKE = r'''#!{python}
import json, os, stat, sys
from pathlib import Path
argv = sys.argv[1:]
mode = os.fstat(0).st_mode
log = {{"argv": argv, "cwd": os.getcwd(),
       "stdin_devnull": stat.S_ISCHR(mode) and os.path.samestat(os.fstat(0), os.stat(os.devnull)),
       "claudecode": os.environ.get("CLAUDECODE")}}
Path(os.environ["FAKE_LOG"]).write_text(json.dumps(log))
answer = {{"variant": "multiagent", "specialists": ["react-developer", "not-an-agent"]}}
if "{kind}" == "codex":
    out = argv[argv.index("-o") + 1]
    Path(out).write_text(json.dumps(answer))
    print("model: gpt-fake", file=sys.stderr)
else:
    style = os.environ.get("FAKE_CLAUDE", "structured")
    payload = {{"type": "result", "subtype": "success", "is_error": False,
               "modelUsage": {{"claude-fake-1": {{"inputTokens": 1}}}}}}
    if style == "structured":
        payload.update(result="", structured_output=answer)
    elif style == "fenced":
        payload.update(result="```json\n" + json.dumps(answer) + "\n```")
    else:
        payload.update(is_error=True, subtype="error_during_execution", result="boom")
    print(json.dumps(payload))
'''


def _load(name: str):
    sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def bl():
    return _load("eval_llm_baseline")


@pytest.fixture
def fake_bins(tmp_path, monkeypatch, bl):
    log = tmp_path / "fake.json"
    monkeypatch.setenv("FAKE_LOG", str(log))
    monkeypatch.setenv("CLAUDECODE", "1")
    bins = {}
    for kind in ("codex", "claude"):
        path = tmp_path / "bin" / kind
        path.parent.mkdir(exist_ok=True)
        path.write_text(FAKE.format(python=sys.executable, kind=kind))
        path.chmod(0o755)
        bins[kind] = path
    monkeypatch.setattr(bl, "CODEX_BIN", str(bins["codex"]))
    monkeypatch.setattr(bl, "CLAUDE_BIN", str(bins["claude"]))
    return lambda: json.loads(log.read_text())


def _config(argv: list[str]) -> dict[str, object]:
    out = {}
    for i, arg in enumerate(argv):
        if arg == "-c":
            key, _, raw = argv[i + 1].partition("=")
            out[key] = tomllib.loads(f"v = {raw}")["v"]
    return out


class TestCodexIsolation:
    def test_argv_uses_permission_profile_not_read_only_sandbox(self, bl, tmp_path, fake_bins):
        labels = tmp_path / "corpus" / "labels.json"
        labels.parent.mkdir()
        deny = bl.deny_roots([labels])
        answer = bl.ask_codex("PROMPT", tmp_path, bl.Options(deny=deny))
        call = fake_bins()
        argv = call["argv"]
        assert argv[:5] == ["exec", "--ephemeral", "--skip-git-repo-check", "--ignore-user-config", "-C"]
        assert "-s" not in argv and "read-only" not in argv
        assert argv[-2:] == ["--", "PROMPT"]
        cfg = _config(argv)
        policy = cfg[f"permissions.{bl.PERMISSION_PROFILE}.filesystem"]
        assert policy[":root"] == "read"
        assert policy[str(bl.REPO_ROOT.resolve())] == "none"
        assert policy[str(labels.parent.resolve())] == "none"
        assert cfg["default_permissions"] == bl.PERMISSION_PROFILE
        assert cfg["web_search"] == "disabled"
        assert call["stdin_devnull"] and Path(call["cwd"]).resolve() == tmp_path.resolve()
        assert answer["_provider_model"] == "gpt-fake"

    def test_default_deny_covers_transcripts_that_quote_labels(self, bl, tmp_path, monkeypatch):
        home = tmp_path / "home"
        for sub in (".claude", ".codex/sessions", ".omp"):
            (home / sub).mkdir(parents=True)
        monkeypatch.setenv("HOME", str(home))
        deny = bl.deny_roots([], ("~/extra-missing",))
        assert {home / ".claude", home / ".codex" / "sessions", home / ".omp"} <= {Path(p) for p in deny}
        assert home / ".codex" not in deny  # Codex itself still needs its home

    def test_scratch_inside_denied_folder_is_refused(self, bl, fake_bins):
        with pytest.raises(SystemExit):
            bl.main(["--provider", "codex", "--labels", str(SAMPLE_LABELS),
                     "--scratch", str(REPO_ROOT / ".pytest-scratch-refused")])
        assert not (REPO_ROOT / ".pytest-scratch-refused").exists()


class TestClaudeProvider:
    def test_argv_has_no_tools_no_mcp_no_user_settings(self, bl, tmp_path, fake_bins):
        answer = bl.ask_claude("PROMPT", tmp_path, bl.Options(model="opus"))
        call = fake_bins()
        argv = call["argv"]
        assert argv[0] == "-p" and argv[-2:] == ["--", "PROMPT"]
        assert argv[argv.index("--tools") + 1] == ""
        assert argv[argv.index("--output-format") + 1] == "json"
        assert json.loads(argv[argv.index("--json-schema") + 1]) == bl.SCHEMA
        assert argv[argv.index("--setting-sources") + 1] == "local"
        assert {"--strict-mcp-config", "--disable-slash-commands", "--no-session-persistence"} <= set(argv)
        assert argv[argv.index("--model") + 1] == "opus"
        assert call["stdin_devnull"] and call["claudecode"] is None
        assert answer["variant"] == "multiagent" and answer["_provider_model"] == "claude-fake-1"

    def test_fenced_result_text_is_parsed(self, bl, tmp_path, fake_bins, monkeypatch):
        monkeypatch.setenv("FAKE_CLAUDE", "fenced")
        assert bl.ask_claude("P", tmp_path)["specialists"] == ["react-developer", "not-an-agent"]

    def test_error_result_raises(self, bl, tmp_path, fake_bins, monkeypatch):
        monkeypatch.setenv("FAKE_CLAUDE", "error")
        with pytest.raises(Exception, match="claude -p failed"):
            bl.ask_claude("P", tmp_path)

    def test_end_to_end_main_filters_unknown_names(self, bl, tmp_path, fake_bins, capsys):
        assert bl.main(["--provider", "claude", "--labels", str(SAMPLE_LABELS),
                        "--scratch", str(tmp_path / "s"), "--workers", "1"]) == 0
        rows = json.loads(capsys.readouterr().out)
        assert rows and all(r["specialists"] == ["react-developer"] and r["unknown_names"] == ["not-an-agent"]
                            for r in rows.values())


class TestQualityCheck:
    @pytest.fixture
    def q(self, bl):
        return _load("check_agent_selection_quality")

    def test_provider_choices_include_claude(self, q):
        assert set(q.PROVIDERS) == {"codex", "claude"}

    def test_missing_corpus_fails_with_actionable_message(self, q, tmp_path, capsys):
        with pytest.raises(SystemExit) as exc:
            q.main(["--provider", "codex", "--labels-dir", str(tmp_path)])
        assert exc.value.code == 2
        err = capsys.readouterr().err
        assert "label corpus missing" in err and "--labels-dir" in err and "RECEIPT_SHA256" in err

    def test_counts_are_derived_from_the_corpus(self, q, tmp_path, capsys):
        cases = json.loads(SAMPLE_LABELS.read_text())["cases"]
        answers = {}
        for i, name in enumerate(q.LABEL_FILES):
            case = {**cases[i % len(cases)], "id": f"case-{i}"}
            (tmp_path / name).write_text(json.dumps({"cases": [case]}))
            answers[case["id"]] = {"variant": case["expected_variant"],
                                   "specialists": case["expected_specialists"], "provider_model": "fake"}
        answers_file = tmp_path / "answers.json"
        answers_file.write_text(json.dumps(answers))
        code = q.main(["--provider", "claude", "--labels-dir", str(tmp_path), "--answers", str(answers_file)])
        result = json.loads(capsys.readouterr().out)
        assert result["cases"] == 3
        assert result["multiagent_cases"] == sum(c["expected_variant"] == "multiagent"
                                                 for c in (cases[0], cases[1], cases[0]))
        assert result["corpus_matches_receipt"] is False
        assert code in (0, 1)

    def test_receipt_hashes_match_the_archived_receipt(self, q):
        receipt = (REPO_ROOT / ".claude" / "sdd" / "archive" / "JEV_AGENT_SELECTION"
                   / "EVAL_JEV_AGENT_SELECTION.json").read_text()
        for digest in q.RECEIPT_SHA256.values():
            assert digest in receipt
