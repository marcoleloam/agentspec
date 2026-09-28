"""Per-(task, arm) state machine: attempt → isolation → evals → retry ≤ N → human."""
from __future__ import annotations

import random
import sys
from collections.abc import Callable
from dataclasses import dataclass, field

from kb_bench import codex_runner, context7_probe, isolation, workspace
from kb_bench.config import ARM_LETTERS, Arm, BenchConfig
from kb_bench.evals import EvalResult, feedback, run_on_copy
from kb_bench.human_queue import HumanQueue
from kb_bench.store import Record, RunStore
from kb_bench.tasks import Task
from kb_bench.transcript import Transcript, parse_jsonl

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
# A failed turn with one of these stops the whole run (resume later) instead of
# burning every remaining pair: the account, not the task, is the problem.
STOP_MARKERS = ("401", "unauthorized", "usage limit", "rate limit", "429", "quota", "insufficient")


class RunStopped(RuntimeError):
    """The run must stop now; the current pair is not recorded, so --resume retries it."""


class BudgetExceeded(RunStopped):
    """Cumulative fresh tokens reported by Codex passed run.budget_tokens."""


class ExecutorStopped(RunStopped):
    """Codex refused to work for account reasons (login, usage limit)."""


class Context7Unavailable(RunStopped):
    """Context7 is down or refusing (quota/auth) for B/C: stop the round instead of recording `unavailable`.

    Recording would let a quota exhaustion silently turn the rest of B and C
    into "D with a preamble"; aborting leaves the pair unrecorded, so
    ``--resume`` retries it once the key or the service is back.
    """


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
    cli_version: str
    spent_tokens: int = 0
    log: Callable[[str], None] = field(default=lambda msg: print(msg, file=sys.stderr))


def _add(a: int | None, b: int | None) -> int | None:
    if a is None:
        return b
    return a if b is None else a + b


def _stop_if_account_problem(t: Transcript, tag: str) -> None:
    if t.failed and any(m in t.error_message.lower() for m in STOP_MARKERS):
        raise ExecutorStopped(f"{tag}: codex turn failed — {t.error_message[:200]}")


def run_pair(task: Task, arm: Arm, ctx: RunContext) -> Record:
    cfg = ctx.cfg
    rec = Record(run_id=ctx.store.run_id, task=task.id, domain=task.domain, stratum=task.stratum,
                 origin=task.origin, arm=arm.letter, outcome="human", attempts=0,
                 seed=cfg.seed, cli_version=ctx.cli_version, model=cfg.model or "account default")
    deny = cfg.deny_paths(arm.letter)
    retry_feedback: str | None = None
    last_results: list[EvalResult] = []
    last_snapshot = None
    for attempt in range(1, cfg.max_retries + 2):
        arm_dir = workspace.prepare(arm, task, cfg, fresh=attempt == 1)
        tag = f"[{arm.letter}] {task.id} attempt {attempt}/{cfg.max_retries + 1}"
        if arm.uses_context7:
            codex_runner.ensure_codex_home(cfg)
            probe = context7_probe.probe(cfg, arm_dir, env=codex_runner.agent_env(cfg, arm))
            if not probe.ok:
                raise Context7Unavailable(f"{tag}: context7 preflight failed: {probe.detail[-200:]}")
        out = codex_runner.run_attempt(build_prompt(task, arm, retry_feedback), arm_dir, cfg, arm)
        rec.attempts = attempt
        rec.latency_s = round(rec.latency_s + out.latency_s, 2)
        ctx.store.transcript_path(task.id, arm.letter, attempt).write_text(out.jsonl, encoding="utf-8")
        t = parse_jsonl(out.jsonl)
        rec.tokens = _add(rec.tokens, t.total_tokens)
        rec.fresh_tokens = _add(rec.fresh_tokens, t.fresh_tokens)
        if attempt == 1:
            rec.input_tokens_first = t.input_tokens
        ctx.spent_tokens += t.fresh_tokens or 0
        _stop_if_account_problem(t, tag)

        verdict = isolation.check(t, uses_context7=arm.uses_context7, deny=deny, cwd=arm_dir)
        rec.context7_calls += verdict.context7_calls
        rec.kb_access_denied += verdict.kb_access_denied
        if verdict.contaminated:
            rec.outcome, rec.contamination_reasons = "contaminated", list(verdict.reasons)
            ctx.log(f"{tag} → contaminated: {verdict.reasons[0]}")
            return rec
        if arm.uses_context7 and (verdict.context7_unavailable or verdict.mcp_missing or verdict.context7_refused):
            why = ("context7 MCP not available in the session" if verdict.mcp_missing else
                   f"context7 refused {verdict.context7_refused} call(s) (quota/auth)" if verdict.context7_refused
                   else "every context7 call failed on transport")
            raise Context7Unavailable(f"{tag}: {why}")
        if out.timed_out or not t.ended:
            why = "wall-clock timeout" if out.timed_out else (
                f"turn failed: {t.error_message[:160]}" if t.failed
                else f"no turn.completed event (exit {out.exit_code})")
            rec.outcome, rec.reason = "timeout", why
            ctx.log(f"{tag} → timeout ({why})")
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
        ctx.log(f"── {i}/{len(todo)} · spent {ctx.spent_tokens:,} fresh tokens")
        rec = run_pair(by_id[task_id], ctx.cfg.arms[letter], ctx)
        ctx.store.append(rec)
        records.append(rec)
        if ctx.spent_tokens > ctx.cfg.budget_tokens:
            raise BudgetExceeded(f"spent {ctx.spent_tokens:,} > budget {ctx.cfg.budget_tokens:,} fresh tokens")
    return records
