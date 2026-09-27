"""Run storage: one folder per run under KB_BENCH_HOME/results/<run_id>/.

Layout:
  runs.jsonl        one Record per (task, arm), append-only
  plan.json         shuffled execution plan + seed
  env.json          grok version, model, commit, host facts
  coverage.json     Context7 coverage per domain (from smoke)
  transcripts/      raw NDJSON per attempt
  evalws/           workspace snapshots the evals ran on
  human/            blind review queue (see human_queue.py)
  REPORT.md         rendered by report.py
"""
from __future__ import annotations

import datetime as dt
import json
import secrets
import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from kb_bench.config import REPO_ROOT

OUTCOMES = ("pass_first", "pass_retry", "human", "unavailable", "timeout", "contaminated")
EXCLUDED = frozenset({"unavailable", "timeout", "contaminated"})


@dataclass
class Record:
    run_id: str
    task: str
    domain: str
    stratum: str
    origin: str
    arm: str
    outcome: str
    attempts: int
    tokens: int | None = None
    input_tokens_first: int | None = None
    cost_usd: float | None = None
    latency_s: float = 0.0
    model: str | None = None
    context7_calls: int = 0
    kb_access_denied: int = 0
    contamination_reasons: list[str] = field(default_factory=list)
    eval_failures_last: list[str] = field(default_factory=list)
    reason: str = ""
    human_id: str | None = None
    seed: int | None = None
    grok_version: str | None = None

    def __post_init__(self) -> None:
        if self.outcome not in OUTCOMES:
            raise ValueError(f"unknown outcome {self.outcome!r}")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Record:
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in known})


def new_run_id() -> str:
    stamp = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"{stamp}-{secrets.token_hex(2)}"


class RunStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        for sub in ("transcripts", "evalws", "human"):
            (self.root / sub).mkdir(exist_ok=True)

    @property
    def run_id(self) -> str:
        return self.root.name

    @property
    def runs_path(self) -> Path:
        return self.root / "runs.jsonl"

    def append(self, record: Record) -> None:
        with self.runs_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")

    def records(self) -> list[Record]:
        if not self.runs_path.is_file():
            return []
        return [Record.from_dict(json.loads(line))
                for line in self.runs_path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def done_pairs(self) -> set[tuple[str, str]]:
        return {(r.task, r.arm) for r in self.records()}

    def write_json(self, name: str, data: Any) -> None:
        (self.root / name).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    def read_json(self, name: str) -> Any:
        path = self.root / name
        return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None

    def transcript_path(self, task: str, arm: str, attempt: int) -> Path:
        return self.root / "transcripts" / f"{task}__{arm}__{attempt}.ndjson"

    def evalws_path(self, task: str, arm: str, attempt: int) -> Path:
        return self.root / "evalws" / f"{task}__{arm}__{attempt}"


def latest_run(results_root: Path) -> Path | None:
    runs = sorted(p for p in results_root.glob("*") if (p / "runs.jsonl").is_file() or (p / "plan.json").is_file())
    return runs[-1] if runs else None


def git_commit() -> str:
    try:
        return subprocess.run(["git", "-C", str(REPO_ROOT), "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True, timeout=10, check=False).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def git_dirty_paths() -> set[str]:
    try:
        out = subprocess.run(["git", "-C", str(REPO_ROOT), "status", "--porcelain"],
                             capture_output=True, text=True, timeout=30, check=False).stdout
    except (OSError, subprocess.SubprocessError):
        return set()
    return {line[3:].strip() for line in out.splitlines() if line.strip()}
