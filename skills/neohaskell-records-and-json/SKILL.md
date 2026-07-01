---
name: neohaskell-records-and-json
description: >-
  Use when defining a NeoHaskell record type, adding JSON serialization, or
  reviewing .hs code for vanilla-Aeson or field-selector reflexes. Covers the
  'data X = X { ... } deriving (Generic)' pattern, empty
  'instance Json.FromJSON X' and 'instance Json.ToJSON X' (never
  deriving/TH/anyclass), 'instance ToSchema X' on query read models only, and
  dot-access syntax for NoFieldSelectors. Also use when a field is referenced as
  a function (field rec) instead of dot access (rec.field), or when
  'import Data.Aeson' appears instead of 'import Json qualified'. Load before
  implement-event-and-update-entity, expand-entity, implement-command, and
  implement-query.
metadata:
  model: haiku
---

**This is NeoHaskell, not vanilla Haskell.** The `.hs` extension is shared, but the prelude, JSON API, and record-access rules are all different: `import Json qualified` not `import Data.Aeson`; empty Generic instances not `deriveJSON`; `rec.field` dot access not `field rec`; `import Core` always first.

---

## Inputs / Outputs / Next

- **Input:** a set of fields plus the record's role (entity, command, query read model, or value object).
- **Output:** `data X = X { ... } deriving (Generic)` + empty `Json.FromJSON`/`ToJSON` instances + `ToSchema` for query read models only + dot-access usage.
- **Next:** `implement-event-and-update-entity` · `expand-entity` · `implement-command` · `implement-query`

---

## Template A — Entity or value-object record

Grounded in `testbed/src/Testbed/Cart/Core.hs` (CartEntity, CartItem) and
`testbed/src/Testbed/Stock/Core.hs` (StockEntity). Adapt `Context`, `Entity`,
and field names to your domain.

```haskell
module <App>.<Context>.Entity where
  -- (export list; see neohaskell-module-layout for placement rules)

import Core
import Json qualified
import Uuid qualified
import Array qualified


-- | The aggregate record.
-- deriving (Generic) is required by the empty Json instances below.
-- Add Eq/Show/Ord only when needed for tests or event ADTs.
data <Entity> = <Entity>
  { <entityId>  :: Uuid
  , <fieldA>    :: Text
  , <fieldB>    :: Int
  }
  deriving (Generic)


-- Empty instance bodies — Generic derives the implementation automatically.
-- NEVER write a body here; NEVER use deriving (FromJSON, ToJSON).
instance Json.FromJSON <Entity>
instance Json.ToJSON <Entity>


-- Default instance for the entity's zero state.
-- Project convention only — neither `command` nor `deriveQuery` checks for it;
-- the macros compile fine without it. Ownership rule: entities get this; see
-- neohaskell-module-layout for placement.
instance Default <Entity> where
  def = initialState


-- The zero / empty state returned before any events have been applied.
initialState :: <Entity>
initialState =
  <Entity>
    { <entityId> = Uuid.nil
    , <fieldA>   = ""
    , <fieldB>   = 0
    }


-- Wiring: entity type family (lives in Entity.hs alongside instance Entity).
type instance NameOf <Entity> = "<Entity>"
```

### Value-object nested record (e.g. CartItem inside CartEntity)

```haskell
data CartItem = CartItem
  { productId :: Uuid
  , amount    :: Natural Int
  }
  deriving (Generic)

instance Json.FromJSON CartItem
instance Json.ToJSON CartItem
```

Fields of a nested record are accessed the same way: `entity.items`, not `items entity`.

---

## Template B — Query read model record

Grounded in `testbed/src/Testbed/Stock/Queries/StockLevel.hs` (StockLevel).
Query read models add `ToSchema` and the access-control pair that `deriveQuery`
wires into the `Query` typeclass instance.

```haskell
{-# LANGUAGE TemplateHaskell #-}

module <App>.<Context>.Queries.<QueryName> (
  <QueryName> (..),
  canAccess,
  canView,
) where

import Core
import Json qualified
import Service.AccessControl (AccessError, UserClaims)
import Service.AccessControl qualified as AccessControl
import Service.Query.TH (deriveQuery)
import <App>.<Context>.Entity (<Entity> (..))


-- Query read model: Generic + Eq + Show (useful in tests).
-- Needs ToSchema so OpenAPI can document the response shape.
data <QueryName> = <QueryName>
  { <queryId>  :: Uuid
  , <fieldA>   :: Text
  , <fieldB>   :: Int
  }
  deriving (Generic, Eq, Show)


-- JSON serialization — always empty bodies (Generic does the work).
instance Json.FromJSON <QueryName>
instance Json.ToJSON <QueryName>


-- ToSchema is ONLY for query read models — never on commands or entities.
-- It generates the OpenAPI response schema served at /openapi.json.
instance ToSchema <QueryName>


-- Access control — BOTH functions are required; deriveQuery fails to compile
-- without them. Choose from AccessControl.publicAccess / authenticatedAccess
-- (for canAccess) and publicView / ownerOnly (for canView).
canAccess :: Maybe UserClaims -> Maybe AccessError
canAccess claims = AccessControl.publicAccess claims

canView :: Maybe UserClaims -> <QueryName> -> Maybe AccessError
canView claims q = AccessControl.publicView claims q


-- TH macro: wires canAccess/canView into the Query instance and registers
-- the query to update when events for the listed entity types arrive.
deriveQuery ''<QueryName> [''<Entity>]


-- Hand-written projection: how each entity state maps to this read model.
-- combine receives the current entity and the existing query (if any).
-- Must be total — handle both Nothing (first time) and Just (update).
instance QueryOf <Entity> <QueryName> where
  queryId entity = entity.<entityId>
  combine entity _maybeExisting =
    Update
      <QueryName>
        { <queryId> = entity.<entityId>
        , <fieldA>  = entity.<fieldA>
        , <fieldB>  = entity.<fieldB>
        }
```

---

## Dot access — NoFieldSelectors

`NoFieldSelectors` is a project-wide GHC extension. Field names are **not**
in scope as functions. The only way to read a field is dot notation.

```haskell
-- Correct: dot access
let name  = entity.<fieldA>   -- rec.field
let total = cart.items |> Array.length

-- Wrong: field as a selector function (vanilla Haskell reflex)
-- let name  = <fieldA> entity   -- does NOT compile in NeoHaskell
-- let total = items cart         -- does NOT compile in NeoHaskell
```

Section syntax `(.fieldA)` is available when you need a function: `Array.map (.cartId) items`.

---

## Backward-compat trap — adding a field to an existing entity

When you hand-write a `FromJSON` instance (instead of using the empty Generic
form), use `(.:?)` and `(.!=)` from `Json` to give new fields a default so old
snapshots without that field still decode:

```haskell
instance Json.FromJSON <Entity> where
  parseJSON = Json.withObject "<Entity>" \obj -> do
    <entityId> <- obj Json..:  "<entityId>"
    <fieldA>   <- obj Json..:  "<fieldA>"
    -- New field added later — optional with a default so old snapshots decode:
    <newField> <- obj Json..:? "<newField>" Json..!= 0
    Json.yield <Entity> {<entityId>, <fieldA>, <newField>}
```

**The empty Generic `FromJSON` rejects an old snapshot that is missing a new
non-`Maybe` field** — it has no concept of a default. If you are expanding an
entity rather than creating one from scratch, use `expand-entity` instead of
this skill; that skill owns the backward-compat field-addition rules.

---

## DO / DON'T

| Vanilla-Haskell reflex — DON'T | NeoHaskell-correct form — DO | Why |
|---|---|---|
| `import Data.Aeson` | `import Json qualified` | Aeson is wrapped; never import it directly |
| `deriving (FromJSON, ToJSON)` | `instance Json.FromJSON X` (empty body) | `deriveJSON` and anyclass derivation are not used |
| `deriveJSON defaultOptions ''X` | `instance Json.FromJSON X` (empty body) | Same — never use the TH derivation shortcut |
| `instance Json.FromJSON X where parseJSON = ...` with a manual body | empty `instance Json.FromJSON X` | Only hand-write when you need custom decoding (e.g. backward-compat optional fields) |
| `field rec` (field as a function) | `rec.field` | `NoFieldSelectors` removes field names from the function namespace |
| `instance ToSchema X` on a command or entity | `instance ToSchema X` on queries only | ToSchema drives the OpenAPI response schema; commands/entities are not response shapes |
| `import Data.Map / Data.Vector / GHC.Generics` directly | qualified `Map` / `Array` / `GHC.Generics qualified as Generics` from Core | Use NeoHaskell wrappers |
| `data X = X { ... } deriving (Generic, FromJSON, ToJSON)` | `data X = X { ... } deriving (Generic)` + separate empty instances | Combine deriving causes GHC to generate conflicting instances |
| `toJSON x = object [...]` (hand-written ToJSON body) | empty `instance Json.ToJSON X` | Let Generic do it unless you need a custom wire format |
| `(.:)` from `Data.Aeson` | `obj Json..: "key"` | Always use the qualified `Json.(.:)` re-export |
| `x .= y` from `Data.Aeson` | `key Json..= value` | Same — use `Json.(.=)` |

---

## Deriving clause by block type

| Block | Typical deriving | Notes |
|---|---|---|
| Entity record | `(Generic)` | Add `Eq, Show` if tests need it |
| Nested value object | `(Generic)` | Same |
| Command record | `(Generic, Typeable, Show)` | `Typeable` is required by the `command` TH macro |
| Event payload | `(Eq, Show, Ord, Generic)` | `Ord` useful; events go in `Events/<Name>.hs` |
| Query read model | `(Generic, Eq, Show)` | `ToSchema` added separately; `deriveQuery` may also emit Generic/Show/JSON for fresh types |

---

## Verify

```
neo build
```

A successful build confirms:
- empty Generic instances compile without a "No instance for" error;
- `NoFieldSelectors` violations (field used as a function) are caught by the compiler;
- `deriveQuery` finds `canAccess` and `canView` in scope;
- the lock gate passes (commands/events/queries under locked dirs are unchanged).

If you see `Ambiguous occurrence` on a field name, you likely have
`DuplicateRecordFields` colliding with an explicit selector — use dot access,
not the selector.
