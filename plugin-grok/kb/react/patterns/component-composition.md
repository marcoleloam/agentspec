# Component Composition

> **Purpose**: Compound components, render props, slots, and composition patterns
> **MCP Validated**: 2026-03-29

## When to Use

- Building reusable UI components (Accordion, Tabs, Dialog)
- Avoiding prop drilling in component hierarchies
- Creating flexible APIs that allow customization

## Implementation

```tsx
// Compound Component Pattern — Accordion example
import { createContext, useContext, useState, ReactNode } from "react";

interface AccordionContextType {
  openItem: string | null;
  toggle: (id: string) => void;
}

const AccordionContext = createContext<AccordionContextType | null>(null);

function useAccordion() {
  const ctx = useContext(AccordionContext);
  if (!ctx) throw new Error("useAccordion must be used within Accordion");
  return ctx;
}

function Accordion({ children }: { children: ReactNode }) {
  const [openItem, setOpenItem] = useState<string | null>(null);
  const toggle = (id: string) => setOpenItem(prev => prev === id ? null : id);
  return (
    <AccordionContext.Provider value={{ openItem, toggle }}>
      <div className="divide-y">{children}</div>
    </AccordionContext.Provider>
  );
}

function AccordionItem({ id, title, children }: {
  id: string;
  title: string;
  children: ReactNode;
}) {
  const { openItem, toggle } = useAccordion();
  const isOpen = openItem === id;
  return (
    <div>
      <button
        onClick={() => toggle(id)}
        aria-expanded={isOpen}
        className="w-full text-left p-4 font-medium"
      >
        {title}
      </button>
      {isOpen && <div className="p-4">{children}</div>}
    </div>
  );
}

// Attach sub-components
Accordion.Item = AccordionItem;
export { Accordion };
```

## Example Usage

```tsx
<Accordion>
  <Accordion.Item id="1" title="What is React?">
    A JavaScript library for building user interfaces.
  </Accordion.Item>
  <Accordion.Item id="2" title="What are hooks?">
    Functions that let you use state in function components.
  </Accordion.Item>
</Accordion>
```

## See Also

- [hooks-patterns.md](../concepts/hooks-patterns.md)
- [form-handling.md](../patterns/form-handling.md)
