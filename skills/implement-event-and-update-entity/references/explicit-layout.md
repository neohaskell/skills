# Extend an existing split or combined layout

Use only the branch needed by the task. Resolve the application revision and capabilities through [nh-app-context](../../nh-app-context/SKILL.md) before adapting API examples. The existing consumer layout and compatible API guide determine the actual imports, markers, and commands.

## Two valid layouts — split vs single-file

Two entity/event layouts are **valid and interchangeable**; pick one per context and mirror it consistently.

- **Split scaffold** — what `neo new` generates, and what Steps 1–3 below describe: `Entity.hs`, `Event.hs`, a `Core.hs` barrel, and one `Events/<Name>.hs` payload module per event (in-file type always named `Event`).
- **Single-file** — the authoritative testbed layout (e.g. `Testbed.Cart.Core`): one `Core.hs` holding the entity **and** the event ADT with **inline record constructors** — no separate `Events/` modules. Fewer files, one template to mirror.

The single-file/inline layout is what triggers the ambiguous-fields caveat in Step 3: its inline event constructors share field names with the entity via `DuplicateRecordFields`.

Import block for a single-file `Core.hs`:

```haskell
import Core                              -- Entity, NameOf/EventOf/EntityOf, Default, Text, Uuid (type), Generic
import Json qualified                    -- FromJSON/ToJSON instances
import Service.Command.Core (Event (..)) -- the Event class (getEventEntityIdImpl)
import Uuid qualified                    -- Uuid.nil (the FUNCTIONS; the type comes from Core)
```

`getEventEntityId` and `update` are **not exported** — they are used only by the `Event`/`Entity` instances. Mirror `Testbed.Cart.Core`'s export list: `(CartEntity (..), CartEvent (..), initialState)`.

---


## Step 1 — Create `Events/<Name>.hs` (payload) [LOCKABLE once deployed]

The **in-file type is always `Event`**, regardless of the file name. `neo inspect` identifies payload files by looking for `data Event` inside any `Events/<Name>.hs` file; a differently named type will be invisible to tooling.

Grounded in the Counter starter layout (verified against `neo/src/inspect/parse.rs` test fixtures and reflected in `neohaskell-module-layout`).

```haskell
-- src/Starter/Counter/Events/CounterIncremented.hs
module Starter.Counter.Events.CounterIncremented (
  Event (..),
) where

import Core


data Event = Event
  { entityId :: Uuid
  , amount   :: Int
  }
  deriving (Generic, Show)
```

Replace `Counter`/`CounterIncremented`/fields with your context and event. Field types must be NeoHaskell types: `Uuid`, `Text`, `Int`, `Natural Int`, `Array Foo`, `Maybe Foo` — never `String`, `[a]`, or `Data.UUID.UUID`.

For a **creation event** the payload always carries the entity id (so `update` can populate the entity's id field):

```haskell
-- src/Starter/Counter/Events/CounterCreated.hs
module Starter.Counter.Events.CounterCreated (
  Event (..),
) where

import Core


data Event = Event
  { entityId :: Uuid
  , label    :: Text
  }
  deriving (Generic, Show)
```

Creation facts (`CounterCreated`, `CartCreated`, `MemberRegistered`, `LoanOpened`) are correct event names — they are **not** CRUD smells. The smell is a present-tense or RPC-echo name (`CreateCounter`, `ProcessIncrement`).

---


## Step 2 — Update `Event.hs` (context ADT)

`Event.hs` holds only the sum type and `getEventEntityId`. Each constructor wraps the corresponding payload module. JSON instances live on the ADT (not on the individual payload types).

**Add the new variant** to the existing ADT and **extend `getEventEntityId`** with a new branch. Both must be exhaustive.

Grounded in the Counter starter (reflected in `neohaskell-module-layout`).

```haskell
-- src/Starter/Counter/Event.hs
module Starter.Counter.Event (
  CounterEvent (..),
  getEventEntityId,
) where

import Core
import Json qualified
import Starter.Counter.Events.CounterCreated     qualified as CounterCreated
import Starter.Counter.Events.CounterIncremented qualified as CounterIncremented


data CounterEvent
  = CounterCreated    CounterCreated.Event
  | CounterIncremented CounterIncremented.Event
  deriving (Generic, Show)


instance Json.FromJSON CounterEvent


instance Json.ToJSON CounterEvent


-- Must cover every constructor — a non-exhaustive match is a compile warning
-- and a runtime crash when an unmatched event fires.
getEventEntityId :: CounterEvent -> Uuid
getEventEntityId event = case event of
  CounterCreated    ev -> ev.entityId
  CounterIncremented ev -> ev.entityId
```

Pattern for adding a third variant `CounterDecremented CounterDecremented.Event`:

1. Add `import Starter.Counter.Events.CounterDecremented qualified as CounterDecremented`.
2. Add `| CounterDecremented CounterDecremented.Event` to the ADT.
3. Add `CounterDecremented ev -> ev.entityId` to `getEventEntityId`.
4. Add the case to `update` in `Entity.hs` (Step 3).

Do all four together — the compiler will tell you exactly which branches are missing.

---


## Step 3 — Extend `update` in `Entity.hs`

`Entity.hs` owns the `update :: CounterEvent -> CounterEntity -> CounterEntity` fold and all type instances. The fold must be **exhaustive**: GHC treats a missing constructor as a warning under `-Wall` and a runtime crash at replay time.

Grounded in `testbed/src/Testbed/Cart/Core.hs` (update fold) and the Counter Entity.hs pattern from `neohaskell-module-layout`.

```haskell
-- src/Starter/Counter/Entity.hs  (excerpt — the update fold)
update :: CounterEvent -> CounterEntity -> CounterEntity
update event entity = case event of
  CounterCreated ev ->
    entity
      { counterId = ev.entityId
      , label     = ev.label
      , value     = 0
      }
  CounterIncremented ev ->
    entity { value = entity.value + ev.amount }
```

The full `Entity.hs` with all instances for reference:

```haskell
-- src/Starter/Counter/Entity.hs
module Starter.Counter.Entity (
  CounterEntity (..),
  initialState,
) where

import Core
import Json qualified
import Service.Command.Core (Event (..))
import Starter.Counter.Event (CounterEvent (..), getEventEntityId)
import Starter.Counter.Events.CounterCreated     qualified as CounterCreated
import Starter.Counter.Events.CounterIncremented qualified as CounterIncremented
import Uuid qualified


data CounterEntity = CounterEntity
  { counterId :: Uuid
  , label     :: Text
  , value     :: Int
  }
  deriving (Generic)


instance Json.FromJSON CounterEntity


instance Json.ToJSON CounterEntity


instance Default CounterEntity where
  def = initialState


initialState :: CounterEntity
initialState =
  CounterEntity
    { counterId = Uuid.nil
    , label     = ""
    , value     = 0
    }


type instance NameOf CounterEntity = "CounterEntity"

-- Both directions of the entity-event relationship live in Entity.hs,
-- not in Event.hs, to avoid orphan-instance warnings and import cycles.
type instance EventOf  CounterEntity = CounterEvent
type instance EntityOf CounterEvent  = CounterEntity


instance Entity CounterEntity where
  initialStateImpl = initialState
  updateImpl       = update


instance Event CounterEvent where
  getEventEntityIdImpl = getEventEntityId


update :: CounterEvent -> CounterEntity -> CounterEntity
update event entity = case event of
  CounterCreated ev ->
    entity
      { counterId = ev.entityId
      , label     = ev.label
      , value     = 0
      }
  CounterIncremented ev ->
    entity { value = entity.value + ev.amount }
```

**Ambiguous-fields caveat (most common in the inline/single-file layout).** Under `DuplicateRecordFields` + `NoFieldSelectors`, `-Werror=ambiguous-fields` (GHC-02256, *"Ambiguous record update with parent type constructor"*) fires on an `update` case whose record *update* `entity {f = .., g = ..}` sets **only** fields that also exist on the matched event constructor — there is no entity-only field to anchor the type. (Most cases are safe because they set an entity-only field such as `status`, or an id the events don't carry.) Two fixes: (a) include an entity-only field in the update, or (b) **reconstruct via the constructor** — `SessionEntity { … }` — since `-Wambiguous-fields` applies to record *update* only, not construction. Canonical detail in `neohaskell-records-and-json`.

---

