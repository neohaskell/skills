# Test integration action intent

Use only the branch needed by the task. Resolve the application revision and capabilities through [nh-app-context](../../nh-app-context/SKILL.md) before adapting API examples. The existing consumer layout and compatible API guide determine the actual imports, markers, and commands.

## Template C — Outbound (integration handleEvent)

Grounded in
`testbed/src/Testbed/Cart/Integrations/ReserveStockOnItemAdded.hs` and
`core/service/Integration.hs`. Replace `ReserveStockOnItemAdded` / `Cart*`
with your handler, entity, and event names.

```haskell
-- tests/Outbound/ReserveStockOnItemAddedSpec.hs
module Outbound.ReserveStockOnItemAddedSpec where

import Array qualified
import Core
import Integration qualified
import Test
import Uuid qualified
-- REPLACE: import your integration handler and entity/event types
import Testbed.Cart.Core (CartEntity (..), CartEvent (..))
import Testbed.Cart.Integrations.ReserveStockOnItemAdded qualified as ReserveStockOnItemAdded


spec :: Spec Unit
spec = do
  describe "ReserveStockOnItemAdded.handleEvent" do

    -- GIVEN a non-matching event constructor — WHEN handleEvent fires — THEN emit no actions
    it "emits no actions for a non-matching event" \_ -> do
      let cart = CartEntity {cartId = Uuid.nil, ownerId = "u1", items = Array.empty}
      let result =
            ReserveStockOnItemAdded.handleEvent
              cart
              (CartCreated {entityId = Uuid.nil, ownerId = "u1"})
      Integration.getActions result |> Array.length |> shouldBe 0

    -- GIVEN the matching event — WHEN handleEvent fires — THEN emit exactly one action
    it "emits one action for the matching ItemAdded event" \_ -> do
      let cart = CartEntity {cartId = Uuid.nil, ownerId = "u1", items = Array.empty}
      let result =
            ReserveStockOnItemAdded.handleEvent
              cart
              (ItemAdded {entityId = Uuid.nil, stockId = Uuid.nil, quantity = 3})
      Integration.getActions result |> Array.length |> shouldBe 1
```

`handleEvent` is a **top-level function** in the integration module (not a
typeclass method) — call it directly with the qualified module alias.
`Integration.getActions :: Outbound -> Array Action` unwraps the action list
for inspection/execution using the revision-compatible `runAction` test context. The count-only example above is a smoke assertion: add assertions for the returned `CommandPayload.commandType` and `commandData`, or test the typed pure plan used by the handler. Use different IDs for cart and stock so swapped destinations fail; change quantity in the input so a hard-coded payload fails. An unrelated event must produce no action. A simulated executor proves the contract, not a real external effect. The wildcard branch in `handleEvent` must return `Integration.none`
(never `panic "TODO"` — see stub rule below).

---

