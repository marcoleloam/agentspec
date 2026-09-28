"""Aggregate a run, apply the decision rule and render REPORT.md (pt-BR).

Decision rule (DEFINE, fixed before the first run; DESIGN Decisão 6):
  per stratum, arm X "satisfies" vs A when resolved_rate(X) >= resolved_rate(A)
  and human_rate(X) <= human_rate(A), rates over valid (non-excluded) runs.
  inconclusive  if any arm has excluded > 1/3 of its runs (or no runs)
  D satisfies → aposentar KB · B → substituir por B · C → enxugar (C) · else manter A
"""
from __future__ import annotations

import statistics
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from kb_bench.config import ARM_LETTERS, STRATA, BenchConfig
from kb_bench.human_queue import HumanQueue
from kb_bench.store import EXCLUDED, Record, RunStore

STRATUM_LABEL = {"library": "Biblioteca", "conceptual": "Conceitual", "niche": "Nicho"}
ARM_LABEL = {"A": "A — KB atual", "B": "B — Context7", "C": "C — KB enxuta + C7", "D": "D — nada"}
INCONCLUSIVE = "inconclusivo"
MIN_SAMPLE_WARNING = 3


@dataclass(frozen=True)
class ArmScore:
    total: int
    excluded: int
    resolved: int
    human: int
    pass_first: int = 0
    pass_retry: int = 0

    @property
    def valid(self) -> int:
        return self.total - self.excluded

    def rate(self, n: int) -> float:
        return n / self.valid if self.valid else 0.0

    @property
    def resolved_rate(self) -> float:
        return self.rate(self.resolved)

    @property
    def human_rate(self) -> float:
        return self.rate(self.human)


def score(records: list[Record]) -> ArmScore:
    excluded = sum(r.outcome in EXCLUDED for r in records)
    first = sum(r.outcome == "pass_first" for r in records)
    retry = sum(r.outcome == "pass_retry" for r in records)
    human = sum(r.outcome == "human" for r in records)
    return ArmScore(len(records), excluded, first + retry, human, first, retry)


def satisfies(x: ArmScore, a: ArmScore) -> bool:
    return x.resolved_rate >= a.resolved_rate and x.human_rate <= a.human_rate


def recommend(scores: dict[str, ArmScore]) -> str:
    if any(scores.get(k) is None for k in ARM_LETTERS):
        return INCONCLUSIVE
    if any(s.total == 0 or s.valid == 0 or s.excluded * 3 > s.total for s in scores.values()):
        return INCONCLUSIVE
    a = scores["A"]
    if satisfies(scores["D"], a):
        return "aposentar KB"
    if satisfies(scores["B"], a):
        return "substituir por B"
    if satisfies(scores["C"], a):
        return "enxugar (C)"
    return "manter A"


def _justify(rec: str, scores: dict[str, ArmScore]) -> str:
    if rec == INCONCLUSIVE:
        bad = [k for k, s in scores.items() if s.total == 0 or s.valid == 0 or s.excluded * 3 > s.total]
        return f"exclusões acima de 1/3 (ou sem execuções) em: {', '.join(bad) or 'braços ausentes'}"
    a = scores["A"]
    pick = {"aposentar KB": "D", "substituir por B": "B", "enxugar (C)": "C"}.get(rec)
    if pick:
        s = scores[pick]
        note = (f"{pick} resolveu {s.resolved_rate:.0%} (A {a.resolved_rate:.0%}) e mandou "
                f"{s.human_rate:.0%} para humano (A {a.human_rate:.0%})")
        if pick == "B" and satisfies(scores["C"], a):
            note += "; C também cumpre — ver tokens no placar"
        return note
    return f"nenhum braço igualou A ({a.resolved_rate:.0%} resolvidas, {a.human_rate:.0%} humano)"


def _median(values: list[float]) -> str:
    vals = [v for v in values if v is not None]
    return f"{statistics.median(vals):,.0f}" if vals else "—"


def _words(path: Path) -> int:
    return sum(len(p.read_text(encoding="utf-8", errors="replace").split()) for p in path.rglob("*.md")) \
        if path.is_dir() else 0


def group(records: list[Record]) -> dict[str, dict[str, list[Record]]]:
    out: dict[str, dict[str, list[Record]]] = defaultdict(lambda: defaultdict(list))
    for r in records:
        out[r.stratum][r.arm].append(r)
    return out


def recommendations(records: list[Record]) -> dict[str, str]:
    grouped = group(records)
    return {s: recommend({a: score(grouped[s][a]) for a in ARM_LETTERS}) for s in STRATA if s in grouped}


def render(store: RunStore, cfg: BenchConfig) -> str:
    records = store.records()
    env = store.read_json("env.json") or {}
    coverage = store.read_json("coverage.json") or {}
    queue = HumanQueue(store.root)
    verdicts, mapping = queue.verdicts(), queue.mapping()
    grouped = group(records)
    plan = store.read_json("plan.json") or {}
    expected = len(plan.get("pairs", [])) or len(records)
    lines = [
        f"# Relatório kb_bench — {store.run_id}",
        "",
        "| Item | Valor |",
        "|------|-------|",
        f"| Commit | `{env.get('commit', '?')}` |",
        f"| Codex CLI | `{env.get('cli_version', '?')}` |",
        (f"| Modelo pedido (esforço) | `{env.get('model', cfg.model or 'account default')}` "
         f"(`{env.get('reasoning_effort', cfg.reasoning_effort or 'model default')}`) |"),
        f"| Seed | `{env.get('seed', cfg.seed)}` |",
        f"| Execuções registradas | {len(records)} de {expected} planejadas |",
        (f"| Tokens (total / novos) | {sum(r.tokens or 0 for r in records):,} / "
         f"{sum(r.fresh_tokens or 0 for r in records):,} (orçamento {cfg.budget_tokens:,} novos) |"),
        "",
        ("> **Custo em US$ não medido.** A Codex CLI com login ChatGPT não reporta custo nem o modelo efetivo; "
         "o orçamento conta tokens novos (entrada fora do cache + saída) e o modelo é o pedido."),
        "",
        ("> **Indicativo, não estatístico.** Cerca de 6 tarefas por estrato e braço: uma tarefa muda a taxa "
         "em ~17 pp. Use o placar como sinal de direção, não como prova."),
        "",
    ]
    if len(records) < expected:
        lines += ["> ⚠️ **Rodada incompleta** — recomendações calculadas só com o que foi registrado.", ""]

    lines += ["## Recomendação por estrato", "", "| Estrato | Recomendação | Justificativa |", "|---|---|---|"]
    for stratum in STRATA:
        if stratum not in grouped:
            continue
        scores = {a: score(grouped[stratum][a]) for a in ARM_LETTERS}
        rec = recommend(scores)
        smallest = min(s.valid for s in scores.values())
        warn = (f" ⚠️ amostra de {smallest} execução(ões) válida(s) por braço — só um sinal, não decida por isto"
                if rec != INCONCLUSIVE and smallest < MIN_SAMPLE_WARNING else "")
        lines.append(f"| {STRATUM_LABEL[stratum]} | **{rec}** | {_justify(rec, scores)}{warn} |")
    lines.append("")

    lines += ["## Placar braço × estrato", "",
              ("| Estrato | Braço | Total | Válidos | 1ª | Retry | Humano | Excl. (u/t/c) | Resolvidas | Humano % "
               "| Tokens (mediana) | Tokens novos (mediana) | Latência s (mediana) | Chamadas C7 | KB negada |"),
              "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for stratum in STRATA:
        for arm in ARM_LETTERS:
            rs = grouped.get(stratum, {}).get(arm, [])
            if not rs:
                continue
            s = score(rs)
            excl = "/".join(str(sum(r.outcome == o for r in rs)) for o in ("unavailable", "timeout", "contaminated"))
            lines.append(
                f"| {STRATUM_LABEL[stratum]} | {ARM_LABEL[arm]} | {s.total} | {s.valid} | {s.pass_first} | "
                f"{s.pass_retry} | {s.human} | {excl} | {s.resolved_rate:.0%} | {s.human_rate:.0%} | "
                f"{_median([r.tokens for r in rs])} | {_median([r.fresh_tokens for r in rs])} | "
                f"{_median([r.latency_s for r in rs])} | "
                f"{sum(r.context7_calls for r in rs)} | {sum(r.kb_access_denied for r in rs)} |"
            )
    lines.append("")

    lines += ["## Cobertura do Context7", ""]
    if coverage:
        lines += ["| Domínio | Cobertura | Melhor library ID |", "|---|---|---|"]
        for domain, info in sorted(coverage.items()):
            lines.append(f"| {domain} | {info.get('status', '?')} | `{info.get('library_id') or '—'}` |")
    else:
        lines.append("Sem `coverage.json` (rode `kb_bench smoke`).")
    lines.append("")

    contaminated = [r for r in records if r.outcome == "contaminated"]
    lines += ["## Isolamento", "",
              f"- Execuções contaminadas: **{len(contaminated)}** (excluídas do placar)."]
    lines += [f"  - `{r.task}` braço {r.arm}: {'; '.join(r.contamination_reasons)}" for r in contaminated]
    denied = defaultdict(int)
    for r in records:
        denied[r.arm] += r.kb_access_denied
    lines.append("- Tentativas de ler KB negadas pelo perfil de permissões: "
                 + ", ".join(f"{a}={denied[a]}" for a in ARM_LETTERS) + ".")
    lines.append("")

    lines += ["## Revisão humana (calibração dos evals)", ""]
    human = [r for r in records if r.outcome == "human"]
    if not human:
        lines.append("Nenhuma execução foi para revisão humana.")
    else:
        lines += ["| Tarefa | Braço | Item | Veredito |", "|---|---|---|---|"]
        for r in sorted(human, key=lambda x: (x.task, x.arm)):
            v = verdicts.get(r.human_id or "", {}).get("verdict", "pendente")
            lines.append(f"| `{r.task}` | {r.arm} | `{r.human_id}` | {v} |")
        approvals = defaultdict(int)
        for item, v in verdicts.items():
            if v.get("verdict") == "approve" and item in mapping:
                approvals[mapping[item]["task"]] += 1
        if approvals:
            lines += ["", "Tarefas com saídas aprovadas pelo humano apesar do eval (eval possivelmente rígido): "
                      + ", ".join(f"`{t}` ({n})" for t, n in sorted(approvals.items())) + "."]
    lines.append("")

    origins = {r.origin for r in records}
    lines += ["## Origem das tarefas", "",
              f"- Origens presentes: {', '.join(sorted(origins)) or '—'}."]
    if origins == {"synthetic"}:
        lines.append("- Só tarefas sintéticas nesta rodada: há risco de viés, apesar da regra de não ler a KB "
                     "na autoria.")
    if len(origins) > 1:
        for origin in sorted(origins):
            sub = [r for r in records if r.origin == origin]
            lines.append(f"- `{origin}`: " + "; ".join(
                f"{STRATUM_LABEL[s]} → {v}" for s, v in recommendations(sub).items()))
    lines.append("")

    first_inputs = [r.input_tokens_first for r in records if r.input_tokens_first]
    kb_words = {d: (_words(cfg.repo_kb / d), _words(cfg.kb_lean_dir / d))
                for d in sorted({r.domain for r in records})}
    lines += ["## Custo de base e tamanho das KBs", "",
              (f"- Tokens de entrada da 1ª chamada (mediana, todos os braços): {_median(first_inputs)}. "
               "Com HOME e CODEX_HOME isolados, é só o prompt de sistema e as ferramentas da Codex, "
               "constantes entre braços."),
              "", "| Domínio | Palavras KB (A) | Palavras KB enxuta (C) |", "|---|---|---|"]
    lines += [f"| {d} | {a:,} | {c:,} |" for d, (a, c) in kb_words.items()]
    dirty = env.get("git_dirty_new") or []
    lines += ["", "## Efeito colateral no repositório", "",
              "- Nenhuma mudança nova fora de `scripts/kb_bench/`." if not dirty
              else "- ⚠️ Mudanças novas detectadas: " + ", ".join(f"`{p}`" for p in dirty)]
    return "\n".join(lines) + "\n"


def write_report(store: RunStore, cfg: BenchConfig) -> Path:
    path = store.root / "REPORT.md"
    path.write_text(render(store, cfg), encoding="utf-8")
    return path
