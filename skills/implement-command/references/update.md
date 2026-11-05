# Modify an existing entity

Use only the branch needed by the task. Resolve the application revision and capabilities through [nh-app-context](../../nh-app-context/SKILL.md) before adapting API examples. The existing consumer layout and compatible API guide determine the actual imports, markers, and commands.

## Template 2 — update command (`IncrementCounter`)

Grounded in the public `neo` test-project (`Starter.Counter.Commands.IncrementCounter`). The update pattern differs in three ways: `getEntityId` returns `Just`, the `decide` case-splits on `entity`, and the accept constructor is `acceptExisting`.

```haskell
-- src/Starter/Counter/Commands/IncrementCounter.hs
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

