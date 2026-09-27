"""Blind human review queue (DESIGN Decisão 8).

Each ``human`` outcome becomes ``human/<opaque-id>.md`` holding the task
prompt, the agent's final files and the failing evals — never the arm or the
transcript. The id → (arm, task) mapping lives in ``human/.mapping.json`` and
is read only by the report. Verdicts go to ``human/verdicts.jsonl``.
"""
from __future__ import annotations

import datetime as dt
import json
import secrets
from pathlib import Path

from kb_bench.evals import EvalResult

MAX_FILE_BYTES = 20_000
VERDICTS = ("approve", "reject")


class HumanQueue:
    def __init__(self, run_root: Path) -> None:
        self.dir = run_root / "human"
        self.dir.mkdir(parents=True, exist_ok=True)

    @property
    def _mapping_path(self) -> Path:
        return self.dir / ".mapping.json"

    @property
    def _verdicts_path(self) -> Path:
        return self.dir / "verdicts.jsonl"

    def mapping(self) -> dict[str, dict[str, str]]:
        if not self._mapping_path.is_file():
            return {}
        return json.loads(self._mapping_path.read_text(encoding="utf-8"))

    def enqueue(self, *, task_id: str, arm: str, prompt: str, workspace: Path,
                failures: list[EvalResult]) -> str:
        item_id = secrets.token_hex(4)
        while (self.dir / f"{item_id}.md").exists():
            item_id = secrets.token_hex(4)
        lines = [f"# Revisão {item_id}", "", "## Tarefa", "", prompt, "", "## Checks que falharam", ""]
        lines += [f"- **{f.name}** (exit {f.exit_code})\n\n```text\n{f.output[:1500]}\n```" for f in failures]
        lines += ["", "## Arquivos entregues", ""]
        for path in sorted(p for p in workspace.rglob("*") if p.is_file()):
            rel = path.relative_to(workspace)
            data = path.read_bytes()[:MAX_FILE_BYTES]
            text = data.decode("utf-8", errors="replace")
            suffix = path.suffix.lstrip(".") or "text"
            lines += [f"### `{rel}`", "", f"```{suffix}", text, "```", ""]
        lines += ["## Veredito", "",
                  f"`python3 -m kb_bench human <run_id> --approve {item_id}` ou `--reject {item_id}`", ""]
        (self.dir / f"{item_id}.md").write_text("\n".join(lines), encoding="utf-8")
        mapping = self.mapping()
        mapping[item_id] = {"arm": arm, "task": task_id}
        self._mapping_path.write_text(json.dumps(mapping, indent=2) + "\n", encoding="utf-8")
        return item_id

    def verdicts(self) -> dict[str, dict[str, str]]:
        """Latest verdict per item id."""
        out: dict[str, dict[str, str]] = {}
        if self._verdicts_path.is_file():
            for line in self._verdicts_path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    rec = json.loads(line)
                    out[rec["id"]] = rec
        return out

    def record(self, item_id: str, verdict: str, note: str = "") -> None:
        if verdict not in VERDICTS:
            raise ValueError(f"verdict must be one of {VERDICTS}")
        if not (self.dir / f"{item_id}.md").is_file():
            raise KeyError(f"no review item {item_id}")
        rec = {"id": item_id, "verdict": verdict, "note": note,
               "at": dt.datetime.now(dt.UTC).isoformat(timespec="seconds")}
        with self._verdicts_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    def pending(self) -> list[str]:
        done = self.verdicts()
        return sorted(p.stem for p in self.dir.glob("*.md") if p.stem not in done)
