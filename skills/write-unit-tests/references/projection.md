# Test projection updates

Use only the branch needed by the task. Resolve the application revision and capabilities through [nh-app-context](../../nh-app-context/SKILL.md) before adapting API examples. The existing consumer layout and compatible API guide determine the actual imports, markers, and commands.

## Template B — Projection (query combine)

Grounded in `testbed/src/Testbed/Cart/Queries/CartSummary.hs` and
`core/service/Service/Query/Core.hs`. Replace `CartSummary` / `CartEntity`
with your query and entity names.

```haskell
-- tests/Projection/CartSummarySpec.hs
module Projection.CartSummarySpec where

import Array qualified
import Core
import Test
import Uuid qualified
-- REPLACE: import your query and entity types
import Testbed.Cart.Core (CartEntity (..))
import Testbed.Cart.Queries.CartSummary (CartSummary (..))


spec :: Spec Unit
spec = do
  describe "CartSummary.combine" do

    -- GIVEN an empty cart — WHEN combined with no existing query — THEN isEmpty is True
    it "reports isEmpty True for a cart with no items" \_ -> do
      let cart = CartEntity {cartId = Uuid.nil, ownerId = "u1", items = Array.empty}
      let result = (combine @CartEntity @CartSummary) cart Nothing
      result
        |> shouldBe
          ( Update
              CartSummary
                { cartSummaryId = Uuid.nil
                , ownerId = "u1"
                , itemCount = 0
                , isEmpty = True
                }
          )
```

`combine` is a method of the `QueryOf entity query` typeclass. Call it with
explicit type applications `@Entity @Query` so the compiler can pick the right
instance. `QueryAction` has three constructors: `Update q`, `Delete`, `NoOp`.
`QueryOf`, `QueryAction(..)`, and `Update` are re-exported by `Core` — do **not**
import `Service.Query.Core` (redundant next to `import Core`, and `-Werror`).

---

