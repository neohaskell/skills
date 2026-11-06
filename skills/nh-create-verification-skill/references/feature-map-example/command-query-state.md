> Adapted for consumer applications from the public NeoHaskell project.

# Command and query state

A caller creates a Cart through the real command entrypoint, captures its identity and observes that exact Cart through the query interface. Command acceptance and observable query state are separate checkpoints.

## Sub-features

- `command-create` creates an entity through the registered command route.
- `query-created` finds exactly that entity after its query projection becomes visible.
- `query-initial` checks the new Cart's independently specified initial query state.

## How to get to it (user POV)

- Submit the request to `/commands/create-cart` through an owned application instance, if that route exists in the selected application.
- Read `/queries/cart-summary` and select the returned Cart identifier.
- Locate the consumer’s maintained command/query scenario and confirm its routes and response shape before using this example.

## Driving it with Hurl

Preconditions:

- The generated Launch/Doctor recipe has established an owned, usable application, isolated state and the port declared by its configuration.
- Required query rebuilds are ready and the harness captures the returned identifier and proof artifacts.

- **Create.** For this illustrative contract, the Hurl recipe posts `[]` to `/commands/create-cart`, requires HTTP 200 and captures `$.entityId`.
- **Observe.** It reads `/queries/cart-summary` with bounded retries, selects `cartSummaryId` equal to the captured identifier and requires exactly one matching row.
- **Check state.** That row must have `itemCount=0` and `isEmpty=true`; an unrelated Cart is not evidence for this action.
- **Drive the consumer recipe.** Resolve the actual scenario path and supported Hurl invocation from the selected application. The generated skill must supply and prove literal setup, driving, evidence-capture and cleanup commands; these teaching names are not executable defaults.
- **Proof.** Retain the creating request/response, captured identifier, query response and assertion result, then verify that cleanup preserved them.

## Gotchas

- HTTP acceptance does not establish projection visibility or every storage durability claim.
- An application runner may reuse a healthy instance. Verify ownership and usable readiness before selecting its startup behavior.
- Background activity creates other Carts; query exact captured identities rather than global totals.
- A failed precondition remains a reported failure; do not replace this journey with a direct state setter or a different convenient entrypoint.
