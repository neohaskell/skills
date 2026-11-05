# Register commands, queries, and integrations

Use only the branch needed by the task. Resolve the application revision and capabilities through [nh-app-context](../../nh-app-context/SKILL.md) before adapting API examples. The existing consumer layout and compatible API guide determine the actual imports, markers, and commands.

## Step 1 — Register commands in Service.hs

Each bounded context has its own `Service.hs` that lists the commands it handles.
Add one `Service.command @Cmd` call per new command. The type application `@Cmd`
is how the framework discovers the command's `decide` function, entity type, and
HTTP transport.

A new **command** is wired **only here** — it needs no `App.hs` edit. Only new
**queries** (`withQuery @Q`) and **integrations** (`withOutbound @I` and friends)
touch `App.hs` (Step 2).

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

`service :: Service _ _` is a **partial type signature** — the `_`s are filled by
inference, which is allowed because `-fno-warn-partial-type-signatures` is on
project-wide. It will **not infer with zero commands**: an empty `Service.new`
leaves the type variables ambiguous and fails to compile, so a context always
needs at least one `Service.command @X`.

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

### Zero-domain app is valid

An app with **no domain at all** compiles and runs. After removing the `Counter`
starter, an `App.hs` whose wiring is just
`withConfig |> withEventStore |> withTransport` — with no `withService` and no
`withQuery` — compiles and runs. Useful when clearing the starter before adding
your first context.

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

