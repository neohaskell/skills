---
name: neohaskell-effects-and-errors
description: "Provides the NeoHaskell effects and error-handling cheatsheet for Task, Result, Maybe, and string interpolation. Use whenever a Haskell reflex reaches for IO, pure/return, Either/Left/Right, let-in/where, or string-formatting with dollar-sign or percent-sign syntax. Covers Task err value (error type first) with Task.yield, Task.throw, Task.andThen, Task.runOrPanic, and Task.fromIO for the IO-to-Task bridge; Result with Ok/Err constructors; Maybe with withDefault and andThen; do-let instead of let-in or where; and the fmt quasi-quoter with hash-brace interpolation. Load this skill when reviewing or writing any NeoHaskell module that performs effects or handles failures."
metadata:
  model: haiku
---

This is NeoHaskell, not vanilla Haskell. The `.hs` extension is shared, but the prelude, effect type, and error type differ — vanilla reflexes (`IO`, `Either`, `pure`, `error`, `let..in`) compile silently and produce the wrong idiom.

## Inputs / Outputs / Next

**Input:** effectful logic, fallible operations, optional values, string-building — or a module suspected of using vanilla Haskell error-handling idioms.

**Output:** idiomatic `Task`/`Result`/`Maybe`/`fmt` code with correct imports and do-let style.

**Next skills:** `neohaskell-core-prelude` (operators, `panic`, `Unit`, full trap table), `neohaskell-collections` (`Array`/`Map`/`Text`), `implement-command` (commands return a `Task`-backed `Decision`), `implement-integration` (outbound handlers are pure; inbound helpers use `Task`).

---

## Quick reference

### Task

`Task err value` is the NeoHaskell effect type. **Error is the first type parameter.** `IO` never appears in domain logic — only inside `main` or `Application.run`.

| Operation | Signature — grounded in Task.hs | Note |
|---|---|---|
| wrap a value | `Task.yield :: value -> Task _ value` | replaces `pure`/`return` |
| fail with typed error | `Task.throw :: err -> Task err _` | replaces `throwIO`/`error` |
| chain | `Task.andThen :: (a -> Task err b) -> Task err a -> Task err b` | or use do-notation |
| transform value | `Task.map :: (a -> b) -> Task err a -> Task err b` | replaces `fmap` for Task |
| transform error | `Task.mapError :: (e1 -> e2) -> Task e1 a -> Task e2 a` | |
| recover from error | `Task.recover :: (err -> Task err2 a) -> Task err a -> Task err2 a` | replaces `catch` |
| capture as Result | `Task.asResult :: Task err a -> Task err2 (Result err a)` | |
| at the boundary only | `Task.runOrPanic :: (HasCallStack, Show err) => Task err a -> IO a` | `main`/`Application.run` |
| wrap any IO action | `Task.fromIO :: IO a -> Task _ a` | IO bridge — see below |
| conditional run | `Task.when :: Bool -> Task err Unit -> Task err Unit` | |
| loop over Array | `Task.forEach :: (a -> Task err Unit) -> Array a -> Task err Unit` | |

**IO bridge rule:** `Console.print :: Text -> Task _ Unit` is already a `Task` — call it directly in do-notation. `Console.log` and `Console.readLine` return `IO` — wrap them with `Task.fromIO`.

### Result

`Result error value` — **error is the first type parameter** (the opposite of `Either`'s convention).

| Operation | Signature — grounded in Result.hs | Note |
|---|---|---|
| success | `Result.Ok :: value -> Result error value` | construct or pattern match |
| failure | `Result.Err :: error -> Result error value` | construct or pattern match |
| fallback value | `Result.withDefault :: a -> Result b a -> a` | |
| transform value | `Result.map :: (a -> b) -> Result x a -> Result x b` | |
| chain | `Result.andThen :: (a -> Result e b) -> Result e a -> Result e b` | |
| transform error | `Result.mapError :: (a -> b) -> Result a c -> Result b c` | |
| to Maybe | `Result.toMaybe :: Result a b -> Maybe b` | |
| from Maybe | `Result.fromMaybe :: a -> Maybe b -> Result a b` | |
| inspect | `Result.isOk :: Result a b -> Bool` / `Result.isErr` | |

### Maybe

`Maybe a` — constructors `Just`/`Nothing` are in scope from `import Core`.

| Operation | Signature — grounded in Maybe.hs | Note |
|---|---|---|
| fallback | `Maybe.withDefault :: a -> Maybe a -> a` | replaces `fromMaybe` |
| transform | `Maybe.map :: (a -> b) -> Maybe a -> Maybe b` | replaces `fmap` for Maybe |
| chain | `Maybe.andThen :: (a -> Maybe b) -> Maybe a -> Maybe b` | short-circuits on Nothing |
| flatten | `Maybe.flatten :: Maybe (Maybe a) -> Maybe a` | |
| unsafe unwrap | `Maybe.getOrDie :: Maybe a -> a` | panics on `Nothing` |

### String interpolation with `fmt`

`fmt` is a `QuasiQuoter` defined in `Basics.hs` as `StringInterpolate.i` and re-exported by `Core`. The interpolation delimiter is **`#{expr}`** — not `${}`, not `%s`, not bare `{name}`. Bare braces appear in some NeoHaskell reference files and are incorrect; always include the `#`.

```haskell
let label = "Counter" :: Text
let n     = 42        :: Int
let msg   = [fmt|#{label} has #{n} items|]
-- Result: "Counter has 42 items"
```

Use `++` for plain `Text` concatenation when no type conversion is needed. Use `fmt` whenever embedding a non-`Text` value inline.

---

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
-- Result error value  (error is the FIRST type parameter, opposite of Either).
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

## DO / DON'T

| Situation | DON'T — vanilla Haskell reflex | DO — NeoHaskell-correct |
|---|---|---|
| effectful function return type | `IO a` | `Task err a` (`IO` only in `main`/`Application.run`) |
| wrap a success value | `pure x` / `return x` | `Task.yield x` |
| signal a pure crash | `error "msg"` / `undefined` | `panic "msg"` (from `Core`) |
| signal a typed failure | `throwIO e` | `Task.throw e` |
| error union type | `Either a b` / `Left x` / `Right y` | `Result error value` / `Result.Err x` / `Result.Ok y` |
| Result type param order | `Result Int Text` (value first?) | `Result Text Int` — error is ALWAYS first |
| recover from Task error | `catch` / `try` | `Task.recover` / `Task.asResult` |
| local binding | `let x = v in body` / `where clause` | do-`let`: inside a `do`-block, `let x = v` on its own line |
| embed a value in a string | `"count: " <> show n` / `printf "%s" n` | `[fmt|count: #{n}|]` |
| fmt interpolation syntax | `[fmt|count: {n}|]` (bare braces — seen in some docs) | `[fmt|count: #{n}|]` (hash required) |
| optional fallback | `Data.Maybe.fromMaybe d m` | `m \|> Maybe.withDefault d` |
| inequality | `a /= b` | `a != b` |
| Console.log in Task context | `Console.log msg` directly | `Task.fromIO (Console.log msg)` |
| Console.readLine in Task context | `Console.readLine` directly | `Task.fromIO Console.readLine` |
| transform inside a Functor | `fmap f t` | `Task.map f t` / `Maybe.map f m` / `Result.map f r` |
| stub body | `todo` | `panic "TODO: not implemented"` — `todo` does not exist |

> `pure`, `return`, and generic `fmap` compile in NeoHaskell (they are in scope via `Basics`) but are style violations. The `neohaskell-code-review` skill flags them. Prefer `Task.yield`, `Task.map`, `Maybe.map`, and `Result.map`.

### Result vs Maybe at a glance

| Need | Type / Constructors |
|---|---|
| Failure with a typed reason | `Result ErrorType Value` / `Result.Ok v` / `Result.Err e` |
| Optional value, no error detail | `Maybe Value` / `Just v` / `Nothing` |
| Fallback for Maybe | `m \|> Maybe.withDefault default` |
| Fallback for Result | `r \|> Result.withDefault default` |
| Chain fallible steps | `Result.andThen` |
| Chain optional steps | `Maybe.andThen` |
| Lift Result into Task | `case r of { Result.Ok v -> Task.yield v; Result.Err e -> Task.throw e }` |
| Catch a Task error | `Task.recover (\err -> ...)` |
| Observe Task outcome as Result | `Task.asResult t` |

---

## Verify

```
neo build
```

A clean build confirms no `IO` leak in domain modules and no missing qualified imports. If `neo build` is unavailable, confirm manually: every effectful function returns `Task err value`; every `let` binding lives inside a do-block; `fmt` uses `#{expr}`; `Result.Err`/`Result.Ok` have the error type in the first position.
