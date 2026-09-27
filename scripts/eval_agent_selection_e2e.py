"""Exercise AgentSpec phase skills in isolated temporary Codex projects."""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import jev_select as selector

ROOT = Path(__file__).resolve().parent.parent
CODEX_SKILLS = ROOT / ".codex" / "skills"

SINGLE_BRAINSTORM = """# BRAINSTORM: Eval Single

## Problema
O painel interno atual não mostra três estados de interface importantes.

## Usuários e resultado esperado
Uma equipe interna quer três telas responsivas para navegar dados simulados. O resultado é um protótipo visual navegável.

## Escopo fechado
Criar apenas componentes React e estilos CSS para as telas Visão, Detalhe e Configuração, com dados mockados em arquivos locais. Não criar API, banco, autenticação, infraestrutura nem integração externa. As outras tecnologias são só contexto.

## Critérios de sucesso
As três telas renderizam em desktop e mobile, a navegação funciona e os estados vazio/erro aparecem. O teste pode usar dados mockados; nenhuma persistência é necessária.

## Decisões
Usar React e CSS existentes. Evitar backend porque o protótipo só valida UX.

## Domínios KB
react, tailwind-css, accessibility
"""

MULTI_DEFINE = """# DEFINE: Eval Multi

## Metadados
| Atributo | Valor |
|----------|-------|
| **Feature** | EVAL_MULTI |
| **Status** | Pronto para Design |
| **Clarity Score** | 15/15 |

## Problema e usuários
Operadores precisam registrar ordens de serviço e acompanhá-las numa interface web; hoje usam planilhas.

## Objetivos
Implementar de verdade duas áreas técnicas: (1) frontend React com formulário, listagem e estados; (2) backend Python com API HTTP, validação e tabelas PostgreSQL persistentes. O frontend deve consumir essa API. Não usar mocks para o backend.

## Critérios de sucesso
Uma ordem criada pela UI é persistida via API e reaparece após recarregar. Campos inválidos retornam erro estruturado. Testes cobrem UI, API e persistência.

## Testes de Aceitação
| ID | Cenário | Dado | Quando | Então |
|----|---------|------|--------|-------|
| AT-001 | Criar ordem | Dados válidos | Usuário salva na UI | API persiste no PostgreSQL e a listagem mostra a ordem |
| AT-002 | Rejeitar ordem inválida | Campo obrigatório ausente | Usuário salva | API devolve 400 e UI mostra erro |

## Fora do Escopo
Autenticação, implantação em nuvem e análise por IA.

## Domínios KB
react, python, sql-patterns
"""

LOCKED_DEFINE = """# DEFINE: Eval Locked

## Metadados
| Atributo | Valor |
|----------|-------|
| **Feature** | EVAL_LOCKED |
| **Status** | Pronto para Design |
| **Clarity Score** | 15/15 |

## Problema e objetivo
Criar apenas um protótipo React com dados mockados. Não implementar API, banco, IA nem infraestrutura. O usuário escolheu explicitamente `/design-m` para revisão com especialistas, mesmo que a rubrica favoreça single.

## Critérios de sucesso
Duas telas responsivas e uma navegação local funcional.

## Testes de Aceitação
| ID | Cenário | Dado | Quando | Então |
|----|---------|------|--------|-------|
| AT-001 | Navegação | Dados locais | Usuário abre a segunda tela | A segunda tela aparece sem chamadas HTTP |

## Domínios KB
react, tailwind-css, accessibility
"""

AUTO_SINGLE_DEFINE = LOCKED_DEFINE.replace("EVAL_LOCKED", "EVAL_AUTO_SINGLE").replace(
    " O usuário escolheu explicitamente `/design-m` para revisão com especialistas, mesmo que a rubrica favoreça single.",
    "",
)

SCENARIOS = {
    "define_single": ("BRAINSTORM_EVAL_SINGLE.md", SINGLE_BRAINSTORM, "source-command-workflow-define", "DEFINE_EVAL_SINGLE.md", "single"),
    "design_multi": ("DEFINE_EVAL_MULTI.md", MULTI_DEFINE, "source-command-workflow-design", "DESIGN_EVAL_MULTI.md", "multiagent"),
    "design_locked": ("DEFINE_EVAL_LOCKED.md", LOCKED_DEFINE, "source-command-workflow-design-m", "DESIGN_EVAL_LOCKED.md", "multiagent"),
    "design_second_opinion": ("DEFINE_EVAL_AUTO_SINGLE.md", AUTO_SINGLE_DEFINE, "source-command-workflow-design", "DESIGN_EVAL_AUTO_SINGLE.md", "single"),
}


def check_document(path: Path, scenario: str, expected: str) -> dict:
    if not path.is_file():
        raise AssertionError(f"expected artifact missing: {path}")
    text = path.read_text(encoding="utf-8")
    if "## Seleção de Agentes" not in text:
        raise AssertionError("Seleção de Agentes section missing")
    section = text.split("## Seleção de Agentes", 1)[1].split("\n## ", 1)[0]
    variant_row = next((line for line in section.splitlines() if "Variante" in line), "")
    if expected.lower() not in variant_row.lower():
        raise AssertionError(f"expected {expected} in variant row; got {variant_row!r}")
    if scenario == "design_locked":
        if "locked" not in section.lower():
            raise AssertionError("explicit multiagent variant was not marked locked")
        if "segunda opinião" not in section.lower() or not re.search(r"disabled|desativad", section, re.IGNORECASE):
            raise AssertionError("JEV second opinion was not recorded as disabled fallback")
    elif "llm (rubrica)" not in section.lower():
        raise AssertionError("LLM rubric source missing")
    if scenario == "design_second_opinion" and ("segunda opinião" not in section.lower() or not re.search(r"disabled|desativad", section, re.IGNORECASE)):
        raise AssertionError("JEV second opinion was not recorded after the design snippet")
    if "justificativa" not in section.lower() or "especialist" not in section.lower():
        raise AssertionError("auditable justification or specialists row missing")
    known_names = {
        str(a["name"])
        for a in selector.load_routing(selector.resolve_routing_path())
        if str(a.get("category", "")) not in selector.WIDE_EXCLUDED_CATEGORIES
    }
    chosen_lines = "\n".join(
        line for line in section.splitlines()
        if line.lower().startswith(("| **especialistas**", "| **especialista adicional**"))
    )
    mentioned = sorted(name for name in known_names if re.search(rf"(?<![\w-]){re.escape(name)}(?![\w-])", chosen_lines))
    if len(mentioned) > selector.MAX_SPECIALISTS:
        raise AssertionError(f"more than four specialists mentioned: {mentioned}")
    if expected == "multiagent" and not mentioned:
        raise AssertionError("multiagent variant listed no valid specialists")
    return {"scenario": scenario, "artifact": path.name, "variant": expected, "specialists_mentioned": mentioned,
            "consultations_unavailable": "pareceres independentes" in section.lower() and "não há" in section.lower()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=SCENARIOS, required=True)
    args = parser.parse_args()
    if not (CODEX_SKILLS / "source-command-workflow-define" / "SKILL.md").is_file():
        parser.error("generated Codex skills missing")
    if shutil.which("codex") is None:
        parser.error("codex CLI missing")

    input_name, source, skill, output_name, expected = SCENARIOS[args.scenario]
    scratch = Path(tempfile.mkdtemp(prefix=f"agentspec-{args.scenario}-"))
    (scratch / input_name).write_text(source, encoding="utf-8")
    environment = os.environ.copy()
    environment["AGENTSPEC_SCRIPTS"] = str(ROOT / "scripts")
    if args.scenario in ("design_locked", "design_second_opinion"):
        environment["JEV_SECOND_OPINION"] = "1"
        environment["JEV_DISABLE"] = "1"
    else:
        environment.pop("JEV_SECOND_OPINION", None)

    command = ["codex", "exec", "--ephemeral", "--skip-git-repo-check", "-s", "workspace-write", "-C", str(scratch), "-o", str(scratch / "codex-final.txt"), "-"]
    prompt = (
        f"Use $agentspec:{skill} to process {input_name} fully. "
        "Produce the feature document and BLACKBOARD in .claude/sdd/features/. "
        "This is an isolated acceptance run with complete input. Apply the Agent Selection rubric, "
        "record the decision in Seleção de Agentes, and do not ask for clarification."
    )
    try:
        timeout = 540 if args.scenario == "define_single" else 780
        result = subprocess.run(command, input=prompt, cwd=scratch, env=environment, capture_output=True, text=True, timeout=timeout, check=False)
        (scratch / "codex-stdout.log").write_text(result.stdout, encoding="utf-8")
        (scratch / "codex-stderr.log").write_text(result.stderr, encoding="utf-8")
        if result.returncode:
            raise RuntimeError(f"codex exited {result.returncode}; stderr tail: {result.stderr[-1200:]}")
        artifact = scratch / ".claude" / "sdd" / "features" / output_name
        summary = check_document(artifact, args.scenario, expected)
        print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
        shutil.rmtree(scratch)
        return 0
    except (AssertionError, OSError, RuntimeError, subprocess.TimeoutExpired) as error:
        print(f"E2E failure ({args.scenario}); inspect {scratch}: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
