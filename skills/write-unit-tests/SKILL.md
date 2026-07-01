---
name: write-unit-tests
description: Writes RED-first Hspec unit specs for the three pure NeoHaskell building blocks — Decider (command decide), Projection (query combine), and Outbound (integration handleEvent) — using the Test testlib, Decider.runDecision, and Auth.emptyContext. Use this skill whenever asked to write unit tests, write specs, test a command decision, test a query projection, or test an outbound integration handler for a NeoHaskell slice. Also invoke at step 3 of the outside-in TDD cycle, even if the user says only "add tests" or "write a spec", before implement-command, implement-query, or implement-integration, to produce the failing RED test that drives implementation. Assumes neohaskell/neo#2 is in place so neo test compiles the test suite.
metadata:
  model: sonnet
---

# write-unit-tests

This is NeoHaskell, not vanilla Haskell — `.hs` is a shared extension but the
prelude, test library, and idioms differ completely. The reader LLM defaults to
hallucinating Haskell; every rule below overrides that reflex.

## Cycle role (outside-in TDD, step 3 — RED)

This skill is **step 3** in the outside-in cycle. Write the spec *before*
implementation; it should fail (RED) until `implement-*` fills in the bodies.

```
write-hurl-e2e  →  write-feature-tests  →  [write-unit-tests HERE]
  → neohaskell-domain-modeling  →  implement-*  →  wire-feature
```

In NeoHaskell, RED often means a **compile error** first (missing types from
domain modeling) and then an **assertion failure** once the types exist but the
stubs are `panic "TODO: not implemented"`.

## Inputs / Outputs / Next

- **In:** a verified command node, query node, or integration node from the
  event model; entity and event types from `neohaskell-domain-modeling` (or a
  type-error RED spec that drives the domain phase).
- **Out:** spec files under `tests/Decider/`, `tests/Projection/`, or
  `tests/Outbound/` — one file per building block, one assertion per `it`.
  All Haskell specs live under `tests/` (the *same* directory as the `.hurl`
  e2e files); `neo test` compiles and runs the specs it discovers there. Never
  use a `test/` directory — `neo` won't compile it.
- **Next:** `neohaskell-domain-modeling` (if types are missing) then
  `implement-command`, `implement-query`, or `implement-integration`.

## The three spec types

| Building block | File location | What is asserted |
|---|---|---|
| Decider (command) | `tests/Decider/<Name>Spec.hs` | `decide cmd (Maybe entity) ctx` returns the expected `CommandResult` |
| Projection (query) | `tests/Projection/<Name>Spec.hs` | `combine @E @Q entity Nothing` returns the expected `QueryAction Q` |
| Outbound (integration) | `tests/Outbound/<Name>Spec.hs` | `handleEvent entity event` produces the expected action count |

---

## Template A — Decider (command decide)

Grounded in `testbed/src/Testbed/Cart/Commands/AddItem.hs` and
`core/service/Decider.hs`. Replace `AddItem` / `Cart*` with your command and
entity names.

```haskell
-- tests/Decider/AddItemSpec.hs
module Decider.AddItemSpec where

import Array qualified
import Core
import Decider (CommandResult (..), DecisionContext (..))
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

---

## Template B — Projection (query combine)

Grounded in `testbed/src/Testbed/Cart/Queries/CartSummary.hs` and
`core/service/Service/Query/Core.hs`. Replace `CartSummary` / `CartEntity`
with your query and entity names.

```haskell
-- tests/Projection/CartSummarySpec.hs
module Projection.CartSummarySpec where

import Array qualified
import Core
import Service.Query.Core (QueryAction (..), QueryOf (..))
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
Import `QueryAction (..)` and `QueryOf (..)` from `Service.Query.Core`.

---

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
for counting. The wildcard branch in `handleEvent` must return `Integration.none`
(never `panic "TODO"` — see stub rule below).

---

## DO / DON'T

| Vanilla-Haskell reflex (wrong) | NeoHaskell-correct (right) | Why |
|---|---|---|
| `import Test.Hspec` | `import Test` | The project testlib re-exports everything: `Spec`, `it`, `describe`, `shouldBe`, `fail` |
| `spec :: IO ()` | `spec :: Spec Unit` | `Unit` not `()`; `Spec` is `Hspec.SpecWith` under the hood |
| `it "x" $ do ...` | `it "x" \\_ctx -> do ...` | `it` takes a `context -> Task Text Unit` lambda; `$` is not NeoHaskell |
| `shouldBe actual expected` (Hspec argument order) | `actual |> shouldBe expected` | NeoHaskell's `shouldBe` takes **expected first**, actual second — the reverse of vanilla Hspec. The pipe form makes this natural |
| `/=` | `!=` | NeoHaskell inequality operator |
| `pure unit` / `return ()` as the **entry point** of a `Task` (i.e. the whole body of a function returning `Task`) | `Task.yield unit` | Inside a Task-do block `pure unit` is a valid continuation step and is fine; the smell is using `pure` *instead of* `Task.yield` when constructing the Task itself |
| Multiple `shouldBe` in one `it` block | One assertion per `it` | Enforces Given-When-Then discipline; the outside-in TDD phase boundary check flags multi-assert tests |
| `panic "TODO: not implemented"` inside outbound `handleEvent` | `Integration.none` + a `-- TODO:` comment | A `panic` in a pure handler crashes the live event dispatcher when that event fires; `Integration.none` is safe |
| `Decider.accept [e]` (invented constructor) | `Decider.acceptNew [e]`, `Decider.acceptExisting [e]`, or `Decider.acceptAny [e]` | These are the real smart constructors; no bare `accept` exists |
| `describe "x" (do ...)` with parens | `describe "x" do ...` | BlockArguments is a default extension |

---

## Verify

```
neo build    # must compile (even with panic stubs in decide/combine; handleEvent wildcard must use Integration.none, not panic — see stub rule above)
neo test     # spec must FAIL (RED) until implement-* fills in the logic
```

Both commands require Nix. Assumes
**[neohaskell/neo#2](https://github.com/neohaskell/neo/issues/2)** (test-suite
stanza generation) is in place so `neo test` runs the generated Hspec suite.
