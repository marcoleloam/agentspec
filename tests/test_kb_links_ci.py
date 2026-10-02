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
        "2 < 3 and [broken](missing.md) > 1\n",
        ".claude/kb/source.md:1: missing.md\n",
        id="angle-bracket-prose-fails-ci",
    ),
    pytest.param(
        "2 < 3 and ![broken](missing.png) > 1\n",
        ".claude/kb/source.md:1: missing.png\n",
        id="angle-bracket-prose-image-fails-ci",
    ),
    pytest.param(
        "2 < 3 and [broken][ref] > 1\n\n[ref]: missing.md\n",
        ".claude/kb/source.md:1: missing.md\n",
        id="angle-bracket-prose-reference-fails-ci",
    ),
    pytest.param(
        '[x](missing.md "<!--")\n[y](other.md)\n',
        ".claude/kb/source.md:1: missing.md\n.claude/kb/source.md:2: other.md\n",
        id="comment-marker-in-title-fails-ci",
    ),
    pytest.param(
        '<a title="<!--">text</a>\n\n[real](missing.md)\n',
        ".claude/kb/source.md:3: missing.md\n",
        id="comment-marker-in-html-attribute-fails-ci",
    ),
    pytest.param(
        "<a title='<!--'>text</a>\n\n[real](missing.md)\n",
        ".claude/kb/source.md:3: missing.md\n",
        id="comment-marker-in-single-quoted-html-attribute-fails-ci",
    ),
    pytest.param(
        '<a title="first line\n<!-- [hidden](hidden.md)">text</a>\n\n'
        '[real](missing.md)\n<!-- [ignored](ignored.md) --> [after](after.md)\n',
        ".claude/kb/source.md:4: missing.md\n.claude/kb/source.md:5: after.md\n",
        id="multiline-html-attribute-preserves-real-ci-failures",
    ),
    pytest.param(
        "paragraph\n    [x](missing.md)\n",
        ".claude/kb/source.md:2: missing.md\n",
        id="indented-paragraph-continuation-fails-ci",
    ),
])
def test_ci_step_propagates_review_regressions(tmp_path, content, expected):
    workflow = yaml.safe_load((ROOT / WORKFLOW).read_text())
    step = next(step for step in workflow["jobs"]["python"]["steps"]
                if step.get("name") == "Lint KB links")
    (tmp_path / "scripts").mkdir()
    shutil.copyfile(ROOT / "scripts/lint_kb_links.py", tmp_path / "scripts/lint_kb_links.py")
    kb = tmp_path / ".claude/kb"
    kb.mkdir(parents=True)
    (kb / "source.md").write_text(content, encoding="utf-8")
    result = subprocess.run(
        ["bash", "--noprofile", "--norc", "-e", "-o", "pipefail", "-c", step["run"]],
        cwd=tmp_path, capture_output=True, text=True, timeout=30,
    )
    assert (result.returncode, result.stdout, result.stderr) == (1, expected, "")


@pytest.mark.parametrize("content, expected", [
    pytest.param(
        " \t[code](missing.md)\n",
        "",
        id="space-tab-indented-code-passes-ci",
    ),
    pytest.param(
        " \t[code](missing.md)\n\n[real](real-missing.md)\n",
        ".claude/kb/source.md:3: real-missing.md\n",
        id="space-tab-code-preserves-real-ci-failure",
    ),
    pytest.param(
        "[text <!-- ignored -->](missing.md)\n",
        ".claude/kb/source.md:1: missing.md\n",
        id="comment-in-link-label-fails-ci",
    ),
    pytest.param(
        "[text <!-- [hidden](hidden.md) -->](#local)\n",
        "",
        id="comment-in-valid-link-label-passes-ci",
    ),
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
    pytest.param(
        "- > ~~~\n  > [code](missing.md)\n  > ~~~\n",
        "",
        id="quoted-fence-inside-list-passes-ci",
    ),
    pytest.param(
        "- > ~~~\n  > [code](missing.md)\n  > ~~~\n"
        "\n[real](real-missing.md)\n",
        ".claude/kb/source.md:5: real-missing.md\n",
        id="quoted-list-fence-preserves-real-ci-failure",
    ),
    pytest.param(
        "`unmatched\n\n[x](missing.md)\n\n`\n",
        ".claude/kb/source.md:3: missing.md\n",
        id="backticks-in-separate-paragraphs-fail-ci",
    ),
    pytest.param(
        "`code\n[x](missing.md)\n`\n",
        "",
        id="inline-code-across-soft-breaks-passes-ci",
    ),
    pytest.param(
        "`open\n~~~\n`\n~~~\n[x](missing.md)\n",
        ".claude/kb/source.md:5: missing.md\n",
        id="unclosed-backtick-before-fence-preserves-ci-failure",
    ),
    pytest.param(
        "- > `open\r\n  > ~~~\r\n  > `\r\n  > ~~~\r\n"
        "  > [x](missing.md)\r\n",
        ".claude/kb/source.md:5: missing.md\n",
        id="unclosed-backtick-before-nested-fence-crlf-fails-ci",
    ),
    pytest.param(
        "`open\n~~~\n` [hidden](missing.md)\n~~~\n[x](#local)\n",
        "",
        id="unclosed-backtick-before-fence-with-valid-link-passes-ci",
    ),
    pytest.param(
        "# `heading\n[x](missing.md)\n`\n",
        ".claude/kb/source.md:2: missing.md\n",
        id="unclosed-heading-backtick-preserves-ci-failure",
    ),
    pytest.param(
        "> # ``heading\r\n[x](missing.md)\r\n``\r\n",
        ".claude/kb/source.md:2: missing.md\n",
        id="quoted-heading-backticks-crlf-preserve-ci-failure",
    ),
    pytest.param(
        "-     [code](missing-code.md)\n",
        "",
        id="list-opening-indented-code-passes-ci",
    ),
    pytest.param(
        "-     [code](missing-code.md)\r\n\r\n[real](missing.md)\r\n",
        ".claude/kb/source.md:3: missing.md\n",
        id="list-opening-code-preserves-real-ci-failure",
    ),
    pytest.param(
        "[a]: a`b.md\n[b]: missing.md\n[c]: c`d.md\n\n[b]\n",
        ".claude/kb/source.md:5: missing.md\n",
        id="literal-definition-backticks-preserve-ci-failure",
    ),
    pytest.param(
        "[a]: a`b.md\r\n[b]: ./missing.png?q=1#part\r\n[c]: c`d.md\r\n"
        "\r\n![b][] [full][b]\r\n",
        ".claude/kb/source.md:5: ./missing.png?q=1#part\n" * 2,
        id="literal-definition-backticks-preserve-image-and-link-ci-failures",
    ),
    pytest.param(
        "[a]: a`b.md\n[b]: #local\n[c]: c`d.md\n\n[b]\n",
        "",
        id="unused-backtick-definitions-with-valid-reference-pass-ci",
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


@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("label, expected", [
    ("a*", ""),
    (r"a\*", ".claude/kb/source.md:1: missing.md\n"),
])
def test_ci_step_keeps_escaped_reference_labels_distinct(tmp_path, reverse, label, expected):
    workflow = yaml.safe_load((ROOT / WORKFLOW).read_text())
    step = next(step for step in workflow["jobs"]["python"]["steps"]
                if step.get("name") == "Lint KB links")
    (tmp_path / "scripts").mkdir()
    shutil.copyfile(ROOT / "scripts/lint_kb_links.py", tmp_path / "scripts/lint_kb_links.py")
    kb = tmp_path / ".claude/kb"
    kb.mkdir(parents=True)
    (kb / "present.md").write_text("", encoding="utf-8")
    definitions = [r"[a\*]: missing.md", "[a*]: present.md"]
    if reverse:
        definitions.reverse()
    (kb / "source.md").write_text(
        f"[plain][{label}]\n\n" + "\n".join(definitions) + "\n", encoding="utf-8",
    )
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
