# Table Accessibility

> **Purpose**: Semantic table markup with headers, scope, caption, sortable columns
> **MCP Validated**: 2026-03-29

## When to Use

- Data tables with rows and columns
- Sortable and filterable tables
- Responsive tables on mobile

## Implementation

```tsx
function DataTable({ data, sortColumn, sortDirection, onSort }: TableProps) {
  return (
    <div className="overflow-x-auto" role="region" aria-label="Products table" tabIndex={0}>
      <table>
        <caption className="text-left text-sm text-muted-foreground mb-2">
          Product inventory — {data.length} items
        </caption>
        <thead>
          <tr>
            <th scope="col">
              <button
                onClick={() => onSort("name")}
                aria-sort={sortColumn === "name" ? sortDirection : "none"}
              >
                Name {sortColumn === "name" && (sortDirection === "ascending" ? "▲" : "▼")}
              </button>
            </th>
            <th scope="col">Category</th>
            <th scope="col" className="text-right">
              <button
                onClick={() => onSort("price")}
                aria-sort={sortColumn === "price" ? sortDirection : "none"}
              >
                Price {sortColumn === "price" && (sortDirection === "ascending" ? "▲" : "▼")}
              </button>
            </th>
            <th scope="col">Status</th>
          </tr>
        </thead>
        <tbody>
          {data.map((item) => (
            <tr key={item.id}>
              <td>{item.name}</td>
              <td>{item.category}</td>
              <td className="text-right">${item.price}</td>
              <td>
                <span className={cn(
                  "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs",
                  item.active ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-800"
                )}>
                  <span className={cn("h-1.5 w-1.5 rounded-full", item.active ? "bg-green-500" : "bg-gray-400")} />
                  {item.active ? "Active" : "Inactive"}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

## Configuration

| Element | Purpose |
|---------|---------|
| `<caption>` | Describes the table content |
| `<th scope="col">` | Column header |
| `<th scope="row">` | Row header |
| `aria-sort` | Current sort direction |
| `role="region"` + `tabIndex={0}` | Scrollable container is focusable |

## See Also

- [wcag-guidelines.md](../concepts/wcag-guidelines.md)
- [form-accessibility.md](../patterns/form-accessibility.md)
