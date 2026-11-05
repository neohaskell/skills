# Test decisions, rejections, and identity

Use only the branch needed by the task. Resolve the application revision and capabilities through [nh-app-context](../../nh-app-context/SKILL.md) before adapting API examples. The existing consumer layout and compatible API guide determine the actual imports, markers, and commands.

## Template A — Decider (command decide)

Grounded in `testbed/src/Testbed/Cart/Commands/AddItem.hs` and
`core/service/Decider.hs`. Replace `AddItem` / `Cart*` with your command and
entity names.

```haskell
-- tests/Decider/AddItemSpec.hs
module Decider.AddItemSpec where

import Array qualified
import Core
import Decider (DecisionContext (..))
import Decider qualified
import Service.Auth qualified as Auth
import Test
import Uuid qualified
-- REPLACE: import your command module and entity/event types
import Testbed.Cart.Commands.AddItem qualified as AddItem
import Testbed.Cart.Core (CartEntity (..), CartEvent (..))


spec :: Spec Unit
spec = do
  describe "AddItem.decide" do

    -- GIVEN entity is absent — WHEN command arrives — THEN reject with not-found message
    it "rejects when the cart does not exist" \_ -> do
      let cmd = AddItem.AddItem {cartId = Uuid.nil, stockId = Uuid.nil, quantity = 1}
      let ctx = DecisionContext {genUuid = Uuid.generate}
      result <- Decider.runDecision ctx (AddItem.decide cmd Nothing Auth.emptyContext)
      result |> shouldBe (RejectCommand "Cart not found!")

    -- GIVEN entity exists but input violates a rule — WHEN command arrives — THEN reject
    it "rejects when quantity is not positive" \_ -> do
      let cart = CartEntity {cartId = Uuid.nil, ownerId = "u1", items = Array.empty}
      let cmd = AddItem.AddItem {cartId = Uuid.nil, stockId = Uuid.nil, quantity = -1}
      let ctx = DecisionContext {genUuid = Uuid.generate}
      result <- Decider.runDecision ctx (AddItem.decide cmd (Just cart) Auth.emptyContext)
      result |> shouldBe (RejectCommand "Quantity must be positive")

    -- GIVEN entity exists and input is valid — WHEN command arrives — THEN accept
    it "accepts when cart exists and quantity is positive" \_ -> do
      let cart = CartEntity {cartId = Uuid.nil, ownerId = "u1", items = Array.empty}
      let cmd = AddItem.AddItem {cartId = Uuid.nil, stockId = Uuid.nil, quantity = 5}
      let ctx = DecisionContext {genUuid = Uuid.generate}
      result <- Decider.runDecision ctx (AddItem.decide cmd (Just cart) Auth.emptyContext)
      case result of
        AcceptCommand _ _ -> Task.yield unit
        RejectCommand msg -> fail [fmt|Unexpected rejection: #{msg}|]
```

**Creation commands** (e.g. `CreateCart`) use `Nothing` entity and
`Decider.acceptNew` in `decide`. For creation, the cases flip: "entity absent
→ accept (generate a uuid with `Decider.generateUuid`)" and "entity present →
reject (already exists)".

**Auth:** `Auth.emptyContext` is an unauthenticated `RequestContext` with a nil
UUID, epoch timestamp, and `trustedBypass = False`. It is fine for RED specs.
Import it from `Service.Auth qualified as Auth`.

**Imports:** `CommandResult(..)` (`AcceptCommand`/`RejectCommand`) is
re-exported by `Core`; `DecisionContext` is **not** — import only
`DecisionContext` from `Decider`. Importing `CommandResult(..)` from `Decider`
as well is redundant and fails under `-Wall -Werror=unused-imports`.

**Record update of a qualified command:** to tweak one field of an
already-built command (e.g. to derive an invalid variant), the field label must
be **qualified** — `cmd {AddItem.quantity = -1}`, not `{quantity = -1}` —
because under `NoFieldSelectors` a bare label from a `qualified`-imported module
isn't in scope for an update (`Not in scope: record field 'quantity'`).
Construction via the qualified constructor `AddItem.AddItem {quantity = …}` is
fine. See **neohaskell-records-and-json**.

---

