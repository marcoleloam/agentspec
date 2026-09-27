# Conventions

## Generator Identity

Give every generator a stable `topic` name — even when its destination is
Postgres or the filesystem, not Kafka — so it can be referenced consistently
by `schedule.stages` and by other generators' `lookup` calls, independent of
the destination-specific shape fields (`table`/`row`, `directory`/`data`).

## Lookup Path Convention

A `lookup.path` array always starts with the shape key of the *referenced*
generator's own connection kind — `row` if it writes to Postgres, `value` if
Kafka, `data` if filesystem — never the shape key of the generator performing
the lookup.

## Staging Structure

- **Stage 0 (seed):** parent/independent entities (e.g. customers, products).
  Finite (`maxEvents` set), unthrottled (`throttle: 0`) so seeding completes
  quickly.
- **Stage 1 (stream):** FK-dependent entities (e.g. orders, reviews) that
  `lookup` into Stage 0's output. Usually continuous, throttled to simulate
  realistic pacing.
- Generators within the same stage run in parallel; a stage must fully
  complete before the next one starts.

## Faker/Datafaker Expression Syntax

Expressions use `#{Namespace.method}` templating (e.g. `#{Name.fullName}`,
`#{Commerce.productName}`), and can be embedded inside a larger literal
string. Parameters to a method are single-quoted and comma-separated with no
space between them.
