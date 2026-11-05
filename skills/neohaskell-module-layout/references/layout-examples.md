# Choose a layout and adapt complete modules

Use only the branch needed by the task. Resolve the application revision and capabilities through [nh-app-context](../../nh-app-context/SKILL.md) before adapting API examples. The existing consumer layout and compatible API guide determine the actual imports, markers, and commands.

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


## Legacy fat-barrel warning (testbed Cart / Stock / Document)

The testbed `Testbed.Cart.Core`, `Testbed.Stock.Core`, and `Testbed.Document.Core` are **legacy fat barrels** — they put the entity record, event ADT, `update` fold, JSON instances, type instances, and `getEventEntityId` all in one `Core.hs` file. This style is retained in the testbed for historical reasons.

New projects must use the **split layout** shown above (Counter):
- `Entity.hs` — aggregate + instances
- `Event.hs` — ADT + `getEventEntityId`
- `Events/<Name>.hs` — payload `data Event = Event { … }`
- `Core.hs` — thin re-export only

When you see a testbed import like `import Testbed.Cart.Core (CartEntity (..), CartEvent (..))`, you are reading legacy code. The Counter split layout is the correct target for all new contexts.

---

