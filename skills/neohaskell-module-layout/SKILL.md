---
name: neohaskell-module-layout
description: >-
  The NeoHaskell per-bounded-context FOLDER and MODULE SKELETON for an event-sourced
  project: the thin Core.hs barrel, Entity.hs aggregate, Event.hs ADT, per-payload Events/
  files (type literally named Event), lockable vs unlockable directories, the instance
  Default rule, and Service.hs command registration. Use when creating a new context,
  deciding WHERE a file goes, what modules a context needs, or migrating a legacy fat-barrel
  Core.hs (testbed Cart/Stock) to the split layout (Counter starter) — 'where does this file
  go', 'what modules does a context need', 'show me the folder structure'. Do NOT use to
  write the code inside those files (the implement-* skills), to register endpoints in
  App.hs (wire-feature), to diagnose why neo inspect shows no domains (neo-run-and-inspect),
  or for the import-Core header inside a module (neohaskell-core-prelude).
metadata:
  model: haiku
---

**This is NeoHaskell, not vanilla Haskell.** The `.hs` extension is shared, but NeoHaskell compiles with a custom `Core` prelude and project-wide extensions. Module names must mirror file paths exactly.

---

## Inputs / Outputs / Next

- **Input:** a context name (e.g. `Counter`) and the list of building blocks to scaffold (entity, events, commands, queries, integrations).
- **Output:** the folder tree + one correctly structured file per building block, with GHC-correct module names and lock-status placement.
- **Next:** `implement-command` · `implement-event-and-update-entity` · `implement-query` · `implement-integration` · `wire-feature`

---

## Folder map

```
src/<App>/<Context>/
  Core.hs          -- thin barrel: re-export Entity + Event only
                   -- NO import Core, NO declarations
  Entity.hs        -- aggregate record + initialState + update fold
                   -- + instance Default + all type instances + entity/event instances
  Event.hs         -- context event ADT (sum type) wrapping payload modules
                   -- + getEventEntityId function
  Events/
    <Name>.hs      -- ONE payload per event; in-file type is literally `Event`   [LOCKABLE]
  Commands/
    <Name>.hs      -- record + getEntityId + decide + `command ''Name`           [LOCKABLE]
  Queries/
    <Name>.hs      -- read model + deriveQuery + QueryOf + canAccess/canView     [LOCKABLE]
  Integrations/
    <Name>.hs      -- per-trigger handler + `outboundIntegration ''Name`         [NOT lockable]
  Service.hs       -- registers commands via Service.command @Cmd                [NOT lockable]
```

`neo lock` locks any file whose path contains a directory component named exactly `Commands`, `Events`, or `Queries`. `Entity.hs`, `Event.hs`, `Core.hs`, `Service.hs`, and `Integrations/*.hs` are **never** locked — they can evolve freely (entities by add-only; others without restriction).

---

## Templates (Counter domain — grounded in public sources)

The Counter is the `neo` starter project. Templates below match the module layout expected by `neo inspect parse` (grounded in `neo/src/inspect/parse.rs`). The testbed Cart/Stock/Document use a **legacy fat-barrel** where everything lives in a single `Core.hs` — see the warning at the end of this skill.

### `src/Starter/Counter/Events/CounterCreated.hs` [LOCKABLE]

The in-file type is **always** `Event`, regardless of the file name. Grounded in `neo/src/inspect/parse.rs` test fixtures.

```haskell
module Starter.Counter.Events.CounterCreated (
  Event (..),
) where

import Core
import Json qualified


data Event = Event
  { entityId :: Uuid
  , label    :: Text
  }
  deriving (Generic, Show)


instance Json.FromJSON Event

instance Json.ToJSON Event
```

### `src/Starter/Counter/Events/CounterIncremented.hs` [LOCKABLE]

```haskell
module Starter.Counter.Events.CounterIncremented (
  Event (..),
) where

import Core
import Json qualified


data Event = Event
  { entityId :: Uuid
  , amount   :: Int
  }
  deriving (Generic, Show)


instance Json.FromJSON Event

instance Json.ToJSON Event
```

### `src/Starter/Counter/Event.hs`

The context event ADT wraps payload modules. Each constructor names the payload module (`CounterCreated.Event`), not the fields inline. `getEventEntityId` lives here. Grounded in `neo/src/inspect/parse.rs` test fixtures.

```haskell
module Starter.Counter.Event (
  CounterEvent (..),
  getEventEntityId,
) where

import Core
import Json qualified
import Starter.Counter.Events.CounterCreated    qualified as CounterCreated
import Starter.Counter.Events.CounterIncremented qualified as CounterIncremented


data CounterEvent
  = CounterCreated    CounterCreated.Event
  | CounterIncremented CounterIncremented.Event
  deriving (Generic, Show)


instance Json.FromJSON CounterEvent

instance Json.ToJSON CounterEvent


getEventEntityId :: CounterEvent -> Uuid
getEventEntityId event = case event of
  CounterCreated    ev -> ev.entityId
  CounterIncremented ev -> ev.entityId
```

### `src/Starter/Counter/Entity.hs`

All entity↔event type instances and instances live here, not in `Event.hs`. `instance Default` sets `def = initialState` — this is the rule for every entity. Grounded in `testbed/src/Testbed/Cart/Core.hs` (same patterns, split across files here).

```haskell
module Starter.Counter.Entity (
  CounterEntity (..),
  initialState,
  update,
) where

import Core
import Json qualified
import Service.Command.Core (Event (..))
import Starter.Counter.Event (CounterEvent (..), getEventEntityId)
import Starter.Counter.Events.CounterCreated    qualified as CounterCreated
import Starter.Counter.Events.CounterIncremented qualified as CounterIncremented
import Uuid qualified


data CounterEntity = CounterEntity
  { counterId :: Uuid
  , label     :: Text
  , count     :: Int
  }
  deriving (Generic)


instance Json.FromJSON CounterEntity

instance Json.ToJSON CounterEntity

-- Every entity must declare this instance. def = initialState is the rule.
instance Default CounterEntity where
  def = initialState


initialState :: CounterEntity
initialState =
  CounterEntity
    { counterId = Uuid.nil
    , label     = ""
    , count     = 0
    }


type instance NameOf CounterEntity = "CounterEntity"

-- Both entity→event and event→entity type instances live in Entity.hs.
type instance EventOf   CounterEntity = CounterEvent
type instance EntityOf  CounterEvent  = CounterEntity


instance Entity CounterEntity where
  initialStateImpl = initialState
  updateImpl       = update


-- instance Event Ev also lives in Entity.hs (not Event.hs).
instance Event CounterEvent where
  getEventEntityIdImpl = getEventEntityId


-- update fold: must be exhaustive over every CounterEvent constructor.
update :: CounterEvent -> CounterEntity -> CounterEntity
update event entity = case event of
  CounterCreated ev ->
    entity
      { counterId = ev.entityId
      , label     = ev.label
      , count     = 0
      }
  CounterIncremented ev ->
    entity { count = entity.count + ev.amount }
```

### `src/Starter/Counter/Core.hs` — thin barrel

Re-exports `Entity` and `Event` only. No `import Core`, no declarations, no instances. Commands import `Starter.Counter.Core` for entity/event types; `Service.hs` uses `Starter.Counter.Core ()` (instance-only import).

```haskell
module Starter.Counter.Core (
  module Starter.Counter.Entity,
  module Starter.Counter.Event,
) where

import Starter.Counter.Entity
import Starter.Counter.Event
```

### `src/Starter/Counter/Service.hs`

Grounded in `testbed/src/Testbed/Cart/Service.hs`.

```haskell
module Starter.Counter.Service (
  service,
) where

import Core
import Service qualified
import Starter.Counter.Commands.IncrementCounter (IncrementCounter)
import Starter.Counter.Core ()   -- instance-only import (brings Entity/Event instances into scope)


service :: Service _ _
service =
  Service.new
    |> Service.command @IncrementCounter
```

`service :: Service _ _` is a **partial type signature** (compiles under `-fno-warn-partial-type-signatures`) that **won't infer with zero commands** — every `Service.hs` needs ≥1 `Service.command @X`. A context with no commands needs no `Service.hs` at all; an app can even run with **zero domains** (`withConfig |> withEventStore |> withTransport`, no `withService`/`withQuery`) and still compile — see **wire-feature** for the App.hs wiring.

---

## instance Default rule

Every entity module must declare:

```haskell
instance Default CounterEntity where
  def = initialState
```

`Default` is re-exported by `Core` — no separate import is needed. Declaring `instance Default` for every entity is a strong project convention; the `command` and `deriveQuery` macros do not enforce it at compile time, but all public examples follow the pattern.

Grounded in: `testbed/src/Testbed/Cart/Core.hs` line 28–30.

---

## Legacy fat-barrel warning (testbed Cart / Stock / Document)

The testbed `Testbed.Cart.Core`, `Testbed.Stock.Core`, and `Testbed.Document.Core` are **legacy fat barrels** — they put the entity record, event ADT, `update` fold, JSON instances, type instances, and `getEventEntityId` all in one `Core.hs` file. This style is retained in the testbed for historical reasons.

New projects must use the **split layout** shown above (Counter):
- `Entity.hs` — aggregate + instances
- `Event.hs` — ADT + `getEventEntityId`
- `Events/<Name>.hs` — payload `data Event = Event { … }`
- `Core.hs` — thin re-export only

When you see a testbed import like `import Testbed.Cart.Core (CartEntity (..), CartEvent (..))`, you are reading legacy code. The Counter split layout is the correct target for all new contexts.

---

## DO / DON'T table

| DON'T | DO | Why |
|---|---|---|
| Put entity record, event ADT, and `update` in one `Core.hs` | Split into `Entity.hs`, `Event.hs`, `Events/`, thin `Core.hs` | The fat barrel blocks the lock mechanism; lockable files must live under `Commands/`/`Events/`/`Queries/` dirs |
| Declare data types or instances in `Core.hs` | `Core.hs` re-exports only — no declarations, no `import Core` | Any declaration in the barrel makes it a module, not a barrel |
| Name the payload type `data CounterCreated = …` | Always `data Event = Event { … }` inside `Events/<Name>.hs` | `neo inspect` looks for a type named `Event` in each payload file |
| Use `Event/` (singular) as the directory | Always `Events/` (plural) | `neo lock` and `neo inspect` key on the plural name |
| Place `type instance EntityOf Ev` or `instance Event Ev` in `Event.hs` | All type instances (both directions) live in `Entity.hs` | Co-location avoids orphan-instance warnings and import cycles |
| Omit `instance Default E where def = initialState` | Declare it in `Entity.hs` for every entity | Strong project convention; all public examples follow the pattern |
| Place `Entity.hs` or `Event.hs` inside `Commands/`, `Events/`, or `Queries/` dirs | Keep them at the context root | Files in those dirs are automatically lockable via `neo lock` |
| Use `import Data.Default` for the `Default` class | `import Core` is sufficient — `Default` is re-exported | Extra imports cause `-Werror` unused-import failures |
| Forget the instance-only `import Context.Core ()` in `Service.hs` | Always add `import Starter.Counter.Core ()` | Brings entity/event instances into scope; without it the macro fails |
| Skip the `-- [LOCKABLE]` comment on new `Events/`/`Commands/`/`Queries/` files | Add `-- [LOCKABLE once deployed]` in the file header | Reminds reviewers that after `neo lock`, these files must never be edited |

---

## Verify

After scaffolding the skeleton, run:

```
neo build
```

A successful build confirms module names mirror paths, all type instances resolve, and `instance Default` compiles. If the build fails with `No instance for (Default …)`, check that `Entity.hs` declares the instance. If `neo inspect domains` does not list the context, check that `Core.hs` re-exports both `Entity` and `Event`.
