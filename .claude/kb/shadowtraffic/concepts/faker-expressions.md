# Faker Expressions

> **Purpose**: Java Faker expressions for realistic text data via ShadowTraffic string generator
> **Confidence**: 0.95
> **MCP Validated**: 2026-04-12

## Overview

The `string` function with `expr` supports Java Faker expressions using `#{Namespace.method}` syntax. ShadowTraffic uses Datafaker v2.4.1 under the hood. Parameters use single quotes with no spaces after commas. Expressions can be embedded in larger strings for templated output.

## The Pattern

```json
{
  "row": {
    "name": { "_gen": "string", "expr": "#{Name.fullName}" },
    "email": { "_gen": "string", "expr": "#{Internet.emailAddress}" },
    "product": { "_gen": "string", "expr": "#{Commerce.productName}" },
    "category": { "_gen": "string", "expr": "#{Commerce.department}" },
    "brand": { "_gen": "string", "expr": "#{Company.name}" },
    "city": { "_gen": "string", "expr": "#{Address.city}" },
    "state": { "_gen": "string", "expr": "#{Address.stateAbbr}" },
    "review": { "_gen": "string", "expr": "#{Lorem.paragraph}" },
    "profile_url": { "_gen": "string", "expr": "https://shop.com/user/#{Name.username}" }
  }
}
```

## Quick Reference (E-Commerce)

| Expression | Example Output | Use Case |
|------------|---------------|----------|
| `#{Name.fullName}` | Maria Silva | Customer names |
| `#{Name.firstName}` | Maria | First name only |
| `#{Name.lastName}` | Silva | Last name only |
| `#{Name.username}` | maria.silva | Usernames |
| `#{Internet.emailAddress}` | maria@example.com | Customer emails |
| `#{Internet.url}` | https://example.com | URLs |
| `#{Commerce.productName}` | Ergonomic Granite Chair | Product names |
| `#{Commerce.department}` | Electronics | Product categories |
| `#{Commerce.price}` | 45.99 | Price strings |
| `#{Company.name}` | TechCorp Ltda | Brand/company names |
| `#{Address.city}` | São Paulo | Cities |
| `#{Address.stateAbbr}` | SP | State abbreviations |
| `#{Address.fullAddress}` | Rua das Flores, 123 | Full addresses |
| `#{Lorem.paragraph}` | Multi-sentence text block | Review comments |
| `#{Lorem.sentence}` | Single sentence | Short descriptions |
| `#{PhoneNumber.phoneNumber}` | (11) 98765-4321 | Phone numbers |
| `#{Date.birthday '18','80'}` | 1985-03-15 | Dates with age range |

## Embedding in Strings

Faker expressions can be mixed with literal text:

```json
{ "_gen": "string", "expr": "Order from #{Name.fullName} in #{Address.city}" }
```

Output: `"Order from Maria Silva in São Paulo"`

## Common Mistakes

### Wrong

```python
# Python Faker syntax — does NOT work in ShadowTraffic
fake.name()
fake.email()
```

### Correct

```json
{ "_gen": "string", "expr": "#{Name.fullName}" }
{ "_gen": "string", "expr": "#{Internet.emailAddress}" }
```

### Wrong (Parameter Spacing)

```json
{ "_gen": "string", "expr": "#{Date.birthday '18', '80'}" }
```

Space after comma breaks the expression.

### Correct

```json
{ "_gen": "string", "expr": "#{Date.birthday '18','80'}" }
```

No spaces between parameters — single quotes, comma, no space.

## Related

- [Functions](../concepts/functions.md)
- [Generators](../concepts/generators.md)
