# Create records or check rejection responses

Use only the branch needed by the task. Resolve the application revision and capabilities through [nh-app-context](../../nh-app-context/SKILL.md) before adapting API examples. The existing consumer layout and compatible API guide determine the actual imports, markers, and commands.

## Request context

Discover the actual transport URL, routes, response schema, authentication, and test-state isolation through [nh-app-context](../../nh-app-context/SKILL.md). The templates use `{{base_url}}`; pass the application URL as a Hurl variable. For bearer authentication add `Authorization: Bearer {{access_token}}` to protected requests and supply a synthetic test identity through a private variables file. Cookie or other authentication follows the application's contract. Keep credentials out of logs and committed fixtures.

Capture the ID created by this run and poll that entity's requested terminal state with a fixed retry budget. Command acceptance proves acceptance only; it does not prove an asynchronous effect completed. Timeout means incomplete evidence, not success. UI behavior belongs to [nh-frontend](../../nh-frontend/SKILL.md).


## Endpoint conventions

| Block | Method + path | Port |
|---|---|---|
| Command | `POST {{base_url}}/commands/<kebab-name>` | 8080 (Config-derived; default env var `PORT`) |
| Query | `GET {{base_url}}/queries/<kebab-name>` | 8080 |

The kebab name is the PascalCase type name lowercased with hyphens: `CreateCart` → `create-cart`, `CartSummary` → `cart-summary`. Confirm the exact name with `neo inspect wiring` after `wire-feature`.

---


## Template 1 — creation command, no fields

Grounded in `testbed/tests/commands/create-cart.hurl`. A command with no payload fields sends `[]` as the request body (the framework's JSON transport accepts an empty value for a nullary record).

```hurl
# CreateEntity Command - Happy Path
# Verifies command execution and response structure

POST {{base_url}}/commands/create-entity
[]

HTTP/1.1 200
Content-Type: application/json

[Asserts]
# Response must have entityId field
jsonpath "$.entityId" exists
jsonpath "$.entityId" isString
jsonpath "$.entityId" matches /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/
```

---


## Template 2 — command with fields

Grounded in `testbed/tests/scenarios/stock-reservation.hurl`. Send a JSON object whose keys mirror the command record's field names.

```hurl
# InitializeStock Command - With Payload Fields

POST {{base_url}}/commands/initialize-stock
{
  "productId": "11111111-1111-1111-1111-111111111111",
  "available": 100
}

HTTP/1.1 200
Content-Type: application/json

[Asserts]
jsonpath "$.entityId" exists
```

---


## Template 4 — reject path

Grounded in `testbed/tests/commands/create-document.hurl`. A `decide` that calls `Decider.reject "message"` produces `HTTP 400` with `{"tag": "Rejected", "reason": "..."}`. A missing required field at parse time produces `{"tag": "Failed"}`.

```hurl
# CreateEntity - Reject Paths

# Path 1: invalid field value → Decider.reject → 400 Rejected
POST {{base_url}}/commands/create-entity
{
  "entityId": "00000000-0000-0000-0000-000000000001",
  "amount": -5
}

HTTP 400
[Asserts]
jsonpath "$.tag" == "Rejected"
jsonpath "$.reason" contains "must be positive"

# Path 2: missing required field → parse failure → 400 Failed
POST {{base_url}}/commands/create-entity
{
  "entityId": "00000000-0000-0000-0000-000000000001"
}

HTTP 400
[Asserts]
jsonpath "$.tag" == "Failed"
```

Both `HTTP 400` (short form) and `HTTP/1.1 400` are accepted by Hurl.

---

