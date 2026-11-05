# Choose a standard value type or build a smart constructor

Use only the branch needed by the task. Resolve the application revision and capabilities through [nh-app-context](../../nh-app-context/SKILL.md) before adapting API examples. The existing consumer layout and compatible API guide determine the actual imports, markers, and commands.

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

