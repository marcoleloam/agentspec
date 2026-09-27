# Anti-Patterns

- **Mismatching the shape keys to the destination connection.** Writing
  `topic`/`value` (the Kafka shape) into a generator meant for a Postgres
  connection means the data never reaches the database — the shape keys must
  match the connection kind (`table`/`row` for Postgres, `topic`/`value` for
  Kafka, `directory`/`data` for filesystem), not just be "close enough."
- **Omitting `tablePolicy` on a Postgres connection.** It silently defaults to
  append, so every restart of a workshop/dev run accumulates duplicate data
  instead of resetting. Missing auth fields (`username`/`password`) is the
  same class of silent-failure omission.
- **Passing `lookup.path` as a plain string instead of an array.** e.g.
  `"path": "customer_id"` fails — the path must be an array starting with the
  shape key of the *referenced* generator (`["row", "customer_id"]`). This is
  called out as the most common mistake with `lookup`.
- **Calling `lookup` multiple times for the same reference inside one
  generator.** Capture it once into `vars` and reuse it via `var` instead of
  re-resolving the same lookup repeatedly.
- **Using Python Faker syntax (`fake.name()`).** ShadowTraffic embeds Java
  Datafaker, not Python Faker — only the `#{Namespace.method}` template syntax
  works.
- **Adding a space after the comma in Faker expression parameters**, e.g.
  `#{Date.birthday '18', '80'}` — this breaks parsing. Parameters must be
  comma-separated with no surrounding spaces.
- **Running generators with `lookup` FK dependencies without
  `schedule.stages`.** All generators start simultaneously by default, so a
  child generator's lookup can fire before the parent/seed data exists.
