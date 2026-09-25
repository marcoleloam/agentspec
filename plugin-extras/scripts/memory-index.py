#!/usr/bin/env python3
"""AgentSpec Living Memory — phase brief, open-question gate, session tail and a
derived MEMORY_INDEX.md, computed from the files we already write
(BLACKBOARD_*, archive/*/{BLACKBOARD,DESIGN,SHIPPED}*, MEMORY.md). Zero dependencies.
Deterministic: no timestamps in output, stable ordering.

Usage:
    python3 memory-index.py brief FEATURE --phase define [--max 15] [--domains a,b]
    python3 memory-index.py gate  FEATURE --to design|build      # exit 1 = blocked
    python3 memory-index.py tail  [FEATURE] [--n 5]              # FEATURE from .active
    python3 memory-index.py build [--verbose]                    # writes MEMORY_INDEX.md

Exit 2 (gate, build) = a blackboard has entry rows the parser cannot read — fix the
table columns (see BLACKBOARD_TEMPLATE.md) instead of losing that memory silently.

All commands accept --root (default .claude/sdd). Contract:
WORKFLOW_CONTRACTS.yaml → living_memory.
"""
from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

PHASES = ("brainstorm", "define", "design", "build", "iterate", "ship")
PHASE_ORDER = {p: i for i, p in enumerate(PHASES)}
KIND_ORDER = {k: i for i, k in enumerate("DQAML")}
GATED = ("build", "design")
BAND_CAPS = {"decisions": 6, "assumptions": 3, "cross": 4}
TEXT_WIDTH = 110
NO_VALUE = {"", "—", "-", "n/a"}
ID_RE = re.compile(r"^[A-Z]+-\d+$")
ENTRY_ID_RE = re.compile(r"^([DAQM])-\d+$")
REF_RE = re.compile(r"\b[A-Z]-\d{3,}\b")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
STATUS_ICON = {
    "open": "🔴", "delegated": "🟡", "resolved": "🟢",
    "pending": "⏳", "validated": "✅", "refuted": "❌",
}


@dataclass(frozen=True)
class Entry:
    feature: str
    phase: str
    kind: str
    id: str
    text: str
    status: str = ""
    supersedes: tuple[str, ...] = ()
    where: str = ""
    date: str = ""
    seq: int = 0


@dataclass
class Memory:
    entries: list[Entry] = field(default_factory=list)
    domains: dict[str, set[str]] = field(default_factory=dict)
    related: dict[str, set[str]] = field(default_factory=dict)
    skipped: int = 0
    sources: dict[str, int] = field(default_factory=dict)
    unreadable: dict[str, list[str]] = field(default_factory=dict)


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def fold(s: str) -> str:
    """Lowercase and strip accents so 'Decisão' == 'Decisao', 'Lições' == 'Licoes'."""
    decomposed = unicodedata.normalize("NFKD", s)
    return "".join(c for c in decomposed if not unicodedata.combining(c)).lower().strip()


def slug(heading: str) -> str:
    """GitHub-style anchor: lowercase, keep word chars/space/hyphen, spaces → '-'."""
    return re.sub(r"[^\w\- ]", "", heading.strip().lower()).replace(" ", "-")


def clean(cell: str) -> str:
    return cell.replace("**", "").strip()


def sections(md: str) -> list[tuple[str, str, str]]:
    """Split a document on '## ' headings → [(folded heading, raw heading, body)]."""
    out: list[tuple[str, str, str]] = []
    current: tuple[str, list[str]] | None = None
    for line in md.splitlines():
        if line.startswith("## "):
            if current:
                out.append((fold(current[0]), current[0], "\n".join(current[1])))
            current = (line[3:].strip(), [])
        elif current:
            current[1].append(line)
    if current:
        out.append((fold(current[0]), current[0], "\n".join(current[1])))
    return out


def section(md: str, prefix: str) -> tuple[str, str]:
    """First '## ' section whose folded heading starts with the folded prefix."""
    want = fold(prefix)
    for folded, raw, body in sections(md):
        if folded.startswith(want):
            return raw, body
    return "", ""


def split_row(line: str) -> list[str]:
    """Split a Markdown table row on unescaped pipes; '\\|' stays inside the cell."""
    body = line.strip().removeprefix("|").removesuffix("|")
    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", body)]


def parse_table(body: str) -> list[dict[str, str]]:
    """Header-driven: map folded column names → cell text. Skips the separator row."""
    rows = [l for l in body.splitlines() if l.lstrip().startswith("|")]
    if len(rows) < 2:
        return []
    header = [fold(clean(c)) for c in split_row(rows[0])]
    out = []
    for line in rows[1:]:
        cells = split_row(line)
        if all(set(c) <= set("-: ") for c in cells):
            continue
        cells += [""] * (len(header) - len(cells))
        out.append(dict(zip(header, cells)))
    return out


def cell(row: dict[str, str], *prefixes: str) -> str:
    for p in prefixes:
        for key, value in row.items():
            if key.startswith(p):
                return value.strip()
    return ""


def phase_of(value: str, default: str = "build") -> str:
    v = fold(value)
    for p in PHASES:
        if p in v:
            return p
    return default


def question_status(value: str) -> str:
    if "🔴" in value:
        return "open"
    if "🟡" in value:
        target = phase_of(value, default="")
        return f"delegated:{target}" if target else "delegated"
    if "🟢" in value:
        return "resolved"
    return ""


def assumption_status(value: str) -> str:
    v = fold(value)
    if "❌" in value or "derrub" in v:
        return "refuted"
    if "nao valid" in v or "⏳" in value:
        return "pending"
    if "✅" in value or "valid" in v:
        return "validated"
    return "pending"


def refs(value: str) -> tuple[str, ...]:
    return tuple(REF_RE.findall(value))


def is_placeholder(text: str) -> bool:
    return not text or text.startswith("{")


def rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def metadata(md: str) -> dict[str, str]:
    _, body = section(md, "Metadados")
    meta = {}
    for row in parse_table(body):
        values = list(row.values())
        if len(values) >= 2:
            meta[fold(clean(values[0]))] = clean(values[1])
    return meta


def entry_id_of(row: dict[str, str], kind: str) -> str:
    """ID column is '#' in the template; accept 'ID' and, failing both, any cell holding one."""
    value = cell(row, "#", "id")
    if ID_RE.match(value):
        return value
    return next((v.strip() for v in row.values() if re.match(rf"^{kind}-\d+$", v.strip())), "")


def entry_rows(md: str) -> set[str]:
    """IDs of every non-placeholder table row that looks like a D/A/Q/M entry, anywhere."""
    found: set[str] = set()
    for line in md.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [clean(c) for c in split_row(line)]
        if any(c.startswith("{") for c in cells):
            continue
        found.update(c for c in cells if ENTRY_ID_RE.match(c))
    return found


def root_relative(where: str, folder: Path, root: Path) -> str:
    """'DESIGN_X.md#a' written next to the blackboard → 'features/DESIGN_X.md#a' (like archive/ entries)."""
    target, sep, anchor = where.partition("#")
    target = target.strip().strip("`")
    if not target or "/" in target or not (folder / target).is_file():
        return where
    return f"{rel(folder / target, root)}{sep}{anchor}"


def blackboard_entries(path: Path, root: Path, feature: str, mem: Memory) -> list[Entry]:
    md = read(path)
    where_file = rel(path, root)
    out: list[Entry] = []
    seq = 0
    tables = (
        ("Log de Decis", "D", ("decis",)),
        ("Premissas", "A", ("premissa",)),
        ("Perguntas", "Q", ("pergunta",)),
        ("Melhorias", "M", ("pedido",)),
    )
    for heading, kind, text_keys in tables:
        raw_heading, body = section(md, heading)
        anchor = f"{where_file}#{slug(raw_heading)}" if raw_heading else where_file
        for row in parse_table(body):
            entry_id = entry_id_of(row, kind)
            text = cell(row, *text_keys)
            if not ID_RE.match(entry_id) or is_placeholder(text):
                mem.skipped += 1
                continue
            status_cell = cell(row, "status")
            if kind == "Q":
                status = question_status(status_cell)
            elif kind == "A":
                status = assumption_status(status_cell)
            else:
                status = ""
            if kind == "M":
                phase = "iterate" if "design" in fold(cell(row, "tipo")) else "build"
            else:
                phase = phase_of(cell(row, "fase"))
            where = root_relative(cell(row, "onde ler"), path.parent, root)
            seq += 1
            out.append(Entry(
                feature=feature, phase=phase, kind=kind, id=entry_id, text=text,
                status=status, supersedes=refs(cell(row, "substitui")),
                where=where if where.lower() not in NO_VALUE else anchor,
                date=_first_date(cell(row, "data")), seq=seq,
            ))
    lost = sorted(entry_rows(md) - {e.id for e in out})
    if lost:
        mem.unreadable[feature] = lost
    return out


def unreadable_warning(mem: Memory, feature: str) -> str:
    lost = mem.unreadable.get(feature, [])
    if not lost:
        return ""
    ids = ", ".join(lost[:6]) + (", …" if len(lost) > 6 else "")
    return (f"  ⚠ BLACKBOARD_{feature}.md: {len(lost)} linha(s) ilegível(is) ({ids}) — use as "
            "seções e colunas do BLACKBOARD_TEMPLATE.md (coluna '#', texto em 'Decisão' / "
            "'Premissa' / 'Pergunta', seções '## Log de Decisões' / '## Premissas' / "
            "'## Perguntas Abertas')")


def _first_date(value: str) -> str:
    m = DATE_RE.search(value)
    return m.group(0) if m else ""


def design_entries(path: Path, root: Path, feature: str) -> list[Entry]:
    """Archived DESIGN without a blackboard: '### Decisão N: título' → D-00N."""
    lines = read(path).splitlines()
    out: list[Entry] = []
    for i, line in enumerate(lines):
        if not line.startswith("### "):
            continue
        heading = line[4:].strip()
        m = re.match(r"^decisao\s+(\d+)\s*:\s*(.+)$", fold(heading))
        if not m:
            continue
        title = heading.split(":", 1)[1].strip()
        date = ""
        for follow in lines[i + 1:]:
            if follow.startswith("#"):
                break
            if "**data**" in fold(follow):
                date = _first_date(follow)
                break
        n = int(m.group(1))
        out.append(Entry(
            feature=feature, phase="design", kind="D", id=f"D-{n:03d}", text=title,
            where=f"{rel(path, root)}#{slug(heading)}", date=date, seq=n,
        ))
    return out


def shipped_entries(path: Path, root: Path, feature: str) -> list[Entry]:
    """Bullets under '## Lições Aprendidas' (accent-insensitive) → L-###."""
    raw_heading, body = section(read(path), "Licoes Aprendidas")
    if not raw_heading:
        return []
    m = DATE_RE.search(path.name)
    date = m.group(0) if m else ""
    out: list[Entry] = []
    for line in body.splitlines():
        bullet = re.match(r"^\s*[-*]\s+(.+)$", line)
        if not bullet:
            continue
        n = len(out) + 1
        out.append(Entry(
            feature=feature, phase="ship", kind="L", id=f"L-{n:03d}",
            text=bullet.group(1).strip(), where=f"{rel(path, root)}#{slug(raw_heading)}",
            date=date, seq=n,
        ))
    return out


def memory_entries(path: Path, root: Path) -> list[Entry]:
    out: list[Entry] = []
    for line in read(path).splitlines():
        if not line.startswith("## "):
            continue
        heading = line[3:].strip()
        n = len(out) + 1
        out.append(Entry(
            feature="—", phase="ship", kind="L", id=f"L-{n:03d}", text=heading,
            where=f"{rel(path, root)}#{slug(heading)}", date=_first_date(heading), seq=n,
        ))
    return out


def known_domains(root: Path) -> set[str]:
    """Keys under the top-level 'domains:' block of kb/_index.yaml (no YAML parser)."""
    text = read(root.parent / "kb" / "_index.yaml")
    found: set[str] = set()
    inside = False
    for line in text.splitlines():
        if re.match(r"^\S", line):
            inside = line.startswith("domains:")
            continue
        if inside:
            m = re.match(r"^  ([a-z0-9][a-z0-9-]*):\s*$", line)
            if m:
                found.add(m.group(1))
    return found


def scan_domains(text: str, known: set[str]) -> set[str]:
    return {d for d in known if re.search(rf"(?<![\w-]){re.escape(d)}(?![\w-])", text)}


def row_value(md: str, label: str) -> str:
    """Value cell of the first table row whose first cell (folded) contains label."""
    want = fold(label)
    for line in md.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = split_row(line)
        if len(cells) >= 2 and want in fold(clean(cells[0])):
            return cells[1]
    return ""


def listed(value: str) -> set[str]:
    value = clean(value).replace("`", "")
    if is_placeholder(value) or value.lower() in NO_VALUE:
        return set()
    return {fold(v) for v in re.split(r"[,;]", value) if v.strip() and v.strip() not in NO_VALUE}


def feature_domains(bb_md: str, docs: list[Path], known: set[str]) -> set[str]:
    """Cascade: blackboard Metadados → DEFINE/BRAINSTORM 'Domínios KB' row → DEFINE scan."""
    declared = listed(metadata(bb_md).get("dominios kb", "")) if bb_md else set()
    if declared:
        return declared
    for doc in docs:
        value = row_value(read(doc), "Dominios KB")
        hits = scan_domains(value, known) if known else listed(value)
        if hits:
            return hits
    define = next((d for d in docs if d.name.startswith("DEFINE_")), None)
    return scan_domains(read(define), known) if define and known else set()


def feature_dirs(root: Path) -> list[tuple[str, Path, bool]]:
    """(feature, directory, archived) for every feature with artifacts."""
    found: dict[str, tuple[Path, bool]] = {}
    features_dir = root / "features"
    if features_dir.is_dir():
        for p in sorted(features_dir.glob("*_*.md")):
            m = re.match(r"^(?:BRAINSTORM|DEFINE|DESIGN|BLACKBOARD)_(.+)\.md$", p.name)
            if m:
                found.setdefault(m.group(1), (features_dir, False))
    archive = root / "archive"
    if archive.is_dir():
        for d in sorted(p for p in archive.iterdir() if p.is_dir()):
            found.setdefault(d.name, (d, True))
    return [(f, d, a) for f, (d, a) in sorted(found.items())]


def collect(root: Path) -> Memory:
    mem = Memory()
    known = known_domains(root)
    for feature, directory, archived in feature_dirs(root):
        bb = directory / f"BLACKBOARD_{feature}.md"
        bb_md = read(bb) if bb.is_file() else ""
        if bb_md:
            mem.entries += blackboard_entries(bb, root, feature, mem)
            mem.sources["blackboard"] = mem.sources.get("blackboard", 0) + 1
            meta = metadata(bb_md)
            related = listed(meta.get("relacionada a", ""))
            if related:
                mem.related[feature] = {r.upper() for r in related}
        elif archived:
            for design in sorted(directory.glob("DESIGN_*.md")):
                mem.entries += design_entries(design, root, feature)
                mem.sources["design"] = mem.sources.get("design", 0) + 1
        if archived:
            for shipped in sorted(directory.glob("SHIPPED_*.md")):
                mem.entries += shipped_entries(shipped, root, feature)
                mem.sources["shipped"] = mem.sources.get("shipped", 0) + 1
        docs = [directory / f"DEFINE_{feature}.md", directory / f"BRAINSTORM_{feature}.md"]
        mem.domains[feature] = feature_domains(bb_md, [d for d in docs if d.is_file()], known)
    memory_md = root / "MEMORY.md"
    if memory_md.is_file():
        mem.entries += memory_entries(memory_md, root)
        mem.sources["memory"] = 1
    mem.entries.sort(key=lambda e: (e.feature, PHASE_ORDER.get(e.phase, 99),
                                    KIND_ORDER.get(e.kind, 99), e.id, e.seq))
    return mem


def superseded(entries: list[Entry]) -> set[tuple[str, str]]:
    return {(e.feature, r) for e in entries for r in e.supersedes}


def current(entries: list[Entry]) -> list[Entry]:
    dead = superseded(entries)
    return [e for e in entries if (e.feature, e.id) not in dead]


def recent_first(entries: list[Entry]) -> list[Entry]:
    """Newest first; on the same date decisions outrank lessons, then later rows win."""
    return sorted(entries, key=lambda e: (e.date, -KIND_ORDER.get(e.kind, 99), e.seq, e.id),
                  reverse=True)


def interleave(first: list[Entry], second: list[Entry]) -> list[Entry]:
    """D, L, D, L, … so both decisions and lessons reach a small band."""
    out: list[Entry] = []
    for i in range(max(len(first), len(second))):
        out += first[i:i + 1] + second[i:i + 1]
    return out


def short(text: str) -> str:
    text = " ".join(text.replace("**", "").split())
    return text if len(text) <= TEXT_WIDTH else text[: TEXT_WIDTH - 1] + "…"


def line_for(e: Entry, cross: bool = False) -> str:
    icon = STATUS_ICON.get(e.status.split(":")[0], "")
    prefix = f"↔ {e.feature} " if cross else ""
    lead = f"{icon} " if icon else ""
    arrow = f" → {e.where}" if e.where and e.kind in "DL" else ""
    return f"  {lead}{prefix}{e.id} [{e.phase}] {short(e.text)}{arrow}"


def open_questions(mem: Memory, feature: str) -> list[Entry]:
    return [e for e in mem.entries if e.feature == feature and e.kind == "Q" and e.status == "open"]


def cross_features(mem: Memory, feature: str, extra_domains: set[str]) -> list[str]:
    mine = mem.domains.get(feature, set()) | extra_domains
    linked = mem.related.get(feature, set())
    out = []
    for other, domains in mem.domains.items():
        if other == feature:
            continue
        if (mine & domains) or other in linked or feature in mem.related.get(other, set()):
            out.append(other)
    return out


def brief(mem: Memory, feature: str, phase: str, budget: int = 15,
          extra_domains: set[str] | None = None) -> list[str]:
    extra = {fold(d) for d in (extra_domains or set())}
    live = current(mem.entries)
    mine = [e for e in live if e.feature == feature]
    header = f"▶ Memória de {feature} — entrando em {phase}"

    bands: list[list[str]] = []
    bands.append([line_for(e) for e in open_questions(mem, feature)])
    bands.append([line_for(e) for e in mine if e.kind == "Q" and e.status.startswith("delegated")
                  and e.status in ("delegated", f"delegated:{phase}")])
    if mine:
        seen = {e.phase for e in mine}
        gaps = [p for p in ("define", "design", "build")
                if PHASE_ORDER[p] < PHASE_ORDER[phase] and p not in seen]
        bands.append([f"  ⚠ sem registro nas fases: {', '.join(gaps)}"] if gaps else [])
    decisions = [line_for(e) for e in recent_first([e for e in mine if e.kind == "D"])]
    assumptions = [line_for(e) for e in recent_first(
        [e for e in mine if e.kind == "A" and e.status == "pending"])]
    others = set(cross_features(mem, feature, extra))
    cross = [line_for(e, cross=True) for e in interleave(
        recent_first([e for e in live if e.feature in others and e.kind == "D"]),
        recent_first([e for e in live if e.feature in others and e.kind == "L"]))]

    capped = [
        (decisions, BAND_CAPS["decisions"]),
        (assumptions, BAND_CAPS["assumptions"]),
        (cross, BAND_CAPS["cross"]),
    ]
    total = sum(len(b) for b in bands) + sum(len(b) for b, _ in capped)
    warning = unreadable_warning(mem, feature)
    top = [header] + ([warning] if warning else [])
    if total == 0:
        return top + [f"  (sem memória registrada para {feature})"]

    selected = [line for band in bands for line in band]
    selected += [line for band, cap in capped for line in band[:cap]]
    room = max(budget - len(top), 1)
    if len(selected) < total or len(selected) > room:
        room = max(room - 1, 1)
    shown = selected[:room]
    lines = top + shown
    omitted = total - len(shown)
    if omitted > 0:
        where = f"features/BLACKBOARD_{feature}.md e MEMORY_INDEX.md" if mine else "MEMORY_INDEX.md"
        lines.append(f"  … {omitted} omitidas — ver {where}")
    return lines


def tail(mem: Memory, feature: str, n: int = 5) -> list[str]:
    mine = recent_first([e for e in mem.entries if e.feature == feature and e.kind != "L"])
    warning = unreadable_warning(mem, feature)
    if not mine:
        return [warning] if warning else []
    head = f"=== Feature ativa: {feature} — últimas {min(n, len(mine))} entradas (BLACKBOARD_{feature}.md) ==="
    return [head] + ([warning] if warning else []) + [line_for(e) for e in mine[:n]]


def index_markdown(mem: Memory) -> str:
    dead = superseded(mem.entries)
    out = [
        "# MEMORY_INDEX",
        "",
        "> Gerado por `memory-index.py build` — não edite. Derivado de BLACKBOARD_*, archive/ e",
        "> MEMORY.md; pode ser apagado e recriado a qualquer momento.",
        "",
        "| Feature | Fase | Tipo | ID | Frase | Status | Domínios KB | Onde Ler |",
        "|---------|------|------|----|-------|--------|-------------|----------|",
    ]
    for e in mem.entries:
        status = "substituída" if (e.feature, e.id) in dead else STATUS_ICON.get(e.status.split(":")[0], "")
        domains = ", ".join(sorted(mem.domains.get(e.feature, set())))
        cells = [e.feature, e.phase, e.kind, e.id, short(e.text), status, domains, e.where]
        out.append("| " + " | ".join(c.replace("|", "\\|") for c in cells) + " |")
    return "\n".join(out) + "\n"


def active_feature(root: Path) -> str:
    m = re.search(r"^feature:\s*(.+)$", read(root / ".active"), re.MULTILINE)
    return m.group(1).strip() if m else ""


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="memory-index.py", description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=".claude/sdd", type=Path)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("brief", help="≤N-line memory brief when entering a phase")
    b.add_argument("feature")
    b.add_argument("--phase", required=True, choices=PHASES)
    b.add_argument("--max", type=int, default=15)
    b.add_argument("--domains", default="", help="comma-separated KB domains to add")
    g = sub.add_parser("gate", help="exit 1 when a 🔴 question blocks the transition")
    g.add_argument("feature")
    g.add_argument("--to", required=True, choices=GATED)
    t = sub.add_parser("tail", help="latest entries of the active feature")
    t.add_argument("feature", nargs="?")
    t.add_argument("--n", type=int, default=5)
    bl = sub.add_parser("build", help="write MEMORY_INDEX.md")
    bl.add_argument("--verbose", action="store_true")
    args = ap.parse_args(argv)

    mem = collect(args.root)
    if args.cmd == "brief":
        extra = {d.strip() for d in args.domains.split(",") if d.strip()}
        print("\n".join(brief(mem, args.feature, args.phase, args.max, extra)))
        return 0
    if args.cmd == "gate":
        warning = unreadable_warning(mem, args.feature)
        if warning:
            print(f"⛔ {args.feature}: o blackboard tem linhas ilegíveis — o gate não consegue "
                  f"verificar perguntas 🔴 para {args.to}.")
            print(warning)
            print("Corrija as colunas e rode o gate de novo.")
            return 2
        blocked = open_questions(mem, args.feature)
        if not blocked:
            print(f"✅ {args.feature}: nenhuma pergunta 🔴 aberta — pode seguir para {args.to}.")
            return 0
        print(f"⛔ {args.feature}: {len(blocked)} pergunta(s) 🔴 aberta(s) bloqueiam a transição para {args.to}:")
        print("\n".join(line_for(e) for e in blocked))
        print("Pergunte ao usuário: uma 🔴 só fecha com a resposta dele (marque 🟢 com a resposta em "
              "Resolução) ou via /iterate — nunca por premissa sua, nem em execução não interativa.")
        return 1
    if args.cmd == "tail":
        feature = args.feature or active_feature(args.root)
        lines = tail(mem, feature, args.n) if feature else []
        if lines:
            print("\n".join(lines))
        return 0
    target = args.root / "MEMORY_INDEX.md"
    target.write_text(index_markdown(mem), encoding="utf-8")
    if args.verbose:
        counts = ", ".join(f"{k}={v}" for k, v in sorted(mem.sources.items()))
        print(f"entries={len(mem.entries)} skipped={mem.skipped} {counts}", file=sys.stderr)
    print(target)
    warnings = [unreadable_warning(mem, f) for f in sorted(mem.unreadable)]
    if warnings:
        print("\n".join(warnings), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
