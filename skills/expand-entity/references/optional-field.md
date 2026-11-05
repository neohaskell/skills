# Old snapshots should decode the field as absent

Use only the branch needed by the task. Resolve the application revision and capabilities through [nh-app-context](../../nh-app-context/SKILL.md) before adapting API examples. The existing consumer layout and compatible API guide determine the actual imports, markers, and commands.

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

