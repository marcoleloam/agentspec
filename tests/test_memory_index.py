"""Tests for plugin-extras/scripts/memory-index.py (Living Memory)."""
from __future__ import annotations

import ast
import importlib.util
import shutil
import sys
import time
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "plugin-extras" / "scripts" / "memory-index.py"
FIX = Path(__file__).parent / "fixtures" / "memory" / "sdd"
REAL = REPO / ".claude" / "sdd"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


mi = _load("memory_index", SCRIPT)


def run(capsys, *argv: str, root: Path = FIX) -> tuple[int, str]:
    code = mi.main(["--root", str(root), *argv])
    return code, capsys.readouterr().out


@pytest.fixture
def tree(tmp_path: Path) -> Path:
    """Writable copy of the fixture tree (sdd/ + kb/)."""
    shutil.copytree(FIX.parent, tmp_path / "memory")
    return tmp_path / "memory" / "sdd"


def write_blackboard(root: Path, feature: str, decisions: int) -> None:
    rows = "\n".join(
        f"| D-{i:03d} | design | @design-agent | Decisão {i} | porque {i} | alt {i} | — | — | 2026-09-{(i % 28) + 1:02d} |"
        for i in range(1, decisions + 1)
    )
    (root / "features" / f"BLACKBOARD_{feature}.md").write_text(
        "# BLACKBOARD\n\n## Log de Decisões\n\n"
        "| # | Fase | Agente | Decisão | Justificativa | Alternativa Rejeitada | Substitui | Onde Ler | Data |\n"
        "|---|------|--------|---------|---------------|-----------------------|-----------|----------|------|\n"
        f"{rows}\n",
        encoding="utf-8",
    )


# --- helpers -----------------------------------------------------------------

@pytest.mark.parametrize("a,b", [("Decisão", "decisao"), ("Lições Aprendidas", "licoes aprendidas"),
                                 ("  PREMISSAS ", "premissas")])
def test_fold_strips_accents_and_case(a, b):
    assert mi.fold(a) == b


def test_slug_matches_github_style():
    assert mi.slug("Decisão 2: Relatório em `Markdown`, não JSON") == "decisão-2-relatório-em-markdown-não-json"
    assert mi.slug("Log de Decisões") == "log-de-decisões"


def test_parse_table_is_header_driven():
    rows = mi.parse_table("| # | Fase | Decisão |\n|---|---|---|\n| D-001 | design | X |\n| D-002 |")
    assert rows[0] == {"#": "D-001", "fase": "design", "decisao": "X"}
    assert rows[1]["fase"] == ""


def test_parse_table_keeps_escaped_pipes_in_cell():
    rows = mi.parse_table("| # | Decisão |\n|---|---|\n| D-001 | `a \\| b` |")
    assert rows[0]["decisao"] == "`a | b`"


def test_parse_table_without_rows_is_empty():
    assert mi.parse_table("no table here") == []


@pytest.mark.parametrize("cell,expected", [
    ("🔴 Aberto", "open"), ("🟡 Delegada ao design", "delegated:design"),
    ("🟡 Delegada", "delegated"), ("🟢 Resolvido", "resolved"), ("?", ""),
])
def test_question_status(cell, expected):
    assert mi.question_status(cell) == expected


@pytest.mark.parametrize("cell,expected", [
    ("⏳ Não validada", "pending"), ("✅ Validada", "validated"),
    ("❌ Derrubada", "refuted"), ("", "pending"),
])
def test_assumption_status(cell, expected):
    assert mi.assumption_status(cell) == expected


def test_known_domains_reads_only_domains_block():
    assert mi.known_domains(FIX) == {"genai", "python", "data-quality"}


def test_known_domains_without_index_is_empty(tmp_path):
    assert mi.known_domains(tmp_path / "sdd") == set()


# --- collection ----------------------------------------------------------------

def test_collect_reads_new_blackboard_with_phases():
    mem = mi.collect(FIX)
    demo = {e.id: e for e in mem.entries if e.feature == "DEMO" and e.kind == "D"}
    assert set(demo) == {"D-001", "D-002", "D-003", "D-004"}
    assert demo["D-001"].phase == "brainstorm"
    assert demo["D-004"].supersedes == ("D-002",)
    assert demo["D-003"].where == "features/BLACKBOARD_DEMO.md#log-de-decisões"


def test_template_placeholder_rows_are_skipped():
    mem = mi.collect(FIX)
    assert not any(e.text.startswith("{") for e in mem.entries)
    assert mem.skipped >= 1


def test_legacy_blackboard_defaults_to_build_phase():
    """AT-010: old columns (no Fase) parse without error as phase build."""
    mem = mi.collect(FIX)
    legacy = [e for e in mem.entries if e.feature == "LEGACY"]
    assert {(e.kind, e.id, e.phase) for e in legacy} == {("D", "D-001", "build"), ("Q", "Q-001", "build")}


def test_archive_design_and_shipped_accent_insensitive():
    mem = mi.collect(FIX)
    old = [e for e in mem.entries if e.feature == "OLDFEAT"]
    decisions = [e for e in old if e.kind == "D"]
    lessons = [e for e in old if e.kind == "L"]
    assert [d.text for d in decisions] == ["Agent dedicado vs extensao", "Relatório em `Markdown`, não JSON"]
    assert decisions[0].date == "2026-01-05"
    assert decisions[1].where.endswith("#decisão-2-relatório-em-markdown-não-json")
    assert len(lessons) == 3
    assert all(l.date == "2026-01-10" for l in lessons)


def test_memory_md_headings_become_lessons():
    mem = mi.collect(FIX)
    lessons = [e for e in mem.entries if e.feature == "—"]
    assert [l.date for l in lessons] == ["2026-08-01", "2026-07-15"]


def test_domain_cascade():
    mem = mi.collect(FIX)
    assert mem.domains["DEMO"] == {"genai"}          # blackboard Metadados
    assert mem.domains["OLDFEAT"] == {"genai"}       # scan of archived DEFINE text
    assert mem.domains["LEGACY"] == set()


def test_domain_cascade_uses_define_row(tree):
    (tree / "features" / "DEFINE_ROWFEAT.md").write_text(
        "| **Domínios KB** | `python` (script), `data-quality` |\n", encoding="utf-8")
    assert mi.collect(tree).domains["ROWFEAT"] == {"python", "data-quality"}


def test_current_drops_superseded():
    live = mi.current(mi.collect(FIX).entries)
    ids = {e.id for e in live if e.feature == "DEMO" and e.kind == "D"}
    assert "D-002" not in ids and "D-004" in ids


# --- brief ---------------------------------------------------------------------

def test_brief_excludes_superseded_and_fits_budget(capsys):
    """AT-004 / SC-5."""
    code, out = run(capsys, "brief", "DEMO", "--phase", "build")
    own = [l.strip() for l in out.splitlines() if not l.lstrip().startswith("↔")]
    assert code == 0
    assert not any(l.startswith("D-002") for l in own)
    assert any(l.startswith("D-004") for l in own)
    assert len(out.splitlines()) <= 15


def test_brief_shows_delegated_questions_to_entering_phase(capsys):
    _, out = run(capsys, "brief", "DEMO", "--phase", "design")
    assert "🟡 Q-002" in out
    _, out_build = run(capsys, "brief", "DEMO", "--phase", "build")
    assert "Q-002" not in out_build


def test_brief_lists_pending_assumptions_only(capsys):
    _, out = run(capsys, "brief", "DEMO", "--phase", "build")
    assert "A-001" in out and "A-002" not in out


def test_brief_warns_about_phases_without_entries(capsys):
    _, out = run(capsys, "brief", "LEGACY", "--phase", "ship")
    assert "⚠ sem registro nas fases: define, design" in out
    _, full = run(capsys, "brief", "DEMO", "--phase", "ship")
    assert "⚠" not in full


def test_brief_includes_other_features_sharing_domain(capsys):
    """AT-007: cross-feature memory with a valid pointer."""
    _, out = run(capsys, "brief", "DEMO", "--phase", "define")
    assert "↔ OLDFEAT D-" in out
    assert "↔ OLDFEAT L-" in out


def test_brief_for_unknown_feature_uses_extra_domains(capsys):
    _, out = run(capsys, "brief", "NEW", "--phase", "define", "--domains", "genai")
    assert "↔ OLDFEAT" in out
    _, empty = run(capsys, "brief", "NEW", "--phase", "define")
    assert "sem memória registrada para NEW" in empty


def test_brief_open_questions_come_first(capsys):
    _, out = run(capsys, "brief", "BLOCKED", "--phase", "design")
    assert out.splitlines()[1].startswith("  🔴 Q-003")


def test_brief_caps_long_history_with_footer(tree, capsys):
    """AT-012: 40 live decisions → ≤ 15 lines and an omission footer."""
    write_blackboard(tree, "BIG", 40)
    _, out = run(capsys, "brief", "BIG", "--phase", "build", root=tree)
    lines = out.splitlines()
    assert len(lines) <= 15
    assert "omitidas" in lines[-1] and "34 omitidas" in lines[-1]


@pytest.mark.parametrize("budget", [3, 5, 15])
def test_brief_respects_custom_budget(tree, capsys, budget):
    write_blackboard(tree, "BIG", 40)
    _, out = run(capsys, "brief", "BIG", "--phase", "build", "--max", str(budget), root=tree)
    assert len(out.splitlines()) <= budget


def test_real_archive_pointer_exists():
    """AT-007 on real data: every cross-feature pointer resolves to an existing file and heading."""
    mem = mi.collect(REAL)
    lines = mi.brief(mem, "NEW", "define", extra_domains={"genai"})
    cross = [l for l in lines if "↔ " in l and "→ " in l]
    assert cross
    for line in cross:
        target = line.rsplit("→ ", 1)[1]
        path, anchor = target.split("#", 1)
        text = (REAL / path).read_text(encoding="utf-8")
        assert any(mi.slug(h.lstrip("#").strip()) == anchor for h in text.splitlines() if h.startswith("#")), target


def test_blackboard_pointers_become_root_relative(tree):
    """'DESIGN_X.md#a' next to the blackboard reads as 'features/DESIGN_X.md#a', like archive/ entries."""
    (tree / "features" / "DESIGN_PTR.md").write_text("# D\n\n### Decisão 1: A\n", encoding="utf-8")
    write_raw_blackboard(tree, "PTR", (
        "## Log de Decisões\n\n| # | Fase | Decisão | Onde Ler |\n|---|---|---|---|\n"
        "| D-001 | design | A | DESIGN_PTR.md#decisão-1-a |\n"
        "| D-002 | design | B | plugin-extras/scripts/x.py |\n"
        "| D-003 | design | C | MISSING.md#x |\n"))
    where = {e.id: e.where for e in mi.collect(tree).entries if e.feature == "PTR"}
    assert where == {"D-001": "features/DESIGN_PTR.md#decisão-1-a",
                     "D-002": "plugin-extras/scripts/x.py", "D-003": "MISSING.md#x"}


# --- gate ----------------------------------------------------------------------

def test_gate_blocks_on_open_question(capsys):
    """AT-005."""
    code, out = run(capsys, "gate", "BLOCKED", "--to", "design")
    assert code == 1
    assert "Q-003" in out and "Q-001" not in out


def test_gate_passes_with_delegated_question(capsys):
    code, out = run(capsys, "gate", "DEMO", "--to", "build")
    assert code == 0 and "nenhuma pergunta" in out


def test_gate_missing_blackboard_never_blocks(capsys):
    code, _ = run(capsys, "gate", "NOPE", "--to", "design")
    assert code == 0


def test_gate_rejects_ungated_transition():
    """AT-006: Brainstorm→Define is not gated."""
    with pytest.raises(SystemExit) as exc:
        mi.main(["--root", str(FIX), "gate", "DEMO", "--to", "define"])
    assert exc.value.code == 2


# --- tail ----------------------------------------------------------------------

def test_tail_uses_active_feature_and_limits(capsys):
    """AT-008."""
    code, out = run(capsys, "tail", "--n", "5")
    lines = out.splitlines()
    assert code == 0
    assert lines[0].startswith("=== Feature ativa: DEMO")
    assert len(lines) == 6
    assert "M-001" in lines[1]


def test_tail_newest_first(tree, capsys):
    write_blackboard(tree, "BIG", 8)
    _, out = run(capsys, "tail", "BIG", "--n", "5", root=tree)
    assert "D-008" in out.splitlines()[1]


def test_tail_without_active_prints_nothing(tree, capsys):
    (tree / ".active").unlink()
    code, out = run(capsys, "tail", root=tree)
    assert code == 0 and out == ""


# --- build / index -------------------------------------------------------------

def test_build_is_deterministic_and_recreatable(tree, capsys):
    """AT-009 / SC-3."""
    run(capsys, "build", root=tree)
    first = (tree / "MEMORY_INDEX.md").read_bytes()
    (tree / "MEMORY_INDEX.md").unlink()
    run(capsys, "build", root=tree)
    assert (tree / "MEMORY_INDEX.md").read_bytes() == first


def test_index_marks_superseded_and_escapes_pipes(tree, capsys):
    run(capsys, "build", root=tree)
    index = (tree / "MEMORY_INDEX.md").read_text(encoding="utf-8")
    assert "| DEMO | design | D | D-002 | Saída em JSON | substituída |" in index
    assert "| BLOCKED | define | Q | Q-003 |" in index and "🔴" in index


def test_build_verbose_reports_counts(tree, capsys):
    mi.main(["--root", str(tree), "build", "--verbose"])
    err = capsys.readouterr().err
    assert "entries=" in err and "skipped=" in err


def test_real_archive_counts():
    """SC-4: 10 archived DESIGN decisions (6 + 4) and lessons from both SHIPPED."""
    mem = mi.collect(REAL)
    archived = [e for e in mem.entries if e.feature in {"KB_EVOLUTION", "FRONTEND_ECOSYSTEM"}]
    decisions = [e for e in archived if e.kind == "D"]
    assert sum(e.feature == "KB_EVOLUTION" for e in decisions) == 6
    assert sum(e.feature == "FRONTEND_ECOSYSTEM" for e in decisions) == 4
    assert {e.feature for e in archived if e.kind == "L"} == {"KB_EVOLUTION", "FRONTEND_ECOSYSTEM"}


# --- off-template blackboards (found by the E2E run, Q-009) ---------------------

def write_raw_blackboard(root: Path, feature: str, body: str) -> None:
    (root / "features" / f"BLACKBOARD_{feature}.md").write_text(f"# BLACKBOARD\n\n{body}", encoding="utf-8")


ID_HEADER = (
    "## Log de Decisões\n\n"
    "| ID | Fase | Decisão | Justificativa | Substitui | Onde Ler |\n"
    "|----|------|---------|---------------|-----------|----------|\n"
    "| D-001 | brainstorm | Dedup em pandas | não mudar a query | — | BRAINSTORM_X.md#abordagem |\n"
    "| D-002 | design | `deduplicate()` auxiliar | testável | — | DESIGN_X.md#decisão-1 |\n\n"
    "## Perguntas Abertas e Bloqueadores\n\n"
    "| ID | Fase | Pergunta | Status | Resolução |\n"
    "|----|------|----------|--------|-----------|\n"
    "| Q-001 | define | Empate de updated_at? | 🔴 Aberto | — |\n"
)


def test_id_header_is_read_like_hash(tree):
    """Agents write `| ID |` instead of `| # |`; those rows must not vanish."""
    write_raw_blackboard(tree, "IDHDR", ID_HEADER)
    mem = mi.collect(tree)
    got = {(e.kind, e.id, e.phase) for e in mem.entries if e.feature == "IDHDR"}
    assert got == {("D", "D-001", "brainstorm"), ("D", "D-002", "design"), ("Q", "Q-001", "define")}
    assert "IDHDR" not in mem.unreadable


def test_id_header_open_question_still_blocks_gate(tree, capsys):
    write_raw_blackboard(tree, "IDHDR", ID_HEADER)
    code, out = run(capsys, "gate", "IDHDR", "--to", "design", root=tree)
    assert code == 1 and "Q-001" in out


OFF_TEMPLATE = (
    "## Decisões\n\n"
    "| ID | Fase | O que | Por quê |\n"
    "|----|------|-------|---------|\n"
    "| D-001 | design | Parquet | Athena lê |\n\n"
    "## Perguntas Abertas e Bloqueadores\n\n"
    "| ID | Fase | Dúvida | Status |\n"
    "|----|------|--------|--------|\n"
    "| Q-001 | define | Quem consome? | 🔴 Aberto |\n"
)


def test_unreadable_rows_are_reported_not_dropped(tree):
    write_raw_blackboard(tree, "OFFTPL", OFF_TEMPLATE)
    mem = mi.collect(tree)
    assert mem.unreadable["OFFTPL"] == ["D-001", "Q-001"]


def test_gate_refuses_to_vouch_for_unreadable_blackboard(tree, capsys):
    """A 🔴 hidden in an unreadable row must not let the transition pass."""
    write_raw_blackboard(tree, "OFFTPL", OFF_TEMPLATE)
    code, out = run(capsys, "gate", "OFFTPL", "--to", "design", root=tree)
    assert code == 2
    assert "ilegíve" in out and "BLACKBOARD_TEMPLATE.md" in out


def test_build_writes_index_but_exits_2_on_unreadable(tree, capsys):
    write_raw_blackboard(tree, "OFFTPL", OFF_TEMPLATE)
    code = mi.main(["--root", str(tree), "build"])
    err = capsys.readouterr().err
    assert code == 2
    assert (tree / "MEMORY_INDEX.md").is_file()
    assert "OFFTPL" in err and "D-001" in err


def test_brief_and_tail_surface_the_warning(tree, capsys):
    write_raw_blackboard(tree, "OFFTPL", OFF_TEMPLATE)
    _, out = run(capsys, "brief", "OFFTPL", "--phase", "design", root=tree)
    assert out.splitlines()[1].startswith("  ⚠ BLACKBOARD_OFFTPL.md: 2 linha(s)")
    _, out = run(capsys, "tail", "OFFTPL", root=tree)
    assert "ilegíve" in out


def test_template_placeholders_are_not_reported_as_unreadable():
    mem = mi.collect(FIX)
    assert mem.unreadable == {}


def test_real_tree_is_fast(tmp_path):
    """SC-7: under 2 s on the real repository."""
    start = time.perf_counter()
    mem = mi.collect(REAL)
    mi.index_markdown(mem)
    assert time.perf_counter() - start < 2.0


# --- constraints ---------------------------------------------------------------

def test_script_imports_stdlib_only():
    """SC-8: zero runtime dependencies."""
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module.split(".")[0])
    assert modules <= set(sys.stdlib_module_names) | {"__future__"}


def test_status_dashboard_reads_legacy_and_new_blackboards(tree, monkeypatch):
    """AT-010 / SC-10: the dashboard keeps working on both formats."""
    dashboard = _load("status_dashboard", REPO / "plugin-extras" / "scripts" / "status-dashboard.py")
    workdir = tree.parent / "work"
    (workdir / ".claude" / "sdd" / "features").mkdir(parents=True)
    for name in ("BLACKBOARD_LEGACY.md", "BLACKBOARD_DEMO.md"):
        shutil.copy(tree / "features" / name, workdir / ".claude" / "sdd" / "features" / name)
    monkeypatch.chdir(workdir)
    for feature in ("LEGACY", "DEMO"):
        monkeypatch.setattr(sys, "argv", ["status-dashboard.py", feature])
        assert dashboard.main() == 0
        html = (workdir / ".claude" / "sdd" / ".status" / "dashboard.html").read_text(encoding="utf-8")
        assert feature in html
