"""Recheck the retrospective agent-selection benchmark with explicit provenance.

The labels are local, unversioned, and were written by the build agent (Claude).
Passing this check is a regression signal, not a human-labelled generalization claim.

Reproducing the 2026-09-25/26 measurement (receipt:
.claude/sdd/archive/JEV_AGENT_SELECTION/EVAL_JEV_AGENT_SELECTION.json):

1. Put the three label files in ``.claude/sdd/evals/`` (git-ignored, they quote
   client specs) or pass ``--labels-dir DIR``. Each is a jev_select ``--eval``
   file: ``{"cases": [{id, phase, summary, kb_domains, expected_variant,
   expected_specialists}, ...]}``.
2. ``python3 scripts/check_agent_selection_quality.py --provider codex``
   (or ``claude``) — one headless CLI call per case, or score saved answers
   with ``--answers FILE`` (no model call).
3. Compare ``label_sha256`` / ``corpus_matches_receipt`` in the output with
   RECEIPT_SHA256 below: a mismatch means a different corpus, not a regression.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import tempfile
from pathlib import Path

import eval_llm_baseline as baseline
import jev_select as selector

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LABELS_DIR = ROOT / ".claude" / "sdd" / "evals"
LABEL_FILES = (
    "agent_selection_labels.json",
    "agent_selection_holdout.json",
    "agent_selection_prd_set.json",
)
LABELS = tuple(DEFAULT_LABELS_DIR / name for name in LABEL_FILES)
# The corpus behind the shipped evidence (46 cases, 31 multiagent), as recorded in the eval receipt.
RECEIPT_SHA256 = {
    "agent_selection_labels.json": "ec6c596ec0044fa84c36cf6c7e2c1a40e702fb13d360c9a9fab1047b30e1344c",
    "agent_selection_holdout.json": "9eb8fb6dab68d705cf80575afcd41e640d13c63c13f4a615e2f52a7ee208034c",
    "agent_selection_prd_set.json": "4d38dec53fc67819e34215dfadba9a26479d4fcc76586b07a29e4db68310b3aa",
}
PROVIDERS = tuple(sorted(baseline.PROVIDERS))


def missing_corpus_message(labels_dir: Path, missing: list[Path]) -> str:
    return (
        f"retrospective label corpus missing: {', '.join(str(p) for p in missing)}\n"
        "  The 46 labels are deliberately not versioned (they quote client specs; .gitignore).\n"
        "  To reproduce the measurement:\n"
        f"    1. copy {', '.join(LABEL_FILES)} into {labels_dir}/ from the maintainer's backup,\n"
        "       or point at another copy with --labels-dir DIR;\n"
        "    2. check the copy is the measured one: sha256 must match RECEIPT_SHA256 in this script\n"
        "       (from .claude/sdd/archive/JEV_AGENT_SELECTION/EVAL_JEV_AGENT_SELECTION.json);\n"
        "    3. rerun this command. Without the corpus the shipped F1/accuracy can't be re-measured."
    )


def measure(cases: list[dict], answers: dict, provider: str) -> dict:
    agents = selector.load_routing(selector.resolve_routing_path())
    known = selector.known_domains(agents)
    rows = []
    for case in cases:
        answer = answers.get(case["id"])
        if not isinstance(answer, dict) or answer.get("error"):
            raise ValueError(f"missing or failed answer for {case['id']}")
        if answer.get("variant") not in selector.VARIANTS:
            raise ValueError(f"invalid variant for {case['id']}")
        if answer.get("unknown_names"):
            raise ValueError(f"unknown specialist names for {case['id']}")
        specialists = answer.get("specialists")
        if not isinstance(specialists, list) or len(specialists) > selector.MAX_SPECIALISTS:
            raise ValueError(f"invalid specialists for {case['id']}")
        domains, _ = selector.normalize_kb_domains(case["kb_domains"], known)
        old_variant, old_specialists = selector.heuristic(
            domains, selector.prefilter_candidates(agents, domains)
        )
        rows.append((case, answer, old_variant, old_specialists))

    multi = [row for row in rows if row[0]["expected_variant"] == "multiagent"]
    if not rows or not multi:
        raise ValueError(f"corpus too small to score: {len(rows)} cases, {len(multi)} multiagent")
    llm_correct = sum(a["variant"] == c["expected_variant"] for c, a, _, _ in rows)
    old_correct = sum(v == c["expected_variant"] for c, _, v, _ in rows)
    llm_accuracy = llm_correct / len(rows)
    old_accuracy = old_correct / len(rows)
    llm_f1 = sum(selector.f1(a["specialists"], c["expected_specialists"]) for c, a, _, _ in multi) / len(multi)
    old_f1 = sum(selector.f1(s, c["expected_specialists"]) for c, _, _, s in multi) / len(multi)
    return {
        "provider": provider,
        "provider_models": sorted({str(a.get("provider_model", "unknown")) for _, a, _, _ in rows}),
        "cases": len(rows),
        "multiagent_cases": len(multi),
        "label_provenance": "build-agent Claude; no independent human review",
        "variant_correct": {"llm": llm_correct, "old_rule": old_correct},
        "variant_accuracy": {"llm": round(llm_accuracy, 4), "old_rule": round(old_accuracy, 4)},
        "specialists_f1": {"llm": round(llm_f1, 4), "old_rule": round(old_f1, 4)},
        "pass": llm_accuracy >= 0.80 and llm_f1 >= 0.40 and llm_accuracy > old_accuracy and llm_f1 > old_f1,
    }


def corpus_paths(labels_dir: Path) -> tuple[Path, ...]:
    return tuple(labels_dir / name for name in LABEL_FILES)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--provider", choices=PROVIDERS, required=True)
    parser.add_argument("--answers", type=Path, help="Score saved baseline answers without calling a model")
    parser.add_argument("--labels-dir", type=Path, default=DEFAULT_LABELS_DIR,
                        help=f"Folder holding {', '.join(LABEL_FILES)} (default: %(default)s)")
    parser.add_argument("--model", default=None, help="Model passed to the provider CLI")
    args = parser.parse_args(argv)
    labels = corpus_paths(args.labels_dir)
    missing = [path for path in labels if not path.is_file()]
    if missing:
        parser.exit(2, f"{parser.prog}: error: {missing_corpus_message(args.labels_dir, missing)}\n")
    cases = [case for path in labels for case in selector.load_labels(path)]
    if len({case["id"] for case in cases}) != len(cases):
        parser.error("duplicate case ids in label corpus")

    if args.answers:
        answers = json.loads(args.answers.read_text(encoding="utf-8"))
    else:
        with tempfile.TemporaryDirectory(prefix="agentspec-quality-") as scratch:
            output = io.StringIO()
            argv_b = ["--provider", args.provider, "--labels", *(str(path) for path in labels), "--scratch", scratch]
            if args.model:
                argv_b += ["--model", args.model]
            with contextlib.redirect_stdout(output):
                if baseline.main(argv_b) != 0:
                    parser.error("baseline CLI failed")
            answers = json.loads(output.getvalue())

    result = measure(cases, answers, args.provider)
    result["label_sha256"] = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in labels}
    result["corpus_matches_receipt"] = result["label_sha256"] == RECEIPT_SHA256
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
