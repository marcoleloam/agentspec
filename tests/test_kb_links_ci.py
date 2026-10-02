"""Check that the workflow runs the KB lint and propagates its failures."""

import fnmatch
from pathlib import Path
import shutil
import subprocess

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ".github/workflows/quality-checks.yml"


def test_kb_ci_event_filters():
    workflow = yaml.safe_load((ROOT / WORKFLOW).read_text())
    # PyYAML's YAML 1.1 loader treats the unquoted key `on` as True.
    events = workflow.get("on", workflow.get(True))
    for event in ("push", "pull_request"):
        config = events[event]
        for branch in ("main", "df/bf02-baseline-9de8ce4"):
            assert branch in config["branches"]
        for path in (
            ".claude/kb/deep/topic.MD", "scripts/lint_kb_links.py",
            "tests/test_lint_kb_links.py", "tests/test_kb_links_ci.py", WORKFLOW,
        ):
            assert any(fnmatch.fnmatchcase(path, pattern) for pattern in config["paths"])


@pytest.mark.parametrize("content, status", [(b"[ok](#local)", 0), (b"[bad](missing.md)", 1), (b"\xff", 2)])
def test_ci_step_propagates_lint_exit_status(tmp_path, content, status):
    workflow = yaml.safe_load((ROOT / WORKFLOW).read_text())
    job = workflow["jobs"]["python"]
    step = next(step for step in job["steps"] if step.get("name") == "Lint KB links")
    assert not job.get("continue-on-error", False)
    assert not step.get("continue-on-error", False)
    assert step["working-directory"] == "."

    (tmp_path / "scripts").mkdir()
    shutil.copyfile(ROOT / "scripts/lint_kb_links.py", tmp_path / "scripts/lint_kb_links.py")
    kb = tmp_path / ".claude/kb"
    kb.mkdir(parents=True)
    (kb / "source.md").write_bytes(content)
    result = subprocess.run(
        ["bash", "--noprofile", "--norc", "-e", "-o", "pipefail", "-c", step["run"]],
        cwd=tmp_path, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == status, result.stdout + result.stderr
    if status == 1:
        assert result.stdout == ".claude/kb/source.md:1: missing.md\n"
    elif status == 2:
        assert "lint_kb_links:" in result.stderr
