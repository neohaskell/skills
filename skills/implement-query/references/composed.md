# Aggregate multiple streams

Use only the branch needed by the task. Resolve the application revision and capabilities through [nh-app-context](../../nh-app-context/SKILL.md) before adapting API examples. The existing consumer layout and compatible API guide determine the actual imports, markers, and commands.

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

