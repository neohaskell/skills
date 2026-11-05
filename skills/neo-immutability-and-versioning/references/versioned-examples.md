# Add a V2 command or event

Use only the branch needed by the task. Resolve the application revision and capabilities through [nh-app-context](../../nh-app-context/SKILL.md) before adapting API examples. The existing consumer layout and compatible API guide determine the actual imports, markers, and commands.

## Copy-paste template: a `V2` command sibling

Adapted from the public Counter command (`Starter.Counter.Commands.IncrementCounter`,
`neo` test-project). The original stays locked and untouched; the V2 carries the new rule.

```haskell
-- FILE: src/Starter/Counter/Commands/IncrementCounterV2.hs   (NEW sibling; original left byte-identical)
module Starter.Counter.Commands.IncrementCounterV2 (
  IncrementCounterV2 (..),
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


data IncrementCounterV2 = IncrementCounterV2
  { entityId :: Uuid
  , amount :: Int
  }
  deriving (Generic, Typeable, Show)


instance Json.FromJSON IncrementCounterV2


getEntityId :: IncrementCounterV2 -> Maybe Uuid
getEntityId cmd = Just cmd.entityId


decide :: IncrementCounterV2 -> Maybe CounterEntity -> RequestContext -> Decision CounterEvent
decide cmd entity _ctx = case entity of
  Nothing -> Decider.reject "Counter not found"
  Just existing ->
    if cmd.amount <= 0
      then Decider.reject "Amount must be positive"
      else
        if cmd.amount > 100
          then Decider.reject "Amount may not exceed 100" -- NEW rule that motivated the V2
          else
            Decider.acceptExisting
              [ CounterIncremented
                  CounterIncremented.Event
                    { entityId = existing.counterId
                    , amount = cmd.amount
                    }
              ]


type instance EntityOf IncrementCounterV2 = CounterEntity


type instance TransportsOf IncrementCounterV2 = '[WebTransport]


command ''IncrementCounterV2
```

This V2 reuses the existing `CounterIncremented` event because only the *rule* changed. If the
**event's shape** must change, version the payload file too (next section).

---


## Special case: versioning a locked event payload

Per-event payload modules are locked, and their in-file type is **literally `Event`**. Version
at the **file/module** level; the type stays `Event`. Then add a new variant to the (unlocked)
singular `Event.hs` ADT and handle it in the (unlocked) entity.

```haskell
-- FILE: src/Starter/Counter/Events/CounterIncrementedV2.hs   (NEW; type is still `Event`)
module Starter.Counter.Events.CounterIncrementedV2 (Event (..)) where

import Core
import Json qualified

data Event = Event
  { entityId :: Uuid
  , amount :: Int
  , reason :: Text -- the new field this V2 exists to carry
  }
  deriving (Generic, Show)


instance Json.FromJSON Event


instance Json.ToJSON Event
```

```haskell
-- FILE: src/Starter/Counter/Event.hs   (NOT locked — add the variant here)
data CounterEvent
  = CounterCreated CounterCreated.Event
  | CounterIncremented CounterIncremented.Event
  | CounterIncrementedV2 CounterIncrementedV2.Event -- NEW variant wrapping the V2 payload
  deriving (Generic, Show)
```

Then extend `getEventEntityId` (in `Event.hs`) and the entity's `update` fold (in `Entity.hs`)
with a case for `CounterIncrementedV2`. Both are unlocked, so you edit them in place — but the
`update` fold must stay **exhaustive**, and the old `CounterIncremented` case must remain (old
logged events still replay through it).

**Wire the V2 in** exactly like a fresh artifact (see `wire-feature`): a new command goes into
`Service.hs` (`Service.command @IncrementCounterV2`); a new query into `App.hs`; a new event
variant into the ADT + `update` as above.

---

