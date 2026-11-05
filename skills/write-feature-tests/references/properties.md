# Check replay and domain invariants

Use only the branch needed by the task. Resolve the application revision and capabilities through [nh-app-context](../../nh-app-context/SKILL.md) before adapting API examples. The existing consumer layout and compatible API guide determine the actual imports, markers, and commands.

## Template 2 — Property spec

Grounds in `core/core/Array.hs` (`Array.foldl`) and `core/test/Service/Integration/TestFixtures.hs` (QuickCheck pattern). Use `import Test.Hspec qualified as Hspec` and `import Test.QuickCheck qualified as QuickCheck` — not `import Test` — because `Test.Hspec.it` accepts `QuickCheck.Property` directly.

`Array.foldl` signature: `(element -> accumulator -> accumulator) -> accumulator -> Array element -> accumulator`. The `update` function is `EventType -> EntityType -> EntityType`, which matches — event (element) is first.

```haskell
-- tests/Property/CounterEntityReplaySpec.hs
module Property.CounterEntityReplaySpec where

import Core
import Array qualified
import Data.List qualified as GhcList
import Prelude qualified as GhcPrelude
import Test.Hspec qualified as Hspec
import Test.QuickCheck qualified as QuickCheck
import Starter.Counter.Entity (CounterEntity (..), initialState, update)
import Starter.Counter.Event (CounterEvent (..))
import Starter.Counter.Events.CounterIncremented qualified as CounterIncremented
import Uuid qualified


-- | Arbitrary instance for the event payload used in the property.
-- Use GhcPrelude.abs to keep generated amounts non-negative (illustrates
-- the smart-constructor guard: real code uses makeNaturalOrPanic or Natural).
instance QuickCheck.Arbitrary CounterIncremented.Event where
  arbitrary = do
    n <- QuickCheck.choose (0, 1000)
    GhcPrelude.pure CounterIncremented.Event
      { entityId = Uuid.nil            -- entity id is irrelevant to the fold
      , amount   = n                   -- bounded non-negative amount
      }


spec :: Hspec.Spec
spec =
  Hspec.describe "Counter entity — update fold properties" do

    Hspec.it "count equals sum of all incremented amounts (replay correctness)" do
      QuickCheck.property \(increments :: [CounterIncremented.Event]) ->
        let events      = Array.fromLinkedList (GhcList.map CounterIncremented increments)
            finalEntity = Array.foldl update initialState events
            expected    = GhcList.sum (GhcList.map (.amount) increments)
        in  finalEntity.value GhcPrelude.== expected

    Hspec.it "count is non-negative after any sequence of valid events (invariant)" do
      QuickCheck.property \(increments :: [CounterIncremented.Event]) ->
        let events      = Array.fromLinkedList (GhcList.map CounterIncremented increments)
            finalEntity = Array.foldl update initialState events
        in  finalEntity.value GhcPrelude.>= 0

    Hspec.it "replaying empty event list is identity (initialState roundtrip)" do
      let finalEntity = Array.foldl update initialState (Array.empty :: Array CounterEvent)
      Hspec.shouldBe finalEntity.value initialState.value
```

---


## Array.foldl — the replay fold

`Array.foldl :: (element -> accumulator -> accumulator) -> accumulator -> Array element -> accumulator`

This is a **left fold** (oldest event first). The element (event) is the **first argument** to the step function, the accumulator (entity) is the **second**:

```
Array.foldl update initialState [ev1, ev2, ev3]
  = update ev3 (update ev2 (update ev1 initialState))   -- left, ev1 applied first
```

`update :: CounterEvent -> CounterEntity -> CounterEntity` matches this signature directly.

**Do not confuse with `Array.reduce`**: that is a right fold (newest event first) and takes `(element -> accumulator -> accumulator)`. For event replay, always use `Array.foldl`.

---

