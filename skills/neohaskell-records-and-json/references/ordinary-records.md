# Adapt an ordinary entity or query record

Use only the branch needed by the task. Resolve the application revision and capabilities through [nh-app-context](../../nh-app-context/SKILL.md) before adapting API examples. The existing consumer layout and compatible API guide determine the actual imports, markers, and commands.

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
-- Ordinary records may use empty instances; invariant-bearing values and
-- persisted formats may require custom decoders. Check what markers emit first.
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

