# Resolve capture, assertion, or option syntax

Use only the branch needed by the task. Resolve the application revision and capabilities through [nh-app-context](../../nh-app-context/SKILL.md) before adapting API examples. The existing consumer layout and compatible API guide determine the actual imports, markers, and commands.

## [Captures] / [Asserts] / [Options] — keyword order

`[Options]` goes **before** the `HTTP` status line. `[Captures]` and `[Asserts]` go **after**. Getting the order wrong causes Hurl to misparse the file.

```hurl
GET {{base_url}}/queries/cart-summary
[Options]           ← BEFORE the HTTP line
retry: 5
retry-interval: 100

HTTP/1.1 200        ← status line
[Captures]          ← AFTER the HTTP line
total: jsonpath "$.items" count
[Asserts]           ← AFTER the HTTP line
jsonpath "$.items" isCollection
```

| Keyword | What it does | Real example |
|---|---|---|
| `[Captures]` | Bind a response value to a named variable | `cart_id: jsonpath "$.entityId"` |
| `{{var}}` | Reuse a captured variable in later steps | `jsonpath "$.entityId" != {{cart_id}}` |
| `retry:` | Max number of retry attempts (retries until all asserts pass) | `retry: 5` |
| `retry-interval:` | Milliseconds between retries | `retry-interval: 100` |
| `delay:` | Milliseconds to wait before sending this request | `delay: 4000` |

---

