#!/usr/bin/env python3
"""Per-phase model routing: load, validate, apply, and check PHASE_MODEL_ROLES.toml.

The manifest maps each SDD workflow agent to an OMP model role, a Claude Code
alias, and a Codex reasoning effort, and marks each workflow command as
``session`` (runs inline) or ``delegated`` (runs in its phase agent). Concrete
model IDs never live in this repo: OMP resolves ``@role`` through the user's
``~/.omp/agent/config.yml``.

Stdlib only (tomllib, Python >= 3.11) so `make check` needs no extra deps.

  python3 scripts/phase_routing.py --check                # fail on drift (CI)
  python3 scripts/phase_routing.py --apply                # sync sources from manifest
  python3 scripts/phase_routing.py --print-omp-overrides  # stdout only, never touches ~/.omp

Exit codes: 0 ok, 1 drift found by --check, 2 invalid manifest or usage error.
"""
from __future__ import annotations

import sys

if sys.version_info < (3, 11):
    print("phase_routing.py needs Python >= 3.11 (tomllib).", file=sys.stderr)
    raise SystemExit(2)

import argparse
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_REL = Path(".claude/sdd/architecture/PHASE_MODEL_ROLES.toml")
AGENTS_REL = Path(".claude/agents/workflow")
COMMANDS_REL = Path(".claude/commands/workflow")
CONTRACTS_REL = Path(".claude/sdd/architecture/WORKFLOW_CONTRACTS.yaml")
PLUGIN_AGENTS_REL = Path("plugin/agents")

CLAUDE_MODELS = frozenset({"opus", "sonnet", "haiku", "fable", "inherit"})
CODEX_EFFORTS = frozenset({"low", "medium", "high"})
MODES = frozenset({"session", "delegated"})
NON_PHASE_COMMANDS = frozenset({"create-pr"})
SKIP_FILES = frozenset({"README.md", "_template.md"})

ROLE_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")
CONCRETE_ID_RE = re.compile(r"(gpt-|grok-|claude-|gemini-|deepseek)[0-9a-z.-]+", re.IGNORECASE)
MARKER_RE = re.compile(r"^<!-- phase-routing: [^>]*-->[ \t]*$", re.MULTILINE)
EXTRA_MARKER_RE = re.compile(r"\n<!-- phase-routing: [^>]*-->[ \t]*(?=\n|\Z)")
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
MODEL_LINE_RE = re.compile(r"^model:[ \t]*(.*?)[ \t]*$", re.MULTILINE)
NAME_LINE_RE = re.compile(r"^name:.*$", re.MULTILINE)
H1_RE = re.compile(r"^# .*$", re.MULTILINE)
CONTRACT_ALIAS_MODEL_RE = re.compile(
    r'^\s+model:\s*"?(opus|sonnet|haiku|fable|inherit)"?\s*$', re.MULTILINE
)


@dataclass(frozen=True)
class AgentRoute:
    name: str
    omp_role: str
    claude_model: str
    codex_effort: str | None


@dataclass(frozen=True)
class CommandRoute:
    stem: str
    mode: str
    agent: str | None
    recommended_role: str | None

    def marker(self) -> str:
        if self.mode == "delegated":
            return f"<!-- phase-routing: mode=delegated agent={self.agent} -->"
        return f"<!-- phase-routing: mode=session role={self.recommended_role} -->"


Routes = tuple[dict[str, AgentRoute], dict[str, CommandRoute]]


def load(path: Path | None = None) -> Routes:
    """Parse and validate the manifest; raise ValueError listing every problem."""
    path = path or REPO_ROOT / MANIFEST_REL
    raw_text = path.read_text(encoding="utf-8")
    try:
        data = tomllib.loads(raw_text)
    except tomllib.TOMLDecodeError as exc:
        raise ValueError(f"{path.name}: invalid TOML: {exc}") from exc

    problems: list[str] = []
    if data.get("schema_version") != 1:
        problems.append(f"schema_version expected 1, found {data.get('schema_version')!r}")
    for match in CONCRETE_ID_RE.finditer(raw_text):
        problems.append(f"concrete model id {match.group(0)!r} is not allowed; use an OMP role")

    agents: dict[str, AgentRoute] = {}
    for name, entry in (data.get("agents") or {}).items():
        role = entry.get("omp_role")
        model = entry.get("claude_model")
        effort = entry.get("codex_effort")
        if not isinstance(role, str) or not ROLE_RE.match(role):
            problems.append(f"agents.{name}.omp_role invalid: {role!r}")
        if model not in CLAUDE_MODELS:
            problems.append(f"agents.{name}.claude_model expected one of {sorted(CLAUDE_MODELS)}, found {model!r}")
        if effort is not None and effort not in CODEX_EFFORTS:
            problems.append(f"agents.{name}.codex_effort expected one of {sorted(CODEX_EFFORTS)}, found {effort!r}")
        agents[name] = AgentRoute(name, str(role), str(model), effort)

    commands: dict[str, CommandRoute] = {}
    for stem, entry in (data.get("commands") or {}).items():
        mode = entry.get("mode")
        agent = entry.get("agent")
        role = entry.get("recommended_role")
        if mode not in MODES:
            problems.append(f"commands.{stem}.mode expected one of {sorted(MODES)}, found {mode!r}")
        elif mode == "delegated" and agent not in agents:
            problems.append(f"commands.{stem}.agent must name an [agents] entry, found {agent!r}")
        elif mode == "session" and (not isinstance(role, str) or not ROLE_RE.match(role)):
            problems.append(f"commands.{stem}.recommended_role invalid: {role!r}")
        commands[stem] = CommandRoute(stem, str(mode), agent, role)

    if not agents:
        problems.append("no [agents] entries")
    if not commands:
        problems.append("no [commands] entries")
    if problems:
        raise ValueError("\n".join(f"{path.name}: {p}" for p in problems))
    return agents, commands


def _workflow_agent_files(repo: Path) -> dict[str, Path]:
    return {
        p.stem: p
        for p in sorted((repo / AGENTS_REL).glob("*.md"))
        if p.name not in SKIP_FILES and not p.name.startswith("_")
    }


def _workflow_command_files(repo: Path) -> dict[str, Path]:
    return {
        p.stem: p
        for p in sorted((repo / COMMANDS_REL).glob("*.md"))
        if p.name not in SKIP_FILES and p.stem not in NON_PHASE_COMMANDS
    }


def _frontmatter(text: str) -> str | None:
    match = FRONTMATTER_RE.match(text)
    return match.group(1) if match else None


def check(repo: Path = REPO_ROOT) -> list[str]:
    """Return human-readable drift errors: '<file>: <field> expected <x>, found <y>'."""
    try:
        agents, commands = load(repo / MANIFEST_REL)
    except (OSError, ValueError) as exc:
        return [str(exc)]

    errors: list[str] = []
    agent_files = _workflow_agent_files(repo)
    command_files = _workflow_command_files(repo)

    for name in sorted(set(agent_files) - set(agents)):
        errors.append(f"{AGENTS_REL / (name + '.md')}: agent missing from {MANIFEST_REL.name} [agents]")
    for name in sorted(set(agents) - set(agent_files)):
        errors.append(f"{MANIFEST_REL.name}: agents.{name} has no file in {AGENTS_REL}")
    for stem in sorted(set(command_files) - set(commands)):
        errors.append(f"{COMMANDS_REL / (stem + '.md')}: command missing from {MANIFEST_REL.name} [commands]")
    for stem in sorted(set(commands) - set(command_files)):
        errors.append(f"{MANIFEST_REL.name}: commands.{stem} has no file in {COMMANDS_REL}")

    for name, path in agent_files.items():
        route = agents.get(name)
        if route is None:
            continue
        rel = path.relative_to(repo)
        frontmatter = _frontmatter(path.read_text(encoding="utf-8"))
        if frontmatter is None:
            errors.append(f"{rel}: frontmatter missing")
            continue
        found = MODEL_LINE_RE.search(frontmatter)
        found_model = found.group(1) if found else None
        if found_model != route.claude_model:
            errors.append(f"{rel}: model expected {route.claude_model}, found {found_model}")
        for match in CONCRETE_ID_RE.finditer(frontmatter):
            errors.append(f"{rel}: frontmatter concrete model id {match.group(0)!r} is not allowed")

    for stem, path in command_files.items():
        route = commands.get(stem)
        if route is None:
            continue
        rel = path.relative_to(repo)
        markers = MARKER_RE.findall(path.read_text(encoding="utf-8"))
        expected = route.marker()
        if len(markers) != 1:
            errors.append(f"{rel}: phase-routing marker expected exactly 1 ({expected}), found {len(markers)}")
        elif markers[0].strip() != expected:
            errors.append(f"{rel}: phase-routing marker expected {expected}, found {markers[0].strip()}")

    contracts = repo / CONTRACTS_REL
    if contracts.exists():
        text = contracts.read_text(encoding="utf-8")
        for match in CONTRACT_ALIAS_MODEL_RE.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            errors.append(
                f"{CONTRACTS_REL}:{line}: model expected none (routing lives in {MANIFEST_REL.name}), "
                f"found {match.group(1)}"
            )

    plugin_agents = repo / PLUGIN_AGENTS_REL
    if plugin_agents.is_dir():
        for sub in sorted(p for p in plugin_agents.iterdir() if p.is_dir()):
            errors.append(f"{sub.relative_to(repo)}: subdirectory expected none (OMP only reads agents/*.md), found one")
        for name in sorted(SKIP_FILES):
            if (plugin_agents / name).exists():
                errors.append(f"{PLUGIN_AGENTS_REL / name}: file expected absent, found present")

    return errors


def _apply_agent(path: Path, route: AgentRoute) -> bool:
    text = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        raise ValueError(f"{path}: frontmatter missing")
    frontmatter = match.group(1)
    wanted = f"model: {route.claude_model}"
    if MODEL_LINE_RE.search(frontmatter):
        new_fm = MODEL_LINE_RE.sub(wanted, frontmatter, count=1)
    elif NAME_LINE_RE.search(frontmatter):
        new_fm = NAME_LINE_RE.sub(lambda m: f"{m.group(0)}\n{wanted}", frontmatter, count=1)
    else:
        new_fm = f"{frontmatter}\n{wanted}"
    if new_fm == frontmatter:
        return False
    path.write_text(f"---\n{new_fm}\n---\n{text[match.end():]}", encoding="utf-8")
    return True


def _apply_command(path: Path, route: CommandRoute) -> bool:
    text = path.read_text(encoding="utf-8")
    expected = route.marker()
    first = MARKER_RE.search(text)
    if first:
        head, tail = text[: first.start()], text[first.end():]
        new_text = head + expected + EXTRA_MARKER_RE.sub("", tail)
    else:
        heading = H1_RE.search(text)
        at = heading.end() if heading else 0
        new_text = f"{text[:at]}\n\n{expected}{text[at:]}"
    if new_text == text:
        return False
    path.write_text(new_text, encoding="utf-8")
    return True


def apply(repo: Path = REPO_ROOT) -> list[Path]:
    """Rewrite frontmatter `model:` and command markers from the manifest; return changed files."""
    agents, commands = load(repo / MANIFEST_REL)
    changed: list[Path] = []
    for name, path in _workflow_agent_files(repo).items():
        if name in agents and _apply_agent(path, agents[name]):
            changed.append(path)
    for stem, path in _workflow_command_files(repo).items():
        if stem in commands and _apply_command(path, commands[stem]):
            changed.append(path)
    return changed


def omp_overrides(agents: dict[str, AgentRoute]) -> str:
    lines = [
        "# Merge under the EXISTING `task.agentModelOverrides` key in",
        "# ~/.omp/agent/config.yml. Roles resolve through your modelRoles;",
        "# keys are agent names. Generated from PHASE_MODEL_ROLES.toml.",
        "task:",
        "  agentModelOverrides:",
    ]
    lines += [f'    {a.name}: "@{a.omp_role}"' for a in sorted(agents.values(), key=lambda a: a.name)]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true", help="fail (exit 1) on drift")
    group.add_argument("--apply", action="store_true", help="sync agent frontmatter and command markers")
    group.add_argument("--print-omp-overrides", action="store_true", help="print task.agentModelOverrides")
    args = parser.parse_args(argv)

    if args.check:
        errors = check()
        if errors:
            print("Phase routing drift (fix sources or run `make phase-routing-apply`):", file=sys.stderr)
            for error in errors:
                print(f"  - {error}", file=sys.stderr)
            return 1
        print("phase routing: in sync with PHASE_MODEL_ROLES.toml")
        return 0

    try:
        agents, _ = load()
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 2

    if args.apply:
        changed = apply()
        for path in changed:
            print(f"updated {path.relative_to(REPO_ROOT)}")
        print(f"phase routing: {len(changed)} file(s) updated")
        return 0

    sys.stdout.write(omp_overrides(agents))
    return 0


if __name__ == "__main__":
    sys.exit(main())
