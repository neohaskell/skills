# Write the behavioral acceptance spec before implementation

Use only the branch needed by the task. Resolve the application revision and capabilities through [nh-app-context](../../nh-app-context/SKILL.md) before adapting API examples. The existing consumer layout and compatible API guide determine the actual imports, markers, and commands.

## Template 1 — Acceptance spec

Grounds in the public Counter test-project. Adapt module paths, entity type, event type, command, and field names to your domain.

The flow is always: **decide → AcceptCommand events → Array.foldl update → assert entity state**. No HTTP, no app boot, no database.

```haskell
-- tests/Acceptance/CounterIncrementSpec.hs
module Acceptance.CounterIncrementSpec where

import Core
import Array qualified
import Decider (DecisionContext (..))
import Decider qualified
import Service.Auth (emptyContext)
import Test
import Uuid qualified
import Starter.Counter.Commands.IncrementCounter qualified as IncrementCounter
import Starter.Counter.Entity (CounterEntity (..), initialState, update)
import Starter.Counter.Event (CounterEvent)


spec :: Spec Unit
spec = do
  describe "IncrementCounter — acceptance" do

    it "accepts a valid increment and applies it to the entity" \_ -> do
      -- GIVEN: an existing counter with count 0
      let existingId = Uuid.nil
      let cmd = IncrementCounter.IncrementCounter
                  { entityId = existingId
                  , amount   = 5
                  }
      let entity = Just CounterEntity
                     { counterId = existingId
                     , value     = 0
                     , label     = "my counter"
                     }

      -- WHEN: decide is called
      result <-
        Decider.runDecision
          (DecisionContext {genUuid = Uuid.generate})
          (IncrementCounter.decide cmd entity emptyContext)

      -- THEN: command is accepted; replaying the emitted events yields the new state
      case result of
        RejectCommand reason ->
          fail [fmt|Expected accept but got reject: #{reason}|]
        AcceptCommand _ events -> do
          let startState  = CounterEntity {counterId = existingId, value = 0, label = "my counter"}
          let finalEntity = Array.foldl update startState events
          finalEntity.value |> shouldBe 5

    it "rejects when the counter does not exist" \_ -> do
      let cmd = IncrementCounter.IncrementCounter {entityId = Uuid.nil, amount = 5}
      result <-
        Decider.runDecision
          (DecisionContext {genUuid = Uuid.generate})
          (IncrementCounter.decide cmd Nothing emptyContext)
      case result of
        AcceptCommand _ _ ->
          fail "Expected reject but got accept"
        RejectCommand reason ->
          reason |> shouldBe "Counter not found"

    it "rejects when the amount is not positive" \_ -> do
      let existingId = Uuid.nil
      let cmd    = IncrementCounter.IncrementCounter {entityId = existingId, amount = 0}
      let entity = Just CounterEntity {counterId = existingId, value = 3, label = "x"}
      result <-
        Decider.runDecision
          (DecisionContext {genUuid = Uuid.generate})
          (IncrementCounter.decide cmd entity emptyContext)
      case result of
        AcceptCommand _ _ -> fail "Expected reject"
        RejectCommand _   -> Task.yield unit  -- any rejection message is fine
```

**Imports:** `CommandResult(..)` (`AcceptCommand`/`RejectCommand`) is re-exported
by `Core`; `DecisionContext` is **not** — import only `DecisionContext` from
`Decider`. Importing `CommandResult(..)` from `Decider` as well is redundant and
fails under `-Wall -Werror=unused-imports`.

---

