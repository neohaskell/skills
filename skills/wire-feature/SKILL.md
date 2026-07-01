---
name: wire-feature
description: >-
  Registers already-implemented NeoHaskell modules as LIVE HTTP endpoints in the GREEN phase
  — step 6 that flips the outer hurl e2e from 404 to the expected response. Use AFTER
  implement-command / implement-event-and-update-entity / implement-query / implement-
  integration produced compiling modules, or when asked to 'wire up', 'register a command',
  'add an endpoint', 'make a query reachable', 'connect an integration', or 'add withService
  to App.hs', or when hitting a missing EntityOf/instance error at a Service.command call
  site. Covers Service.hs (Service.new, Service.command @Cmd), App.hs (withService /
  withQuery @Q / withOutbound @H / withInbound @Config / withOutboundLifecycle), the
  instance-only import pattern (import Context.Core ()), and multi-context Service barrels.
  Do NOT use to write the decide/combine/handleEvent logic (the implement-* skills) or the
  tests (write-* skills). After this, neo inspect wiring lists the endpoints.
metadata:
  model: sonnet
---

**This is NeoHaskell, not vanilla Haskell.** The `.hs` extension is shared, but
NeoHaskell runs a custom `Core` prelude — `import Core`, not `import Prelude`.
Every identifier and wiring call in this skill is grounded in the public testbed
sources (`Testbed.Cart.Service`, `Testbed.Stock.Service`, `testbed/src/App.hs`).

---

## TDD cycle role — GREEN phase (step 6)

This skill runs in **step ⑥ (GREEN)** of the outside-in cycle, immediately after
the implement-* skills have produced compiling modules:

```
write-hurl-e2e (RED outer, 404) →
  write-feature-tests (RED) →
    write-unit-tests (RED) →
      neohaskell-domain-modeling (DOMAIN) →
        implement-command / event / query / integration (GREEN, bodies) →
          ► wire-feature (GREEN, endpoint live) ◄
            refactor + write-feature-tests / property
```

Wiring is the step that moves the outer hurl test from 404 to the expected
response. In Claude Code, you may delegate this step to a sub-agent spawned with
`model: sonnet`; in Cursor or Codex this is advisory and runs inline.

---

## Inputs / Outputs / Next

- **Input:** the compiling command, event, query, and integration modules produced
  by the implement-* skills.
- **Output:** edited `Service.hs` (commands registered) and edited `App.hs`
  (service, queries, and integrations registered).
- **Next:** `write-unit-tests` (Decider/Projection/Outbound specs go green) ·
  `write-feature-tests` (acceptance spec goes green) · `write-hurl-e2e` (outer
  hurl goes green at `POST /commands/create-counter`)

---

## Step 1 — Register commands in Service.hs

Each bounded context has its own `Service.hs` that lists the commands it handles.
Add one `Service.command @Cmd` call per new command. The type application `@Cmd`
is how the framework discovers the command's `decide` function, entity type, and
HTTP transport.

Grounded in `Testbed.Cart.Service` and `Testbed.Stock.Service` (public testbed).
Replace `Starter`, `Counter`, and command names for your domain.

```haskell
-- src/Starter/Counter/Service.hs
module Starter.Counter.Service (
  service,
) where

import Core
import Service qualified
import Starter.Counter.Commands.CreateCounter (CreateCounter)
import Starter.Counter.Commands.IncrementCounter (IncrementCounter)
import Starter.Counter.Core ()


service :: Service _ _
service =
  Service.new
    |> Service.command @CreateCounter
    |> Service.command @IncrementCounter
```

The `import Starter.Counter.Core ()` is an **instance-only import** — it brings
the `Entity`, `Event`, `EntityOf`, and `EventOf` instances into scope without
importing any names. Without it, `Service.command @CreateCounter` fails because
the framework cannot resolve the `EntityOf CreateCounter` instance. See the
instance-only import section below.

`Service.hs` contains **only registration calls** — no logic, no `Config.get`,
no HTTP handling. It is a pure descriptor.

---

## Step 2 — Register in App.hs

`App.hs` is the top-level application builder. Append one line per new item:
`withService` for the context service, `withQuery @Q` for each query, and the
appropriate integration call.

### Single-context app (most projects)

Import the context service module directly — do **not** create an aggregating
barrel when there is only one context.

```haskell
-- src/App.hs
module App (app) where

import Core
import Service.Application (Application)
import Service.Application qualified as Application
import Service.Transport.Web qualified as WebTransport
import Starter.Counter.Core ()
import Starter.Counter.Integrations (periodicCounterCreator)
import Starter.Counter.Integrations.NotifyOnThreshold (NotifyOnThreshold)
import Starter.Counter.Queries.CounterSummary (CounterSummary)
import Starter.Counter.Service qualified as Counter


app :: Application
app =
  Application.new
    |> Application.withTransport WebTransport.server
    |> Application.withService Counter.service
    |> Application.withQuery @CounterSummary
    |> Application.withOutbound @NotifyOnThreshold
    |> Application.withInbound @() (\_ -> periodicCounterCreator)
```

### Integration wiring variants

Each integration pattern maps to its own `with*` call. Choose the one that
matches the integration kind your `implement-integration` produced:

```haskell
-- Outbound per-trigger (most common): one line per handler type.
-- Grounded in testbed/src/App.hs withOutbound @ReserveStockOnItemAdded.
|> Application.withOutbound @NotifyOnThreshold

-- Inbound timer or webhook: factory lambda; @() = no config dependency.
-- Grounded in testbed/src/App.hs withInbound @() (\_ -> periodicCartCreator).
|> Application.withInbound @() (\_ -> periodicCounterCreator)

-- Lifecycle outbound (stateful worker): @Config @Entity factory.
-- Grounded in testbed/src/App.hs withOutboundLifecycle @() @CartEntity.
|> Application.withOutboundLifecycle @() @CounterEntity (\_ -> counterLifecycleIntegration)
```

Replace `@()` with `@YourConfig` if the integration reads from application
config. The lambda receives the config value after `Application.run` loads it —
this is the factory pattern that avoids reading config at wiring time.

---

## Step 3 — Aggregating Service barrel (multi-context only)

Create a top-level `src/<App>/Service.hs` barrel **only when the app has more
than one bounded context** (as in the testbed, which has Cart, Stock, and
Document). For a single-context app, skip this step and import the context
service directly in `App.hs` (as shown above).

Grounded in `testbed/src/Testbed/Service.hs` (public testbed):

```haskell
-- src/Starter/Service.hs  -- ONLY for multi-context apps
module Starter.Service (
  counterService,
  stockService,
) where

import Starter.Counter.Service qualified as CounterService
import Starter.Stock.Service qualified as StockService


counterService :: _
counterService = CounterService.service


stockService :: _
stockService = StockService.service
```

Then in `App.hs`, reference the aggregating barrel:

```haskell
import Starter.Service qualified

app :: Application
app =
  Application.new
    |> Application.withTransport WebTransport.server
    |> Application.withService Starter.Service.counterService
    |> Application.withService Starter.Service.stockService
    |> Application.withQuery @CounterSummary
    |> Application.withQuery @StockLevel
    ...
```

---

## Instance-only imports

Any module that references a command, query, or integration type needs the
context's `Core` barrel in scope for its type-class instances. The instance-only
import pattern is:

```haskell
import Starter.Counter.Core ()   -- instances only; no names imported
```

Without this import, GHC cannot resolve `EntityOf CreateCounter` or
`EventOf CounterEntity` at the `Service.command @CreateCounter` call site, and
you will see an error like:

```
No instance for (EntityOf CreateCounter)
```

Add `import <App>.<Context>.Core ()` in **both** `Service.hs` and `App.hs`.
The `()` explicit import list suppresses the "unused import" warning while still
making all instances visible.

---

## DO / DON'T

| Vanilla-Haskell reflex -- DON'T | NeoHaskell-correct -- DO | Why |
|---|---|---|
| `Application.withQuery CounterSummary` (missing @) | `Application.withQuery @CounterSummary` | The type application `@Q` is required; passing the constructor is a type error |
| `Application.withService Counter` where `Counter` is the entity module | `import Starter.Counter.Service qualified as Counter` then `Counter.service` | `withService` takes the service value, not a module or type |
| `let cfg = Config.get @CounterConfig` inside the `app` wiring chain | Factory lambda: `Application.withInbound @CounterConfig (\cfg -> ...)` | `Config.get` panics before `Application.run` loads the config; the factory is called after |
| Skip `import Starter.Counter.Core ()` in Service.hs | Always add the instance-only import | Missing instances cause a `No instance for EntityOf` compile error at the `Service.command` call |
| Create an aggregating Service barrel for a single-context app | Import the context service module directly in `App.hs` | An extra barrel adds indirection with no benefit; only needed when two or more contexts share an App.hs |
| Add logic or `Config.get` inside `Service.hs` | `Service.hs` contains only `Service.new |> Service.command @Cmd` calls | `Service.hs` is a pure registration descriptor; all logic lives in `Commands/`, `Queries/`, `Integrations/` |
| `import Prelude` or no `import Core` | `import Core` first in every module | `NoImplicitPrelude` is on project-wide; without `import Core`, basic types like `Text`, `Uuid`, and `Array` are not in scope |
| `|> Application.withOutbound ReserveStockOnItemAdded` (value, not type) | `|> Application.withOutbound @ReserveStockOnItemAdded` | `withOutbound` takes a type application; passing a value is a type error |
| `Service.new $ Service.command @CreateCounter` | `Service.new |> Service.command @CreateCounter` | NeoHaskell uses `|>` (pipe forward); `$` is not in scope from `Core` |
| Use `$` or `.` between wiring calls | `|>` for forward pipe, `.>` for forward function composition | `$` and `.` are vanilla Haskell operators not re-exported by `Core` |

---

## Verify

```
neo build
```

A successful build confirms all `Service.command @Cmd` calls resolved (entity and
transport instances found), all `withQuery @Q` calls resolved (`QueryOf` and
`ToSchema` instances present), and all `withOutbound @H` calls resolved
(`OutboundIntegration H` instance generated by the `outboundIntegration` macro).

Confirm endpoints are live:

```
neo inspect wiring
```

Each registered command appears as `POST /commands/<kebab-name>` and each query
as `GET /queries/<kebab-name>`. If an endpoint is absent, check that `Service.hs`
includes the matching `Service.command @Cmd` call and that `App.hs` includes
`Application.withService`.

Common compile errors after wiring:

| Error | Cause | Fix |
|---|---|---|
| `No instance for (EntityOf CreateCounter)` | Missing `import Starter.Counter.Core ()` in Service.hs | Add the instance-only import |
| `Couldn't match type 'Application' with '...'` | Missing `@` in `withQuery Q` or `withOutbound H` | Change to `withQuery @Q` / `withOutbound @H` |
| `Variable not in scope: counterService` | Service module not imported in App.hs | Add `import Starter.Counter.Service qualified as Counter` |
| `No instance for (OutboundIntegration NotifyOnThreshold)` | The `outboundIntegration ''NotifyOnThreshold` macro is missing from the integration module | See `implement-integration` — the macro must close the integration module |
