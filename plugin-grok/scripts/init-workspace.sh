#!/usr/bin/env bash
# =============================================================================
# init-workspace.sh — AgentSpec Workspace Initializer
#
# Creates SDD workspace directories and detects project stack at session
# start. Runs on SessionStart — idempotent, silent on success.
#
# Prerequisites:
#   - bash 3.2+ (uses ${BASH_SOURCE} and mapfile-free patterns)
#   - Standard POSIX utilities: mkdir, cat
#   - Called with the project working directory as CWD
#
# Usage:
#   ./init-workspace.sh          # normal run (SessionStart hook)
#   ./init-workspace.sh --help   # show this help
#
# Behavior:
#   - No-ops unless the CWD looks like an AgentSpec-aware project
#     (has .git/, CLAUDE.md, or .claude/)
#   - Creates .claude/sdd/{features,reports,archive}/ if missing
#   - Creates ${GROK_PLUGIN_ROOT}/agents/{workflow,custom}/ with a README explaining
#     the local-first override pattern (only on first run)
#   - Writes .claude/sdd/.detected-stack.md with inferred tech-stack hints
# =============================================================================

set -euo pipefail

# Parse --help early, before side effects
if [[ "${1:-}" == "--help" ]] || [[ "${1:-}" == "-h" ]]; then
    sed -n '3,22p' "$0"
    exit 0
fi

# ---------------------------------------------------------------------------
# Phase 1: Workspace Initialization (existing behavior)
# ---------------------------------------------------------------------------

init_workspace() {
    if [[ -d ".git" ]] || [[ -f "CLAUDE.md" ]] || [[ -d ".claude" ]]; then
        mkdir -p .claude/sdd/features || true
        mkdir -p .claude/sdd/reports  || true
        mkdir -p .claude/sdd/archive  || true
    fi
}

# ---------------------------------------------------------------------------
# Phase 1.5: Local Agent Override Scaffolding
# ---------------------------------------------------------------------------
# Creates ${GROK_PLUGIN_ROOT}/agents/{workflow,custom}/ so users have a discoverable
# place to drop local agents that override AgentSpec's plugin agents.
# Claude Code's native precedence is: user-level/project-level agents win
# over plugin agents when names collide. This function makes that pattern
# visible and ergonomic.
#
# Idempotent. Only writes the README on first run; user edits are preserved.

init_agent_overrides() {
    if [[ ! -d ".git" ]] && [[ ! -f "CLAUDE.md" ]] && [[ ! -d ".claude" ]]; then
        return 0
    fi

    mkdir -p ${GROK_PLUGIN_ROOT}/agents/workflow ${GROK_PLUGIN_ROOT}/agents/custom 2>/dev/null || true

    local readme="${GROK_PLUGIN_ROOT}/agents/README.md"
    if [[ -f "$readme" ]]; then
        return 0
    fi

    cat > "$readme" <<'EOF'
# Local Agents — Override AgentSpec

Agents in this directory **take precedence over AgentSpec plugin agents**
of the same name. Use this to customize phase agents to your project's
conventions without forking the plugin.

## Layout

| Folder | Purpose |
|---|---|
| `workflow/` | Override SDD phase agents (`brainstorm-agent`, `define-agent`, `design-agent`, `build-agent`, `ship-agent`, `iterate-agent`) |
| `custom/` | New project-specific agents that don't replace anything |

## Override an AgentSpec agent

1. Find the plugin agent at `${GROK_PLUGIN_ROOT}/agents/<category>/<name>.md`
2. Copy it to `${GROK_PLUGIN_ROOT}/agents/<name>.md` — keep the `name:` field identical
3. Edit freely; your version is now what runs

Example: override `build-agent` so `/build` runs your team's review checklist:

```bash
cp $CLAUDE_PLUGIN_ROOT/agents/workflow/build-agent.md \
   ${GROK_PLUGIN_ROOT}/agents/build-agent.md
# edit ${GROK_PLUGIN_ROOT}/agents/build-agent.md
```

## Add a custom agent

Drop a new `.md` file in `custom/` with valid frontmatter (`name`, `description`,
`tools`). It becomes available to `/build` and other phase commands automatically.

## Resolution Order

```text
${GROK_PLUGIN_ROOT}/agents/<name>.md   (your local override — wins)
        ↓ if absent
${GROK_PLUGIN_ROOT}/agents/<name>.md   (AgentSpec plugin)
```

This is enforced by Claude Code's native plugin loader. No config required.
EOF
}

# ---------------------------------------------------------------------------
# Phase 2: Project Stack Detection
# ---------------------------------------------------------------------------

detect_project_stack() {
    local -a detected_techs=()
    local -a kb_domains=()
    local -a agents=()
    local -a commands=()

    # --- dbt ---
    if [[ -f "dbt_project.yml" ]] || [[ -f "profiles.yml" ]]; then
        detected_techs+=("dbt")
        kb_domains+=("dbt/ -- model types, incremental strategies, testing")
        kb_domains+=("sql-patterns/ -- window functions, CTEs, optimization")
        agents+=("dbt-specialist -- dbt model development")
        agents+=("sql-optimizer -- query performance")
        agents+=("schema-designer -- dimensional modeling")
        commands+=("/schema -- design star schema")
        commands+=("/sql-review -- review SQL code")
        commands+=("/data-quality -- generate quality checks")

        if [[ -f "profiles.yml" ]]; then
            if grep -q "snowflake" profiles.yml 2>/dev/null; then
                detected_techs+=("Snowflake (profiles.yml target)")
                kb_domains+=("cloud-platforms/ -- Snowflake, Databricks, BigQuery")
            fi
            if grep -q "bigquery" profiles.yml 2>/dev/null; then
                detected_techs+=("BigQuery (profiles.yml target)")
                kb_domains+=("gcp/ -- Cloud Run, Pub/Sub, BigQuery")
                kb_domains+=("cloud-platforms/ -- Snowflake, Databricks, BigQuery")
            fi
            if grep -q "databricks" profiles.yml 2>/dev/null; then
                detected_techs+=("Databricks (profiles.yml target)")
                kb_domains+=("cloud-platforms/ -- Snowflake, Databricks, BigQuery")
                kb_domains+=("lakehouse/ -- Iceberg, Delta, catalogs")
            fi
        fi
    fi

    # --- Lakeflow / Databricks ---
    if [[ -f "databricks.yml" ]] || compgen -G "**/bronze.py" >/dev/null 2>&1 || compgen -G "**/silver.py" >/dev/null 2>&1; then
        detected_techs+=("Databricks Lakeflow")
        kb_domains+=("lakeflow/ -- DLT pipelines, expectations, streaming tables")
        kb_domains+=("medallion/ -- Bronze/Silver/Gold architecture")
        kb_domains+=("lakehouse/ -- Iceberg, Delta, catalogs")
        agents+=("lakeflow-specialist -- DLT pipeline development")
        agents+=("lakeflow-architect -- Lakeflow design patterns")
        agents+=("medallion-architect -- medallion layer design")
        commands+=("/pipeline -- DAG/pipeline scaffolding")
        commands+=("/lakehouse -- table format and catalog guidance")
    fi

    # --- AWS Lambda (SAM) ---
    if [[ -f "template.yaml" ]] && [[ -f "samconfig.toml" ]]; then
        detected_techs+=("AWS Lambda (SAM)")
        kb_domains+=("aws/ -- Lambda, S3, Glue, SAM")
        agents+=("aws-lambda-architect -- Lambda design")
        agents+=("lambda-builder -- Lambda implementation")
        agents+=("aws-deployer -- SAM deployment")
        commands+=("/pipeline -- DAG/pipeline scaffolding")
    fi

    # --- Airflow ---
    if [[ -d "dags" ]] || [[ -f "airflow.cfg" ]] || [[ -d "airflow" ]]; then
        detected_techs+=("Apache Airflow")
        kb_domains+=("airflow/ -- DAG design, operators, TaskFlow API")
        agents+=("airflow-specialist -- DAG development")
        agents+=("pipeline-architect -- orchestration design")
        commands+=("/pipeline -- DAG/pipeline scaffolding")
    fi

    # --- Supabase ---
    if [[ -f "docker-compose.yml" ]] && grep -q "supabase" docker-compose.yml 2>/dev/null; then
        detected_techs+=("Supabase")
        kb_domains+=("supabase/ -- Auth, Edge Functions, Realtime, RLS")
        agents+=("supabase-specialist -- Supabase development")
    fi

    # --- Terraform / IaC ---
    if compgen -G "*.tf" >/dev/null 2>&1; then
        detected_techs+=("Terraform")
        kb_domains+=("terraform/ -- IaC modules, state, workspaces")
        agents+=("data-platform-engineer -- infrastructure design")
        commands+=("/pipeline -- infrastructure pipeline scaffolding")
    fi

    # --- Spark ---
    local spark_source=""
    if [[ -f "pyproject.toml" ]] && grep -q "pyspark" pyproject.toml 2>/dev/null; then
        spark_source="pyproject.toml"
    elif [[ -f "setup.py" ]] && grep -q "pyspark" setup.py 2>/dev/null; then
        spark_source="setup.py"
    elif [[ -f "requirements.txt" ]] && grep -q "pyspark" requirements.txt 2>/dev/null; then
        spark_source="requirements.txt"
    fi
    if [[ -n "$spark_source" ]]; then
        detected_techs+=("PySpark (${spark_source})")
        kb_domains+=("spark/ -- DataFrames, performance, Delta integration")
        agents+=("spark-engineer -- Spark job development")
        agents+=("spark-specialist -- Spark architecture")
        agents+=("spark-performance-analyzer -- Spark tuning")
        commands+=("/pipeline -- pipeline scaffolding")
    fi

    # --- Streaming ---
    if [[ -d "streaming" ]] || compgen -G "**/kafka*.properties" >/dev/null 2>&1 || compgen -G "**/kafka*.yml" >/dev/null 2>&1 || compgen -G "**/kafka*.yaml" >/dev/null 2>&1; then
        detected_techs+=("Streaming / Kafka")
        kb_domains+=("streaming/ -- Flink, Kafka, Spark Streaming, CDC")
        agents+=("streaming-engineer -- stream processing")
        agents+=("spark-streaming-architect -- Spark Streaming design")
        commands+=("/pipeline -- streaming pipeline scaffolding")
    fi

    # --- Microsoft Fabric ---
    if [[ -d "Fabric" ]] || compgen -G "*.pbix" >/dev/null 2>&1; then
        detected_techs+=("Microsoft Fabric")
        kb_domains+=("microsoft-fabric/ -- Lakehouse, Warehouse, Pipelines")
        agents+=("fabric-architect -- Fabric architecture")
        agents+=("fabric-pipeline-developer -- Fabric pipelines")
        commands+=("/pipeline -- Fabric pipeline scaffolding")
    fi

    # --- Data Quality ---
    local dq_found=false
    if [[ -f "requirements.txt" ]]; then
        if grep -qE "great.expectations|soda" requirements.txt 2>/dev/null; then
            dq_found=true
        fi
    fi
    if [[ -f "pyproject.toml" ]]; then
        if grep -qE "great.expectations|soda" pyproject.toml 2>/dev/null; then
            dq_found=true
        fi
    fi
    if [[ "$dq_found" == "true" ]]; then
        detected_techs+=("Data Quality (Great Expectations / Soda)")
        kb_domains+=("data-quality/ -- expectations, validation, observability")
        agents+=("data-quality-analyst -- quality checks")
        agents+=("data-contracts-engineer -- data contracts")
        commands+=("/data-quality -- generate quality checks")
        commands+=("/data-contract -- contract authoring")
    fi

    # --- Always-useful additions based on Python projects ---
    if [[ -f "pyproject.toml" ]] || [[ -f "setup.py" ]] || [[ -f "requirements.txt" ]]; then
        if [[ -f "pyproject.toml" ]] && grep -qE "pydantic" pyproject.toml 2>/dev/null; then
            detected_techs+=("Pydantic")
            kb_domains+=("pydantic/ -- validation, LLM output schemas")
        fi
        if [[ -f "requirements.txt" ]] && grep -qE "pydantic" requirements.txt 2>/dev/null; then
            detected_techs+=("Pydantic")
            kb_domains+=("pydantic/ -- validation, LLM output schemas")
        fi
    fi

    # Return results via global arrays
    DETECTED_TECHS=("${detected_techs[@]+"${detected_techs[@]}"}")
    KB_DOMAINS=("${kb_domains[@]+"${kb_domains[@]}"}")
    AGENTS=("${agents[@]+"${agents[@]}"}")
    COMMANDS=("${commands[@]+"${commands[@]}"}")
}

# ---------------------------------------------------------------------------
# Phase 3: Generate Context Hint File
# ---------------------------------------------------------------------------

generate_context_hint() {
    local output_file=".claude/sdd/.detected-stack.md"

    detect_project_stack

    # If nothing detected, skip file generation
    if [[ ${#DETECTED_TECHS[@]} -eq 0 ]]; then
        # Remove stale file from a previous session if it exists
        rm -f "$output_file" 2>/dev/null || true
        return 0
    fi

    mkdir -p .claude/sdd

    # Deduplicate arrays (preserving order)
    local -a unique_kb=()
    local -A seen_kb=()
    for item in "${KB_DOMAINS[@]}"; do
        if [[ -z "${seen_kb[$item]+x}" ]]; then
            seen_kb[$item]=1
            unique_kb+=("$item")
        fi
    done

    local -a unique_agents=()
    local -A seen_agents=()
    for item in "${AGENTS[@]}"; do
        if [[ -z "${seen_agents[$item]+x}" ]]; then
            seen_agents[$item]=1
            unique_agents+=("$item")
        fi
    done

    local -a unique_cmds=()
    local -A seen_cmds=()
    for item in "${COMMANDS[@]}"; do
        local cmd_key="${item%% -- *}"
        if [[ -z "${seen_cmds[$cmd_key]+x}" ]]; then
            seen_cmds[$cmd_key]=1
            unique_cmds+=("$item")
        fi
    done

    # Write the file
    {
        echo "# Detected Project Stack"
        echo ""
        echo "> Auto-generated by AgentSpec on $(date +%Y-%m-%d). Do not edit manually."
        echo ""
        echo "## Technologies Found"
        for tech in "${DETECTED_TECHS[@]}"; do
            echo "- ${tech}"
        done
        echo ""
        echo "## Recommended KB Domains"
        for domain in "${unique_kb[@]}"; do
            echo "- \`${domain}\`"
        done
        echo ""
        echo "## Recommended Agents"
        for agent in "${unique_agents[@]}"; do
            echo "- \`${agent}\`"
        done
        echo ""
        echo "## Quick Commands"
        for cmd in "${unique_cmds[@]}"; do
            echo "- \`${cmd}\`"
        done
    } > "$output_file"
}

# ---------------------------------------------------------------------------
# Phase 4: Surface Memory Index (cross-session, cross-project, cross-PC)
# ---------------------------------------------------------------------------
# Injects a COMPACT INDEX of memory into the session context at SessionStart so
# AgentSpec "remembers" across machines and projects — without paying to inject
# the full memory every session. The model reads the full file on demand (pointer,
# not payload — same principle as the blackboard). Two tiers:
#   - Global : ${AGENTSPEC_MEMORY_DIR:-$HOME/.agentspec}/MEMORY.md  (all projects)
#   - Project: .claude/sdd/MEMORY.md                                 (this repo, via git)
#
# The index = each block's "## " heading (its dated summary), or, if the file has
# no headings, its top-level bullets. The model reads the file for full detail.
#
# Cross-PC sync: point AGENTSPEC_MEMORY_DIR at a synced folder (git repo,
# Dropbox, iCloud). Project memory syncs with the project's own git.
#
# Tuning env vars:
#   AGENTSPEC_MEMORY_SILENT=1      → disable index injection (read on demand only)
#   AGENTSPEC_MEMORY_MAX_LINES=N   → cap index entries per tier (default 30)

# Extract a compact index from a MEMORY.md file: prefer "## " headings; if none,
# fall back to top-level bullets. Echoes nothing when the file has no real content.
memory_index() {
    local f="$1"
    local cap="$2"
    local idx
    idx="$(grep -E '^## ' "$f" 2>/dev/null || true)"
    if [[ -z "${idx//[$'\n\t ']/}" ]]; then
        idx="$(grep -E '^(- |\* )' "$f" 2>/dev/null || true)"
    fi
    [[ -z "${idx//[$'\n\t ']/}" ]] && return 0
    printf '%s\n' "$idx" | head -n "$cap"
}

surface_memory() {
    local global_dir="${AGENTSPEC_MEMORY_DIR:-$HOME/.agentspec}"
    local global_file="${global_dir}/MEMORY.md"
    local project_file=".claude/sdd/MEMORY.md"
    local cap="${AGENTSPEC_MEMORY_MAX_LINES:-30}"

    # Seed the global memory store on first run (idempotent)
    if [[ ! -f "$global_file" ]]; then
        mkdir -p "$global_dir" 2>/dev/null || true
        if [[ -d "$global_dir" ]]; then
            cat > "$global_file" <<'EOF'
# AgentSpec Global Memory

> Cross-project, cross-PC memory. Curated high-signal insights that apply to ANY
> project: preferences, conventions, reusable gotchas, architecture lessons.
> Updated via `/memory --global`. Keep it small and high-signal.
>
> Sync across machines by pointing AGENTSPEC_MEMORY_DIR at a synced folder
> (git repo, Dropbox, iCloud Drive).
>
> Use "## {date} — {summary}" blocks so the SessionStart index stays compact.

<!-- Add durable insights below as ## blocks (preferred) or bullets. -->
EOF
        fi
    fi

    [[ "${AGENTSPEC_MEMORY_SILENT:-0}" == "1" ]] && return 0

    local project_idx="" global_idx=""
    [[ -f "$project_file" ]] && project_idx="$(memory_index "$project_file" "$cap")"
    [[ -f "$global_file" ]] && global_idx="$(memory_index "$global_file" "$cap")"

    [[ -z "$project_idx" && -z "$global_idx" ]] && return 0

    echo "=== AgentSpec Memory index — read the file for full detail when relevant ==="
    echo ""
    if [[ -n "$project_idx" ]]; then
        echo "## Project memory — read .claude/sdd/MEMORY.md for detail on any entry below"
        printf '%s\n' "$project_idx"
        echo ""
    fi
    if [[ -n "$global_idx" ]]; then
        echo "## Global memory — read ${global_file} for detail on any entry below"
        printf '%s\n' "$global_idx"
        echo ""
    fi
    echo "=== end memory index (update with /memory or /memory --global) ==="
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

init_workspace
init_agent_overrides
generate_context_hint
surface_memory
