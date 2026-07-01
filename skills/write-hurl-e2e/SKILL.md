---
name: write-hurl-e2e
description: >-
  Writes Hurl end-to-end test files under tests/ for NeoHaskell features —
  POST /commands/kebab-name and GET /queries/kebab-name on localhost:8080 — with
  [Captures] to bind entityId, [Asserts] to verify responses, and [Options]
  retry for eventually-consistent queries. Run with neo test. Use this skill
  first in each outside-in TDD slice (RED outer loop, before implementation
  exists, while the endpoint returns 404). Also use when asked to add an e2e
  test, write a .hurl file, test a command or query over HTTP, assert a 400
  Rejected response on a reject path, verify an integration side-effect fires,
  or capture an entityId and reuse it across steps. Teaches both query response
  shapes: paginated items-wrapped ($.items / $.total / $.hasMore) and bare array
  ($[?...]), with detection guidance for each.
metadata:
  model: sonnet
---

**This is NeoHaskell, not vanilla Haskell.** The `.hs` extension is shared, but `.hurl` files talk to a NeoHaskell application — the endpoint conventions, response shapes, and reject structure are all framework-specific. Every pattern below is grounded in the public testbed sources.

---

## TDD cycle role — ① RED outer loop

This skill runs **first** in each outside-in TDD slice, before any implementation exists:

```
► write-hurl-e2e (RED outer — neo test returns 404 until wired) ◄
  write-feature-tests (RED acceptance, in-domain)
    write-unit-tests (RED, one assertion, GWT)
      neohaskell-domain-modeling (DOMAIN — types + panic stubs)
        implement-command / implement-event / implement-query (GREEN — minimal)
          wire-feature (GREEN — endpoint live → hurl turns green)
```

Write the `.hurl` file first. Running `neo test` immediately after will show a 404 — that is the correct RED state. The test only turns green after `wire-feature` registers the command/query in `Service.hs` and `App.hs`.

In Claude Code, delegate this step to a sub-agent spawned with `model: sonnet`. In Cursor or Codex the tier is advisory — run it inline.

---

## Inputs / Outputs / Next

- **Input:** a verified command + query node from `event-model.json` (name, fields, create-vs-update intent, slice).
- **Output:** `tests/commands/<kebab>.hurl`, `tests/queries/<kebab>.hurl`, and optionally `tests/scenarios/<scenario>.hurl`.
- **Next:** `write-feature-tests` (in-domain RED acceptance) · `neo-run-and-inspect` (manual curl verification once the app is running)

---

## Endpoint conventions

| Block | Method + path | Port |
|---|---|---|
| Command | `POST http://localhost:8080/commands/<kebab-name>` | 8080 (Config-derived; default env var `PORT`) |
| Query | `GET http://localhost:8080/queries/<kebab-name>` | 8080 |

The kebab name is the PascalCase type name lowercased with hyphens: `CreateCart` → `create-cart`, `CartSummary` → `cart-summary`. Confirm the exact name with `neo inspect wiring` after `wire-feature`.

---

## Template 1 — creation command, no fields

Grounded in `testbed/tests/commands/create-cart.hurl`. A command with no payload fields sends `[]` as the request body (the framework's JSON transport accepts an empty value for a nullary record).

```hurl
# CreateEntity Command - Happy Path
# Verifies command execution and response structure

POST http://localhost:8080/commands/create-entity
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

POST http://localhost:8080/commands/initialize-stock
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

## Template 3 — create command → capture → query with retry (lifecycle)

Grounded in `testbed/tests/queries/cart-summary-after-create.hurl`. This is the standard two-step pattern: create an entity, then verify it appears in the query result. The `[Options] retry` is required because queries are eventually consistent — the query subscriber processes events asynchronously.

```hurl
# Entity Lifecycle - Create and Verify Query State

# Step 1: Create the entity
POST http://localhost:8080/commands/create-entity
[]

HTTP/1.1 200

[Captures]
new_entity_id: jsonpath "$.entityId"

[Asserts]
jsonpath "$.entityId" exists

# Step 2: Query and find the entity
# retry handles eventual consistency — the query subscriber is async
GET http://localhost:8080/queries/entity-summary
[Options]
retry: 5
retry-interval: 100

HTTP/1.1 200
Content-Type: application/json

[Asserts]
jsonpath "$.items[?(@.entitySummaryId == '{{new_entity_id}}')]" count == 1
jsonpath "$.items[?(@.entitySummaryId == '{{new_entity_id}}')].isActive" nth 0 == true
```

---

## Query response shapes — both patterns

NeoHaskell queries return one of two shapes depending on the `QueryOf.combine` implementation. Detect the shape by running the endpoint manually during development (`neo run` then `curl http://localhost:8080/queries/<name> | jq`), or by reading the query source.

### Shape A — paginated (items-wrapped)

The testbed `CartSummary` and `StockLevel` queries both use this shape. Grounded in `testbed/tests/queries/cart-summary.hurl` and `testbed/tests/queries/stock-level.hurl`.

```hurl
GET http://localhost:8080/queries/cart-summary

HTTP/1.1 200
Content-Type: application/json

[Asserts]
jsonpath "$.items" isCollection
jsonpath "$.total" isInteger
jsonpath "$.hasMore" isBoolean
jsonpath "$.effectiveLimit" isInteger
```

To filter by a captured id and check a field:

```hurl
# Grounded in testbed/tests/scenarios/multiple-carts.hurl
jsonpath "$.items[?(@.cartSummaryId == '{{cart_id}}')]" count == 1
jsonpath "$.items[?(@.cartSummaryId == '{{cart_id}}')].itemCount" nth 0 == 0
jsonpath "$.items[?(@.cartSummaryId == '{{cart_id}}')].isEmpty" nth 0 == true
```

The `nth 0` predicate is required when the filter expression returns a collection — scalar comparison without `nth` will fail with a type mismatch.

### Shape B — bare array

Some queries return a plain JSON array. Use a root-level JSONPath filter:

```hurl
GET http://localhost:8080/queries/my-query

HTTP/1.1 200
Content-Type: application/json

[Asserts]
jsonpath "$" isCollection
jsonpath "$[?(@.id == '{{entity_id}}')]" count == 1
jsonpath "$[?(@.id == '{{entity_id}}')].status" nth 0 == "active"
```

If you write `$.items[?...]` against a bare-array response, the assert silently fails with "no such path" — that is not a NeoHaskell bug; it means you used the wrong shape.

---

## Template 4 — reject path

Grounded in `testbed/tests/commands/create-document.hurl`. A `decide` that calls `Decider.reject "message"` produces `HTTP 400` with `{"tag": "Rejected", "reason": "..."}`. A missing required field at parse time produces `{"tag": "Failed"}`.

```hurl
# CreateEntity - Reject Paths

# Path 1: invalid field value → Decider.reject → 400 Rejected
POST http://localhost:8080/commands/create-entity
{
  "entityId": "00000000-0000-0000-0000-000000000001",
  "amount": -5
}

HTTP 400
[Asserts]
jsonpath "$.tag" == "Rejected"
jsonpath "$.reason" contains "must be positive"

# Path 2: missing required field → parse failure → 400 Failed
POST http://localhost:8080/commands/create-entity
{
  "entityId": "00000000-0000-0000-0000-000000000001"
}

HTTP 400
[Asserts]
jsonpath "$.tag" == "Failed"
```

Both `HTTP 400` (short form) and `HTTP/1.1 400` are accepted by Hurl.

---

## Template 5 — multi-step scenario

Grounded in `testbed/tests/scenarios/multiple-carts.hurl` and `testbed/tests/scenarios/stock-reservation.hurl`. Put cross-entity flows in `tests/scenarios/`; keep individual command/query tests in their own files.

```hurl
# Scenario: Create two entities, verify they appear independently in query

# Step 1: Create first entity
POST http://localhost:8080/commands/create-entity
[]

HTTP/1.1 200
[Captures]
entity_1_id: jsonpath "$.entityId"

# Step 2: Create second entity
POST http://localhost:8080/commands/create-entity
[]

HTTP/1.1 200
[Captures]
entity_2_id: jsonpath "$.entityId"

[Asserts]
# Entities must have distinct ids
jsonpath "$.entityId" != {{entity_1_id}}

# Step 3: Query — verify both exist independently
GET http://localhost:8080/queries/entity-summary
[Options]
retry: 5
retry-interval: 100

HTTP/1.1 200
Content-Type: application/json

[Asserts]
jsonpath "$.items[?(@.entitySummaryId == '{{entity_1_id}}')]" count == 1
jsonpath "$.items[?(@.entitySummaryId == '{{entity_2_id}}')]" count == 1
jsonpath "$.items[?(@.entitySummaryId == '{{entity_1_id}}')].isEmpty" nth 0 == true
jsonpath "$.items[?(@.entitySummaryId == '{{entity_2_id}}')].isEmpty" nth 0 == true
```

For integration flows that require a longer wait (e.g. verifying an outbound integration fired). Grounded in `testbed/tests/scenarios/stock-reservation.hurl`:

```hurl
# Step 4: Verify integration side-effect (takes longer — raise retry count)
GET http://localhost:8080/queries/stock-level
[Options]
retry: 10
retry-interval: 200

HTTP/1.1 200
[Asserts]
jsonpath "$.items[?(@.stockLevelId == '{{stock_id}}')].reserved" nth 0 == 5
```

For timer-based inbound integrations that need a real-time wait. Grounded in `testbed/tests/scenarios/periodic-cart-creation.hurl`:

```hurl
GET http://localhost:8080/queries/cart-summary
[Options]
delay: 4000
retry: 5
retry-interval: 500

HTTP/1.1 200
[Captures]
count_after: jsonpath "$.items" count

[Asserts]
jsonpath "$.items" count > {{count_before}}
```

---

## [Captures] / [Asserts] / [Options] — keyword order

`[Options]` goes **before** the `HTTP` status line. `[Captures]` and `[Asserts]` go **after**. Getting the order wrong causes Hurl to misparse the file.

```hurl
GET http://localhost:8080/queries/cart-summary
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

## DO / DON'T

| Wrong — DON'T | Correct — DO | Why |
|---|---|---|
| `POST http://localhost:8080/command/create-cart` | `POST http://localhost:8080/commands/create-cart` | Path is always plural: `/commands/` and `/queries/` |
| `GET http://localhost:8080/queries/CartSummary` | `GET http://localhost:8080/queries/cart-summary` | Kebab-case, not PascalCase — matches the `NameOf` type family |
| Omit `[Options] retry:` on query asserts that follow a command | Always add `retry: 5` + `retry-interval: 100` | Queries are eventually consistent; the subscriber processes events asynchronously |
| `jsonpath "$.total" == 1` to check a specific entity exists | `jsonpath "$.items[?(@.cartSummaryId == '{{id}}')]" count == 1` | Total counts the whole collection; filter to the specific id |
| `jsonpath "$.items[?(@.id == '{{id}}')].field" == "val"` | `jsonpath "$.items[?(@.id == '{{id}}')].field" nth 0 == "val"` | A filter expression returns a collection; `nth 0` selects the element for scalar comparison |
| `$.items[?...]` when the query returns a bare array | `$[?...]` for bare arrays; `$.items[?...]` for paginated | Wrong shape gives "no such path" — detect from the query source or a manual curl |
| Add `Authorization: Bearer ...` headers on happy-path tests | Write happy-path tests unauthenticated | Auth is only enforced when `Application.withAuth` is wired; without it, commands return 200 unauthenticated |
| Assert `HTTP/1.1 200` on a `Decider.reject` path | Assert `HTTP 400` + `jsonpath "$.tag" == "Rejected"` | The framework converts a reject decision into a 400 with the `Rejected` tag |
| Emit `.hs` files from this step | Only `.hurl` files under `tests/` | This is the RED phase — no implementation belongs here |
| Put `[Options]` after the HTTP status line | Put `[Options]` before the HTTP status line | Hurl misparsing silently ignores options placed in the wrong position |

---

## Verify

```
neo test
```

`neo test` boots the application, waits approximately 2 seconds, then discovers and runs every `tests/**/*.hurl` file. The correct RED output (before implementation) is:

```
error: Assert failure
  --> tests/commands/create-entity.hurl:7:0
  asserting response status 200 but received 404
```

After `wire-feature` connects the endpoint, re-run `neo test` to confirm all assertions pass (green).

To run the app manually and explore responses during development:

```
neo run
# In another shell:
curl -s -X POST http://localhost:8080/commands/create-cart \
     -H 'Content-Type: application/json' \
     -d '[]' | jq
curl -s http://localhost:8080/queries/cart-summary | jq
```

See `neo-run-and-inspect` for the full endpoint list, including `/openapi.json`, `/docs`, and `/health`.
