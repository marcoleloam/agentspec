#!/usr/bin/env python3
"""AgentSpec Mission Control — render the active feature's live state as a
self-contained HTML dashboard from the plain files we already write
(.active, BLACKBOARD, BUILD_REPORT). Zero dependencies.

Usage:
    python3 status-dashboard.py [FEATURE]

Reads .claude/sdd/.active when FEATURE is omitted. Writes
.claude/sdd/.status/dashboard.html and prints its path.
"""
from __future__ import annotations

import html
import re
import sys
from datetime import datetime
from pathlib import Path

SDD = Path(".claude/sdd")


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def resolve_feature(arg: str | None) -> tuple[str, str]:
    if arg:
        return arg, "unknown"
    active = read(SDD / ".active")
    feat = re.search(r"^feature:\s*(.+)$", active, re.M)
    phase = re.search(r"^phase:\s*(.+)$", active, re.M)
    return (feat.group(1).strip() if feat else ""), (phase.group(1).strip() if phase else "unknown")


def section(md: str, heading: str) -> str:
    """Return the body of a '## {heading}' section up to the next '## '."""
    pat = re.compile(r"^##\s+" + re.escape(heading) + r".*$", re.M)
    m = pat.search(md)
    if not m:
        return ""
    start = m.end()
    nxt = re.search(r"^##\s+", md[start:], re.M)
    return md[start: start + nxt.start()] if nxt else md[start:]


def count(md: str, *needles: str) -> int:
    return sum(md.count(n) for n in needles)


def file_status_counts(files_md: str) -> dict[str, int]:
    """Parse the 'Status dos Arquivos' table and classify by the Status column
    (3rd cell), so a ✅ in the 'Verificado' column never inflates the count."""
    res = {"done": 0, "doing": 0, "todo": 0, "blocked": 0}
    for line in files_md.splitlines():
        if not re.match(r"^\s*\|", line):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3 or "Arquivo" in cells[0] or set(cells[0]) <= set("-: "):
            continue
        status = cells[2]
        if "✅" in status:
            res["done"] += 1
        elif "🔄" in status:
            res["doing"] += 1
        elif "⏳" in status:
            res["todo"] += 1
        elif "❌" in status:
            res["blocked"] += 1
    return res


# --- minimal markdown -> HTML (headings, tables, lists, quotes, code, bold) ---
def md_to_html(md: str) -> str:
    lines = md.splitlines()
    out: list[str] = []
    i, n = 0, len(lines)

    def inline(s: str) -> str:
        s = html.escape(s)
        s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
        s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
        s = re.sub(r"\[(.+?)\]\((.+?)\)", r"\1", s)
        return s

    while i < n:
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if line.startswith("```"):
            i += 1
            buf = []
            while i < n and not lines[i].startswith("```"):
                buf.append(html.escape(lines[i]))
                i += 1
            i += 1
            out.append("<pre>" + "\n".join(buf) + "</pre>")
            continue
        if re.match(r"^#{1,6}\s", line):
            lvl = len(line) - len(line.lstrip("#"))
            out.append(f"<h{min(lvl,6)}>{inline(line.lstrip('# ').rstrip())}</h{min(lvl,6)}>")
            i += 1
            continue
        if re.match(r"^\s*\|", line) and i + 1 < n and re.match(r"^\s*\|[-:\s|]+\|?\s*$", lines[i + 1]):
            header = [c.strip() for c in line.strip().strip("|").split("|")]
            i += 2
            rows = []
            while i < n and re.match(r"^\s*\|", lines[i]):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            thead = "".join(f"<th>{inline(c)}</th>" for c in header)
            tbody = "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in rows)
            out.append(f"<table><thead><tr>{thead}</tr></thead><tbody>{tbody}</tbody></table>")
            continue
        if re.match(r"^\s*[-*]\s", line):
            items = []
            while i < n and re.match(r"^\s*[-*]\s", lines[i]):
                items.append(f"<li>{inline(lines[i].strip()[2:])}</li>")
                i += 1
            out.append("<ul>" + "".join(items) + "</ul>")
            continue
        if line.startswith(">"):
            out.append(f"<blockquote>{inline(line.lstrip('> ').rstrip())}</blockquote>")
            i += 1
            continue
        if re.match(r"^---+\s*$", line):
            out.append("<hr>")
            i += 1
            continue
        out.append(f"<p>{inline(line)}</p>")
        i += 1
    return "\n".join(out)


def chip(label: str, value: int, kind: str) -> str:
    return f'<div class="chip {kind}"><span class="v">{value}</span><span class="l">{label}</span></div>'


def build_html(feature: str, phase: str, blackboard: str, report: str) -> str:
    fs = file_status_counts(section(blackboard, "Status dos Arquivos"))
    done, doing, todo, blocked_files = fs["done"], fs["doing"], fs["todo"], fs["blocked"]
    open_blockers = count(section(blackboard, "Perguntas Abertas e Bloqueadores"), "🔴")
    improvements = len([l for l in section(blackboard, "Melhorias / Iterações").splitlines()
                        if re.match(r"^\s*\|\s*M-\d", l)])
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    chips = "".join([
        chip("Completos", done, "ok"),
        chip("Em andamento", doing, "go"),
        chip("Pendentes", todo, "wait"),
        chip("Bloqueados", blocked_files + open_blockers, "bad"),
        chip("Melhorias", improvements, "info"),
    ])

    sections = ""
    if blackboard.strip():
        sections += f'<section class="card"><h2 class="ct">Blackboard</h2>{md_to_html(blackboard)}</section>'
    else:
        sections += '<section class="card empty">Sem blackboard ainda — rode <code>/build</code> para criá-lo.</section>'
    if report.strip():
        sections += f'<section class="card"><h2 class="ct">Build Report</h2>{md_to_html(report)}</section>'

    title = feature or "(nenhuma feature ativa)"
    return f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AgentSpec · {html.escape(title)}</title>
<style>
:root{{--bg:#0d1117;--panel:#161b22;--bd:#30363d;--fg:#e6edf3;--mut:#8b949e;
--ok:#3fb950;--go:#58a6ff;--wait:#d29922;--bad:#f85149;--info:#bc8cff;--acc:#ff7b29}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--fg);
font:14px/1.55 -apple-system,Segoe UI,Roboto,sans-serif}}
header{{padding:22px 28px;border-bottom:1px solid var(--bd);
background:linear-gradient(180deg,#161b22,#0d1117)}}
h1{{margin:0;font-size:20px;letter-spacing:.3px}}
h1 .acc{{color:var(--acc)}}
.meta{{color:var(--mut);font-size:12px;margin-top:4px}}
.meta b{{color:var(--fg)}}
.strip{{display:flex;gap:12px;flex-wrap:wrap;padding:18px 28px}}
.chip{{background:var(--panel);border:1px solid var(--bd);border-radius:10px;
padding:12px 16px;min-width:104px;display:flex;flex-direction:column;gap:2px}}
.chip .v{{font-size:24px;font-weight:700}}.chip .l{{font-size:11px;color:var(--mut);text-transform:uppercase;letter-spacing:.5px}}
.chip.ok .v{{color:var(--ok)}}.chip.go .v{{color:var(--go)}}.chip.wait .v{{color:var(--wait)}}
.chip.bad .v{{color:var(--bad)}}.chip.info .v{{color:var(--info)}}
main{{padding:8px 28px 40px;max-width:1100px}}
.card{{background:var(--panel);border:1px solid var(--bd);border-radius:12px;
padding:8px 22px 18px;margin:16px 0}}
.card.empty{{color:var(--mut);padding:24px}}
.ct{{color:var(--acc);border-bottom:1px solid var(--bd);padding-bottom:8px;font-size:15px}}
h3,h4{{color:var(--fg)}}
table{{border-collapse:collapse;width:100%;margin:10px 0;font-size:13px}}
th,td{{border:1px solid var(--bd);padding:7px 10px;text-align:left;vertical-align:top}}
th{{background:#1c2230;color:var(--mut);font-weight:600}}
tr:nth-child(even) td{{background:#11161e}}
code{{background:#1c2230;padding:1px 6px;border-radius:5px;font-size:12px;color:#ffa657}}
pre{{background:#010409;border:1px solid var(--bd);border-radius:8px;padding:12px;overflow:auto}}
blockquote{{border-left:3px solid var(--acc);margin:8px 0;padding:2px 14px;color:var(--mut)}}
ul{{margin:6px 0}}hr{{border:0;border-top:1px solid var(--bd);margin:14px 0}}
a{{color:var(--go)}}.foot{{color:var(--mut);font-size:11px;padding:0 28px 24px}}
</style></head><body>
<header>
  <h1>AgentSpec <span class="acc">·</span> Mission Control</h1>
  <div class="meta">Feature <b>{html.escape(title)}</b> &nbsp;·&nbsp; fase <b>{html.escape(phase)}</b>
  &nbsp;·&nbsp; gerado em {ts}</div>
</header>
<div class="strip">{chips}</div>
<main>{sections}</main>
<div class="foot">Snapshot estático — rode <code>/work --status</code> de novo para atualizar.</div>
</body></html>"""


def main() -> int:
    feature, phase = resolve_feature(sys.argv[1] if len(sys.argv) > 1 else None)
    blackboard = read(SDD / "features" / f"BLACKBOARD_{feature}.md") if feature else ""
    report = read(SDD / "reports" / f"BUILD_REPORT_{feature}.md") if feature else ""
    out_dir = SDD / ".status"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "dashboard.html"
    out_file.write_text(build_html(feature, phase, blackboard, report), encoding="utf-8")
    print(str(out_file))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
