"""Recheck the retrospective agent-selection benchmark with explicit provenance.

The labels are local, unversioned, and were written by the build agent (Claude).
Passing this check is a regression signal, not a human-labelled generalization claim.
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
LABELS = tuple(
    ROOT / ".claude" / "sdd" / "evals" / name
    for name in (
        "agent_selection_labels.json",
        "agent_selection_holdout.json",
        "agent_selection_prd_set.json",
    )
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
    if len(rows) != 46 or len(multi) != 31:
        raise ValueError(f"unexpected corpus composition: {len(rows)} cases, {len(multi)} multiagent")
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=("codex", "grok"), required=True)
    parser.add_argument("--answers", type=Path, help="Score saved baseline answers without calling a model")
    args = parser.parse_args()
    missing = [str(path) for path in LABELS if not path.is_file()]
    if missing:
        parser.error(f"retrospective label corpus missing: {', '.join(missing)}")
    cases = [case for path in LABELS for case in selector.load_labels(path)]
    if len({case["id"] for case in cases}) != len(cases):
        parser.error("duplicate case ids in label corpus")

    if args.answers:
        answers = json.loads(args.answers.read_text(encoding="utf-8"))
    else:
        with tempfile.TemporaryDirectory(prefix="agentspec-quality-") as scratch:
            output = io.StringIO()
            argv = ["--provider", args.provider, "--labels", *(str(path) for path in LABELS), "--scratch", scratch]
            with contextlib.redirect_stdout(output):
                if baseline.main(argv) != 0:
                    parser.error("baseline CLI failed")
            answers = json.loads(output.getvalue())

    result = measure(cases, answers, args.provider)
    result["label_sha256"] = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in LABELS}
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
