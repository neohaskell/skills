# Old snapshots need a documented default

Use only the branch needed by the task. Resolve the application revision and capabilities through [nh-app-context](../../nh-app-context/SKILL.md) before adapting API examples. The existing consumer layout and compatible API guide determine the actual imports, markers, and commands.

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

