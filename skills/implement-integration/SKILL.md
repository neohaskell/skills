---
name: implement-integration
description: >-
  Implements NeoHaskell integration modules under Integrations/ for a context.
  Use in the GREEN phase of the outside-in TDD cycle when a verified integration
  node (kind: outbound or inbound) needs code. Covers three patterns: (1)
  outbound per-trigger -- a nullary marker type, EntityOf instance, pure
  handleEvent, and the outboundIntegration macro, stubbed with Integration.none
  plus a TODO comment when unbuilt; (2) inbound timer or webhook via
  Integration.Inbound and Integration.Timer; (3) stateful lifecycle outbound via
  withOutboundLifecycle. Also use when asked to fire a cross-aggregate command
  from an event, wire a periodic timer, add a stateful worker, or stub an
  outbound handler safely. Never panic inside handleEvent -- that crashes the
  dispatcher on every matching event; use Integration.none instead. This is
  NeoHaskell -- the reader defaults to IO, Either, pure, and dollar-sign
  application; all of those are wrong here.
metadata:
  model: sonnet
---

**This is NeoHaskell, not vanilla Haskell.** The `.hs` extension is shared, but
NeoHaskell uses a custom `Core` prelude — `import Core`, not `import Prelude`.
Every identifier and macro in this skill is grounded in the public testbed
sources (`Testbed.Cart.Integrations.ReserveStockOnItemAdded`,
`Testbed.Cart.Integrations.EventCounter`, `Testbed.Cart.Integrations`).

---

## TDD cycle role — GREEN phase

This skill runs in **step ⑤ (GREEN)** of the outside-in TDD cycle:

```
write-hurl-e2e (RED outer) →
  write-feature-tests (RED) →
    write-unit-tests (RED, Outbound spec) →
      neohaskell-domain-modeling (DOMAIN, types + Integration.none stubs) →
        ► implement-integration (GREEN, fill in handleEvent logic) ◄
          wire-feature (GREEN, withOutbound/withInbound registered)
```

The Outbound unit test must be RED (failing on the assertion, not a type error)
before you write real `handleEvent` logic here. In Claude Code you may delegate
the implementation step to a sub-agent with `model: sonnet`; in Cursor or Codex
this is advisory and the skill runs inline.

---

## Inputs / Outputs / Next

- **Input:** a verified integration node from `event-model.json`
  (`kind: outbound` or `kind: inbound`), the entity type, and the event ADT
  produced by `implement-event-and-update-entity`.
- **Output:** `src/<App>/<Context>/Integrations/<Handler>.hs` for each outbound
  trigger; or the inbound/lifecycle value in
  `src/<App>/<Context>/Integrations.hs`.
- **Next:** `wire-feature` (register with `withOutbound`, `withInbound`, or
  `withOutboundLifecycle` in `App.hs`) · `implement-command` (if the emitted
  cross-aggregate command is new) · `write-unit-tests` (Outbound spec)

---

## Three integration patterns

| Pattern | File | Closing macro / type |
|---|---|---|
| Outbound per-trigger | `Integrations/<Handler>.hs` | `outboundIntegration ''Handler` |
| Inbound (timer / webhook) | `Integrations.hs` or `Integrations/<Name>.hs` | Returns `Integration.Inbound` value |
| Lifecycle outbound (stateful) | `Integrations/<Name>.hs` | Returns `Lifecycle.OutboundConfig state` |

Choose **one** per node from the event model. Outbound triggers are the most
common; inbound and lifecycle are used when the event model has `kind: inbound`
or a stateful automation node.

---

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

## Template 3 — Inbound (Timer)

An inbound integration fires a command on a schedule or from a webhook. It
produces an `Integration.Inbound` value. There is no marker type and no macro;
the value is passed directly to `withInbound` in `App.hs`.

Illustrative example using the Library domain (structural pattern grounded in
`Testbed.Cart.Integrations.periodicCartCreator`, public testbed):

```haskell
-- src/Library/Integrations.hs
-- Illustrative: Library domain — check for overdue loans every 30 minutes.
module Library.Integrations (
  overdueChecker,
) where

import Integration qualified
import Integration.Timer qualified as Timer
import Library.Commands.CheckOverdueLoans (CheckOverdueLoans (..))


-- | Fires a CheckOverdueLoans command every 30 minutes.
-- The command must use InternalTransport (not WebTransport) since it is
-- emitted by the framework, not an HTTP client.
overdueChecker :: Integration.Inbound
overdueChecker =
  Timer.every Timer.Every
    { interval = Timer.seconds (30 * 60)
    , toCommand = \_ -> CheckOverdueLoans
    }
```

The testbed version uses `Timer.seconds 3` and `CreateCartInternal`. The
`toCommand` lambda receives a timer tick value and returns any command whose
`type instance TransportsOf Cmd = '[InternalTransport]`.

---

## Template 4 — Lifecycle outbound (stateful worker)

A lifecycle integration holds per-entity state across events — for example, a
connection pool, a gRPC channel, or a counter. It is wired with
`withOutboundLifecycle`, not `withOutbound`.

Illustrative example using the Library domain (structurally grounded in
`Testbed.Cart.Integrations.EventCounter`, public testbed):

```haskell
-- src/Library/Integrations/LoanNotifier.hs
-- Illustrative: Library domain — stateful per-member notification worker.
module Library.Integrations.LoanNotifier (
  loanNotifierIntegration,
  LoanNotifierState (..),
) where

import Console qualified
import Core
import Integration.Lifecycle qualified as Lifecycle
import Service.Event.StreamId qualified as StreamId
import Task qualified


-- | State held by each entity's worker for the lifetime of the worker process.
data LoanNotifierState = LoanNotifierState
  { memberId :: Text
  }
  deriving (Generic)


-- | Lifecycle config: initialize on first event, processEvent on each event,
-- cleanup when the worker is reaped after idle timeout.
loanNotifierIntegration :: Lifecycle.OutboundConfig LoanNotifierState
loanNotifierIntegration = Lifecycle.OutboundConfig
  { initialize = \streamId -> do
      let memberIdText = StreamId.toText streamId
      Console.print [fmt|[LoanNotifier] Starting worker for member: #{memberIdText}|]
      Task.yield LoanNotifierState { memberId = memberIdText }

  , processEvent = \state _event -> do
      -- TODO: send notification; return commands to emit, or [] for none.
      Task.yield []

  , cleanup = \state -> do
      Console.print [fmt|[LoanNotifier] Worker done for: #{state.memberId}|]
  }
```

`initialize` returns the initial state wrapped in `Task`. `processEvent` returns
`Task _ (Array cmd)` — emit cross-aggregate commands by including them in the
returned array, or `Task.yield []` for none. `cleanup` runs when the worker is
reaped; it returns `Task _ Unit`.

---

## Wiring in App.hs

After writing the integration file, `wire-feature` adds the registration to
`App.hs`. The three patterns correspond to the three templates:

```haskell
-- Template 1: per-trigger outbound (one line per handler type)
|> Application.withOutbound @ReserveStockOnItemAdded

-- Template 3: inbound timer (factory lambda; @() = no config dependency)
|> Application.withInbound @() (\_ -> periodicCartCreator)

-- Template 4: lifecycle outbound (factory lambda; @() @CartEntity = config + entity type)
|> Application.withOutboundLifecycle @() @CartEntity (\_ -> EventCounter.eventCounterIntegration)
```

Grounded in `App.hs` (public testbed). Replace `@()` with `@YourConfig` if the
integration reads from application configuration.

---

## DO / DON'T

| Vanilla-Haskell reflex — DON'T | NeoHaskell-correct — DO | Why |
|---|---|---|
| `panic "TODO: not implemented"` inside `handleEvent` | `Integration.none` + a `-- TODO:` comment | `handleEvent` is pure and called on every matching event; a `panic` crashes the dispatcher immediately when any event fires |
| `IO a` or `Task err a` inside `handleEvent` | Keep `handleEvent` pure; effectful work goes in the `ToAction` instance (framework-internal, not user-land) | The type `Entity -> Event -> Integration.Outbound` is fully pure |
| `data Handler = Handler { someField :: Text }` | `data Handler = Handler deriving (Generic, Typeable, Show)` — nullary, no fields | The marker is just a tag; all data comes from the entity and event arguments |
| Hand-write an `OutboundIntegration` class instance | Close the module with `outboundIntegration ''Handler` | The TH macro generates the registration boilerplate; writing it by hand is error-prone and may diverge |
| Omit the `_ -> Integration.none` wildcard | Always include `_ -> Integration.none` as the last case | A non-exhaustive `handleEvent` triggers a GHC warning and a runtime error on an unexpected event variant |
| `import Core` only, then use `Integration` unqualified | `import Integration qualified` and `import Integration.Command qualified as Command` | `Integration` is not re-exported by `Core`; `Command.Emit` lives in `Integration.Command` |
| `todo` as a stub | No `todo` exists in NeoHaskell | Use `Integration.none` for `handleEvent` stubs; `panic "TODO: not implemented"` for `Task`/pure function stubs elsewhere |
| `_ -> error "unhandled event"` | `_ -> Integration.none` | `error` terminates the process; `Integration.none` is the correct no-op |
| Emit commands as a plain list `[ReserveStock {..}]` | `Integration.batch [ Integration.outbound Command.Emit { command = ReserveStock {..} } ]` | The framework expects `Integration.Outbound`, not a raw list |
| `String` fields or `[Char]` in state types | `Text` fields, `import Core` | `NoImplicitPrelude` is on project-wide; `String` is `[Char]` and is not the NeoHaskell string type |
| `<>` for text concatenation | `++` or `[fmt|...#{expr}...|]` | NeoHaskell uses `++` (Appendable) and `fmt` quasi-quotes; `<>` is a review smell |
| `fmap f xs` / `<$>` | `Array.map f xs` or `Task.map f t` | Generic `fmap` compiles but is a review smell; use the type-specific form |
| `import Service.AccessControl (RequestContext)` | `import Service.Auth (RequestContext)` | `RequestContext` lives in `Service.Auth`; `Service.AccessControl` exports `AccessError`, `UserClaims`, `publicAccess` |

---

## Verify

```
neo build
```

A successful build confirms:

- `outboundIntegration ''ReserveStockOnItemAdded` resolves and generates the
  `OutboundIntegration` instance (no `No instance for OutboundIntegration`).
- `type instance EntityOf` is accepted without orphan-instance warnings.
- `handleEvent` is total — GHC exhaustiveness check passes (all event variants
  are covered by the wildcard `_ -> Integration.none`).
- No `IO` or `Task` appears inside `handleEvent`.

**Common errors:**

- `outboundIntegration not in scope` — add
  `import Service.OutboundIntegration.TH (outboundIntegration)`.
- `EntityOf not in scope` — it is re-exported by `Core`; no extra import needed.
- `Integration.Outbound not in scope` — add `import Integration qualified`.
- `Command.Emit not in scope` — add
  `import Integration.Command qualified as Command`.
