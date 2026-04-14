# Expressions & Data Mapping

> **Purpose**: n8n expression syntax, data access, and transformation patterns
> **Confidence**: 0.90
> **MCP Validated**: 2026-04-14

## Overview

n8n expressions use `{{ }}` syntax to access data dynamically. Expressions are evaluated at runtime and can reference current items, other nodes, environment variables, and built-in functions.

## Data Access

### Current Item
```javascript
{{ $json.fieldName }}           // Direct field access
{{ $json.nested.field }}        // Nested access
{{ $json["field-with-dash"] }}  // Bracket notation
{{ $json.array[0] }}            // Array index
{{ $json.field ?? "default" }}  // Nullish coalescing
```

### Other Nodes
```javascript
{{ $node["Node Name"].json.field }}    // Specific node output
{{ $("Node Name").first().json.field }} // First item from node
{{ $("Node Name").all() }}             // All items from node
{{ $("Node Name").item.json.field }}   // Matched item (Merge)
```

### Input Data
```javascript
{{ $input.first().json }}     // First input item
{{ $input.all() }}            // All input items
{{ $input.item.json }}        // Current item in loop
{{ $items().length }}          // Item count
```

### Environment & Execution
```javascript
{{ $env.API_KEY }}             // Environment variable
{{ $execution.id }}            // Current execution ID
{{ $workflow.id }}             // Workflow ID
{{ $workflow.name }}           // Workflow name
{{ $now }}                     // Current timestamp (luxon DateTime)
{{ $today }}                   // Today at midnight
```

## DateTime (Luxon)

```javascript
{{ DateTime.now().toISO() }}                    // 2026-04-14T10:30:00.000Z
{{ DateTime.now().minus({ hours: 24 }).toISO() }} // Yesterday
{{ DateTime.fromISO($json.date).toFormat("yyyy-MM-dd") }}  // Format
{{ $now.startOf("day").toISO() }}               // Today midnight
{{ $json.date ? DateTime.fromISO($json.date) : DateTime.now() }} // Conditional
```

## Common Transformations

### String Operations
```javascript
{{ $json.name.toLowerCase() }}
{{ $json.text.split(",").map(s => s.trim()) }}
{{ `Hello ${$json.firstName}` }}
{{ $json.email.includes("@gmail") }}
```

### Number Operations
```javascript
{{ Math.round($json.price * 100) / 100 }}
{{ $json.items.reduce((sum, i) => sum + i.amount, 0) }}
{{ parseInt($json.count) || 0 }}
```

### Array/Object
```javascript
{{ $json.tags.join(", ") }}
{{ Object.keys($json).length }}
{{ JSON.stringify($json.data) }}
{{ $json.items.filter(i => i.active) }}
```

## Code Node Patterns

### Map Items
```javascript
return $input.all().map(item => ({
  json: {
    id: item.json.id,
    processed: true,
  }
}));
```

### Filter Items
```javascript
return $input.all().filter(item => item.json.status === "active");
```

### Aggregate
```javascript
const items = $input.all();
const total = items.reduce((sum, i) => sum + i.json.amount, 0);
return [{ json: { total, count: items.length } }];
```

## Common Mistakes

### Wrong: String concatenation in expression
```javascript
{{ $json.first + " " + $json.last }}
```

### Correct: Template literal
```javascript
{{ `${$json.first} ${$json.last}` }}
```

### Wrong: No null safety
```javascript
{{ $json.user.name }}  // Fails if user is null
```

### Correct: Optional chaining
```javascript
{{ $json.user?.name ?? "Unknown" }}
```

## Related

- [node-types](node-types.md) — Where expressions are used
- [workflow-fundamentals](workflow-fundamentals.md) — Data flow model
