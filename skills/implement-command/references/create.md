# Create with a generated ID

Use only the branch needed by the task. Resolve the application revision and capabilities through [nh-app-context](../../nh-app-context/SKILL.md) before adapting API examples. The existing consumer layout and compatible API guide determine the actual imports, markers, and commands.

## Template 1 — creation command (`CreateCounter`)

Grounded in the public `neo` test-project (`Starter.Counter.Commands.CreateCounter`). Adapt `App`, `Context`, `Cmd`, `Entity`, `Event`, and field names to your domain.

```haskell
-- src/Starter/Counter/Commands/CreateCounter.hs
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

