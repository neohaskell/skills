---
name: expand-entity
description: >-
  Adds a new field to an existing NeoHaskell entity module backward-compatibly:
  record declaration, initialState value, update fold case, and a JSON decoder
  that still loads old snapshots missing the new field. Use whenever a feature
  slice needs a field that does not yet exist on an entity, when implement-event-and-update-entity
  identifies a missing field, or when asked to "add a field to the entity", "extend
  the aggregate", or "add state to the entity". This is NeoHaskell — the reader
  defaults to vanilla Haskell; every identifier here is grounded in the public
  testbed Cart and Stock entities plus the Json module source.
metadata:
  model: sonnet
---

**This is NeoHaskell, not vanilla Haskell.** The `.hs` extension is shared, but NeoHaskell uses a custom `Core` prelude — `import Core`, not `import Prelude`. Every identifier in this skill comes from the public `testbed` Cart/Stock entity source and the `Json` module.

---

## TDD cycle role

`expand-entity` is a sub-step of **step 5 (GREEN)**, called on demand during `implement-event-and-update-entity` or `implement-command` whenever a required field is missing from the entity:

```
write-unit-tests (RED) →
  neohaskell-domain-modeling (DOMAIN, types + panic stubs) →
    ► implement-event-and-update-entity ─→ expand-entity (if a new field is needed) ◄
      wire-feature (GREEN, endpoint live)
```

In Claude Code you may delegate this step to a sub-agent spawned with `model: sonnet`. In Cursor or Codex this is advisory — run it inline.

---

## Inputs / Outputs / Next

- **Input:** the name of the new field, its type, and the `update` event case(s) that should set it.
- **Output:** an edited `src/<App>/<Context>/Entity.hs` that still decodes old snapshots (from before the field existed) and that compiles.
- **Next:** `implement-event-and-update-entity` (to add the event case that populates the field) · `write-unit-tests` (Decider/Projection RED specs) · `write-feature-tests` (replay property spec)

---

## The add-only rule — why it matters

Entities are **not** locked (they live outside `Commands/`, `Events/`, `Queries/`), so there is no automated immutability guard. The convention is your only protection:

- **Add fields only.** Never remove a field, rename a field, or change its type.
- **Removing or renaming a field breaks replay** — the event log is replayed from the beginning on every fetch; any old snapshot that contains the old field name will fail to decode after a rename.
- **Retyping a field** (`Int` to `Natural Int`, `Text` to `Uuid`) silently changes decode semantics and may panic on old values.

Because entities are not locked, they do **not** get a V2 sibling. The right fix for a breaking change is a fresh design discussion. The right fix for an additive need is this skill.

---

## Choosing the JSON backward-compat strategy

When you add a field, old snapshots on disk do not have that field. The empty Generic `FromJSON` derived from `deriving (Generic)` will **reject** a JSON object that is missing a required (non-`Maybe`) field. Choose one strategy:

| Strategy | Use when | How |
|---|---|---|
| **A: `Maybe` field** | the field is genuinely optional, or the "not yet set" state makes domain sense | Add `newField :: Maybe TheType`; Generic `FromJSON` tolerates its absence and decodes it as `Nothing` |
| **B: custom `parseJSON` with `.:?` / `.!=`** | the field is conceptually required but must have a sensible default on old snapshots | Write a `parseJSON` using `Json.withObject` + `obj Json..:? "key" Json..!= defaultValue` |

Never add a required non-`Maybe` field and leave the empty Generic `FromJSON` in place — that silently breaks all old snapshots the moment the code is deployed.

---

## Template A: `Maybe` field (illustrative `Library.Loan` domain)

Grounded in the public testbed `CartEntity`/`StockEntity` pattern; `Library.Loan` is the neutral illustrative domain used across this skill set for examples that need entity evolution.

```haskell
-- src/Library/Loan/Entity.hs   (illustrative — adapt App/Context/fields)
module Library.Loan.Entity (
  LoanEntity (..),
  initialState,
) where

import Core
import Json qualified
import Uuid qualified


-- STEP 1 — add the new field to the record.
-- Make it Maybe so old snapshots (which lack the field) still decode.
data LoanEntity = LoanEntity
  { loanId    :: Uuid
  , memberId  :: Uuid
  , bookTitle :: Text
  , returnedAt :: Maybe Text   -- NEW: Nothing = not yet returned
  }
  deriving (Generic)


-- STEP 2 — empty Generic instances remain unchanged.
-- Generic FromJSON tolerates a missing Maybe field, decoding it as Nothing.
instance Json.FromJSON LoanEntity


instance Json.ToJSON LoanEntity


instance Default LoanEntity where
  def = initialState


-- STEP 3 — give the new field a value in initialState.
initialState :: LoanEntity
initialState =
  LoanEntity
    { loanId     = Uuid.nil
    , memberId   = Uuid.nil
    , bookTitle  = ""
    , returnedAt = Nothing   -- NEW default
    }


type instance NameOf LoanEntity = "LoanEntity"


instance Entity LoanEntity where
  initialStateImpl = initialState
  updateImpl = update


-- STEP 4 — update the fold: every relevant event case sets the new field.
-- Cases that don't affect the field leave it unchanged via record-update syntax.
update :: LoanEvent -> LoanEntity -> LoanEntity
update event entity = case event of
  LoanOpened {entityId, memberId, bookTitle} ->
    LoanEntity
      { loanId     = entityId
      , memberId   = memberId
      , bookTitle  = bookTitle
      , returnedAt = Nothing   -- new field initialised on creation
      }
  BookReturned {returnedAt} ->
    entity { returnedAt = Just returnedAt }   -- NEW: set on the return event
```

---

## Template B: non-`Maybe` field with a JSON default

When the new field is conceptually required (e.g., a quantity or a flag) but must have a sensible value on old snapshots, write a custom `parseJSON` using `Json.withObject`, `.:?`, and `.!=`. These operators are exported directly by `Json` and grounded in `/core/json/Json.hs`.

```haskell
-- src/Library/Loan/Entity.hs   (illustrative — adapt fields)
module Library.Loan.Entity (
  LoanEntity (..),
  initialState,
) where

import Core
import Json qualified
import Uuid qualified


data LoanEntity = LoanEntity
  { loanId       :: Uuid
  , memberId     :: Uuid
  , bookTitle    :: Text
  , durationDays :: Int   -- NEW: required conceptually; old snapshots lack it
  }
  deriving (Generic)


-- STEP 2 — write a CUSTOM parseJSON; do NOT keep the empty Generic instance.
-- .:?  extracts an optional field (returns Parser (Maybe value))
-- .!=  provides the default when the field is absent
instance Json.FromJSON LoanEntity where
  parseJSON = Json.withObject "LoanEntity" \obj -> do
    loanId       <- obj Json..: "loanId"
    memberId     <- obj Json..: "memberId"
    bookTitle    <- obj Json..: "bookTitle"
    durationDays <- obj Json..:? "durationDays" Json..!= 14  -- 14-day default for old snapshots
    Json.yield LoanEntity {loanId, memberId, bookTitle, durationDays}


instance Json.ToJSON LoanEntity


instance Default LoanEntity where
  def = initialState


-- STEP 3 — give the field a value in initialState.
initialState :: LoanEntity
initialState =
  LoanEntity
    { loanId       = Uuid.nil
    , memberId     = Uuid.nil
    , bookTitle    = ""
    , durationDays = 14   -- NEW default
    }


type instance NameOf LoanEntity = "LoanEntity"


instance Entity LoanEntity where
  initialStateImpl = initialState
  updateImpl = update


-- STEP 4 — update the fold.
update :: LoanEvent -> LoanEntity -> LoanEntity
update event entity = case event of
  LoanOpened {entityId, memberId, bookTitle, durationDays} ->
    LoanEntity
      { loanId       = entityId
      , memberId     = memberId
      , bookTitle    = bookTitle
      , durationDays = durationDays   -- NEW: set from the creation event
      }
  BookReturned {} ->
    entity   -- durationDays unchanged on return
```

---

## The four-step checklist

Every field addition requires all four steps. Skipping any one breaks compilation or replay:

1. **Record** — add `newField :: FieldType` to the `data Entity` declaration.
2. **`initialState`** — add `newField = defaultValue` to the `initialState` expression.
3. **`update` fold** — add (or update) the relevant `case event of` branches to set `newField`. Branches that don't touch the field leave it via `entity { ... }` record-update; do not duplicate all fields.
4. **JSON decode** — either make the field `Maybe` (Generic `FromJSON` tolerates absence) or write a custom `parseJSON` with `.:?` / `.!=`.

The `update` fold must remain **exhaustive** — every constructor in the event ADT must have a branch.

---

## DO / DON'T

| Vanilla-Haskell reflex — DON'T | NeoHaskell-correct — DO | Why |
|---|---|---|
| Remove or rename an existing field | Add new fields only | Removing breaks replay of the event log and decoding of old snapshots |
| Add a non-`Maybe` required field and keep the empty `instance Json.FromJSON Entity` | Use `Maybe` or write a custom `parseJSON` with `.:?` / `.!=` | aeson's Generic `FromJSON` rejects a JSON object missing a required field — old snapshots break on deploy |
| `import Data.Aeson` and use `(.:?)` from aeson directly | `import Json qualified` and use `Json..:?` / `Json..!=` | The NeoHaskell `Json` module re-exports these operators with `Text` keys; mixing aeson directly causes import conflicts |
| `entity { newField = val, existingField = entity.existingField }` | `entity { newField = val }` | Record-update syntax preserves all unmentioned fields automatically — never re-copy them |
| `where` clauses or `let .. in` for local bindings in `parseJSON` | `do let x = ..` inside the `do` block | NeoHaskell's style guide forbids `where` and `let..in` |
| `pure LoanEntity {..}` at the end of `parseJSON` | `Json.yield LoanEntity {..}` | `pure` is the vanilla Haskell reflex; `Json.yield` (re-exported from aeson's `Parser`) is idiomatic in NeoHaskell `Json` context |
| `instance Json.FromJSON Entity where parseJSON = genericParseJSON defaultOptions` | Leave the empty `instance Json.FromJSON Entity` OR write the custom body | The empty instance `instance Json.FromJSON Entity` already uses Generic; adding an explicit `genericParseJSON` call is redundant and verbose |
| Write a `V2` sibling for the entity | Edit the existing `Entity.hs` (add only) | Entities are not locked — a `LoanEntityV2.hs` is wrong; only files under `Commands/`, `Events/`, `Queries/` get V2 siblings |
| Non-exhaustive `update` fold (missing event cases) | `case event of` with a branch for every constructor | A non-exhaustive match compiles with `-Wincomplete-patterns` but panics at runtime when the missing event fires |

---

## Replay-safety check (mental model)

Before deploying, reason through the following scenario:

1. The event store contains 1 000 events from before the field was added. None of their snapshots contain `"newField"`.
2. On the next fetch, the framework replays all events through `update`, starting from `initialState`.
3. `initialState` must give `newField` a value.
4. Every `update` case must propagate or set `newField`.
5. If there are any stored entity snapshots (the framework can cache them), those snapshots are decoded by `FromJSON`. If they lack `"newField"`, the decoder must tolerate its absence — which requires either `Maybe` or `.:?` / `.!=`.

If all five points hold, the expansion is replay-safe.

---

## Verify

```
neo build
```

A successful build confirms:
- The new field is in scope everywhere `Entity.hs` is imported.
- The `update` fold is exhaustive (no `-Wincomplete-patterns`).
- The custom `parseJSON` (if used) compiles against `Json.withObject`, `Json..:?`, and `Json..!=`.

To confirm backward-compat manually, construct an old-format JSON object without the new field and decode it:

```haskell
-- In a REPL or test:
let oldJson = "{\"loanId\":\"...\",\"memberId\":\"...\",\"bookTitle\":\"Dune\"}"
Json.decodeText @LoanEntity oldJson
-- Should be: Ok LoanEntity { ..., returnedAt = Nothing }
-- or:        Ok LoanEntity { ..., durationDays = 14 }
```
