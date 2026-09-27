# Decisions

## Choosing a Workload: Lakehouse vs Warehouse vs Eventhouse

Decision order: is the data streaming/real-time -> Eventhouse (KQL). Else, do
you need full T-SQL DML (UPDATE/DELETE/MERGE) -> Warehouse. Else, do you need
Spark/PySpark processing -> Lakehouse. Else, is the team SQL-first with
stored procedures -> Warehouse; otherwise Lakehouse is the default
recommendation.

Layer-by-layer guidance: **Bronze** is almost always Lakehouse (schema-on-read,
raw file support) — there's no real exception. **Silver** is Lakehouse for
Spark-first teams, or Warehouse only if the team is purely SQL and needs DML
for cleansing; Lakehouse is generally recommended for its transformation
flexibility. **Gold** goes to Warehouse for BI-heavy orgs needing RLS, column
security, and masking, or stays in Lakehouse if the team uses Spark SQL and
Direct Lake is sufficient — match it to what the downstream consumer needs.

Regulated industries (finance, health) should put gold in Warehouse for its
superior RLS/column-security/masking model. IoT/streaming plus batch
analytics should pair Lakehouse with Eventhouse.

## Hybrid Architecture: When to Combine All Three Workloads

Use a hybrid (Lakehouse + Warehouse + Eventhouse) architecture for enterprise
scenarios needing both batch analytics and real-time monitoring, mixed
structured/semi-structured/streaming data, and teams split between Spark and
BI/SQL skill sets. Do **not** use it for single-team batch-only projects (use
all-Lakehouse), pure streaming with no batch need (use Eventhouse only),
datasets under 1 GB (a single Lakehouse is sufficient), or teams with no KQL
experience and no real-time requirement — hybrid is over-engineering in these
cases.

## Capacity Sizing

Start with a small SKU (e.g. F16), monitor CU utilization via the Capacity
Metrics app, enable autoscale with a cost cap, and right-size after 2-4 weeks
of real usage data — rather than guessing a large SKU up front. Reserved
capacity (1-year or 3-year) is worth the discount only once usage is
predictable; pay-as-you-go plus pausing off-hours suits variable/dev usage.

## Workspace Organization: Domain-Based vs Layer-Based

Domain-based workspaces (one per business domain per environment) give team
autonomy and clear ownership — best for large orgs with multiple teams, at
the cost of more workspaces to manage. Layer-based workspaces (one per
medallion layer) are simpler and make data flow obvious — best for small orgs
or a single team, at the cost of cross-team contention. A hybrid
(domain + layer) balances governance for mid-size organizations but adds
naming-convention complexity.

## Direct Lake Fallback Mitigation

When Direct Lake falls back to DirectQuery, match the mitigation to the
trigger: data exceeding memory -> increase the capacity SKU or reduce model
scope; unsupported DAX patterns -> simplify the measure; very high column
cardinality -> reduce or exclude that column; stale frame -> increase refresh
frequency. Also: minimizing columns in the model, reducing cardinality, and
using a star schema in the source all reduce fallback risk by speeding up
frame loading.

## Deployment/Promotion Strategy

Workspace-per-stage (each environment is its own workspace bound to a
deployment pipeline stage) suits teams that want UI-driven promotion with
lower setup complexity. Branch-per-stage (each environment maps to a Git
branch) suits teams with strong Git workflows, at the cost of higher setup
complexity, but gains version control and a Git-based audit trail as a
byproduct.

Cross-stage rule of thumb: auto-deployment is appropriate dev -> test, but
test -> prod should require an approval gate with at least one non-requestor
approver — production promotion should never be fully automatic.

## Git Branching Strategy

Feature branches (one per developer/feature, merged via PR) give the highest
isolation for multiple developers working in parallel, at medium complexity.
Environment-branches-only suits small teams making sequential changes.
Trunk-based (dev branch only) suits a solo developer or prototyping. Gitflow
suits enterprises with formal release cycles, at the highest complexity.

For conflict resolution during Git sync: `PreferRemote` (Git wins) is the
safe default for shared branches; `PreferWorkspace` (workspace wins) is only
appropriate for personal feature branches.

## Choosing a Security Mechanism

| Need | Mechanism |
|------|-----------|
| Users should see only their own data rows | Row-Level Security (RLS) |
| Hide sensitive columns entirely | Column-Level Security (CLS) |
| Show partially obfuscated values, not full denial | Dynamic Data Masking (DDM) |
| Control workspace/item visibility | Workspace roles |
| Classify and track sensitive data | Sensitivity labels |
| Authenticate pipelines/CI-CD securely | Service principals |

These are layered, not alternatives to each other — combine RLS (rows) + CLS
(column visibility) + DDM (column obfuscation) + sensitivity labels for
defense in depth, and always test the combined effect rather than reasoning
about each layer in isolation.

Encryption (vs masking/CLS/RLS): choose encryption when the compliance
requirement is about data at rest (e.g. HIPAA), masking when analysts need to
work with PII without seeing raw values, CLS when a column (e.g. salary)
should be invisible to a role entirely, and RLS when different tenants/regions
must not see each other's rows.
