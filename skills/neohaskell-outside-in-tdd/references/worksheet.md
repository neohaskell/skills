# Track a business slice across the double loop

Use only the branch needed by the task. Resolve the application revision and capabilities through [nh-app-context](../../nh-app-context/SKILL.md) before adapting API examples. The existing consumer layout and compatible API guide determine the actual imports, markers, and commands.

## Copy-paste: the per-slice worksheet

Copy this, fill in the slice, and work top to bottom. Placeholders (`<Cmd>`, `<Event>`, `<Query>`,
`<Entity>`) are the frozen node names from `verify-event-model`. The example column is grounded in the
public `Cart`/`Stock` testbed slice "add an item to a cart."

```
SLICE: <one user-meaningful step>            e.g. "AddItem to a cart"
  entity  : <Entity>                          CartEntity   (exists — build on it)
  command : <Cmd>  -> event <Event>           AddItem -> ItemAdded
  query   : <Query> (field touched)           CartSummary (itemCount)

[ ] ① RED  outer   write-hurl-e2e        tests/scenarios/add-item.hurl   -> expect 404 (not wired)
[ ] ② RED  accept. write-feature-tests   tests/Acceptance/AddItemSpec.hs  -> compile error
[ ] ③ RED  inner   write-unit-tests      tests/Decider/AddItemSpec.hs     -> 1 assert, GWT, compile error
[ ] ④ DOMAIN       neohaskell-domain-modeling
                   - event payload Events/<Event>.hs (type `Event`) + variant in Event.hs
                   - entity field(s) in Entity.hs / expand-entity (add-only, replay-safe)
                   - `decide`/`combine`/`handleEvent` bodies STUBBED
                     pure/Task  -> panic "TODO: not implemented"
                     outbound   -> Integration.none  -- TODO:
                   -> `neo build` compiles; ③ now fails on the ASSERTION
[ ] ⑤ GREEN        implement-command / -event-and-update-entity / -query / -integration
                   -> minimal body; ③ goes green; repeat ③→④→⑤ for each remaining assertion
[ ] ⑥ GREEN  wire  wire-feature          Service.command @<Cmd>; App.hs withService/withQuery/...
                   -> ① hurl goes green (endpoint now answers 200)
[ ] ⑦ REFACTOR     tidy (all green) + write-feature-tests property replay (Array.foldl update)
[ ] DONE           `neo test` all green (hspec + hurl); phase boundaries respected

If <Cmd>/<Event>/<Query> is LOCKED (deployed): do NOT edit it. Run this WHOLE worksheet on a V2
sibling (`<Cmd>V2`) per neo-immutability-and-versioning, then wire the V2 in.
```

### The phases, grounded (Cart `AddItem`)

**① outer RED** — grounded in `testbed/tests/queries/cart-summary-after-create.hurl`. Fails 404 until ⑥:

```hurl
POST http://localhost:8080/commands/create-cart
[]
HTTP/1.1 200
[Captures]
cart_id: jsonpath "$.entityId"

POST http://localhost:8080/commands/add-item
{ "cartId": "{{cart_id}}", "stockId": "11111111-1111-1111-1111-111111111111", "quantity": 5 }
HTTP/1.1 200

GET http://localhost:8080/queries/cart-summary
[Options]
retry: 5
retry-interval: 100
HTTP/1.1 200
[Asserts]
jsonpath "$.items[?(@.cartSummaryId == '{{cart_id}}')].itemCount" nth 0 == 5
```

**④ DOMAIN stub** — the types exist; the body does not. It compiles, so ③ can fail on the assertion:

```haskell
-- Commands/AddItem.hs, DOMAIN phase: stub only
decide :: AddItem -> Maybe CartEntity -> RequestContext -> Decision CartEvent
decide _cmd _entity _ctx = panic "TODO: not implemented"
```

For an **outbound** handler the stub is `Integration.none`, never `panic` (grounded in
`testbed/.../Integrations/ReserveStockOnItemAdded.hs`, whose fall-through is `_ -> Integration.none`):

```haskell
handleEvent :: CartEntity -> CartEvent -> Integration.Outbound
handleEvent _cart _event = Integration.none   -- TODO: emit the cross-aggregate command in GREEN
```

**⑤ GREEN** — replace the one stub with the minimal real body (the actual `Testbed.Cart.Commands.AddItem`):

```haskell
decide :: AddItem -> Maybe CartEntity -> RequestContext -> Decision CartEvent
decide cmd entity _ctx = case entity of
  Nothing -> Decider.reject "Cart not found!"
  Just cart ->
    if cmd.quantity <= 0
      then Decider.reject "Quantity must be positive"
      else
        Decider.acceptExisting
          [ ItemAdded {entityId = cart.cartId, stockId = cmd.stockId, quantity = cmd.quantity} ]
```

(Creation slices end in `Decider.acceptNew [...]` with ids from `newId <- Decider.generateUuid`, as in
`Testbed.Cart.Commands.CreateCart`. The full per-block templates live in the `implement-*` skills.)

**⑦ REFACTOR** — with everything green, add the property replay spec that folds the event log oldest
event first with the entity's `update` (`Array.foldl update initialState events`), per
`write-feature-tests`.

---

