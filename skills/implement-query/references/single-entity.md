# Implement a simple query and its access policy

Use only the branch needed by the task. Resolve the application revision and capabilities through [nh-app-context](../../nh-app-context/SKILL.md) before adapting API examples. The existing consumer layout and compatible API guide determine the actual imports, markers, and commands.

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

