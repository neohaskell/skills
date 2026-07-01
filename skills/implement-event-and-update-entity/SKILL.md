---
name: implement-event-and-update-entity
description: >-
  Implements a NeoHaskell event: creates the payload module under Events/Name.hs
  (in-file type always named Event), adds the variant to the context Event.hs ADT,
  extends getEventEntityId with a new branch, and adds the corresponding case to
  the Entity.hs update fold. Use immediately after verify-event-model produces a
  verified event node, or whenever a command's decide needs to emit an event type
  that does not yet have a payload module. Also use when told to "add a new event",
  "wire the event", or "implement the event side" of a command. Covers the locked
  payload V2 rule (never edit a deployed Events/ file -- create a sibling V2
  instead), creation-fact naming (CounterCreated and similar are correct, not CRUD
  smells), and the command-first vs event-first ordering rule. Runs in the GREEN
  phase of the outside-in TDD cycle.
metadata:
  model: sonnet
---

**This is NeoHaskell, not vanilla Haskell.** The `.hs` extension is shared, but the payload type is always named `Event` (not after the file), the `update` fold must be exhaustive, and all imports go through `import Core` and qualified modules — never `import Prelude` or `import Data.Aeson`.

---

## Inputs / Outputs / Next

- **Input:** a verified event node from `verify-event-model` (event name, entity, fields).
- **Output:** `Events/<Name>.hs` payload module + updated `Event.hs` ADT + extended `Entity.hs` `update` fold.
- **Next:** `expand-entity` (if a new field is needed on the entity) · `implement-command` · `write-unit-tests` · `write-feature-tests`

---

## TDD role — GREEN

This skill runs in the **GREEN phase**: the red unit test (`write-unit-tests`) has already described the event's effect on the entity. Implement exactly enough to make that test pass. Do not add fields or logic the test has not asked for.

Command↔event ordering: create the event payload + ADT variant **before or alongside** the emitting command (`implement-command`), not after. The `decide` function references event constructors that must compile first.

---

## Step 1 — Create `Events/<Name>.hs` (payload) [LOCKABLE once deployed]

The **in-file type is always `Event`**, regardless of the file name. `neo inspect` identifies payload files by looking for `data Event` inside any `Events/<Name>.hs` file; a differently named type will be invisible to tooling.

Grounded in the Counter starter layout (verified against `neo/src/inspect/parse.rs` test fixtures and reflected in `neohaskell-module-layout`).

```haskell
-- src/Starter/Counter/Events/CounterIncremented.hs
-- [LOCKABLE once deployed — create CounterIncrementedV2.hs for any change]
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
-- [LOCKABLE once deployed]
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

---

## Locked payload — V2 rule

If `Events/<Name>.hs` is listed in `.locked-files` (check with `grep "src/.../Events/<Name>.hs" .locked-files`), **do not edit it**. Instead:

1. Create `Events/<Name>V2.hs`. The **in-file type is still `Event`** (not `EventV2`); only the module path changes.
2. Add a new ADT variant `<Name>V2 <Name>V2.Event` to `Event.hs`.
3. Add the corresponding `<Name>V2 ev -> ...` branch to `getEventEntityId` and `update`.
4. Wire the new variant into the emitting command (see `neo-immutability-and-versioning`).

Leave the original `Events/<Name>.hs` byte-identical. Do not rename or delete it.

Wrong V2 naming forms (reject these): `Events/foo_v2.hs`, `Events/Foo.V2.hs`, `Events/Foov2.hs` (lowercase v), `data EventV2 = ...`.

---

## DO / DON'T table

| DON'T | DO | Why |
|---|---|---|
| `data CounterIncremented = CounterIncremented { ... }` in the payload file | `data Event = Event { ... }` | `neo inspect` matches the literal type name `Event`; any other name is invisible to tooling |
| Put all events in one ADT file and skip `Events/` | One `Events/<Name>.hs` per event; ADT in `Event.hs` | `Events/` path is what `neo lock` watches; fat-ADT payloads cannot be individually locked |
| `entityId :: String` or `amount :: [Char]` | `entityId :: Uuid`, `amount :: Text` or `Int` | `String` does not exist in the NeoHaskell prelude |
| `import Data.Aeson` / `deriving (FromJSON)` | `import Json qualified` + empty `instance Json.FromJSON CounterEvent` | The framework resolves JSON via `Json` module, not `Data.Aeson` directly |
| Partial `case event of` in `update` (only some constructors) | Exhaustive `case event of` covering every constructor | A missing branch silently passes `-Wall` but crashes at replay time for the missing event |
| Leave `getEventEntityId` without the new branch | Add the branch in the same commit as the payload | The dispatcher panics at runtime when an unmatched event fires |
| `pure entity` at the end of `update` for no-op events | `entity` (the record, unchanged) | `pure` is not a NeoHaskell idiom in a pure function; it compiles but violates style |
| Use `$` or `<>` in `update` | Use `|>` for piping, `++` for append, `{}` record update | Vanilla operators leak into code that looks correct but violates the style guide |
| Edit a deployed (locked) payload file | Create `Events/<Name>V2.hs` (still `data Event`) | The lock gate in `neo build` and the git pre-commit hook both reject modifications to locked files |
| Flag `CounterCreated` / `CartCreated` / `MemberRegistered` as a CRUD smell | Allow creation facts -- they are correct, specific business events | The smell is present-tense (`CreateCounter`) or vague (`CounterUpdated`), not the word "Created" |
| Place `type instance EntityOf CounterEvent` in `Event.hs` | Place it in `Entity.hs` alongside `type instance EventOf CounterEntity` | Co-location in `Entity.hs` avoids orphan-instance warnings; `Event.hs` holds only the ADT and `getEventEntityId` |
| Create the payload after `implement-command` | Create the payload module before or alongside `decide` | `decide` references event constructors -- they must be in scope when the command compiles |

---

## Verify

After writing the three changes, run:

```
neo build
```

A successful build confirms:

- `Events/<Name>.hs` exports `Event (..)` and the module name mirrors the file path.
- The ADT variant compiles (qualified import resolves).
- `getEventEntityId` is exhaustive (no GHC pattern-match warnings).
- `update` is exhaustive over all constructors.
- `type instance EntityOf` / `type instance EventOf` resolve without orphan warnings.

If `neo build` reports a pattern-match warning on `update` or `getEventEntityId`, add the missing branch — do not use `_ -> entity` wildcards (they mask future exhaustiveness regressions).
