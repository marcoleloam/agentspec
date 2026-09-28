"""Bench configuration: bench.toml + environment, resolved to absolute paths."""
from __future__ import annotations

import glob
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import tomllib

BENCH_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = BENCH_DIR.parent
REPO_ROOT = SCRIPTS_DIR.parent
DEFAULT_CONFIG = BENCH_DIR / "bench.toml"
ARM_LETTERS = ("A", "B", "C", "D")
STRATA = ("library", "conceptual", "niche")


class ConfigError(RuntimeError):
    """Invalid or unusable bench configuration."""


@dataclass(frozen=True)
class Arm:
    letter: str
    kb: str            # repo | lean | none
    uses_context7: bool

    @property
    def dirname(self) -> str:
        return self.letter.lower()


@dataclass(frozen=True)
class BenchConfig:
    model: str                 # "" = the Codex account default
    reasoning_effort: str      # "" = the model default
    attempt_timeout_s: int
    max_retries: int
    seed: int
    budget_tokens: int
    retry_feedback_bytes: int
    eval_timeout_s: int
    home: Path
    repo_kb: Path
    permission_profile: str
    disabled_features: tuple[str, ...]
    deny_globs: tuple[str, ...]
    context7_command: str
    context7_args: tuple[str, ...]
    context7_startup_timeout_s: int
    user_codex_home: Path
    arms: dict[str, Arm] = field(default_factory=dict)

    @property
    def arms_root(self) -> Path:
        return self.home / "arms"

    @property
    def results_root(self) -> Path:
        return self.home / "results"

    @property
    def backups_dir(self) -> Path:
        return self.home / "backups"

    @property
    def canary_dir(self) -> Path:
        return self.home / "canary"

    @property
    def npm_cache_dir(self) -> Path:
        return self.home / "npm-cache"

    @property
    def agent_home(self) -> Path:
        """HOME of every attempt: keeps the user's shell rc, skills and ~ paths out of reach."""
        return self.home / "agent-home"

    @property
    def codex_home(self) -> Path:
        """CODEX_HOME of every attempt: only a symlink to the user's auth.json survives a reset."""
        return self.agent_home / ".codex"

    @property
    def user_auth_file(self) -> Path:
        return self.user_codex_home / "auth.json"

    @property
    def tasks_dir(self) -> Path:
        return BENCH_DIR / "tasks"

    @property
    def solutions_dir(self) -> Path:
        return BENCH_DIR / "solutions"

    @property
    def kb_lean_dir(self) -> Path:
        return BENCH_DIR / "kb_lean"

    @property
    def eval_venv_bin(self) -> Path:
        return BENCH_DIR / ".venv" / "bin"

    def arm_dir(self, letter: str) -> Path:
        return self.arms_root / self.arms[letter].dirname

    def deny_paths(self, arm: str | None = None) -> tuple[Path, ...]:
        """Resolved deny roots for an attempt in ``arm`` (None = the roots shared by every arm).

        Always: the repo, the canary, the user's Codex home, the bench results
        and backups (earlier transcripts quote KB files) and every *other* arm
        folder (arm A's ``kb/`` stays on disk until its next reset).
        """
        roots: set[Path] = {REPO_ROOT.resolve(), self.canary_dir.resolve(), self.user_codex_home.resolve(),
                            self.results_root.resolve(), self.backups_dir.resolve()}
        for pattern in self.deny_globs:
            for match in glob.glob(os.path.expanduser(pattern)):
                roots.add(Path(match).resolve())
        top = _git_toplevel(REPO_ROOT)
        if top:
            roots.add(top)
        if arm is not None:
            roots.update(self.arm_dir(other).resolve() for other in self.arms if other != arm)
        return tuple(sorted(roots))


def _git_toplevel(path: Path) -> Path | None:
    try:
        out = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True, timeout=10,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None
    return Path(out).resolve() if out else None


def inside_git_repo(path: Path) -> bool:
    probe = path
    while not probe.exists() and probe != probe.parent:
        probe = probe.parent
    return _git_toplevel(probe) is not None


def _user_codex_home() -> Path:
    return Path(os.environ.get("KB_BENCH_USER_CODEX_HOME") or os.environ.get("CODEX_HOME")
                or os.path.expanduser("~/.codex")).resolve()


def load_config(path: Path | None = None) -> BenchConfig:
    data = tomllib.loads((path or DEFAULT_CONFIG).read_text(encoding="utf-8"))
    run, paths, codex, sandbox, c7 = (data["run"], data["paths"], data["codex"], data["sandbox"],
                                      data["context7"])
    home = Path(os.environ.get("KB_BENCH_HOME") or os.path.expanduser(paths["home"])).resolve()
    arms = {
        letter: Arm(letter, spec["kb"], bool(spec["context7"]))
        for letter, spec in data["arms"].items()
    }
    if set(arms) != set(ARM_LETTERS):
        raise ConfigError(f"bench.toml must define arms {ARM_LETTERS}, got {sorted(arms)}")
    bad_kb = [a.letter for a in arms.values() if a.kb not in {"repo", "lean", "none"}]
    if bad_kb:
        raise ConfigError(f"arms {bad_kb}: kb must be repo|lean|none")
    return BenchConfig(
        model=os.environ.get("KB_BENCH_MODEL", run["model"]),
        reasoning_effort=str(run.get("reasoning_effort", "")),
        attempt_timeout_s=int(run["attempt_timeout_s"]),
        max_retries=int(run["max_retries"]),
        seed=int(run["seed"]),
        budget_tokens=int(run["budget_tokens"]),
        retry_feedback_bytes=int(run["retry_feedback_bytes"]),
        eval_timeout_s=int(run.get("eval_timeout_s", 120)),
        home=home,
        repo_kb=(REPO_ROOT / paths["repo_kb"]).resolve(),
        permission_profile=codex["profile"],
        disabled_features=tuple(codex.get("disabled_features", ())),
        deny_globs=tuple(sandbox["deny_globs"]),
        context7_command=c7["command"],
        context7_args=tuple(c7["args"]),
        context7_startup_timeout_s=int(c7["startup_timeout_s"]),
        user_codex_home=_user_codex_home(),
        arms=arms,
    )
