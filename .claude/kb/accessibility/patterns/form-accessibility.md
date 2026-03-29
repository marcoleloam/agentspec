# Form Accessibility

> **Purpose**: Labels, error messages, required fields, fieldsets
> **MCP Validated**: 2026-03-29

## When to Use

- Every form in the application
- Anywhere users provide input

## Implementation

```tsx
function ContactForm() {
  return (
    <form noValidate>
      {/* Every input has a visible label */}
      <div>
        <label htmlFor="name">
          Full Name <span aria-hidden="true">*</span>
        </label>
        <input
          id="name"
          type="text"
          required
          aria-required="true"
          aria-invalid={!!errors.name}
          aria-describedby={errors.name ? "name-error" : undefined}
        />
        {errors.name && (
          <p id="name-error" role="alert" className="text-sm text-red-500">
            {errors.name}
          </p>
        )}
      </div>

      {/* Group related fields with fieldset */}
      <fieldset>
        <legend>Contact Preference</legend>
        <label>
          <input type="radio" name="contact" value="email" /> Email
        </label>
        <label>
          <input type="radio" name="contact" value="phone" /> Phone
        </label>
      </fieldset>

      {/* Error summary at form level */}
      {hasErrors && (
        <div role="alert" aria-live="polite">
          <h3>Please fix the following errors:</h3>
          <ul>
            {Object.entries(errors).map(([field, msg]) => (
              <li key={field}>
                <a href={`#${field}`}>{msg}</a>
              </li>
            ))}
          </ul>
        </div>
      )}

      <button type="submit">Send</button>
    </form>
  );
}
```

## Configuration

| Attribute | Purpose |
|-----------|---------|
| `htmlFor` + `id` | Associates label with input |
| `aria-required` | Marks field as required for AT |
| `aria-invalid` | Indicates validation error |
| `aria-describedby` | Links to error/hint text |
| `role="alert"` | Announces errors immediately |

## See Also

- [wcag-guidelines.md](../concepts/wcag-guidelines.md)
- [aria-patterns.md](../concepts/aria-patterns.md)
