# Capture IDs and wait for query/effect completion

Use only the branch needed by the task. Resolve the application revision and capabilities through [nh-app-context](../../nh-app-context/SKILL.md) before adapting API examples. The existing consumer layout and compatible API guide determine the actual imports, markers, and commands.

## Template 3 — create command → capture → query with retry (lifecycle)

Grounded in `testbed/tests/queries/cart-summary-after-create.hurl`. This is the standard two-step pattern: create an entity, then verify it appears in the query result. The `[Options] retry` is required because queries are eventually consistent — the query subscriber processes events asynchronously. The command (`POST`) step, by contrast, is **strongly consistent** — never add `retry` to it; the write path is synchronous. Only the query step needs retry while the projection catches up.

```hurl
# Entity Lifecycle - Create and Verify Query State

# Step 1: Create the entity
POST {{base_url}}/commands/create-entity
[]

HTTP/1.1 200

[Captures]
new_entity_id: jsonpath "$.entityId"

[Asserts]
jsonpath "$.entityId" exists

# Step 2: Query and find the entity
# retry handles eventual consistency — the query subscriber is async
GET {{base_url}}/queries/entity-summary
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

NeoHaskell queries return one of two shapes depending on the `QueryOf.combine` implementation. Detect the shape by running the endpoint manually during development (`neo run` then `curl {{base_url}}/queries/<name> | jq`), or by reading the query source.

### Shape A — paginated (items-wrapped)

The testbed `CartSummary` and `StockLevel` queries both use this shape. Grounded in `testbed/tests/queries/cart-summary.hurl` and `testbed/tests/queries/stock-level.hurl`.

```hurl
GET {{base_url}}/queries/cart-summary

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
GET {{base_url}}/queries/my-query

HTTP/1.1 200
Content-Type: application/json

[Asserts]
jsonpath "$" isCollection
jsonpath "$[?(@.id == '{{entity_id}}')]" count == 1
jsonpath "$[?(@.id == '{{entity_id}}')].status" nth 0 == "active"
```

If you write `$.items[?...]` against a bare-array response, the assert silently fails with "no such path" — that is not a NeoHaskell bug; it means you used the wrong shape.

---


## Template 5 — multi-step scenario

Grounded in `testbed/tests/scenarios/multiple-carts.hurl` and `testbed/tests/scenarios/stock-reservation.hurl`. Put cross-entity flows in `tests/scenarios/`; keep individual command/query tests in their own files.

```hurl
# Scenario: Create two entities, verify they appear independently in query

# Step 1: Create first entity
POST {{base_url}}/commands/create-entity
[]

HTTP/1.1 200
[Captures]
entity_1_id: jsonpath "$.entityId"

# Step 2: Create second entity
POST {{base_url}}/commands/create-entity
[]

HTTP/1.1 200
[Captures]
entity_2_id: jsonpath "$.entityId"

[Asserts]
# Entities must have distinct ids
jsonpath "$.entityId" != {{entity_1_id}}

# Step 3: Query — verify both exist independently
GET {{base_url}}/queries/entity-summary
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
GET {{base_url}}/queries/stock-level
[Options]
retry: 10
retry-interval: 200

HTTP/1.1 200
[Asserts]
jsonpath "$.items[?(@.stockLevelId == '{{stock_id}}')].reserved" nth 0 == 5
```

For timer-based inbound integrations that need a real-time wait. Grounded in `testbed/tests/scenarios/periodic-cart-creation.hurl`:

```hurl
GET {{base_url}}/queries/cart-summary
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

