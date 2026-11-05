# Adapt a complete effect module

Use only the branch needed by the task. Resolve the application revision and capabilities through [nh-app-context](../../nh-app-context/SKILL.md) before adapting API examples. The existing consumer layout and compatible API guide determine the actual imports, markers, and commands.

## Complete template

Copy this module, substitute your context path and module name, and fill `TODO` stubs before testing. Every identifier is grounded in the public `core/core/Task.hs`, `Result.hs`, `Maybe.hs`, and `Basics.hs`.

```haskell
-- src/Starter/Counter/CounterValidation.hs
-- Illustrative: Counter domain (public NeoHaskell test-project).
-- Adapt the module path, error type, and field names to your context.
module Starter.Counter.CounterValidation where

import Core
import Console qualified    -- Console.print (Task), Console.log (IO)
import Maybe qualified      -- Maybe.withDefault, Maybe.map, Maybe.andThen
import Result qualified     -- Result.Ok, Result.Err, Result.withDefault, etc.
import Task qualified       -- Task.yield, Task.throw, Task.andThen, Task.fromIO, etc.
import Text qualified       -- Text.length, Text.split, Text.joinWith, etc.


-- 1. CUSTOM ERROR ADT
-- A sum type lets callers pattern-match on the failure reason.
-- deriving (Show) is required by Task.runOrPanic.

data CounterError
  = LabelTooShort Text
  | AmountOutOfRange Int
  deriving (Show)


-- 2. PURE VALIDATION: returns Result — no Task needed for pure logic.
-- Result error value  (error is the FIRST type parameter, as with Either error value).
-- Constructors: Result.Ok value | Result.Err error  (never Left/Right).

validateLabel :: Text -> Result CounterError Text
validateLabel label =
  if Text.length label > 0
    then Result.Ok label
    else Result.Err (LabelTooShort label)


validateAmount :: Int -> Result CounterError Int
validateAmount n =
  if n > 0
    then Result.Ok n
    else Result.Err (AmountOutOfRange n)


-- 3. MAYBE: safe optional access; pipeline with |> and Maybe.*
-- Just/Nothing are in scope from import Core.

currentLabel :: Maybe Text -> Text
currentLabel mLabel =
  mLabel
    |> Maybe.withDefault "unlabelled"


-- 4. TASK: effectful pipeline.
-- do-let ONLY — never let..in, never a where clause.
-- Task.throw lifts a typed error; Task.yield wraps a success.

logCounterAction :: Text -> Int -> Task CounterError Unit
logCounterAction label amount = do
  validLabel <- case validateLabel label of
    Result.Err e -> Task.throw e
    Result.Ok v  -> Task.yield v
  case validateAmount amount of
    Result.Err e -> Task.throw e
    Result.Ok n  -> do
      let line = [fmt|#{validLabel} — incrementing by #{n}|]
      Console.print line  -- Console.print :: Text -> Task _ Unit; already a Task


-- 5. ANDTHEN: explicit chaining (equivalent to the do-block above)

logAndConfirm :: Text -> Int -> Task CounterError Text
logAndConfirm label amount =
  logCounterAction label amount
    |> Task.andThen (\_ -> Task.yield [fmt|Done: #{label}|])


-- 6. IO BRIDGE: Console.log and Console.readLine return IO, not Task.
-- Wrap them with Task.fromIO before using in a Task do-block.

debugLog :: Text -> Task Never Unit
debugLog msg =
  Task.fromIO (Console.log msg)

promptUser :: Task Never Text
promptUser =
  Task.fromIO Console.readLine


-- 7. STUB CONVENTION for unimplemented bodies:
--   pure or Task bodies   -> panic "TODO: not implemented"
--   outbound handleEvent  -> Integration.none  (never panic inside a pure handler)
-- There is NO `todo` function in NeoHaskell.

unimplementedHelper :: Text -> Result CounterError Int
unimplementedHelper _label = panic "TODO: not implemented"

unimplementedTask :: Text -> Task CounterError Unit
unimplementedTask _label = panic "TODO: not implemented"


-- 8. BOUNDARY: Task.runOrPanic converts Task err a to IO a.
-- Use ONLY at main / Application.run — never inside domain logic.

main :: IO Unit
main =
  logCounterAction "MyCounter" 5
    |> Task.runOrPanic

-- Alternative: map error to Text for Task.runMain (prints error to stderr).
mainViaRunMain :: IO Unit
mainViaRunMain =
  logCounterAction "MyCounter" 5
    |> Task.mapError (\e -> [fmt|Fatal: #{e}|])
    |> Task.runMain
```

---

