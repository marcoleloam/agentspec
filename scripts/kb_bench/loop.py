"""Per-(task, arm) state machine: attempt → isolation → evals → retry ≤ N → human."""
from __future__ import annotations

import random
import sys
from collections.abc import Callable
from dataclasses import dataclass, field

from kb_bench import grok_runner, isolation, workspace
from kb_bench.config import ARM_LETTERS, Arm, BenchConfig
from kb_bench.evals import EvalResult, feedback, run_on_copy
from kb_bench.human_queue import HumanQueue
from kb_bench.store import Record, RunStore
from kb_bench.tasks import Task
from kb_bench.transcript import parse_ndjson

ARM_PREAMBLE = {
    "A": "Reference material for this domain is in ./kb/. Consult it before acting.",
    "B": "You may use the context7 MCP tools to look up current official documentation.",
    "C": "Reference material for this domain is in ./kb/. Consult it before acting. "
         "You may also use the context7 MCP tools to look up current official documentation.",
    "D": "",
}
COMMON_RULES = (
    "Work only inside the current directory. Do not install packages or use the network "
    "(other than the tools you were given). When the deliverable is complete, stop — the "
    "result will be checked automatically."
)
_MAX_TURN_MARKERS = ("max_turn", "max-turn", "turn_limit", "max_tokens")


class BudgetExceeded(RuntimeError):
    """Cumulative CLI-reported cost passed run.budget_usd."""


def build_prompt(task: Task, arm: Arm, retry_feedback: str | None = None) -> str:
    parts = [p for p in (ARM_PREAMBLE[arm.letter], task.prompt, COMMON_RULES) if p]
    if retry_feedback:
        parts.append(
            "Your previous attempt failed these automated checks. The files you wrote are still "
            f"in place; fix them so the checks pass.\n\n{retry_feedback}"
        )
    return "\n\n".join(parts)


def plan(tasks: list[Task], arms: list[str], seed: int) -> list[tuple[str, str]]:
    pairs = [(t.id, a) for t in tasks for a in arms]
    random.Random(seed).shuffle(pairs)
    return pairs


@dataclass
class RunContext:
    cfg: BenchConfig
    store: RunStore
    queue: HumanQueue
    grok_version: str
    spent_usd: float = 0.0
    log: Callable[[str], None] = field(default=lambda msg: print(msg, file=sys.stderr))


def _add(a: float | None, b: float | None):
    if a is None:
        return b
    return a if b is None else a + b


def run_pair(task: Task, arm: Arm, ctx: RunContext) -> Record:
    cfg = ctx.cfg
    rec = Record(run_id=ctx.store.run_id, task=task.id, domain=task.domain, stratum=task.stratum,
                 origin=task.origin, arm=arm.letter, outcome="human", attempts=0,
                 seed=cfg.seed, grok_version=ctx.grok_version)
    deny = cfg.deny_paths()
    retry_feedback: str | None = None
    last_results: list[EvalResult] = []
    last_snapshot = None
    for attempt in range(1, cfg.max_retries + 2):
        arm_dir = workspace.prepare(arm, task, cfg, fresh=attempt == 1)
        tag = f"[{arm.letter}] {task.id} attempt {attempt}/{cfg.max_retries + 1}"
        if arm.uses_context7:
            healthy, detail = grok_runner.mcp_doctor(arm_dir, sandbox=cfg.sandbox_profile)
            if not healthy:
                rec.outcome, rec.reason = "unavailable", f"context7 preflight failed: {detail[-200:]}"
                ctx.log(f"{tag} → unavailable (preflight)")
                return rec
        out = grok_runner.run_attempt(build_prompt(task, arm, retry_feedback), arm_dir, cfg)
        rec.attempts = attempt
        rec.latency_s = round(rec.latency_s + out.latency_s, 2)
        ctx.store.transcript_path(task.id, arm.letter, attempt).write_text(out.ndjson, encoding="utf-8")
        t = parse_ndjson(out.ndjson)
        rec.tokens = _add(rec.tokens, t.total_tokens)
        rec.cost_usd = _add(rec.cost_usd, t.cost_usd)
        if attempt == 1:
            rec.input_tokens_first = t.input_tokens
        rec.model = t.model or rec.model
        ctx.spent_usd += t.cost_usd or 0.0

        verdict = isolation.check(t, uses_context7=arm.uses_context7, deny=deny, cwd=arm_dir)
        rec.context7_calls += verdict.context7_calls
        rec.kb_access_denied += verdict.kb_access_denied
        if verdict.contaminated:
            rec.outcome, rec.contamination_reasons = "contaminated", list(verdict.reasons)
            ctx.log(f"{tag} → contaminated: {verdict.reasons[0]}")
            return rec
        if out.timed_out or not t.ended or any(m in (t.stop_reason or "") for m in _MAX_TURN_MARKERS):
            why = "wall-clock timeout" if out.timed_out else (
                f"stop_reason={t.stop_reason}" if t.ended else f"no end event (exit {out.exit_code})")
            rec.outcome, rec.reason = "timeout", why
            ctx.log(f"{tag} → timeout ({why})")
            return rec
        if arm.uses_context7 and (verdict.context7_unavailable or verdict.mcp_missing):
            why = "context7 MCP not available in the session" if verdict.mcp_missing else \
                "every context7 call failed on transport"
            rec.outcome, rec.reason = "unavailable", why
            ctx.log(f"{tag} → unavailable (context7 transport)")
            return rec

        last_snapshot = ctx.store.evalws_path(task.id, arm.letter, attempt)
        workspace.snapshot(arm_dir, last_snapshot)
        eval_dir = last_snapshot.with_name(last_snapshot.name + ".run")
        last_results = run_on_copy(task, [last_snapshot], cfg, keep_at=eval_dir)
        failed = [r for r in last_results if not r.passed]
        rec.eval_failures_last = [r.name for r in failed]
        if not failed:
            rec.outcome = "pass_first" if attempt == 1 else "pass_retry"
            ctx.log(f"{tag} → {rec.outcome}")
            return rec
        ctx.log(f"{tag} → eval fail ({len(failed)}/{len(last_results)})")
        retry_feedback = feedback(last_results, cfg.retry_feedback_bytes, workdir=eval_dir)

    rec.outcome = "human"
    if last_snapshot is not None:
        rec.human_id = ctx.queue.enqueue(task_id=task.id, arm=arm.letter, prompt=task.prompt,
                                         workspace=last_snapshot,
                                         failures=[r for r in last_results if not r.passed])
    ctx.log(f"[{arm.letter}] {task.id} → human ({rec.human_id})")
    return rec


def run_plan(tasks: list[Task], arms: list[str], ctx: RunContext, *,
             pairs: list[tuple[str, str]] | None = None) -> list[Record]:
    by_id = {t.id: t for t in tasks}
    done = ctx.store.done_pairs()
    todo = [p for p in (pairs or plan(tasks, arms, ctx.cfg.seed)) if p not in done]
    records: list[Record] = []
    for i, (task_id, letter) in enumerate(todo, 1):
        if letter not in ARM_LETTERS:
            continue
        ctx.log(f"── {i}/{len(todo)} · spent ${ctx.spent_usd:.2f}")
        rec = run_pair(by_id[task_id], ctx.cfg.arms[letter], ctx)
        ctx.store.append(rec)
        records.append(rec)
        if ctx.spent_usd > ctx.cfg.budget_usd:
            raise BudgetExceeded(f"spent ${ctx.spent_usd:.2f} > budget ${ctx.cfg.budget_usd:.2f}")
    return records
