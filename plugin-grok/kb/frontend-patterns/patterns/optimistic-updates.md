# Optimistic Updates

> **Purpose**: useMutation with optimistic UI, rollback on error, cache invalidation
> **MCP Validated**: 2026-03-29

## When to Use

- Actions that should feel instant (toggle, delete, update)
- When server response is predictable
- Improving perceived performance

## Implementation

```tsx
"use client";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

interface Todo {
  id: string;
  title: string;
  completed: boolean;
}

function useTodoToggle() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (todo: Todo) =>
      fetch(`/api/todos/${todo.id}`, {
        method: "PATCH",
        body: JSON.stringify({ completed: !todo.completed }),
      }),

    // Optimistic update — update UI before server responds
    onMutate: async (todo) => {
      // Cancel outgoing queries to prevent overwrite
      await queryClient.cancelQueries({ queryKey: ["todos"] });

      // Snapshot previous value for rollback
      const previous = queryClient.getQueryData<Todo[]>(["todos"]);

      // Optimistically update cache
      queryClient.setQueryData<Todo[]>(["todos"], (old) =>
        old?.map((t) =>
          t.id === todo.id ? { ...t, completed: !t.completed } : t
        )
      );

      return { previous }; // context for onError
    },

    // Rollback on error
    onError: (err, todo, context) => {
      queryClient.setQueryData(["todos"], context?.previous);
      toast.error("Failed to update todo");
    },

    // Refetch after success or error to ensure consistency
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["todos"] });
    },
  });
}

// Usage in component
function TodoItem({ todo }: { todo: Todo }) {
  const toggle = useTodoToggle();

  return (
    <label className="flex items-center gap-2">
      <input
        type="checkbox"
        checked={todo.completed}
        onChange={() => toggle.mutate(todo)}
        disabled={toggle.isPending}
      />
      <span className={todo.completed ? "line-through" : ""}>
        {todo.title}
      </span>
    </label>
  );
}
```

## Configuration

| Callback | Purpose | Required |
|----------|---------|----------|
| `mutationFn` | Server call | Yes |
| `onMutate` | Optimistic update + snapshot | For optimistic |
| `onError` | Rollback with snapshot | For optimistic |
| `onSettled` | Refetch for consistency | Recommended |
| `onSuccess` | Post-success logic | Optional |

## See Also

- [api-integration.md](../patterns/api-integration.md)
- [data-fetching.md](../../react/patterns/data-fetching.md)
