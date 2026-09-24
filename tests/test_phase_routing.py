"""Tests for scripts/phase_routing.py — manifest validation, drift checks, apply, OMP output."""
from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import phase_routing as pr

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "phase_routing.py"

MANIFEST = """\
schema_version = 1

[agents.design-agent]
omp_role = "slow"
claude_model = "opus"
codex_effort = "high"

[agents.ship-agent]
omp_role = "smol"
claude_model = "haiku"
codex_effort = "low"

[commands.design]
mode = "delegated"
agent = "design-agent"

[commands.brainstorm]
mode = "session"
recommended_role = "plan"
"""

AGENT = """\
---
name: {name}
description: test agent
tier: T2
model: {model}
tools: [Read, Write]
---

# {name}
"""

COMMAND = """\
---
name: {stem}
description: test command
---

# {stem} Command
{marker}
Body.
"""

CONTRACTS = """\
workflow:
  phases:
    - name: "Design"
      agent: "design-agent"

eval:
  jev:
    model: "typesafe/jev-1.13"
"""


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A minimal repo that is fully in sync with MANIFEST."""
    _write(tmp_path / pr.MANIFEST_REL, MANIFEST)
    _write(tmp_path / pr.AGENTS_REL / "design-agent.md", AGENT.format(name="design-agent", model="opus"))
    _write(tmp_path / pr.AGENTS_REL / "ship-agent.md", AGENT.format(name="ship-agent", model="haiku"))
    _write(tmp_path / pr.AGENTS_REL / "README.md", "# Workflow agents\n")
    _write(
        tmp_path / pr.COMMANDS_REL / "design.md",
        COMMAND.format(stem="design", marker="\n<!-- phase-routing: mode=delegated agent=design-agent -->\n"),
    )
    _write(
        tmp_path / pr.COMMANDS_REL / "brainstorm.md",
        COMMAND.format(stem="brainstorm", marker="\n<!-- phase-routing: mode=session role=plan -->\n"),
    )
    _write(tmp_path / pr.COMMANDS_REL / "create-pr.md", COMMAND.format(stem="create-pr", marker=""))
    _write(tmp_path / pr.CONTRACTS_REL, CONTRACTS)
    _write(tmp_path / pr.PLUGIN_AGENTS_REL / "design-agent.md", AGENT.format(name="design-agent", model="opus"))
    return tmp_path


# ── load() ──────────────────────────────────────────────────────────────────


def test_load_parses_routes(repo: Path) -> None:
    agents, commands = pr.load(repo / pr.MANIFEST_REL)
    assert agents["design-agent"] == pr.AgentRoute("design-agent", "slow", "opus", "high")
    assert commands["design"].marker() == "<!-- phase-routing: mode=delegated agent=design-agent -->"
    assert commands["brainstorm"].marker() == "<!-- phase-routing: mode=session role=plan -->"


@pytest.mark.parametrize(
    ("old", "new", "fragment"),
    [
        ('claude_model = "opus"', 'claude_model = "gpt5"', "claude_model expected"),
        ('codex_effort = "high"', 'codex_effort = "xhigh"', "codex_effort expected"),
        ('omp_role = "slow"', 'omp_role = "@slow"', "omp_role invalid"),
        ('agent = "design-agent"', 'agent = "ghost-agent"', "must name an [agents] entry"),
        ('recommended_role = "plan"', 'recommended_role = ""', "recommended_role invalid"),
        ('mode = "session"', 'mode = "forked"', "mode expected"),
        ("schema_version = 1", "schema_version = 2", "schema_version expected 1"),
        ('omp_role = "smol"', 'omp_role = "smol"  # was gpt-6-astra', "concrete model id"),
    ],
)
def test_load_rejects_invalid_manifest(repo: Path, old: str, new: str, fragment: str) -> None:
    path = repo / pr.MANIFEST_REL
    path.write_text(path.read_text().replace(old, new, 1))
    with pytest.raises(ValueError, match=None) as excinfo:
        pr.load(path)
    assert fragment in str(excinfo.value)


def test_load_rejects_invalid_toml(repo: Path) -> None:
    path = repo / pr.MANIFEST_REL
    path.write_text("schema_version = \n")
    with pytest.raises(ValueError, match="invalid TOML"):
        pr.load(path)


# ── check() ─────────────────────────────────────────────────────────────────


def test_check_clean_repo_has_no_errors(repo: Path) -> None:
    assert pr.check(repo) == []


def test_check_reports_frontmatter_drift(repo: Path) -> None:
    agent = repo / pr.AGENTS_REL / "design-agent.md"
    agent.write_text(agent.read_text().replace("model: opus", "model: sonnet"))
    errors = pr.check(repo)
    assert errors == [".claude/agents/workflow/design-agent.md: model expected opus, found sonnet"]


def test_check_reports_concrete_id_in_frontmatter(repo: Path) -> None:
    agent = repo / pr.AGENTS_REL / "ship-agent.md"
    agent.write_text(agent.read_text().replace("tier: T2", "tier: T2\nnote: tuned-for-grok-4.6"))
    assert any("concrete model id 'grok-4.6'" in e for e in pr.check(repo))


def test_check_reports_agent_set_mismatch(repo: Path) -> None:
    _write(repo / pr.AGENTS_REL / "extra-agent.md", AGENT.format(name="extra-agent", model="opus"))
    (repo / pr.AGENTS_REL / "ship-agent.md").unlink()
    errors = pr.check(repo)
    assert any("extra-agent.md: agent missing from" in e for e in errors)
    assert any("agents.ship-agent has no file" in e for e in errors)


def test_check_reports_command_set_mismatch(repo: Path) -> None:
    _write(repo / pr.COMMANDS_REL / "newphase.md", COMMAND.format(stem="newphase", marker=""))
    errors = pr.check(repo)
    assert any("newphase.md: command missing from" in e for e in errors)
    assert not any("create-pr" in e for e in errors)


def test_check_reports_wrong_and_duplicate_markers(repo: Path) -> None:
    design = repo / pr.COMMANDS_REL / "design.md"
    design.write_text(design.read_text().replace("mode=delegated agent=design-agent", "mode=session role=slow"))
    brainstorm = repo / pr.COMMANDS_REL / "brainstorm.md"
    brainstorm.write_text(brainstorm.read_text() + "\n<!-- phase-routing: mode=session role=plan -->\n")
    errors = pr.check(repo)
    assert any("design.md: phase-routing marker expected <!-- phase-routing: mode=delegated" in e for e in errors)
    assert any("brainstorm.md: phase-routing marker expected exactly 1" in e and "found 2" in e for e in errors)


def test_check_reports_alias_model_in_contracts_but_not_jev(repo: Path) -> None:
    contracts = repo / pr.CONTRACTS_REL
    contracts.write_text(contracts.read_text().replace('agent: "design-agent"', 'agent: "design-agent"\n      model: "opus"'))
    errors = pr.check(repo)
    assert errors == [
        ".claude/sdd/architecture/WORKFLOW_CONTRACTS.yaml:5: model expected none "
        "(routing lives in PHASE_MODEL_ROLES.toml), found opus"
    ]


def test_check_reports_nested_plugin_agents(repo: Path) -> None:
    _write(repo / pr.PLUGIN_AGENTS_REL / "workflow" / "ship-agent.md", "x")
    _write(repo / pr.PLUGIN_AGENTS_REL / "README.md", "x")
    errors = pr.check(repo)
    assert any("plugin/agents/workflow: subdirectory expected none" in e for e in errors)
    assert any("plugin/agents/README.md: file expected absent" in e for e in errors)


def test_check_reports_invalid_manifest_as_single_error(repo: Path) -> None:
    (repo / pr.MANIFEST_REL).write_text("schema_version = 1\n")
    errors = pr.check(repo)
    assert len(errors) == 1 and "no [agents] entries" in errors[0]


# ── apply() ─────────────────────────────────────────────────────────────────


def test_apply_syncs_models_and_markers_idempotently(repo: Path) -> None:
    ship = repo / pr.AGENTS_REL / "ship-agent.md"
    ship.write_text(ship.read_text().replace("model: haiku", "model: sonnet"))
    design_agent = repo / pr.AGENTS_REL / "design-agent.md"
    design_agent.write_text(design_agent.read_text().replace("model: opus\n", ""))
    brainstorm = repo / pr.COMMANDS_REL / "brainstorm.md"
    brainstorm.write_text(COMMAND.format(stem="brainstorm", marker=""))
    design = repo / pr.COMMANDS_REL / "design.md"
    design.write_text(
        design.read_text().replace("mode=delegated agent=design-agent", "mode=session role=x")
        + "<!-- phase-routing: mode=session role=y -->\n"
    )

    changed = {p.name for p in pr.apply(repo)}

    assert changed == {"ship-agent.md", "design-agent.md", "brainstorm.md", "design.md"}
    assert pr.check(repo) == []
    assert "name: design-agent\nmodel: opus\n" in design_agent.read_text()
    assert brainstorm.read_text().startswith("---\nname: brainstorm")
    assert "# brainstorm Command\n\n<!-- phase-routing: mode=session role=plan -->" in brainstorm.read_text()
    assert design.read_text().count("phase-routing:") == 1
    assert pr.apply(repo) == []


def test_apply_touches_only_model_line(repo: Path) -> None:
    ship = repo / pr.AGENTS_REL / "ship-agent.md"
    before = ship.read_text()
    ship.write_text(before.replace("model: haiku", "model: sonnet"))
    pr.apply(repo)
    assert ship.read_text() == before


# ── OMP overrides ───────────────────────────────────────────────────────────


def test_omp_overrides_format(repo: Path) -> None:
    agents, _ = pr.load(repo / pr.MANIFEST_REL)
    out = pr.omp_overrides(agents)
    lines = out.splitlines()
    assert "task:" in lines and "  agentModelOverrides:" in lines
    assert lines[-2:] == ['    design-agent: "@slow"', '    ship-agent: "@smol"']


def test_print_overrides_never_touches_home(tmp_path: Path) -> None:
    home = tmp_path / "home"
    config = home / ".omp" / "agent" / "config.yml"
    _write(config, "modelRoles:\n  slow: provider/model\n")
    digest = hashlib.sha256(config.read_bytes()).hexdigest()

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--print-omp-overrides"],
        capture_output=True, text=True, env={"HOME": str(home), "PATH": "/usr/bin:/bin"}, check=True,
    )

    assert 'design-agent: "@slow"' in result.stdout
    assert hashlib.sha256(config.read_bytes()).hexdigest() == digest
    assert sorted(p.relative_to(home) for p in home.rglob("*") if p.is_file()) == [Path(".omp/agent/config.yml")]


# ── real repository ─────────────────────────────────────────────────────────


def test_real_manifest_covers_workflow_sources() -> None:
    agents, commands = pr.load()
    assert set(agents) == set(pr._workflow_agent_files(REPO_ROOT))
    assert set(commands) == set(pr._workflow_command_files(REPO_ROOT))
    assert commands["design"].mode == "delegated" and commands["ship"].mode == "delegated"
    assert commands["brainstorm"].mode == "session" and commands["design-m"].mode == "session"


def test_real_sources_in_sync_except_generated_plugin(tmp_path: Path) -> None:
    """Source files (not the generated plugin/) must match the manifest."""
    for rel in (pr.MANIFEST_REL, pr.CONTRACTS_REL):
        _write(tmp_path / rel, (REPO_ROOT / rel).read_text())
    shutil.copytree(REPO_ROOT / pr.AGENTS_REL, tmp_path / pr.AGENTS_REL)
    shutil.copytree(REPO_ROOT / pr.COMMANDS_REL, tmp_path / pr.COMMANDS_REL)
    assert pr.check(tmp_path) == []
