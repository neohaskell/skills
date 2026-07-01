---
name: neohaskell-domain-modeling
description: >-
  The NeoHaskell DOMAIN-PHASE discipline for turning a failing test's implied types into
  precise domain types: value objects with smart constructors, ADTs that make illegal states
  unrepresentable, parse-don't-validate at the boundary, and the
  Natural/Decimal/Redacted/Uuid wrappers and enum sum types. Use whenever a red test
  references a type that does not exist yet, when adding a
  field/quantity/money/id/secret/status value, or when replacing a Text or Int primitive
  with a domain type — even if the user says only 'add a field' or 'model this'. Stubs
  bodies with panic 'TODO' (or Integration.none) so the module compiles and the test fails
  on the assertion. Do NOT use to fill in real decide/combine/handleEvent LOGIC (the
  implement-* skills), to derive JSON instances (neohaskell-records-and-json), to add a
  field to a live entity's snapshot decoder (expand-entity), or to run event-
  storming/discovery (augment-feature-request). Load after write-unit-tests, before the
  implement-* skills.
metadata:
  model: sonnet
---

**This is NeoHaskell, not vanilla Haskell.** The `.hs` extension is shared, but the prelude, wrapper types, and error type differ — a vanilla reflex (`Int` for a count, `Either` for a smart constructor, `error` for a stub, `String` for an id) compiles silently and produces the wrong model. Every module opens with `import Core`.

---

## Inputs / Outputs / Next

- **Input:** a **red** `write-unit-tests` / acceptance spec (from the RED phase) that references types, fields, value objects, or enums that do not exist yet.
- **Output:** the **type definitions** — records, value objects, enums, smart constructors, and function signatures — with **stubbed bodies**, so the module compiles and the red spec now fails on its **assertion**, not on a missing type.
- **Next:** `implement-command` · `implement-event-and-update-entity` · `implement-query` · `implement-integration` (the GREEN phase fills the stubs in).

---

## Where this sits in the cycle: the DOMAIN phase (jwilger ④)

The per-slice loop is **RED → DOMAIN → GREEN → REFACTOR**. This skill owns **DOMAIN**, and the phase boundary is strict — `neohaskell-code-review` flags violations:

- **RED** touches only test files (`write-unit-tests`, `write-feature-tests`, `write-hurl-e2e`).
- **DOMAIN** (here) touches only **type definitions** — new records, value objects, enums, and function *signatures* — with bodies stubbed via `panic "TODO: not implemented"` (or `Integration.none` for an outbound `handleEvent`). Write **no real logic**; that is GREEN's job.
- **GREEN** (the `implement-*` skills) touches only implementation **bodies**, replacing the stubs.

The goal of DOMAIN is narrow and mechanical: **make the red test compile.** In a compiled language the RED signal is often a *type error* ("no such field", "not in scope"). DOMAIN introduces exactly the types the test names — no more — so the compiler is satisfied and the test now fails on its `shouldBe` assertion instead. That is the handoff signal to GREEN.

> **Model tier — sonnet.** This skill is template-driven reasoning. In Claude Code, delegate the type-design step to a sub-agent spawned with `model: sonnet`; in hosts without sub-agents (Cursor/Codex) that is advisory and the skill runs inline. Either way the output is the same: stubbed type definitions.

Deeper rationale, worked refactors, and the full principle list live in **[`references/domain-modeling-principles.md`](references/domain-modeling-principles.md)** (adapted, MIT-attributed, from John Wilger's `domain-modeling`). Read it when a model is non-obvious; this file is the fast path.

---

## The four moves

1. **Replace primitives with value objects.** A count is not an `Int`; money is not a `Float`; a secret is not a `Text`; an id is not a `Text`. Reach for `Natural`, `Decimal`, `Redacted`, `Uuid`, or a bespoke `newtype`/enum.
2. **Make illegal states unrepresentable.** Model the domain so a wrong value *cannot be constructed*. An enum of the three legal statuses beats a `Text` that could hold `"bananas"`; a sum type of records beats a bag of `Maybe` fields that can be simultaneously set and unset.
3. **Parse, don't validate — at the boundary.** Convert untrusted input into a valid type *once*, at the edge, via a **smart constructor** that returns `Result`/`Maybe`. After that, the type itself is the proof; downstream code never re-checks.
4. **Stub the bodies.** Give every new function a real signature and a stub body so the module compiles: `panic "TODO: not implemented"` for pure/`Task` bodies, `Integration.none` for an outbound `handleEvent`. There is **no `todo`** in NeoHaskell.

---

## Value-object catalogue (grounded in `core/core` + `core/decimal`)

The `Natural`, `Decimal`, `Redacted`, and `Uuid` **types** are re-exported by `Core` — no import needed for the type. Their **functions** need a qualified import of the wrapper module.

| Domain need | Type | Import for its functions | Construct with | Notes |
|---|---|---|---|---|
| a count / quantity that must be > 0 | `Natural Int` | (in `Core`) | `makeNatural :: (Ord n, Num n) => n -> Maybe (Natural n)` or `makeNaturalOrPanic` | constructor is exported (`Natural (..)`) but always use the smart constructor — the bare constructor bypasses the positivity check. Grounded: `Basics.hs`, `Cart/Core.hs` (`amount :: Natural Int`). |
| money / precise decimal | `Decimal` | `import Decimal qualified` | `Decimal.decimal :: Float -> Decimal`, `Decimal.fromCents`, `Decimal.zero`, `Decimal.parseDecimal :: Text -> Maybe Decimal` | fixed-point `Int64`, no float error; divide with `Decimal.divide :: Decimal -> Decimal -> Maybe Decimal` (not `/`). Grounded: `Decimal.hs`. |
| a secret / PII | `Redacted Text` | `import Redacted qualified` | `Redacted.wrap`, `Redacted.labeled`, `Redacted.empty` | `Show` prints `<redacted>`; read with `Redacted.unwrap`. Has **no** `ToJSON`, **no** `Eq`, **no** `Generic` — by design. Grounded: `Redacted.hs`. |
| an identity | `Uuid` | `import Uuid qualified` | `Uuid.generate :: Task _ Uuid`, `Uuid.fromText :: Text -> Maybe Uuid`, `Uuid.nil` | never a `Text`. Ids are generated inside `decide` with `Decider.generateUuid`. Grounded: `Uuid.hs`, `Cart/Core.hs`. |
| a fixed set of states | your own enum | (in the module) | `data S = A \| B \| C deriving (Eq, Show, Ord, Generic)` + empty `Json` instances | see the enum template below. Grounded pattern: `Log.hs` (`data Level = Debug \| Info \| Warn \| Error`). |

### Natural — a quantity that cannot be zero-or-negative

```haskell
-- Grounded in testbed/src/Testbed/Cart/Core.hs (CartItem.amount :: Natural Int)
import Core   -- brings Natural, makeNatural, makeNaturalOrPanic into scope

-- Field on an entity or event payload:
--   amount :: Natural Int      -- NOT `amount :: Int`

-- Smart-constructor use (returns Maybe — Nothing when input <= 0):
mkQty :: Int -> Maybe (Natural Int)
mkQty raw = makeNatural raw

-- When you have already proven positivity (e.g. inside an update fold after
-- decide accepted the command), makeNaturalOrPanic converts a raw Int:
--   amount = makeNaturalOrPanic quantity
```

### Decimal — money without floating-point error

```haskell
import Core
import Decimal (Decimal)   -- also re-exported by Core; explicit here for clarity
import Decimal qualified

-- Field:  price :: Decimal        -- NOT `price :: Float`
-- Build:  Decimal.decimal 12.50   -- Decimal (represents 12.5000)
-- Parse at the edge (Text -> Maybe Decimal):
mkPrice :: Text -> Maybe Decimal
mkPrice raw = Decimal.parseDecimal raw
-- Divide safely (NeoHaskell's `/` is Float-only): Decimal.divide a b :: Maybe Decimal
```

### Redacted — a secret that never leaks into logs

```haskell
import Core
import Redacted qualified

-- Field:  apiToken :: Redacted Text     -- NOT `apiToken :: Text`
-- Wrap incoming secret:   Redacted.wrap rawToken
-- Show apiToken           -- prints "<redacted>", not the value
-- Use it (explicit):      sendAuth (Redacted.unwrap apiToken)
-- Redacted has NO ToJSON — you cannot accidentally serialize it.
```

### Enum — make an illegal status unrepresentable

```haskell
-- Illustrative Library domain (BookTitle / Member / Loan) — neutral, not a real project.
-- Grounded pattern: core/core/Log.hs `data Level = Debug | Info | Warn | Error`.
module Library.Loan.LoanStatus (
  LoanStatus (..),
) where

import Core
import Json qualified


-- A Loan is exactly one of these three. A `status :: Text` field could hold
-- "bananas"; this type cannot. That is "illegal states unrepresentable".
data LoanStatus
  = OnLoan
  | Returned
  | Overdue
  deriving (Eq, Show, Ord, Generic)


-- Empty Generic instances (never deriving/TH). See neohaskell-records-and-json.
instance Json.FromJSON LoanStatus
instance Json.ToJSON LoanStatus
```

---

## Template — a bespoke value object with a smart constructor

Parse-don't-validate in one module: the data constructor is **hidden** (export `Isbn`, not `Isbn (..)`), so the *only* way to build one is `makeIsbn`, which enforces the invariant. The pattern mirrors how `Natural`, `Uuid`, and `Decimal` hide their constructors behind `makeNatural` / `fromText` / `parseDecimal`.

```haskell
-- Illustrative Library domain. Grounded idioms: hidden-constructor + smart
-- constructor (Basics.hs Natural, Uuid.hs), Json.withText parse (Json.hs).
module Library.Loan.Isbn (
  Isbn,        -- export the TYPE only — NOT `Isbn (..)` — to hide the constructor
  makeIsbn,
  toText,
) where

import Core
import Json qualified
import Text qualified


-- newtype over Text, but the constructor never escapes this module.
newtype Isbn = Isbn Text
  deriving (Eq, Show, Ord, Generic)


-- Smart constructor: the boundary. Returns Result with a typed reason so the
-- caller must handle the failure (parse, don't validate).
makeIsbn :: Text -> Result Text Isbn
makeIsbn raw =
  case Text.length (Text.trim raw) == 13 of
    True -> Result.Ok (Isbn (Text.trim raw))
    False -> Result.Err [fmt|ISBN must be 13 characters, got: #{raw}|]


-- Read the underlying value when you truly need the Text (e.g. rendering).
toText :: Isbn -> Text
toText (Isbn value) = value


instance Json.ToJSON Isbn


-- JSON decode also goes through the invariant — a malformed wire value is
-- rejected at parse time, not silently trusted. Grounded: Json.hs `withText`.
instance Json.FromJSON Isbn where
  parseJSON =
    Json.withText "Isbn" \text ->
      case makeIsbn text of
        Result.Ok isbn -> Json.yield isbn
        Result.Err msg -> Json.fail msg
```

> An **empty** `instance Json.FromJSON Isbn` would let any 5-character string decode into an `Isbn`, bypassing `makeIsbn`. Hand-write `parseJSON` (as above) whenever a value object has an invariant to preserve at the wire boundary. Use empty Generic instances only for plain records with no invariant.

---

## Template — the DOMAIN-phase deliverable for a slice

When the red unit test says `decide` should reject a zero quantity, DOMAIN introduces the command record, the value-object-typed fields, and a **stubbed** `decide` so it compiles. GREEN (`implement-command`) writes the real `decide`.

```haskell
-- Grounded in testbed/src/Testbed/Cart/Commands/AddItem.hs (structure + imports)
-- and Decider.hs (Decision). DOMAIN phase: types real, body stubbed.
module Library.Loan.Commands.BorrowBook (
  BorrowBook (..),
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
import Library.Loan.Core


data BorrowBook = BorrowBook
  { memberId :: Uuid            -- an id is a Uuid, never a Text
  , copies   :: Natural Int     -- a count is a Natural Int, never a plain Int
  }
  deriving (Generic, Typeable, Show)


instance Json.FromJSON BorrowBook


getEntityId :: BorrowBook -> Maybe Uuid
getEntityId cmd = Just cmd.memberId


-- Signature is real; body is a STUB so the module compiles. panic :: Text -> a,
-- so it type-checks as Decision LoanEvent. GREEN replaces this.
decide :: BorrowBook -> Maybe LoanEntity -> RequestContext -> Decision LoanEvent
decide _cmd _entity _ctx = panic "TODO: not implemented"


type instance EntityOf BorrowBook = LoanEntity


type instance TransportsOf BorrowBook = '[WebTransport]


command ''BorrowBook
```

### Stub for an outbound integration handler

A pure `handleEvent` is called by the dispatcher for *every* event of its entity, so a `panic` there **crashes the running app** the moment that event fires. Stub it with `Integration.none` and a comment instead:

```haskell
-- Grounded in testbed/.../Integrations/ReserveStockOnItemAdded.hs
handleEvent :: LoanEntity -> LoanEvent -> Integration.Outbound
handleEvent _entity _event =
  -- TODO: emit the cross-aggregate command in GREEN (implement-integration)
  Integration.none
```

---

## Event-sourced design patterns

Four recurring decisions that shape the DOMAIN types. The *mechanics* live in the `implement-*` skills; the *design rationale* is here.

### Natural-key identity — uniqueness without reading other aggregates

A `decide` sees only its own aggregate (its entity `Maybe`, never another stream), so it cannot enforce "no duplicate by business key `x`" (e.g. unique project name) by looking around. Instead, derive the entity's **stream id deterministically** from `x` — `getEntityId cmd = Just (deriveId cmd.x)`, **not** a random `Uuid`. A second create then resolves to the *same* stream, so `decide` sees `Just entity` and rejects the duplicate. Request/response shape is identical to a generated-id create.

**Sharp edge — this was the code-review finding.** Because the id *is* the natural key, once the stream exists it can **never** be re-created — even after "archiving" it. A creation command uses `acceptNew`, which requires the stream to *not* exist (`StreamCreation`), so there is no "re-register as new". Reactivation must be a **separate `Unarchive`-style command** acting on the *existing* stream (`acceptExisting`), not a re-create. → `implement-command` holds the `acceptNew`/`StreamCreation` mechanics.

### Trusted / denormalized cross-aggregate references

Because a `decide` cannot read another aggregate's state, a reference to another entity — `task.projectId`, `worktree.repoPath`, `session.worktreeId` — is **carried on the command (and event) and trusted**: the UI supplies a valid id, and the command stores it denormalized without confirming the referenced aggregate exists or is in a valid state. Strict cross-aggregate enforcement (reject a task whose project was deleted) is *not* expressible in `decide`; it would need a **saga / process manager** reacting to both streams. Model these references as plain `Uuid`/`Text` fields on the entity and event, and accept the trust boundary — do not try to validate them inside `decide`.

### Status-as-ADT, expose-as-text

Hold an entity's status as an **ADT** so illegal states are unrepresentable (the enum move above) — never a `Text` that could be `"bananas"`. But do **not** leak that ADT into a read model's JSON: the query's `combine` maps it to a **stable `Text` tag** (a small `statusToText` helper) so the wire contract survives the ADT later gaining constructors. Entity holds the ADT; read model exposes `Text`. → `implement-query` holds the `statusToText`-in-`combine` how.

### Composed read models + count-via-id-set

One read model can be fed by **several** entity streams keyed by a common id — e.g. `deriveQuery ''ProjectOverview [''ProjectEntity, ''TaskEntity, ''WorktreeEntity]`, one `QueryOf` instance per entity, each contributing its slice to the same `queryId` row (the dashboard / aggregate-view pattern). Caveat for **distinct counts**: `combine` fires on every event of a contributor and only ever sees *that* entity's current folded state, never the set of contributors — so `count = existing.count + 1` **over-counts**. Hold an **id-set** (a deduped `Array Uuid`, or a `Set`) in the read model and derive the count from its size. → `implement-query` holds the multi-entity `deriveQuery` mechanics.

---

## DO / DON'T

| Vanilla reflex — DON'T | NeoHaskell / domain-modeling — DO | Why |
|---|---|---|
| `quantity :: Int` for a count | `quantity :: Natural Int` | A count is never zero-or-negative; encode it in the type. |
| `price :: Float` for money | `price :: Decimal` | `Float` accumulates rounding error; `Decimal` is exact fixed-point. |
| `id :: Text` | `id :: Uuid` | Ids are `Uuid`; a `Text` id invites malformed values. |
| `apiToken :: Text` for a secret | `apiToken :: Redacted Text` | `Redacted` hides the value in `Show`/logs and refuses `ToJSON`. |
| `status :: Text` | an enum: `data Status = A \| B \| C` | A `Text` can hold an illegal status; an enum cannot. |
| `Either Err a` from a smart constructor | `Result Err a` (`Result.Ok` / `Result.Err`) | Error is the **first** param and constructors are `Ok`/`Err`, not `Left`/`Right`. |
| `error "TODO"` / `undefined` as a stub | `panic "TODO: not implemented"` | `panic :: Text -> a`; there is no `todo`. |
| `panic` inside an outbound `handleEvent` | `Integration.none` + a `-- TODO:` comment | A pure handler is called per-event; a panic there crashes the dispatcher. |
| exporting `Isbn (..)` (constructor visible) | export `Isbn` only + a `makeIsbn` smart constructor | A visible constructor lets callers bypass the invariant. |
| empty `Json.FromJSON` on a validated value object | hand-write `parseJSON` via `Json.withText` + the smart constructor | Parse-don't-validate: reject bad wire input at the boundary. |
| writing the real `decide`/`combine` logic here | a stub body; leave logic to the `implement-*` GREEN step | DOMAIN only defines types; mixing phases breaks the boundary. |
| a bag of `Maybe` fields that can all be set/unset | a sum type where each case carries exactly its own data | Prevents representable-but-illegal combinations. |
| `String` / `[Char]` anywhere | `Text` | String literals are already `Text`. |

---

## Verify

```
neo build
```

DOMAIN is done when **the module compiles with stubbed bodies** and the previously-red test now fails on its **assertion** (e.g. `shouldBe`) rather than a "not in scope" / "no instance" type error. That failure is the green light to move to the GREEN phase (`implement-*`).

If `neo build` reports a missing type or field, you have not yet introduced everything the test names — add the type, keep the body stubbed. If it reports "No instance for (Json.FromJSON …)", add the empty Generic instance (plain record) or the hand-written `parseJSON` (validated value object). If a `handleEvent` stub uses `panic`, switch it to `Integration.none`.
