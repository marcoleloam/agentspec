# DESIGN: Seleção de Agentes via JEV

> Design técnico para que `/define` e `/design` escolham a variante (single ou `-multiagent`) e os especialistas consultados a partir da especificação, via JEV (TypeSafe, pelo OpenRouter), com fallback determinístico e registro auditável.

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | JEV_AGENT_SELECTION |
| **Data** | 2026-09-23 |
| **Autor** | design-agent |
| **DEFINE** | [DEFINE_JEV_AGENT_SELECTION.md](./DEFINE_JEV_AGENT_SELECTION.md) |
| **Status** | Pronto para Build |

---

## Visão Geral da Arquitetura

```text
┌────────────────────────────────────────────────────────────────────────────┐
│  /define <BRAINSTORM>   /design <DEFINE>   /define-m ...   /design-m ...   │
│        (comando executado pelo Claude — agente da fase)                    │
└───────────────┬────────────────────────────────────────────────────────────┘
                │ 1. monta input JSON: phase, summary (≤4000 chars), kb_domains,
                │    variant_locked (null | "multiagent")
                ▼
┌────────────────────────────────────────────────────────────────────────────┐
│  scripts/jev_select.py  (Python stdlib, exit 0 sempre em modo select)      │
│                                                                            │
│  load_routing() ──► prefilter_candidates() ──► heuristic()  (sempre roda)  │
│        │                     │                      │                      │
│        │                     ▼                      │ baseline + fallback  │
│        │            build_request()                 │                      │
│        │                     │                      │                      │
│        │                     ▼                      │                      │
│        │   post_decisions()  ── thread daemon + timeout total ──┐          │
│        │        │                                               │          │
│        │        ▼                                               ▼          │
│        │   parse_answers() ─► normalize_confidence()     TransportError    │
│        │        │                                               │          │
│        │        ▼                                               │          │
│        └──► gate()  ◄───────────────────────────────────────────┘          │
│                 │   variant: conf ≥ 0.7 ? jev : heuristic                  │
│                 │   specialists: Noul ≥ 0.5 (top 4) ? jev : heuristic      │
│                 ▼                                                          │
│           SelectionResult (JSON em stdout)                                 │
└───────────────┬────────────────────────────────────────────────────────────┘
                │ 2. o comando lê o JSON
                ▼
   variant=single      → segue define-agent / design-agent
   variant=multiagent  → segue o processo de define-m / design-m com os especialistas escolhidos
   sempre              → grava a seção "Seleção de Agentes" no documento gerado

   Externo:  POST https://openrouter.ai/api/alpha/decisions   model typesafe/jev-1.13
   Offline:  jev_select.py --eval labels.json → acurácia de variante + F1 de especialistas (JEV × heurística)
```

---

## Componentes

| Componente | Propósito | Tecnologia |
|------------|-----------|------------|
| `jev_select.py` — núcleo | Pré-filtro, heurística, montagem da requisição, portão, resultado | Python 3.10+ stdlib, dataclasses frozen/slots |
| `jev_select.py` — transporte | `post_decisions()`: única função que faz HTTP; isolada para extração futura (cliente JEV compartilhado com `POST_BUILD_EVALS`) | `urllib.request`, `threading` |
| `jev_select.py` — CLI | Modo `select` (padrão) e modo `--eval` | `argparse` |
| Comandos de fase | Montam o input, chamam o script, seguem a variante e gravam a seção | Markdown (`.claude/commands/workflow/`) |
| Agentes `-multiagent` | Consomem os especialistas escolhidos em vez de calcular o overlap | Markdown (`.claude/agents/workflow/`) |
| Templates DEFINE/DESIGN | Seção "Seleção de Agentes" | Markdown (`.claude/sdd/templates/`) |
| Conjunto rotulado | 20 specs (resumo + domínios + rótulo) para `--eval` | JSON |
| Empacotamento | Copia o script para `plugin/scripts/` e para o bundle Grok | `build-plugin.sh`, `generate-grok-plugin.py` |

---

## Decisões Principais

### Decisão 1: a heurística é reimplementada em Python e roda sempre

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-09-23 |

**Contexto:** hoje a heurística ("≥ 3 domínios", "top 3-4 por overlap") é aplicada pelo LLM a partir do texto do prompt. Não é reprodutível e não serve como baseline de avaliação.

**Escolha:** `heuristic()` em Python roda em toda chamada, antes do JEV. O resultado serve de fallback e, no `--eval`, de baseline. Regra: `multiagent` se houver ≥ 3 domínios distintos; especialistas = top 4 por overlap de `kb_domains`, com desempate por nome.

**Justificativa:** o mesmo código produz o fallback e a métrica de comparação, então não existe "heurística do prompt" diferente da "heurística do eval".

**Alternativas Rejeitadas:**
1. Deixar o fallback para o LLM — rejeitada porque não é determinística nem comparável.
2. Heurística nova "melhorada" — rejeitada porque o DEFINE compara o JEV com a regra *atual*.

**Consequências:**
- O fallback reproduz os erros de hoje. Exemplo real, esta própria feature: top-4 = `ai-prompt-specialist`, `ai-prompt-specialist-gcp`, `genai-architect`, `kb-evolution-agent`, sem `python-developer` nem `test-generator`.
- Ganho: baseline mensurável.

---

### Decisão 2: uma requisição com fan-out (1 Choice + N Nouls), candidatos pré-filtrados, no máximo 12

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-09-23 |

**Contexto:** a doc da TypeSafe não define limite de perguntas por requisição e documenta queda de precisão com state grande e irrelevante. Mandar os 73 agentes num Choice pediria uma escolha de "um" quando precisamos de "vários".

**Escolha:**
- Candidatos = agentes de `routing.json` com `category != "workflow"` e overlap de `kb_domains` ≥ 1, ordenados por overlap desc e nome, limitados a `MAX_CANDIDATES = 12`.
- Uma pergunta `variant` (Choice `single` | `multiagent`) e uma `fit_<i>` (Noul) por candidato.
- A descrição do agente vai no `instructions` do Noul, não no state.

**Justificativa:** mesmo padrão do re-rank do cookbook *Skill suggestion*. O Noul dá probabilidade independente por agente, o que permite multi-seleção. A latência fica em uma ida e volta.

**Alternativas Rejeitadas:**
1. Choice sobre os 73 agentes — rejeitada porque devolve uma distribuição que soma 1, ruim para escolher vários, e o state fica inflado.
2. Duas chamadas (rank amplo + rerank) — adiada (YAGNI); o pré-filtro já reduz a lista.

**Consequências:**
- O recall de especialistas fica limitado pelo pré-filtro (premissa A-004). Um agente sem domínio em comum nunca é candidato.
- Chaves `fit_0..fit_11` evitam depender de regras de nome não documentadas; o mapa índice→agente fica no código.

---

### Decisão 3: `-m` explícito trava a variante e deixa de rebaixar para single

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-09-23 |

**Contexto:** hoje `define-m.md:52` e `design-m.md:53` voltam para a variante simples quando há menos de 3 domínios. O DEFINE (AT-009) exige que `-m` explícito respeite a variante.

**Escolha:** `/define-m` e `/design-m` passam `variant_locked: "multiagent"`. O script não pergunta a variante (`variant.source = "locked"`) e só decide os especialistas. O passo "Detect Domains → fall back" sai dos dois comandos.

**Justificativa:** a escolha explícita do usuário prevalece, e a autonomia do JEV vale para os comandos sem sufixo.

**Alternativas Rejeitadas:**
1. Manter o rebaixamento por contagem — rejeitada porque contradiz AT-009.
2. Deixar o JEV rebaixar `-m` — rejeitada na validação do brainstorm.

**Consequências:**
- Mudança de comportamento: `-m` com 1–2 domínios agora roda multiagent. Registrar no CHANGELOG.

---

### Decisão 4: timeout total garantido com thread daemon

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-09-23 |

**Contexto:** o `timeout` do `urllib` vale por operação de socket, não para a requisição inteira (DNS, connect e leitura somados podem passar de 4 s). O DEFINE exige no máximo 5 s no pior caso.

**Escolha:** `post_decisions()` roda numa `threading.Thread(daemon=True)`; o chamador faz `join(timeout_s)`. Se a thread continuar viva, vale `fallback_reason = "timeout"` e o processo sai sem esperar por ela (daemon).

**Justificativa:** limite de tempo total real sem dependências. `ThreadPoolExecutor` foi evitado porque faz join das threads no encerramento, o que estouraria o limite.

**Alternativas Rejeitadas:**
1. Só `urlopen(timeout=4)` — rejeitada porque não garante tempo total.
2. `signal.alarm` — rejeitada porque não funciona no Windows nem fora da thread principal.

**Consequências:**
- Uma requisição abandonada pode continuar em voo até o processo terminar; aceitável porque o processo é curto.

---

### Decisão 5: o resultado tem uma fonte por decisão; o `source` do topo segue a variante

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-09-23 |

**Contexto:** AT-008 pede variante vinda do JEV e especialistas vindos do fallback no mesmo resultado; o DEFINE define `source: "jev" | "fallback"`.

**Escolha:** `variant.source ∈ {jev, fallback, locked}`, `specialists.source ∈ {jev, fallback, none}`, cada um com seu `fallback_reason`. O `source` do topo espelha a decisão primária (a variante, ou os especialistas quando a variante está travada), e o `fallback_reason` do topo é o primeiro motivo encontrado.

**Justificativa:** mantém o contrato do DEFINE e deixa a auditoria precisa.

**Alternativas Rejeitadas:**
1. Um `source` único com valor `"partial"` — rejeitada porque muda o contrato do DEFINE.

**Consequências:**
- A seção do documento mostra as duas fontes separadamente.

---

### Decisão 6: rótulos em JSON; o conjunto completo fica fora do git

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-09-23 |

**Contexto:** o repositório não usa PyYAML (stdlib only), e 18 das 20 specs vêm de projetos de clientes em `~/projetos`. Os resumos podem conter informação confidencial.

**Escolha:**
- Formato JSON.
- `tests/fixtures/agent_selection/labels_sample.json` (versionado): 2 casos das features arquivadas deste repo (`FRONTEND_ECOSYSTEM`, `KB_EVOLUTION`).
- `.claude/sdd/evals/agent_selection_labels.json` (conjunto completo de 20): adicionado ao `.gitignore`.

**Justificativa:** não publicar conteúdo de cliente num repositório distribuído; os testes continuam determinísticos com a amostra.

**Alternativas Rejeitadas:**
1. YAML — rejeitada porque exigiria dependência nova.
2. Versionar os 20 — rejeitada por risco de vazamento de conteúdo de cliente.

**Consequências:**
- O resultado do `--eval` sobre os 20 fica registrado no BUILD_REPORT, não em arquivo versionado.

---

### Decisão 7: o script fica em `scripts/` e é copiado explicitamente no build

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-09-23 |

**Contexto:** `build-plugin.sh` só leva para `plugin/scripts/` o que está em `plugin-extras/scripts/`, e é por isso que o `judge.py` não é distribuído. Já o `generate-grok-plugin.py:414` copia o `judge.py` explicitamente.

**Escolha:** a fonte fica em `scripts/jev_select.py` (junto com os testes e o `judge.py`). `build-plugin.sh` ganha um `cp` explícito para `plugin/scripts/`, e `generate-grok-plugin.py` passa a copiar o script ao lado do `judge.py`. Um teste de drift compara `plugin/scripts/jev_select.py` com a fonte.

**Justificativa:** uma fonte única, e o mesmo padrão já usado no Grok.

**Alternativas Rejeitadas:**
1. Colocar a fonte em `plugin-extras/scripts/` — rejeitada porque separa o script dos testes e do padrão de `scripts/`.

**Consequências:**
- Os bundles Codex e DSH não levam scripts; nesses casos os comandos caem na regra "script indisponível" (ver Tratamento de Erros).
- Corrigir o empacotamento do `judge.py` continua fora do escopo (DEFINE).

---

### Decisão 8: o comando localiza `routing.json` pelo caminho do próprio script

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-09-23 |

**Contexto:** no repo o arquivo fica em `.claude/skills/agent-router/routing.json`; no plugin, em `${CLAUDE_PLUGIN_ROOT}/skills/agent-router/routing.json`.

**Escolha:** `resolve_routing_path()` tenta, nesta ordem: `--routing`, `<script>/../.claude/skills/agent-router/routing.json` (repo) e `<script>/../skills/agent-router/routing.json` (plugin). Sem arquivo, não há candidatos, e os especialistas ficam com `fallback_reason = "no_routing"`.

**Justificativa:** funciona nos dois layouts sem depender de variável de ambiente.

**Consequências:**
- Overrides locais de agentes (`.claude/agents/` do projeto do usuário) não entram no `routing.json` do plugin. Aceito no MVP; os candidatos são sempre os agentes do AgentSpec.

---

## Manifesto de Arquivos

| # | Arquivo | Ação | Propósito | Agente | Dependências |
|---|---------|------|-----------|--------|--------------|
| 1 | `scripts/jev_select.py` | Criar | Núcleo, transporte, portão, CLI `select` e `--eval` | @python-developer | Nenhuma |
| 2 | `tests/fixtures/jev/*.json` | Criar | Respostas gravadas: feliz multiagent, feliz single, sem `confidence`, baixa confiança, Noul inválido, todos abaixo do limiar | @test-generator | 1 |
| 3 | `tests/fixtures/agent_selection/labels_sample.json` | Criar | 2 casos rotulados das features arquivadas do repo | (direto) | 1 |
| 4 | `tests/test_jev_select.py` | Criar | Unitários (pré-filtro, heurística, portão, normalização, métricas) e CLI com transporte injetado; AT-003 a AT-008, AT-010, AT-011, AT-013 | @test-generator | 1, 2, 3 |
| 5 | `tests/test_plugin_scripts_sync.py` | Criar | AT-012: `plugin/scripts/jev_select.py` idêntico à fonte | @test-generator | 1, 7 |
| 6 | `.claude/sdd/templates/DEFINE_TEMPLATE.md`, `.claude/sdd/templates/DESIGN_TEMPLATE.md` | Modificar | Seção "Seleção de Agentes" | (direto) | Nenhuma |
| 7 | `build-plugin.sh` | Modificar | `cp scripts/jev_select.py plugin/scripts/` + `chmod +x` | @shell-script-specialist | 1 |
| 8 | `scripts/generate-grok-plugin.py` | Modificar | Copiar `jev_select.py` junto do `judge.py` | @python-developer | 1 |
| 9 | `.claude/commands/workflow/define.md`, `.claude/commands/workflow/design.md` | Modificar | Novo "Step 1b: Agent Selection"; seguir a variante decidida; gravar a seção | (direto) | 1, 6 |
| 10 | `.claude/commands/workflow/define-m.md`, `.claude/commands/workflow/design-m.md` | Modificar | Trocar "Detect Domains → fall back" por seleção com `variant_locked` | (direto) | 1, 6 |
| 11 | `.claude/agents/workflow/define-multiagent.md`, `.claude/agents/workflow/design-multiagent.md` | Modificar | Usar os especialistas da seleção; calcular overlap só se ausente | (direto) | 9, 10 |
| 12 | `.claude/agents/workflow/define-agent.md`, `.claude/agents/workflow/design-agent.md` | Modificar | Incluir a seção "Seleção de Agentes" no output | (direto) | 6 |
| 13 | `.claude/sdd/architecture/WORKFLOW_CONTRACTS.yaml` | Modificar | Bloco `agent_selection` (entrada, saída, portão, fallback) | (direto) | 1 |
| 14 | `docs/concepts/jev-agent-selection.md` | Criar | Como funciona, variáveis de ambiente, dados enviados ao OpenRouter, `JEV_DISABLE`, como rodar `--eval` | @code-documenter | 1, 9 |
| 15 | `.gitignore` | Modificar | `.claude/sdd/evals/agent_selection_labels.json` | (direto) | Nenhuma |
| 16 | `CHANGELOG.md` | Modificar | Entrada da feature + mudança de comportamento do `-m` (Decisão 3) | (direto) | 9, 10 |
| 17 | `.claude/sdd/evals/agent_selection_labels.json` | Criar (não versionado) | 20 specs rotuladas pelo maintainer (≥ 5 single, ≥ 5 multiagent) | (maintainer) | 1 |

**Total de Arquivos:** 17 entradas (≈ 26 arquivos físicos contando os fixtures e os pares). Os artefatos gerados (`plugin/`, `plugin-grok/`, `plugin-dsh/`, `.codex/`) são regenerados por `make build`, não editados à mão.

---

## Justificativa de Atribuição de Agentes

| Agente | Arquivos Atribuídos | Por Que Este Agente |
|--------|---------------------|---------------------|
| @python-developer | 1, 8 | Python stdlib com dataclasses e tipagem; mesmo estilo de `judge.py` e dos geradores |
| @test-generator | 2, 4, 5 | pytest com fixtures e transporte injetado, no padrão de `tests/test_judge.py` |
| @shell-script-specialist | 7 | `build-plugin.sh` com sed portável e permissões |
| @code-documenter | 14 | Doc conceitual do usuário |
| (direto) | 3, 6, 9–13, 15, 16 | Edições em prompts, templates e contratos do próprio framework; nenhum especialista acrescenta valor |
| (maintainer) | 17 | A rotulagem precisa de julgamento humano (decidido no DEFINE) |

**Descoberta de Agentes:**
- Escaneado: `.claude/skills/agent-router/routing.json` (73 agentes)
- Correspondido por: tipo de arquivo, propósito e domínios KB (`python`, `testing`)

---

## Seleção de Agentes

> Seção nova introduzida por esta feature, preenchida aqui à mão como dogfooding, porque `jev_select.py` ainda não existe.

| Campo | Valor |
|-------|-------|
| **Fonte da variante** | fallback |
| **Motivo** | `script_unavailable` (a feature ainda não foi construída) e `missing_key` (`OPENROUTER_API_KEY` não exportada nesta sessão) |
| **Variante pela heurística** | multiagent (4 domínios: `genai`, `prompt-engineering`, `python`, `testing`) |
| **Variante executada** | single (`/design` invocado explicitamente antes de a feature existir) |
| **Especialistas pela heurística** | `ai-prompt-specialist`, `ai-prompt-specialist-gcp`, `genai-architect`, `kb-evolution-agent` |
| **Observação** | A escolha da heurística é um exemplo real do problema: especialistas de prompt/GCP/KB para um script Python, sem `python-developer` nem `test-generator`. Incluir este caso no conjunto rotulado. |

---

## Padrões de Código

### Padrão 1: contratos de entrada e saída

```python
# scripts/jev_select.py — tipos principais (frozen + slots, como judge.py)
from __future__ import annotations

from dataclasses import dataclass, field

Variant = str  # "single" | "multiagent"


@dataclass(frozen=True, slots=True)
class Candidate:
    name: str
    category: str
    description: str
    kb_domains: tuple[str, ...]
    overlap: int


@dataclass(frozen=True, slots=True)
class SelectionInput:
    phase: str                          # "define" | "design"
    summary: str                        # truncated to SUMMARY_MAX_CHARS
    kb_domains: tuple[str, ...]
    variant_locked: Variant | None = None


@dataclass(frozen=True, slots=True)
class Decision:
    value: object                        # Variant, or tuple[str, ...] for specialists
    source: str                          # "jev" | "fallback" | "locked" | "none"
    fallback_reason: str | None = None
    confidence: float | None = None
    probabilities: dict[str, float] = field(default_factory=dict)
```

```json
// stdin de `jev_select.py` (montado pelo comando)
{"phase": "design", "summary": "<≤4000 chars>", "kb_domains": ["dbt", "spark"], "variant_locked": null}
```

```json
// stdout (sempre, exit 0)
{
  "version": 1,
  "phase": "design",
  "source": "jev",
  "fallback_reason": null,
  "model": "typesafe/jev-1.13",
  "latency_ms": 312,
  "variant": {"value": "multiagent", "source": "jev", "fallback_reason": null,
              "confidence": 0.91, "probabilities": {"single": 0.09, "multiagent": 0.91}},
  "specialists": {"value": ["dbt-specialist", "spark-engineer"], "source": "jev", "fallback_reason": null,
                  "probabilities": {"dbt-specialist": 0.82, "spark-engineer": 0.64, "sql-optimizer": 0.21}},
  "heuristic": {"variant": "single", "specialists": ["dbt-specialist", "sql-optimizer", "spark-engineer"]},
  "usage": {"input_tokens": 1830, "output_tokens": 40}
}
```

### Padrão 2: montagem da requisição (instruções fora do state)

```python
MODEL = os.environ.get("JEV_MODEL", "typesafe/jev-1.13")
SUMMARY_MAX_CHARS = 4000
MAX_CANDIDATES = 12


def build_request(inp: SelectionInput, candidates: list[Candidate]) -> dict[str, object]:
    """State carries only spec data; every instruction lives in a question."""
    questions: dict[str, object] = {}
    if inp.variant_locked is None:
        questions["variant"] = {
            "type": "choice",
            "instructions": "How many distinct specialist domains must be consulted to get this spec right?",
            "criteria": {
                "single": {"what": "One main domain; a single generalist designer can handle it",
                           "not_for": "Specs whose risks cross several technical domains"},
                "multiagent": {"what": "Several interacting domains whose risks a single designer would miss",
                               "not_for": "Specs that merely mention extra technologies in passing"},
            },
        }
    for i, cand in enumerate(candidates):
        questions[f"fit_{i}"] = {
            "type": "noul",
            "instructions": (
                f"Would the specialist '{cand.name}' — {cand.description} — materially change "
                f"the quality of this {inp.phase} phase for this spec?"
            ),
            "criteria": {
                "true": "The spec needs this specialist's domain expertise to avoid mistakes",
                "false": "The domain is absent, incidental, or already covered by another specialist",
            },
        }
    return {
        "model": MODEL,
        "state": {"phase": inp.phase, "spec_summary": inp.summary[:SUMMARY_MAX_CHARS],
                  "kb_domains": list(inp.kb_domains)},
        "questions": questions,
    }
```

### Padrão 3: transporte isolado com tempo total garantido

```python
JEV_URL = os.environ.get("JEV_URL", "https://openrouter.ai/api/alpha/decisions")


class TransportError(RuntimeError):
    def __init__(self, reason: str) -> None:   # "http_404", "network", "invalid_json", "timeout"
        super().__init__(reason)
        self.reason = reason


def post_decisions(payload: dict[str, object], api_key: str, timeout_s: float) -> dict[str, object]:
    """The only function that touches the network. Future shared JEV client lives here."""
    box: dict[str, object] = {}

    def _run() -> None:
        req = urllib.request.Request(
            JEV_URL, data=json.dumps(payload).encode(), method="POST",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json",
                     "HTTP-Referer": "https://github.com/marcoleloam/agentspec",
                     "X-Title": "AgentSpec JEV Agent Selection"},
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout_s) as resp:
                box["raw"] = resp.read().decode()
        except urllib.error.HTTPError as e:
            box["error"] = f"http_{e.code}"
        except (urllib.error.URLError, OSError):
            box["error"] = "network"

    worker = threading.Thread(target=_run, daemon=True)
    worker.start()
    worker.join(timeout_s)
    if worker.is_alive():
        raise TransportError("timeout")
    if "error" in box:
        raise TransportError(str(box["error"]))
    try:
        return json.loads(str(box["raw"]))
    except json.JSONDecodeError as e:
        raise TransportError("invalid_json") from e
```

### Padrão 4: portão e normalização

```python
MIN_CONFIDENCE = float(os.environ.get("JEV_MIN_CONFIDENCE", "0.7"))
FIT_THRESHOLD = float(os.environ.get("JEV_FIT_THRESHOLD", "0.5"))
MAX_SPECIALISTS = 4


def choice_confidence(answer: dict[str, object]) -> float:
    """Some gateways omit confidence; the winning probability stands in (jev-gateway rule)."""
    conf = answer.get("confidence")
    if isinstance(conf, (int, float)):
        return float(conf)
    probs = answer.get("probabilities") or {}
    return max((float(p) for p in probs.values()), default=0.0)


def gate_specialists(nouls: dict[str, float], fallback: tuple[str, ...]) -> Decision:
    fit = sorted(((n, p) for n, p in nouls.items() if p >= FIT_THRESHOLD), key=lambda t: (-t[1], t[0]))
    if not fit:
        return Decision(fallback, "fallback", "no_fit_above_threshold", probabilities=nouls)
    return Decision(tuple(n for n, _ in fit[:MAX_SPECIALISTS]), "jev", probabilities=nouls)
```

### Padrão 5: seção "Seleção de Agentes" nos templates

```markdown
## Seleção de Agentes

> Gerada por `scripts/jev_select.py` a partir desta especificação. Não editar à mão.

| Campo | Valor |
|-------|-------|
| **Variante** | {single \| multiagent} — fonte: {jev \| fallback \| locked} {(motivo)} |
| **Confiança da variante** | {0.00–1.00 ou —} |
| **Especialistas** | {@agente (p=0.82), @agente (p=0.64) \| nenhum} — fonte: {jev \| fallback \| none} {(motivo)} |
| **Heurística (referência)** | variante {…}; especialistas {…} |
| **Modelo / latência** | {typesafe/jev-1.13} / {N ms} |
```

### Padrão 6: passo nos comandos (define.md / design.md)

```markdown
### Step 1b: Agent Selection

1. From the input document, write a summary (≤ 4000 chars: problem, goals, key constraints)
   and list its KB domains (from "Domínios KB" / "Domínios KB Relevantes").
2. Run:

   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT:-.}/scripts/jev_select.py <<'JSON'
   {"phase": "design", "summary": "...", "kb_domains": ["..."], "variant_locked": null}
   JSON
   ```

3. If `variant.value == "multiagent"`, continue with the `/design-m` process using
   `specialists.value` as the specialists to consult (skip its own selection).
4. If the script is unavailable (file missing / python3 missing), apply the rule by hand
   (≥ 3 domains → multiagent; top 4 by kb_domains overlap) and record
   `fonte: fallback (script_unavailable)`.
5. Always write the "Seleção de Agentes" section into the generated document.
```

### Padrão 7: formato dos rótulos

```json
{
  "version": 1,
  "cases": [
    {
      "id": "FRONTEND_ECOSYSTEM-design",
      "source_path": ".claude/sdd/archive/FRONTEND_ECOSYSTEM/DEFINE_FRONTEND_ECOSYSTEM.md",
      "phase": "design",
      "summary": "...",
      "kb_domains": ["react", "nextjs", "tailwind-css", "accessibility", "design-systems", "frontend-patterns"],
      "expected_variant": "multiagent",
      "expected_specialists": ["react-developer", "css-specialist", "a11y-specialist", "frontend-architect"]
    }
  ]
}
```

---

## Fluxo de Dados

```text
1. Comando (/define ou /design) lê o documento de entrada
   │
   ▼
2. Agente escreve summary (≤ 4000 chars) + kb_domains; comandos -m adicionam variant_locked
   │
   ▼
3. jev_select.py: resolve routing.json → pré-filtra ≤ 12 candidatos → calcula a heurística
   │
   ▼
4. Checagens locais: JEV_DISABLE? chave ausente? → fallback imediato (sem HTTP)
   │
   ▼
5. POST alpha/decisions (thread daemon, join ≤ JEV_TIMEOUT_MS)
   │
   ▼
6. Parse: answers.variant (Choice) + answers.fit_i (Noul) → validação de tipo/intervalo
   │
   ▼
7. Portão: variante (conf ≥ 0.7) e especialistas (Noul ≥ 0.5, top 4); o que falhar → heurística
   │
   ▼
8. JSON em stdout (exit 0) → comando segue a variante → grava "Seleção de Agentes" no documento
```

---

## Pontos de Integração

| Sistema Externo | Tipo de Integração | Autenticação |
|----------------|-------------------|--------------|
| OpenRouter `POST /api/alpha/decisions` (modelo `typesafe/jev-1.13`) | REST JSON (mesmo corpo da API TypeSafe `v1/systemone`, conforme `jev-gateway/src/providers.json`) | `Authorization: Bearer $OPENROUTER_API_KEY` |
| API TypeSafe direta (opcional) | Mesmo contrato via `JEV_URL=https://api.typesafe.ai/v1/systemone` e `JEV_MODEL=jev-1.13.0` | Bearer (chave TypeSafe, colocada em `OPENROUTER_API_KEY` ou `JEV_API_KEY`) |
| `routing.json` (interno) | Leitura de arquivo | — |

---

## Estratégia de Testes

| Tipo de Teste | Escopo | Arquivos | Ferramentas | Meta de Cobertura |
|---------------|--------|----------|-------------|-------------------|
| Unitário | `prefilter_candidates`, `heuristic`, `build_request`, `choice_confidence`, `gate_*`, `parse_answers`, métricas de eval (acurácia, F1) | `tests/test_jev_select.py` | pytest | ≥ 90% das funções puras |
| Integração (sem rede) | `select()` com transporte injetado: caminho feliz multi/single, cada `fallback_reason`, variante travada, top 4 | `tests/test_jev_select.py` + `tests/fixtures/jev/` | pytest + `monkeypatch` em `post_decisions` | Todos os AT do script (003–008, 010, 011, 013) |
| Timeout real | `post_decisions` contra um servidor local que dorme 3 s, com `JEV_TIMEOUT_MS=500` | `tests/test_jev_select.py` | `http.server` em thread | AT-004 (≤ timeout + 1 s) |
| Drift de empacotamento | `plugin/scripts/jev_select.py == scripts/jev_select.py` | `tests/test_plugin_scripts_sync.py` | pytest | AT-012 |
| E2E manual | `/define` e `/design` em uma spec real, com e sem chave | — | Claude Code | AT-001, AT-002, AT-009 |
| Avaliação offline | `--eval` nos 20 rótulos (precisa de chave) | `.claude/sdd/evals/agent_selection_labels.json` | CLI | Critérios de sucesso do DEFINE |

---

## Tratamento de Erros

| Tipo de Erro | Estratégia de Tratamento | Retry? |
|-------------|-------------------------|--------|
| `JEV_DISABLE=1` | Sem HTTP; `fallback_reason=disabled` | Não |
| Chave ausente | Sem HTTP; `fallback_reason=missing_key` | Não |
| HTTP 4xx/5xx (401, 404, 422, 429, 529...) | `fallback_reason=http_<code>`; uma linha no stderr | Não (o custo de latência não compensa) |
| Rede (DNS, conexão) | `fallback_reason=network` | Não |
| Timeout total | `fallback_reason=timeout`; a thread daemon é abandonada | Não |
| Corpo não-JSON ou sem `answers` | `fallback_reason=invalid_response` | Não |
| `variant` ausente ou com `choice` fora de {single, multiagent} | Variante pela heurística, `invalid_response` | Não |
| `noul` fora de [0, 1] ou não numérico | O candidato é ignorado; se todos forem inválidos → `invalid_response` nos especialistas | Não |
| Confiança < limiar | Variante pela heurística, `low_confidence`; as probabilidades ficam registradas | Não |
| Nenhum Noul ≥ limiar (multiagent) | Especialistas pela heurística, `no_fit_above_threshold` | Não |
| Nenhum candidato ou `routing.json` ausente | Especialistas `none`/`fallback`, `no_candidates` ou `no_routing` | Não |
| stdin inválido | Resultado de fallback com `invalid_input`; exit 0 | Não |
| Script ou `python3` indisponível (bundles Codex/DSH) | O comando aplica a regra à mão e registra `script_unavailable` | Não |
| `--eval` com rótulos inválidos | Exit 2 com mensagem (modo offline não é caminho de fase) | Não |

---

## Configuração

| Chave de Config | Tipo | Padrão | Descrição |
|----------------|------|--------|-----------|
| `OPENROUTER_API_KEY` | string | — | Chave (a mesma do Judge Layer) |
| `JEV_API_KEY` | string | — | Opcional; se definida, tem precedência sobre `OPENROUTER_API_KEY` (uso com `JEV_URL` direto) |
| `JEV_URL` | string | `https://openrouter.ai/api/alpha/decisions` | Endpoint |
| `JEV_MODEL` | string | `typesafe/jev-1.13` | Modelo (versão fixada) |
| `JEV_MIN_CONFIDENCE` | float | `0.7` | Limiar da variante |
| `JEV_FIT_THRESHOLD` | float | `0.5` | Limiar do Noul de especialista (calibrar com `--eval`) |
| `JEV_TIMEOUT_MS` | int | `4000` | Tempo total máximo da chamada |
| `JEV_DISABLE` | bool (`1`) | vazio | Desliga o envio; sempre fallback |

---

## Considerações de Segurança

- **Dados enviados:** o resumo da spec (≤ 4000 caracteres) e os domínios de KB vão para OpenRouter e TypeSafe. A doc `jev-agent-selection.md` precisa dizer isso claramente. `JEV_DISABLE=1` desliga o envio.
- **Chave:** lida só do ambiente; nunca é impressa, nem em stderr nem no JSON de saída.
- **Conteúdo adversarial (jaggedness jev-1.13):** o state carrega só dados; todas as instruções ficam nas perguntas. Uma spec maliciosa pode no máximo enviesar a escolha, e a saída é restrita a nomes do `routing.json` (validação por conjunto fechado).
- **Rótulos de clientes:** o conjunto completo fica fora do git (Decisão 6).
- **Execução:** o script não executa nada vindo da resposta; só lê números e nomes validados.

---

## Observabilidade

| Aspecto | Implementação |
|---------|---------------|
| Logging | Uma linha no stderr por chamada: `[jev_select] source=… reason=… latency_ms=…`. Sem conteúdo da spec. |
| Métricas | `latency_ms` e `usage` no JSON; `--eval` imprime acurácia, F1 e contagem de fallbacks por motivo |
| Auditoria | A seção "Seleção de Agentes" em cada DEFINE/DESIGN é o registro permanente |
| Tracing | N/A |

---

## Fronteiras (lembrete para o Build)

| Frente | O que NÃO fazer aqui |
|--------|----------------------|
| `LLM_PHASE_ROUTING` | Não escolher modelo por fase; não ler nem escrever configuração de modelo |
| `POST_BUILD_EVALS` | Não criar um módulo JEV compartilhado; só manter `post_decisions()` isolada |
| `LIVING_MEMORY` | Não gravar decisões fora do documento SDD |
| `KB_CONTEXT7_REFRESH` | Não mudar `kb_domains` nem os KBs; o pré-filtro depende deles como estão |

---

## Histórico de Revisões

| Versão | Data | Autor | Mudanças |
|--------|------|-------|----------|
| 1.0 | 2026-09-23 | design-agent | Versão inicial a partir de DEFINE_JEV_AGENT_SELECTION.md |

---

## Próximo Passo

**Pronto para:** `/build .claude/sdd/features/DESIGN_JEV_AGENT_SELECTION.md`
