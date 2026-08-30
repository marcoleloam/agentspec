# Testing Components

> **Purpose**: Testing Library, user-event, MSW for API mocking
> **MCP Validated**: 2026-03-29

## When to Use

- Unit testing React components
- Testing user interactions (clicks, typing, form submission)
- Mocking API calls in tests

## Implementation

```tsx
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Counter } from "./Counter";

// 1. Render test — component displays correctly
test("renders counter with initial value", () => {
  render(<Counter initialValue={5} />);
  expect(screen.getByText("Count: 5")).toBeInTheDocument();
});

// 2. Interaction test — user clicks button
test("increments on click", async () => {
  const user = userEvent.setup();
  render(<Counter initialValue={0} />);

  await user.click(screen.getByRole("button", { name: "Increment" }));

  expect(screen.getByText("Count: 1")).toBeInTheDocument();
});

// 3. Async test — waits for API data
test("loads and displays user", async () => {
  render(<UserProfile userId="123" />);

  expect(screen.getByText("Loading...")).toBeInTheDocument();
  expect(await screen.findByText("John Doe")).toBeInTheDocument();
});

// 4. MSW mock — intercept API calls
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";

const server = setupServer(
  http.get("/api/users/:id", () =>
    HttpResponse.json({ name: "John Doe", email: "john@example.com" })
  )
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `user.setup()` | — | Create user-event instance (required for v14+) |
| `screen` | — | Query rendered DOM by role, text, label |
| `findBy*` | — | Async query — waits for element to appear |
| `getBy*` | — | Sync query — throws if not found |

## See Also

- [component-composition.md](../patterns/component-composition.md)
- [form-handling.md](../patterns/form-handling.md)
