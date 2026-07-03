---
name: implement-integration
description: >-
  Implements NeoHaskell INTEGRATION modules under Integrations/ for a context, in the GREEN
  phase when a verified integration node (outbound or inbound) needs code. Covers three
  patterns: outbound per-trigger (nullary marker type, EntityOf instance, pure handleEvent,
  outboundIntegration macro, stubbed with Integration.none plus a TODO); inbound timer or
  webhook via Integration.Inbound and Integration.Timer; and stateful lifecycle outbound via
  withOutboundLifecycle. Use when asked to fire a cross-aggregate command from an event,
  wire a periodic timer, add a stateful worker, run a real side effect (decode the event and
  shell out via Subprocess), or safely stub an outbound handler. Never panic inside
  handleEvent — use Integration.none. Do NOT use for a command's decide
  (implement-command), event payload (implement-event-and-update-entity), query/combine
  (implement-query), or registering the integration in App.hs (wire-feature). This is
  NeoHaskell — IO, Either, pure, and dollar-sign application are all wrong here.
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

**Decision rule — command vs. real side effect (read this first):**

- **Emit a cross-aggregate command → Template 1 (pure).**
  `Integration.batch [ Integration.outbound Command.Emit { command = … } ]`.
- **Do a real side effect (run `git worktree add`, POST to an API, watch a
  file) → Template 5 (decode the event + shell out).** A lifecycle
  `processEvent :: state -> Event Json.Value -> Task Text (Array CommandPayload)`
  that decodes the payload and runs the effect. (Template 4 is the minimal
  stateful worker; Template 5 is the real, event-decoding side effect.)

A real side effect **cannot** live in a per-trigger outbound `handleEvent`: its
type `Entity -> Event -> Integration.Outbound` is **pure** and can only emit
commands. If you find yourself wanting `IO`/`Task`/a shell call in `handleEvent`,
you picked the wrong template — move it to Template 4.

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
      -- TODO: send notification or other side-effecting work.
      Task.yield []

  , cleanup = \state -> do
      Console.print [fmt|[LoanNotifier] Worker done for: #{state.memberId}|]
  }
```

`initialize` returns the initial state wrapped in `Task`. `processEvent` has type
`state -> Event Json.Value -> Task Text (Array Integration.CommandPayload)` — the
element type is the framework wrapper `Integration.CommandPayload`, not a raw
command. Lifecycle `processEvent` is for side-effecting work (incrementing
counters, sending notifications, writing to external stores); the testbed
`EventCounter` just returns `Task.yield []` without touching the payload. For a
**real** side effect that decodes the event and shells out, see **Template 5**.
Cross-aggregate command dispatch belongs in a per-trigger outbound handler
(Template 1), not in a lifecycle `processEvent`. `cleanup` runs when the worker is
reaped; it returns `Task Text Unit`.

---

## Template 5 — Real outbound side effect (Subprocess: decode the event + shell out)

Templates 1 and 4 never touch the event *payload* — Template 1's `handleEvent` is
pure, and the Template 4 counter returns `Task.yield []` without decoding. A
**real** side effect (run `git worktree add`, POST to an API) must (a) decode the
triggering `Event Json.Value` into your typed event ADT, (b) act on a specific
variant, and (c) run the effect — all inside a lifecycle `processEvent`. Every
signature below is grounded in NeoHaskell source (file:line in the comments).

```haskell
-- src/App/Context/Integrations/GitWorktreeProvisioner.hs
module App.Context.Integrations.GitWorktreeProvisioner (
  gitWorktreeProvisioner,
) where

import Array qualified
import Core
import Integration qualified                        -- Integration.CommandPayload
import Integration.Lifecycle qualified as Lifecycle  -- Lifecycle.OutboundConfig
import Json qualified                               -- Json.decode :: Json.Value -> Result Text a
import Path qualified                               -- Path.fromText :: Text -> Maybe Path
import Service.Event (Event)                        -- the Event record; theEvent.event :: Json.Value
import Subprocess qualified                         -- Subprocess.run / .Error / .Completion
import Task qualified                               -- Task.yield / .throw / .mapError
import App.Context.Core (WorktreeEvent (..))        -- your event ADT (derives FromJSON)


-- | processEvent :: state -> Event Json.Value -> Task Text (Array Integration.CommandPayload)
--   (Integration.Lifecycle.OutboundConfig, core/service/Integration/Lifecycle.hs:74)
processEvent :: Unit -> Event Json.Value -> Task Text (Array Integration.CommandPayload)
processEvent _state theEvent =
  -- theEvent.event :: Json.Value                        (core/service/Service/Event.hs:33)
  -- Json.decode :: Json.Value -> Result Text WorktreeEvent  (core/json/Json.hs:71)
  --   — a RESULT (Ok/Err), NOT the bare event; your ADT derives FromJSON.
  case Json.decode theEvent.event of
    Err _ -> Task.yield Array.empty                      -- undecodable / unrelated → no effect
    Ok decoded -> case decoded of
      WorktreeCreated {repoPath, worktreePath, branch} -> do
        -- Path.fromText :: Text -> Maybe Path            (core/system/Path.hs:47)
        dir <- case Path.fromText repoPath of
          Nothing   -> Task.throw [fmt|Invalid repo path: #{repoPath}|]
          Just aDir -> Task.yield aDir
        -- Subprocess.run :: Text -> Array Text -> Path -> Task Subprocess.Error Subprocess.Completion
        --   (core/system/Subprocess.hs:83). Task.mapError bridges Subprocess.Error → the
        --   Text error channel processEvent requires (core/core/Task.hs:89).
        _completion <-
          Subprocess.run "git" ["worktree", "add", "-b", branch, worktreePath] dir
            |> Task.mapError (\err -> [fmt|git worktree add failed: #{err}|])
        Task.yield Array.empty                            -- pure side effect, no follow-up command
      _ -> Task.yield Array.empty                         -- other variants: nothing to do


-- Stateless config (state = Unit). Field types: Lifecycle.hs:68/74/83.
gitWorktreeProvisioner :: Lifecycle.OutboundConfig Unit
gitWorktreeProvisioner =
  Lifecycle.OutboundConfig
    { initialize   = \_streamId -> Task.yield unit
    , processEvent = processEvent
    , cleanup      = \_state -> Task.yield unit
    }
```

Wire it (see **Wiring in App.hs** below):
`Application.withOutboundLifecycle @() @WorktreeEntity (\_ -> gitWorktreeProvisioner)`.

**Exact primitives (so no source grep is ever needed):**

| Need | API (grounded) |
|---|---|
| The event payload | `Event { entityName :: EntityName, streamId :: StreamId, event :: eventType, metadata :: EventMetadata }` (`Service.Event`). In `processEvent`, `theEvent.event :: Json.Value`; `theEvent.entityName` identifies the source entity. |
| Decode payload → typed event | `Json.decode :: (FromJSON a) => Json.Value -> Result Text a` (`Json.hs:71`). Returns a **`Result`** — match `Ok`/`Err`; do **not** expect the bare event. |
| Run a command | `Subprocess.run :: Text -> Array Text -> Path -> Task Subprocess.Error Subprocess.Completion`; `Completion { exitCode :: Int, stdout :: Text, stderr :: Text }`. Also `which`, `runWithTimeout` (timeout `Int` is its **first** arg), `open`. |
| Working-dir `Path` | `Path.fromText :: Text -> Maybe Path` (`Path.hs:47`). |
| Error channel | `Subprocess.Error = ProcessError Text \| TimeoutError Text \| ToolNotFound Text` (Show, Eq). `processEvent` is `Task Text …`, so bridge with `Task.mapError` (`Task.hs:89`). |
| No follow-up command | return `Array.empty :: Array Integration.CommandPayload`. To emit one, build it with `Integration.makeCommandPayload yourCommand`. |
| Wire it | `Application.withOutboundLifecycle @() @WorktreeEntity (\_ -> provisioner)`. |

> **⚠️ `Subprocess.run` does not fail on a non-zero exit code.** It returns a
> `Completion` even when `git` exits non-zero, and only fails the `Task` on
> spawn/IO errors (e.g. the tool is missing). If a non-zero exit should be an
> error, inspect `_completion.exitCode` yourself and `Task.throw`. Also: the wired
> entity type (`WorktreeEntity`) needs a `TypeName.Inspectable` instance, and the
> `@()` config form is required for `Application.runWith`.

### Testing a real side effect — NOT with `Test.AppSpec`

**`Test.AppSpec` is currently a structural spec-*builder* skeleton, not a runner —
do not reach for it to test integrations.** On the pinned toolchain, `verifyAppSpec`
is wired to `panic "verifyScenario: not implemented"` and crashes on any non-empty
spec, and the scenario combinators (`given`, `expect`, `and`, `receivedCommand`,
`registeredEvent`, `executedTask`) are all `panic "… not implemented"`
(`core/testlib/Test/AppSpec/*`). The only thing that works today is building an
`AppSpec` record with `specificationFor`/`scenario` and comparing it via `shouldBe`;
nothing executes an app, dispatches a command, or mocks/captures a task. It does
**not** "run the app with integrations mocked." Treat the
`given → expect … executedTask` surface as aspirational/WIP.

So test a real side effect at the layers that *do* run:

- **Keep the side effect thin; unit-test the pure part directly.** Factor decoding +
  variant selection into a pure helper (e.g. `Event Json.Value -> Maybe GitPlan`) and
  unit-test that with sample payloads (`write-unit-tests`). Assert the *intent* — the
  decoded plan / the exact args you would pass to `git` — not the OS effect.
- **Hurl smoke for the real spawn** (`write-hurl-e2e`): drive the command that emits
  the triggering event against the running app and assert the observable outcome (the
  worktree exists, the endpoint reports it). This is the only end-to-end coverage of
  the actual process spawn.

---

## Wiring in App.hs

After writing the integration file, `wire-feature` adds the registration to
`App.hs`. The three patterns correspond to the three templates:

```haskell
-- Template 1: per-trigger outbound (one line per handler type)
|> Application.withOutbound @ReserveStockOnItemAdded

-- Template 3: inbound timer (factory lambda; @() = no config dependency)
|> Application.withInbound @() (\_ -> periodicCartCreator)

-- Template 4 / Template 5: lifecycle outbound (factory lambda; @() @CartEntity = config + entity type)
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
