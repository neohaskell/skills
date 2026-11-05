# Build actions in a pure per-trigger handler

Use only the branch needed by the task. Resolve the application revision and capabilities through [nh-app-context](../../nh-app-context/SKILL.md) before adapting API examples. The existing consumer layout and compatible API guide determine the actual imports, markers, and commands.

## Template 1 — Outbound per-trigger

One handler type per event trigger. The marker is a **nullary data type** (no
fields). `handleEvent` is **pure** — no `IO`, no `Task`, no HTTP calls.
Cross-aggregate commands are emitted via `Integration.outbound Command.Emit`.

Grounded in `Testbed.Cart.Integrations.ReserveStockOnItemAdded` (public testbed).
Adapt `App`, `Context`, entity, event, and emitted command names to your domain.

```haskell
-- src/Testbed/Cart/Integrations/ReserveStockOnItemAdded.hs
-- Not under Commands/Events/Queries/ so this file is NOT locked by neo lock.
module Testbed.Cart.Integrations.ReserveStockOnItemAdded (
  ReserveStockOnItemAdded (..),
  handleEvent,
) where

import Core
import Integration qualified
import Integration.Command qualified as Command
import Service.OutboundIntegration.TH (outboundIntegration)
import Testbed.Cart.Core (CartEntity (..), CartEvent (..))
import Testbed.Stock.Commands.ReserveStock (ReserveStock (..))


-- | Nullary marker — no fields. One type per trigger.
data ReserveStockOnItemAdded = ReserveStockOnItemAdded
  deriving (Generic, Typeable, Show)


type instance EntityOf ReserveStockOnItemAdded = CartEntity


-- | Pure — no IO, no Task. Must be total: the wildcard _ -> Integration.none
-- handles every event variant this handler does not act on. Omitting the
-- wildcard makes handleEvent non-exhaustive and crashes the dispatcher.
handleEvent :: CartEntity -> CartEvent -> Integration.Outbound
handleEvent cart event =
  case event of
    ItemAdded {stockId, quantity} ->
      Integration.batch
        [ Integration.outbound
            Command.Emit
              { command =
                  ReserveStock
                    { stockId = stockId
                    , quantity = quantity
                    , cartId = cart.cartId
                    }
              }
        ]
    _ -> Integration.none


outboundIntegration ''ReserveStockOnItemAdded
```

**Naming convention:** `<Verb><TargetEntity>On<TriggeringEvent>`, for example
`ReserveStockOnItemAdded`, `SendEmailOnOrderPlaced`, `NotifyMemberOnLoanOverdue`.

**Import note on `Core.hs`:** The testbed uses a legacy combined `Core.hs`
(`Testbed.Cart.Core` holds both `CartEntity` and `CartEvent` in one file). In a
fresh NeoHaskell project the thin-barrel layout is preferred — `Core.hs` only
re-exports from `Entity.hs` and `Event.hs`. Either way, import the context's
`Core` barrel: `import App.Context.Core (AppEntity (..), AppEvent (..))`.

---


## Template 2 — Stub (DOMAIN phase or unbuilt trigger)

During the DOMAIN phase `neohaskell-domain-modeling` creates the file with a
safe stub. For `handleEvent`, the correct stub is `Integration.none` with a
`-- TODO:` comment — **not `panic`**. A `panic` in a pure `handleEvent` crashes
the dispatcher the moment the matching event is replayed.

```haskell
-- DOMAIN-phase stub — safe to compile and run; fails only on the unit test
-- assertion, not on a runtime crash.
handleEvent :: CartEntity -> CartEvent -> Integration.Outbound
handleEvent _cart _event =
  -- TODO: implement reservation logic
  Integration.none
```

For `Task` or plain `IO`-equivalent function bodies elsewhere, use
`panic "TODO: not implemented"`. The two conventions differ because `handleEvent`
is **pure and called by the framework on every event in the stream**.

---

