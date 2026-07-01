---
name: implement-command
description: >-
  Implements a NeoHaskell COMMAND module at Commands/Name.hs — the record, getEntityId, a
  three-argument decide function, EntityOf and TransportsOf type instances, and the command
  TH macro. Use in the GREEN phase after neohaskell-domain-modeling stubbed the types and
  write-unit-tests left a failing Decider spec. Also use when asked to add a command,
  implement or fill in decide logic, replace a decide panic stub, handle a verified command
  node, or distinguish a create command (getEntityId Nothing, acceptNew) from an update
  command (getEntityId Just, acceptExisting). Do NOT use for the EVENT payload module or
  entity update fold (implement-event-and-update-entity), the query/combine module
  (implement-query), the integration handler (implement-integration), or registering the
  endpoint (wire-feature). This is NeoHaskell — the reader defaults to IO, pure, Either, and
  dollar-sign application; all of those are wrong here.
metadata:
  model: sonnet
---

**This is NeoHaskell, not vanilla Haskell.** The `.hs` extension is shared, but NeoHaskell runs a custom `Core` prelude — `import Core`, not `import Prelude`. Every identifier, operator, and module name in this skill is grounded in the public Counter test-project source.

---

## TDD cycle role — GREEN phase

This skill runs in **step ⑤ (GREEN)** of the outside-in cycle:

```
write-hurl-e2e (RED outer) →
  write-feature-tests (RED) →
    write-unit-tests (RED, Decider spec) →
      neohaskell-domain-modeling (DOMAIN, types + panic stubs) →
        ► implement-command (GREEN, fill in decide logic) ◄
          wire-feature (GREEN, endpoint live)
```

The Decider unit test must be RED (failing on the assertion, not a type error) before you write this file. The `decide` body you write here should make it go green.

In Claude Code, you may delegate the implementation step to a sub-agent spawned with `model: sonnet`. In Cursor or Codex this is advisory — run it inline.

---

## Inputs / Outputs / Next

- **Input:** a verified command node from `event-model.json` (name, entity, fields, create-vs-update intent) and the matching event payload(s) from `implement-event-and-update-entity`.
- **Output:** `src/<App>/<Context>/Commands/<Name>.hs` with a compiling, test-passing `decide`.
- **Next:** `write-unit-tests` (Decider spec goes green) · `implement-event-and-update-entity` (event payloads the command emits) · `wire-feature` (register the command in `Service.hs`)

---

## Create vs update — the only decision you make first

| Pattern | `getEntityId` returns | `decide` accept constructor | When `entity` arg is |
|---|---|---|---|
| **Creation** — the entity does not exist yet | `Nothing` | `Decider.acceptNew [..]` | always `Nothing` (framework never loads) |
| **Update** — the entity must already exist | `Just cmd.entityId` | `Decider.acceptExisting [..]` | `Nothing` = reject "not found"; `Just existing` = proceed |

Generate a new id inside the `decide` `do` block with `Decider.generateUuid` — never pass a UUID in from outside for creation.

---

## Accept constructors carry a stream-state requirement

Each `Decider.accept*` constructor asserts a precondition on the event stream (from `core/service/Decider.hs`):

| Constructor | Stream-state requirement |
|---|---|
| `Decider.acceptNew [..]` | `StreamCreation` — the stream must **not** already exist |
| `Decider.acceptExisting [..]` | `ExistingStream` — the stream must already exist |
| `Decider.acceptAny [..]` | `AnyStreamState` — no precondition |
| `Decider.acceptAfter pos [..]` | optimistic concurrency — stream must be at expected position `pos` |

Consequence: a creation command whose `getEntityId` resolves to an **already-existing** stream cannot `acceptNew` — it would violate `StreamCreation`. So an entity whose id is a natural key can never be re-created once its stream exists (see *Natural-key identity* below).

---

## Template 1 — creation command (`CreateCounter`)

Grounded in the public `neo` test-project (`Starter.Counter.Commands.CreateCounter`). Adapt `App`, `Context`, `Cmd`, `Entity`, `Event`, and field names to your domain.

```haskell
-- src/Starter/Counter/Commands/CreateCounter.hs
-- [LOCKABLE once deployed — never edit; add CreateCounterV2.hs instead]
module Starter.Counter.Commands.CreateCounter (
  CreateCounter (..),
  getEntityId,
  decide,
) where

import Core
import Decider qualified
import Json qualified
import Service.Auth (RequestContext)
import Service.Command.Core (TransportsOf)
import Service.CommandExecutor.TH (command)
import Service.Transport.Web (WebTransport)
import Starter.Counter.Core
import Starter.Counter.Events.CounterCreated qualified as CounterCreated


data CreateCounter = CreateCounter
  { label :: Text
  }
  deriving (Generic, Typeable, Show)


instance Json.FromJSON CreateCounter


-- | Nothing => creation. The framework will NOT load an existing entity.
getEntityId :: CreateCounter -> Maybe Uuid
getEntityId _cmd = Nothing


decide :: CreateCounter -> Maybe CounterEntity -> RequestContext -> Decision CounterEvent
decide cmd _entity _ctx = do
  newId <- Decider.generateUuid
  Decider.acceptNew
    [ CounterCreated
        CounterCreated.Event
          { entityId = newId
          , label    = cmd.label
          }
    ]


type instance EntityOf CreateCounter = CounterEntity


type instance TransportsOf CreateCounter = '[WebTransport]


command ''CreateCounter
```

---

## Template 2 — update command (`IncrementCounter`)

Grounded in the public `neo` test-project (`Starter.Counter.Commands.IncrementCounter`). The update pattern differs in three ways: `getEntityId` returns `Just`, the `decide` case-splits on `entity`, and the accept constructor is `acceptExisting`.

```haskell
-- src/Starter/Counter/Commands/IncrementCounter.hs
-- [LOCKABLE once deployed — never edit; add IncrementCounterV2.hs instead]
module Starter.Counter.Commands.IncrementCounter (
  IncrementCounter (..),
  getEntityId,
  decide,
) where

import Core
import Decider qualified
import Json qualified
import Service.Auth (RequestContext)
import Service.Command.Core (TransportsOf)
import Service.CommandExecutor.TH (command)
import Service.Transport.Web (WebTransport)
import Starter.Counter.Core
import Starter.Counter.Events.CounterIncremented qualified as CounterIncremented


data IncrementCounter = IncrementCounter
  { entityId :: Uuid
  , amount   :: Int
  }
  deriving (Generic, Typeable, Show)


instance Json.FromJSON IncrementCounter


-- | Just => load the existing entity before decide is called.
getEntityId :: IncrementCounter -> Maybe Uuid
getEntityId cmd = Just cmd.entityId


decide :: IncrementCounter -> Maybe CounterEntity -> RequestContext -> Decision CounterEvent
decide cmd entity _ctx = case entity of
  Nothing ->
    Decider.reject "Counter not found"
  Just existing ->
    if cmd.amount <= 0
      then Decider.reject "Amount must be positive"
      else
        Decider.acceptExisting
          [ CounterIncremented
              CounterIncremented.Event
                { entityId = existing.counterId
                , amount   = cmd.amount
                }
          ]


type instance EntityOf IncrementCounter = CounterEntity


type instance TransportsOf IncrementCounter = '[WebTransport]


command ''IncrementCounter
```

---

## Natural-key identity — uniqueness by business key

`decide` cannot read other aggregates, so to enforce "no duplicate by business key `x`" (e.g. unique project name) do **not** generate a random id — derive the entity's stream id deterministically from `x`, so a second create resolves to the *same* stream:

`deriveId` here is **your own** helper — NeoHaskell has no built-in deterministic UUID in a pinned rev yet (pending neohaskell#596), so vendor `Data.UUID.V5` in one helper module and swap later; see `neohaskell-collections` (Uuid section).

```haskell
getEntityId :: RegisterProject -> Maybe Uuid
getEntityId cmd = Just (deriveId cmd.name)   -- deterministic from the natural key, NOT random

decide :: RegisterProject -> Maybe ProjectEntity -> RequestContext -> Decision ProjectEvent
decide cmd entity _ctx = case entity of
  Just _existing -> Decider.reject "A project with that name already exists"
  Nothing        ->                          -- stream absent → this is the first create
    Decider.acceptNew
      [ ProjectRegistered ProjectRegistered.Event { entityId = deriveId cmd.name, name = cmd.name } ]
```

`getEntityId` returns `Just` (so the framework loads that deterministic stream), but `entity` is still `Nothing` until the stream has events — so the first create legitimately `acceptNew`s (no stream yet), and every subsequent create sees `Just` and rejects. Request/response shape is identical to a generated-id create. See `neohaskell-domain-modeling` for the design write-up (choosing the key, deriving the id).

**Sharp edge:** because the id *is* the natural key, once the stream exists it can never be re-created (the `acceptNew`/`StreamCreation` requirement above) — even after "archiving" it. There is no "re-register as new"; reactivation must be a separate `acceptExisting` command (e.g. `Unarchive`) on the existing stream.

---

## DOMAIN-phase stub (before GREEN)

When `neohaskell-domain-modeling` creates the file and you need it to compile but not yet pass:

```haskell
decide :: IncrementCounter -> Maybe CounterEntity -> RequestContext -> Decision CounterEvent
decide _cmd _entity _ctx =
  panic "TODO: not implemented"
```

`panic` is the only correct stub for a pure function body. Do not use `pure`, `return`, or `undefined`. The Decider unit test will fail on the `panic`, which is the expected RED state.

---

## DO / DON'T

| Vanilla-Haskell reflex — DON'T | NeoHaskell-correct — DO | Why |
|---|---|---|
| `import Prelude` or no `import Core` | `import Core` first | `NoImplicitPrelude` is always on |
| `import Service.AccessControl (RequestContext)` | `import Service.Auth (RequestContext)` | `RequestContext` lives in `Service.Auth`; `Service.AccessControl` exports `AccessError`, `UserClaims`, `publicAccess` |
| `import Decider (Decision)` or `Decider.Decision` in the signature | `Decision` unqualified — it's re-exported by `Core` | Only the smart-constructors (`acceptNew`/`acceptExisting`/`reject`/`generateUuid`) are qualified `Decider.*`; the `Decision` return type itself comes from `Core` |
| `decide cmd entity ctx = pure [SomeEvent ..]` | `Decider.acceptNew [..]` or `Decider.acceptExisting [..]` | A `do` block or bare `pure` that ends without a `Decider.*` constructor throws at runtime |
| `decide cmd entity ctx = [SomeEvent ..]` | Always end in a `Decider.*` constructor | Returning a list directly is a type error |
| `IO a` inside `decide` | `decide` is pure — no `IO`, no `Task` | Commands run decide in a pure context |
| `getEntityId cmd = Just uuid` for creation | `getEntityId _cmd = Nothing` | Returning `Just` for creation tells the framework to load an entity that does not exist |
| `getEntityId _cmd = Nothing` for update | `getEntityId cmd = Just cmd.entityId` | Returning `Nothing` for an update means the framework will pass `Nothing` as the entity — your `case entity of Just e ->` will never match |
| `Decider.acceptNew` for an update | `Decider.acceptExisting` | `acceptNew` signals stream creation; `acceptExisting` signals a mutation; the wrong one will cause an event-stream conflict |
| `data CreateCounter = CreateCounter { .. }` with `field rec` selectors | dot access `cmd.label` | `NoFieldSelectors` is on project-wide — field names are not functions |
| `error "not found"` / `undefined` | `Decider.reject "Counter not found"` | `error` / `undefined` crash the process; `reject` returns a well-typed rejection the HTTP layer turns into a 400 |
| `newId = Uuid.generate` at top level | `newId <- Decider.generateUuid` inside the `do` block | UUID generation is a side effect; it must be sequenced inside the `do`, not called as a pure expression |
| `import Service.Command.Core (EntityOf)` | Import nothing extra for `EntityOf` — it's re-exported by `Core` | Only `TransportsOf` needs `Service.Command.Core`; double-importing `EntityOf` causes ambiguity |

---

## Auth policy

Commands are **secure by default**: if you omit `canAccess`, the `command` macro falls back to `authenticatedAccess` (login required). This is enforced only when the application wires `Application.withAuth`. Without `withAuth`, every command is reachable unauthenticated and returns 200 — so `write-hurl-e2e` happy-path tests work without a token.

To open a command to unauthenticated callers explicitly:

```haskell
import Service.AccessControl (publicAccess)

canAccess :: Maybe UserClaims -> Maybe AccessError
canAccess = publicAccess
```

The public Counter source does not override `canAccess` — the default `authenticatedAccess` is the correct starting point for all new commands.

---

## Verify

```
neo build
```

A successful build confirms:
- `command ''IncrementCounter` (or `CreateCounter`) resolves and generates the HTTP transport wiring.
- `type instance EntityOf` and `type instance TransportsOf` are accepted without orphan-instance warnings.
- No `Prelude` leakage; no `IO` in `decide`.

If you see `No instance for (Default CounterEntity)`, the entity's `instance Default` is missing from `Entity.hs` — see `neohaskell-module-layout`. If `command` is not in scope, check the import `Service.CommandExecutor.TH (command)`.
