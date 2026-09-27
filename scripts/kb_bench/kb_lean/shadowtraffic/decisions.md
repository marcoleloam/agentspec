# Decisions

## Choosing a Destination Connection

| Use case | Choose |
|----------|--------|
| Relational data that needs SQL queries (e.g. customers, products, orders) | Postgres generators |
| Unstructured text destined for RAG/embedding pipelines (e.g. reviews) | Filesystem generators writing JSONL |
| Foreign-key relationships between generators | `lookup` function, combined with `schedule.stages` |
| Realistic names/emails/products/text | Faker (Datafaker) expressions via the `string` function |

## tablePolicy: dropAndCreate vs append

Choose `"dropAndCreate"` for workshop/dev environments where a clean,
deterministic reset on every run is wanted. Choose the default, `"append"`,
for production, where data should accumulate over time rather than being
wiped.

## When to Use schedule.stages

Use staged execution whenever any generator's fields depend on `lookup` into
another generator's output — i.e. whenever there's a parent/child (FK)
relationship. Put the parent/seed generators in an earlier stage with a finite
`maxEvents` and no throttle (seed as fast as possible); put the FK-dependent,
usually continuous generators in a later stage with a throttle to pace
realistic output. The earlier stage must fully complete before the later one
starts — this is what guarantees referenced rows already exist when a lookup
runs.

## Weighted vs Uniform Choice Distributions

Prefer `weightedOneOf` over a uniform `oneOf` whenever the real-world
distribution isn't even — e.g. order status skewed toward "delivered" rather
than equally split across delivered/shipped/processing/cancelled, or review
ratings skewed positive. Uniform `oneOf` is appropriate only when there's no
reason to prefer one choice over another.
