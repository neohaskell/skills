---
name: write-feature-tests
description: >-
  Writes two NeoHaskell feature-level specs for a completed slice: an Acceptance
  spec (pure in-domain flow: decide then Array.foldl update then combine, no HTTP)
  and a Property spec (QuickCheck replay of the entity update fold via
  Array.foldl update, oldest event first). Use in the outside-in TDD cycle at
  step 2 (acceptance RED, before inner unit tests) and step 7 (property replay
  after refactor). Also use when asked to write feature tests, acceptance tests,
  property tests, QuickCheck replay tests, or fold-based invariant tests for a
  NeoHaskell entity. This is NeoHaskell, not vanilla Haskell — io, pure, foldl
  with the wrong arg order, and Array.filter are all wrong here.
metadata:
  model: sonnet
---

**This is NeoHaskell, not vanilla Haskell.** The `.hs` extension is shared, but NeoHaskell uses a custom `Core` prelude — `import Core`, never `import Prelude`. Every identifier in this skill is grounded in the public NeoHaskell core source (`core/testlib/Test.hs`, `core/service/Decider.hs`, `core/core/Array.hs`).

---

## TDD cycle role

This skill covers **two distinct steps** in the outside-in cycle:

```
write-hurl-e2e  (RED outer — HTTP, step ①)
  ► write-feature-tests / Acceptance (RED, step ②)  ◄  ← write this FIRST (before unit tests)
      write-unit-tests  (RED inner, step ③)
        neohaskell-domain-modeling  (DOMAIN, step ④)
          implement-* / wire-feature  (GREEN, steps ⑤–⑥)
  ► write-feature-tests / Property (step ⑦, after refactor)  ◄
```

**Step ②** — Write the Acceptance spec RED-first (before any implementation). It will fail at a type error or assertion, not a compile error, once DOMAIN types are in place.

**Step ⑦** — After the slice is green and refactored, add the Property spec. It replay-folds arbitrary event arrays through the entity `update` function and asserts invariants.

In Claude Code you may delegate this step to a sub-agent spawned with `model: sonnet`. In Cursor or Codex it runs inline.

---

## Inputs / Outputs / Next

- **Input:** a completed feature slice with typed events, entity `update` fold, and query `combine`. The Acceptance spec needs the types to exist (from `neohaskell-domain-modeling`); the Property spec needs a compiling `update` fold.
- **Output:** `tests/Acceptance/<Feature>Spec.hs` (step ②) and `tests/Property/<Entity>ReplaySpec.hs` (step ⑦). All Haskell specs live under `tests/` — the *same* directory as the `.hurl` e2e files — because `neo test` discovers and compiles specs there; never use a `test/` directory.
- **Next:** `write-unit-tests` (after Acceptance spec is red) · `write-hurl-e2e` (outer loop companion)

---

## Template 1 — Acceptance spec

Grounds in the public Counter test-project. Adapt module paths, entity type, event type, command, and field names to your domain.

The flow is always: **decide → AcceptCommand events → Array.foldl update → assert entity state**. No HTTP, no app boot, no database.

```haskell
-- tests/Acceptance/CounterIncrementSpec.hs
module Acceptance.CounterIncrementSpec where

import Core
import Array qualified
import Decider (CommandResult (..), DecisionContext (..))
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

---

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
    n <- QuickCheck.arbitrary
    GhcPrelude.pure CounterIncremented.Event
      { entityId = Uuid.nil            -- entity id is irrelevant to the fold
      , amount   = GhcPrelude.abs n    -- non-negative amount
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

## DO / DON'T

| Vanilla-Haskell reflex — DON'T | NeoHaskell-correct — DO | Why |
|---|---|---|
| `shouldBe actual expected` | `actual \|> shouldBe expected` | The NeoHaskell `shouldBe` takes `expected` as first arg; pipe reads naturally |
| `import Test.Hspec` directly in the Acceptance spec | `import Test` | `Test` re-exports the NeoHaskell wrappers; bare `import Test.Hspec` gives you the wrong `it` signature |
| `import Test.Hspec` directly in the Property spec | `import Test.Hspec qualified as Hspec` | In the Property spec you need `Hspec.it` so it accepts `QuickCheck.Property` |
| `Array.foldl update events initialState` (wrong arg order) | `Array.foldl update initialState events` | `Array.foldl` is `f -> acc -> array -> acc`; accumulator before array |
| `foldl (\acc ev -> update ev acc) initialState events` | `Array.foldl update initialState events` | `Array.foldl` already puts element first — no need to flip |
| `Array.filter` | `Array.takeIf` / `Array.dropIf` | `Array.filter` does not exist in NeoHaskell |
| `Decider.runDecision ctx` without `<-` | `result <- Decider.runDecision ctx ...` | Returns `Task Text (CommandResult ev)`; bind it in the `Task` do-block |
| `pure` in the Acceptance spec's `Task` body | `Task.yield unit` | `pure` compiles but the wrong type; use `Task.yield` |
| `pure` inside `QuickCheck.Arbitrary` | `GhcPrelude.pure` | In the QuickCheck `Gen` monad `pure` is unambiguous but qualify it to make the context explicit |
| `not`, `all`, `sum`, `length` unqualified in property bodies | `GhcPrelude.not`, `GhcList.sum`, etc. | These names clash with NeoHaskell equivalents; qualify to avoid ambiguity |
| Booting the app / making HTTP calls | No HTTP in these specs | HTTP belongs in `write-hurl-e2e`; Acceptance is purely in-domain |
| `panic "TODO: not implemented"` in the spec | No panics in specs | Stubs belong in domain/implementation modules, not in test assertions |
| Generating negative quantities with `QuickCheck.arbitrary` directly | `GhcPrelude.abs n` in the `Arbitrary` instance, or use `Natural` | Negative generated values can violate domain invariants and produce misleading failures |
| Calling `decide` then checking events inside `RejectCommand` | Always case-split and handle both constructors | `CommandResult` has two constructors; use `fail` on the unexpected branch |

---

## DOMAIN-phase stub (before GREEN)

While the implementation is not ready, the spec still compiles but fails at the assertion (not a type error). The stub state:

- `decide` body returns `panic "TODO: not implemented"` — the Acceptance spec's `Decider.runDecision` call will panic at runtime, which shows up as a test failure on the assertion step. This is the expected RED state.
- Do **not** write `panic` in an outbound `handleEvent` — use `Integration.none` instead (see `implement-integration`).

---

## Verify

```
neo build
```

Both spec files must compile. Once the implementation exists:

```
neo test
```

All Acceptance and Property specs pass when `neo test` exits 0. The inner Hspec runner discovers `spec` exports automatically (assumes `neo#2` in place so the generated `test-suite` stanza runs Hspec).
