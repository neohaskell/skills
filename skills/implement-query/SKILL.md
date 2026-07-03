---
name: implement-query
description: >-
  Implements a NeoHaskell QUERY / read-model module at Queries/Name.hs — the record, Json
  and ToSchema instances, canAccess and canView auth functions, the deriveQuery macro, and a
  hand-written QueryOf instance whose combine returns Update, NoOp, or Delete. Use in the
  GREEN phase after neohaskell-domain-modeling stubbed the types and write-unit-tests left a
  failing Projection spec. Also use when asked to add a read model, implement or fill in
  combine logic, replace a projection panic stub, handle a verified query node, or set up
  per-instance access control. Both canAccess and canView are required — deriveQuery fails
  to compile if either is missing. Do NOT use for the command/decide module (implement-
  command), the event payload (implement-event-and-update-entity), the integration handler
  (implement-integration), or wiring (wire-feature). This is NeoHaskell — IO, Data.Aeson,
  Either, and unqualified list functions are all wrong here.
metadata:
  model: sonnet
---

**This is NeoHaskell, not vanilla Haskell.** The `.hs` extension is shared, but NeoHaskell runs a custom `Core` prelude — `import Core`, not `import Prelude`. Every identifier, operator, and module name in this skill is grounded in public testbed sources (`Testbed.Cart.Queries.CartSummary`, `Testbed.Stock.Queries.StockLevel`) and the framework's `Service.Query.Core`.

---

## TDD cycle role — GREEN phase

This skill runs in **step ⑤ (GREEN)** of the outside-in cycle:

```
write-hurl-e2e (RED outer) →
  write-feature-tests (RED) →
    write-unit-tests (RED, Projection spec) →
      neohaskell-domain-modeling (DOMAIN, types + panic stubs) →
        ► implement-query (GREEN, fill in combine logic) ◄
          wire-feature (GREEN, endpoint live)
```

The Projection unit test must be RED (failing on the assertion, not a type error) before you write this file. The `combine` body you write here should make it go green.

In Claude Code, delegate the implementation step to a sub-agent spawned with `model: sonnet`. In Cursor or Codex this is advisory — run it inline.

---

## Inputs / Outputs / Next

- **Input:** a verified query node from `event-model.json` (name, entity or entities, field list) and the entity record(s) produced by `implement-event-and-update-entity` / `expand-entity`.
- **Output:** `src/<App>/<Context>/Queries/<Name>.hs` with a compiling, test-passing `combine`.
- **Next:** `wire-feature` (register the query with `withQuery @Q`) · `write-unit-tests` (Projection spec goes green)

---

## Why both canAccess and canView are mandatory

`deriveQuery` resolves `canAccess` and `canView` **by name in the current module** at Template Haskell splice time. If either is missing, the macro emits a compile error with an explicit message. There is no default — always write both, even for public data.

| Function | When it runs | Signature |
|---|---|---|
| `canAccess` | Before any storage lookup — "may this user query this type at all?" | `Maybe UserClaims -> Maybe AccessError` |
| `canView` | After data is fetched — "may this user see this specific instance?" | `Maybe UserClaims -> Query -> Maybe AccessError` |

Secure starting point (recommended for non-public data):

```haskell
canAccess :: Maybe UserClaims -> Maybe AccessError
canAccess = AccessControl.authenticatedAccess   -- requires a valid JWT

canView :: Maybe UserClaims -> CartSummary -> Maybe AccessError
canView = AccessControl.ownerOnly (.ownerId)    -- only the owner sees their record
```

Public/demo variant (used in CartSummary and StockLevel testbed sources):

```haskell
canAccess :: Maybe UserClaims -> Maybe AccessError
canAccess claims = AccessControl.publicAccess claims

canView :: Maybe UserClaims -> CartSummary -> Maybe AccessError
canView claims cartSummary = AccessControl.publicView claims cartSummary
```

---

## Template — single-entity query

Adapted from `Testbed.Cart.Queries.CartSummary` (public testbed). Replace `App`, `Context`, `Query`, `Entity`, and field names for your domain.

```haskell
-- src/<App>/<Context>/Queries/<Name>.hs
-- [LOCKABLE once deployed — never edit; add <Name>V2.hs instead]
module App.Context.Queries.CartSummary (
  CartSummary (..),
  canAccess,
  canView,
) where

import Array qualified
import Core
import Json qualified
import Service.AccessControl (AccessError, UserClaims)
import Service.AccessControl qualified as AccessControl
import Service.Query.TH (deriveQuery)
import App.Context.Core (CartEntity (..))


-- | Read model — denormalised view of cart state for fast reads.
data CartSummary = CartSummary
  { cartSummaryId :: Uuid
  , ownerId       :: Text
  , itemCount     :: Int
  , isEmpty       :: Bool
  }
  deriving (Eq, Show, Generic)


instance Json.ToJSON CartSummary


instance Json.FromJSON CartSummary


instance ToSchema CartSummary


-- | Checked BEFORE any storage access.
canAccess :: Maybe UserClaims -> Maybe AccessError
canAccess = AccessControl.authenticatedAccess


-- | Checked AFTER data is fetched, per instance.
canView :: Maybe UserClaims -> CartSummary -> Maybe AccessError
canView = AccessControl.ownerOnly (.ownerId)


-- | Generates: NameOf, EntitiesOf, Query instance (wiring canAccess/canView),
-- KnownHash, ToSchema instance, and Json boilerplate.
deriveQuery ''CartSummary [''CartEntity]


-- | How CartEntity contributes to CartSummary.
instance QueryOf CartEntity CartSummary where
  -- Key: which query instance does this entity update?
  queryId cart = cart.cartId

  -- Called every time the entity changes. Returns Update/NoOp/Delete.
  combine cart _maybeExisting = do
    let count = cart.items |> Array.length
    Update
      CartSummary
        { cartSummaryId = cart.cartId
        , ownerId       = cart.ownerId
        , itemCount     = count
        , isEmpty       = count == 0
        }
```

---

## Template — simpler combine (no derived field)

When the read model is a direct projection of the entity (no computed field), pattern from `Testbed.Stock.Queries.StockLevel`:

```haskell
instance QueryOf StockEntity StockLevel where
  queryId stock = stock.stockId

  combine stock _maybeExisting =
    Update
      StockLevel
        { stockLevelId = stock.stockId
        , productId    = stock.productId
        , available    = stock.available
        , reserved     = stock.reserved
        }
```

---

## Pattern — expose a status ADT as a stable text tag

When the entity holds status as an **ADT** (illegal states unrepresentable), do **not** leak that ADT into the read model's JSON. Map it to a stable `Text` tag in `combine` via a small `statusToText` helper, so the JSON contract stays stable even if the ADT later gains constructors:

```haskell
-- Entity carries the ADT (in App.Context.Core):
--   data TaskStatus = Open | InProgress | Done

statusToText :: TaskStatus -> Text
statusToText status = case status of
  Open       -> "open"
  InProgress -> "in-progress"
  Done       -> "done"


instance QueryOf TaskEntity TaskSummary where
  queryId task = task.taskId

  combine task _maybeExisting =
    Update TaskSummary
      { taskSummaryId = task.taskId
      , status        = statusToText task.status   -- Text, not the ADT
      }
```

The read model field is `status :: Text`; the entity keeps the ADT. Illegal states stay unrepresentable in the domain while API consumers get a stable string enum (`"open"`/`"in-progress"`/…). See `neohaskell-domain-modeling` for the entity-side ADT.

---

## DOMAIN-phase stub (before GREEN)

When `neohaskell-domain-modeling` creates the file and you need it to compile but not yet pass:

```haskell
instance QueryOf CartEntity CartSummary where
  queryId _cart = panic "TODO: not implemented"

  combine _cart _maybeExisting = panic "TODO: not implemented"
```

`panic` is the only correct stub for pure function bodies. Never use `pure`, `return`, or `undefined`. The Projection test will fail on the `panic`, which is the expected RED state.

---

## combine return values

The `combine` function returns a `QueryAction query`, which has exactly three constructors — all in scope via `import Core`:

| Constructor | Meaning |
|---|---|
| `Update q` | Write or overwrite this query instance with the new value `q` |
| `NoOp` | Leave the stored query instance unchanged |
| `Delete` | Remove this query instance from the store |

`combine` receives the **current entity state** (after replaying all events) and the **existing query instance** (`Maybe query`). The existing value lets you merge without losing prior data:

```haskell
combine order maybeExisting = case maybeExisting of
  Nothing       -> NoOp   -- can't attach an order to a non-existent summary
  Just existing -> Update existing { orderCount = existing.orderCount + 1 }
```

`combine` must be **total** — cover every branch. A non-exhaustive `combine` causes a runtime crash when an uncovered entity state is processed.

---

## Query response shape

The HTTP endpoint returns results as a JSON object with an `items` array:

```json
{ "items": [ { "cartSummaryId": "...", "ownerId": "...", ... } ] }
```

When writing hurl assertions (see `write-hurl-e2e`), use `$.items[?...]` JSONPath, not `$[?...]`.

---

## Composed read models — collection fields, `(..)` imports, constructor-merge

Before writing a read model that aggregates **more than one** source entity, three facts — each costs a build cycle if missed:

**1. Query fields may be collections.** `ToSchema (Array element)` and `ToSchema [element]` both exist (`core/schema/Schema.hs:161`/`:165`), and `Array a` has `Json.ToJSON`/`Json.FromJSON` whenever `a` does (`core/json/Json.hs:77`/`:80` — the instances live in `Json.hs`, *not* `Array.hs`). So `Array Uuid` is a legal read-model field — the basis for the idempotent id-set count below. (`Uuid` is `ToSchema` as `SText`, so `Array Uuid` self-describes as a JSON array of strings.)

**2. Import every record you read via dot with `(..)` — a type-only import fails.** Under `NoFieldSelectors` + `DuplicateRecordFields` + `OverloadedRecordDot`, `entity.projectId` desugars to `getField @"projectId" entity`, needing `HasField "projectId" Entity _`. GHC only conjures that instance when the field **label** `projectId` is in scope at the use site, and with `NoFieldSelectors` the label is brought in **only** by importing the record with `(..)`. A type-only `import M (Entity)` brings the type but not the labels, so dot access fails:

```
error: [GHC-39999] • No instance for 'HasField "projectId" WorktreeEntity Uuid'
      NB: There is no field selector 'projectId :: WorktreeEntity'
```

This bites twice: import **every source entity** you read via dot as `Entity (..)` in the query module, **and** import the **read-model type itself** as `ReadModel (..)` in any downstream projection spec that reads it via dot (e.g. `o.taskCount`). Always export your read model with `(..)` so specs can. (The single-entity templates above already import their entity with `(..)` because they *construct* rows — the same `(..)` is what makes dot *reads* resolve.)

**3. Merge by re-invoking the constructor, not record update.** In a composed projection each `combine` should rebuild the whole row via its **constructor** — `Update ReadModel { field = … }` — carrying the *other* entities' fields forward from `maybeExisting`, rather than `Update existing { field = … }`. Record-update syntax on a field name shared with a source entity (e.g. `name`, `projectId`) trips `-Wambiguous-fields` under `DuplicateRecordFields`; the constructor form is unambiguous and side-steps it entirely.

---

## Multi-entity query (ADVANCED — illustrative Library domain)

**Haddock-grounded from `Service.Query.Core` — not a compiling public source. Mark as advanced in code comments.**

When a read model aggregates two entities, declare one `instance QueryOf E Q` per entity and pass both to `deriveQuery`. Each `combine` **rebuilds the whole row via the constructor** (rule 3 above), carrying the *other* entity's fields forward from `maybeExisting`, and derives any **count** from a deduped `Array Uuid` id-set instead of incrementing:

```haskell
-- The read model carries an id-set so the distinct count is idempotent.
data MemberLoanSummary = MemberLoanSummary
  { summaryId       :: Uuid
  , memberName      :: Text
  , loanIds         :: Array Uuid   -- id-set → the count is derived from its size
  , activeLoanCount :: Int
  }
  deriving (Eq, Show, Generic)


-- deriveQuery wires BOTH entities as subscribers
deriveQuery ''MemberLoanSummary [''MemberEntity, ''LoanEntity]


-- Entity 1: the member seeds identity + name; carries the loan-side fields forward.
instance QueryOf MemberEntity MemberLoanSummary where
  queryId member = member.memberId

  combine member maybeExisting =
    Update
      MemberLoanSummary
        { summaryId       = member.memberId
        , memberName      = member.name
        , loanIds         = maybeExisting |> Maybe.map (.loanIds) |> Maybe.withDefault Array.empty
        , activeLoanCount = maybeExisting |> Maybe.map (.activeLoanCount) |> Maybe.withDefault 0
        }


-- Entity 2: loans fold into the id-set; the count is its size. Rebuild via the
-- constructor and carry the member-side fields (summaryId, memberName) forward.
instance QueryOf LoanEntity MemberLoanSummary where
  queryId loan = loan.memberId   -- same key space as MemberEntity

  combine loan maybeExisting = case maybeExisting of
    Nothing       -> NoOp  -- don't create a summary for a non-existent member
    Just existing -> do
      let loanIds =
            if existing.loanIds |> Array.contains loan.loanId
              then existing.loanIds
              else existing.loanIds |> Array.push loan.loanId
      Update
        MemberLoanSummary
          { summaryId       = existing.summaryId       -- carried forward
          , memberName      = existing.memberName      -- carried forward
          , loanIds         = loanIds                  -- deduped id-set
          , activeLoanCount = loanIds |> Array.length  -- derived, never `+ 1`
          }
```

*Imports: on top of the single-entity template, add `import Array qualified` (id-set ops) and `import Maybe qualified` (`Maybe.map`/`Maybe.withDefault`), and import **each** source entity with `(..)` (rule 2 above).*

Rules:
- `queryId` must return the **same Uuid key space** across all entities — the framework uses it to look up the stored query instance.
- The entity that "creates" the query instance (here `MemberEntity`) should handle `Nothing` with `Update`; secondary entities (here `LoanEntity`) should return `NoOp` when `Nothing` so they do not create phantom instances.
- Order of `instance QueryOf` declarations does not matter; `deriveQuery` uses the type-level list for subscription, not declaration order.

> **⚠️ Why an id-set, not `+ 1`.** `combine entity maybeExisting` fires on **every** event of a contributing entity and only ever sees **that** entity's *current* folded state — never the set of all contributors. So `activeLoanCount = existing.activeLoanCount + 1` increments on *every* loan event and **over-counts** (re-folds and repeated events all re-fire it). Holding the deduped `Array Uuid` and taking `loanIds |> Array.length` makes the count **idempotent** — replaying the same event is a no-op because `existing.loanIds |> Array.contains` already saw the id, so `Array.push` is skipped. (A `Set` works too.) The broader design rationale for composed read models lives in `neohaskell-domain-modeling`.

---

## DO / DON'T

| Vanilla-Haskell reflex — DON'T | NeoHaskell-correct — DO | Why |
|---|---|---|
| `import Data.Aeson` or `deriving (FromJSON, ToJSON)` | `import Json qualified`; empty `instance Json.ToJSON Q` and `instance Json.FromJSON Q` | NeoHaskell uses `Json` (aeson wrapper); `deriving` needs `anyclass` and is not the convention |
| `import Data.OpenApi` or `deriving (ToSchema)` | `instance ToSchema Q` (empty, Generic-derived) — `ToSchema` is in scope from `import Core` | `deriveQuery` generates a further `ToSchema` boilerplate call; the empty instance declaration seeds Generic |
| Skip `canAccess` or `canView` | Write **both** before `deriveQuery ''Q [''E]` | The macro fails at compile time with a clear error if either is absent; there is no default |
| `import Service.Auth (RequestContext)` for queries | Auth for queries uses `Service.AccessControl` only — `RequestContext` is the command `decide` argument, not needed here | Different auth API for commands vs queries |
| `combine entity existing = pure (Update q)` | `combine entity existing = Update q` (no `pure`) | `combine` returns `QueryAction query`, not `Task`/`IO`; `pure` wraps into the wrong type |
| `combine entity _existing = Update q` when `existing` carries data you need | Always inspect `_maybeExisting` if the read model preserves prior state across events | Ignoring `maybeExisting` silently drops aggregated data on each entity change |
| `combine entity existing = undefined` / non-exhaustive | Cover all cases: `Update`/`NoOp`/`Delete` as appropriate | A non-exhaustive `combine` crashes the query updater at runtime when the uncovered branch fires |
| `Array.filter` inside `combine` | `Array.takeIf` (keep matching) / `Array.dropIf` (drop matching) | `Array.filter` does not exist in NeoHaskell; `takeIf`/`dropIf` are the correct names |
| Dot access `(.cartSummaryId) cartSummary` | `cartSummary.cartSummaryId` | `NoFieldSelectors` is on project-wide — field names are not functions |
| `<>` to join text | `++` or `[fmt|...#{expr}...|]` | `<>` is `Appendable`; prefer interpolation for text; `++` for arrays/text concat |
| `/=` | `!=` | NeoHaskell operator for inequality |

---

## Verify

```
neo build
```

A successful build confirms:

- `deriveQuery ''CartSummary [''CartEntity]` splices without errors — `canAccess`, `canView`, `NameOf`, `EntitiesOf`, `Query`, and `KnownHash` all resolved.
- `instance QueryOf CartEntity CartSummary` is accepted — `QueryOf` is in scope from `Core`.
- `ToSchema CartSummary` instance is generated — the record fields are GHC-Generic-traversable.
- No `Prelude` leakage; no `IO` or `Task` inside `combine`.

Common compile errors:

| Error | Cause | Fix |
|---|---|---|
| `ERROR: Missing 'canAccess' function` | The function is absent or declared after `deriveQuery` | Declare `canAccess` and `canView` **before** `deriveQuery ''Q [''E]` in the file |
| `No instance for (ToSchema ...)` on an entity field type | A field's type lacks a `ToSchema` instance | Add a `deriving (Generic)` to the field type and an empty `instance ToSchema FieldType` |
| `Couldn't match type 'QueryAction Q' with 'IO ...'` | `combine` body uses `pure` or `return` | Remove `pure`/`return` — `combine` is a pure function returning `QueryAction` |
| `No instance for (QueryOf E Q)` at wire time | The `instance QueryOf` is missing | Add the `instance QueryOf EntityType QueryType where ...` block |
