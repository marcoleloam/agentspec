"""Check that the workflow runs the KB lint and propagates its failures."""

import fnmatch
import os
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


def test_ci_lints_real_checkout_kb():
    workflow = yaml.safe_load((ROOT / WORKFLOW).read_text())
    job = workflow["jobs"]["python"]
    steps = job["steps"]
    step = next(step for step in steps if step.get("name") == "Lint KB links")
    assert step["run"] == "python3 scripts/lint_kb_links.py"
    assert step["working-directory"] == "."
    assert "if" not in job and "if" not in step
    assert any(previous.get("uses", "").startswith("actions/checkout@")
               for previous in steps[:steps.index(step)])
    assert any(previous.get("uses", "").startswith("actions/setup-python@")
               for previous in steps[:steps.index(step)])
    result = subprocess.run(
        ["bash", "--noprofile", "--norc", "-e", "-o", "pipefail", "-c", step["run"]],
        cwd=ROOT, capture_output=True, text=True, timeout=90,
    )
    assert (result.returncode, result.stdout, result.stderr) == (0, "", "")


@pytest.mark.parametrize("content, expected", [
    pytest.param(
        "> [texto][ref]\n>\n> [ref]: ausente.md\n",
        ".claude/kb/source.md:1: ausente.md\n",
        id="quoted-reference-fails-ci",
    ),
    pytest.param(
        "- ~~~markdown\n  [exemplo](ausente.md)\n  ~~~\n\n"
        "[real](real-ausente.md)\n",
        ".claude/kb/source.md:5: real-ausente.md\n",
        id="list-fence-preserves-real-failure",
    ),
    pytest.param(
        "- ~~~markdown\n  [exemplo](ausente.md)\n  ~~~\n",
        "",
        id="list-code-example-passes-ci",
    ),
])
def test_ci_step_handles_markdown_containers(tmp_path, content, expected):
    workflow = yaml.safe_load((ROOT / WORKFLOW).read_text())
    step = next(step for step in workflow["jobs"]["python"]["steps"]
                if step.get("name") == "Lint KB links")
    (tmp_path / "scripts").mkdir()
    shutil.copyfile(ROOT / "scripts/lint_kb_links.py", tmp_path / "scripts/lint_kb_links.py")
    kb = tmp_path / ".claude/kb"
    kb.mkdir(parents=True)
    (kb / "source.md").write_bytes(content.encode("utf-8"))
    result = subprocess.run(
        ["bash", "--noprofile", "--norc", "-e", "-o", "pipefail", "-c", step["run"]],
        cwd=tmp_path, capture_output=True, text=True, timeout=30,
    )
    assert (result.returncode, result.stdout, result.stderr) == (
        1 if expected else 0, expected, "",
    )


@pytest.mark.parametrize("name, script", [
    ("Check agent-router drift", "generate-agent-router.py"),
    ("Check Codex agents and command skills drift", "generate-codex-plugin.py"),
    ("Check Grok plugin drift", "generate-grok-plugin.py"),
    ("Check plugin mirror drift", "build-plugin.sh"),
])
@pytest.mark.parametrize("status, dirty", [(0, False), (1, False), (0, True)])
def test_ci_drift_checks_remain_mandatory(tmp_path, name, script, status, dirty):
    workflow = yaml.safe_load((ROOT / WORKFLOW).read_text())
    job = workflow["jobs"]["python"]
    step = next(step for step in job["steps"] if step.get("name") == name)
    assert "if" not in job and "if" not in step
    assert not job.get("continue-on-error", False)
    assert not step.get("continue-on-error", False)

    # Execute the actual YAML command against stand-ins outside the checkout.
    # The generators and build must never write to the protected mirrors here.
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    if script.endswith(".py"):
        (scripts / script).write_text(
            "import sys\nfrom pathlib import Path\n"
            "assert sys.argv[1:] == ['--check']\n"
            "Path('invoked').write_text('yes')\n"
            f"raise SystemExit({status})\n"
        )
    else:
        build = tmp_path / script
        build.write_text(f"#!/bin/sh\nprintf yes > invoked\nexit {status}\n")
        build.chmod(0o755)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    git = bin_dir / "git"
    git.write_text(
        '#!/bin/sh\nif [ "$1" = status ]; then\n'
        + ('  echo " M plugin/drift.md"\n' if dirty else "  :\n")
        + "fi\nexit 0\n"
    )
    git.chmod(0o755)
    result = subprocess.run(
        ["bash", "--noprofile", "--norc", "-e", "-o", "pipefail", "-c", step["run"]],
        cwd=tmp_path, capture_output=True, text=True, timeout=30,
        env={**os.environ, "PATH": str(bin_dir) + os.pathsep + os.environ["PATH"]},
    )
    assert (tmp_path / "invoked").read_text() == "yes"
    expected = 1 if status or (dirty and script == "build-plugin.sh") else 0
    assert result.returncode == expected, result.stdout + result.stderr
