---
name: neohaskell-core-prelude
description: >-
  The NeoHaskell CORE PRELUDE cheatsheet: the canonical 'import Core' module header, the
  Core-exported pipe / compose / append operators and their vanilla-Haskell dollar-dot
  equivalents, panic / Unit / unit / pass, the #{expr} fmt string-interpolation SYNTAX, the
  Int vs Float math split (division, integer division, powers), and the Console.print / log
  / readLine Task-vs-IO distinction — plus the full vanilla-Haskell trap table. Use when
  writing a NeoHaskell module header, correcting operator/import muscle-memory reflexes, or
  fixing 'Module not found: Prelude'. Load BEFORE the other cheatsheets. Do NOT use for
  Array/Map/Text/Set operations (neohaskell-collections), Task/Result/Maybe control flow and
  error recovery (neohaskell-effects-and-errors), record/JSON instances (neohaskell-records-
  and-json), folder/module placement (neohaskell-module-layout), designing domain value
  objects (neohaskell-domain-modeling), or reviewing a whole diff (neohaskell-code-review).
metadata:
  model: haiku
---

**This is NeoHaskell, not vanilla Haskell.** The file extension `.hs` is shared, but NeoHaskell ships a custom `Core` prelude that replaces `Prelude` project-wide (`NoImplicitPrelude` is always on). Every module must open with `import Core`.

---

## Inputs / Outputs / Next

- **Input:** a vanilla-Haskell reflex, a module header, or a `.hs` module under review.
- **Output:** a correct `import Core` header, Core-idiomatic expressions, and the DO/DON'T map.
- **Next:** `neohaskell-collections` · `neohaskell-effects-and-errors` · `neohaskell-records-and-json` · `neohaskell-module-layout`

---

## Module header template

Adapt `App`, `Context`, and `Module` to your project. Keep this import order.

```haskell
module App.Context.Module (
  ExportedType (..),
  exportedFunction,
) where

-- 1. Core is ALWAYS first. It replaces Prelude entirely. Do NOT add `import Prelude`.
import Core

-- 2. Import each collection type unqualified (for type annotations),
--    then qualified (for operations).
import Array (Array)
import Array qualified
import Map (Map)
import Map qualified
import Text (Text)
import Text qualified
import Task (Task)
import Task qualified
import Console qualified   -- Core re-exports log/print/readLine unqualified; qualify for Console.print etc.
import Maybe qualified     -- Maybe (..) is already in Core; import qualified for Maybe.withDefault etc.
import Result qualified    -- Result (..) is already in Core; import qualified for Result.andThen etc.

-- Set is NOT re-exported by Core. If you need it, import both lines:
-- import Set (Set)
-- import Set qualified
```

---

## What `Core` re-exports vs what you must import

Don't grep `Core.hs` — use this table. Grounded in `NeoHaskell/core/core/Core.hs`.

**Re-exported by `Core`** (use unqualified, no extra import line):

| Symbol | Note |
|---|---|
| `Uuid` | **The TYPE ONLY** (`import Uuid as Reexported (Uuid)`). The FUNCTIONS `Uuid.nil` / `Uuid.generate` / `Uuid.fromText` / `Uuid.toText` still need `import Uuid qualified`. This split is the single most common trip-up. |
| `CommandResult (..)` | constructors `AcceptCommand` / `RejectCommand` |
| `Decision` | the type only — smart-constructors `Decider.acceptNew`/`reject`/`generateUuid`/… are NOT (import `Decider qualified`) |
| `Entity`, `NameOf`, `EventOf`, `EntityOf` | entity type + type families |
| `Default`, `def` | |
| `QueryOf (..)`, `QueryAction (..)`, `Query (..)`, `EntitiesOf` | via `Service.Query` |
| `ToSchema (..)`, `FieldSchema (..)`, `Schema (..)` | via `Schema` |
| `Natural`, `Array`, `Text`, `Task`, `Maybe`, `otherwise`, `not`, `fmt`, … | the usual prelude surface |

**NOT re-exported — must import explicitly:**

| Symbol | Import line |
|---|---|
| `DecisionContext` | `import Decider (DecisionContext)` |
| `Event (..)` (the class) | `import Service.Command.Core (Event (..))` |
| `TransportsOf` | `import Service.Command.Core (TransportsOf)` |
| `AccessError`, `UserClaims` | `import Service.AccessControl (AccessError, UserClaims)` |
| `publicAccess`, `publicView` | `import Service.AccessControl qualified as AccessControl` |
| `RequestContext` | `import Service.Auth (RequestContext)` |
| `WebTransport` | `import Service.Transport.Web (WebTransport)` |
| `command` | `import Service.CommandExecutor.TH (command)` |
| `deriveQuery`, `outboundIntegration`, `Integration.*` | the TH macros — imported in `implement-query` / `implement-integration` |

`Decision` (unqualified, from `Core`) vs its smart-constructors (qualified, from `Decider`) is the second most common trip-up — see `implement-command`.

---

## Operators and built-ins (all from `Core` via `Basics`)

Grounded in `NeoHaskell/core/core/Basics.hs`.

```haskell
-- Pipe / apply
x |> f          -- forward pipe:   f x     (replaces  f $ x)
f <| x          -- reverse apply:  f x     (rare; prefer |>)

-- Compose
f .> g          -- forward compose:  \x -> g (f x)   (replaces  g . f)
g <. f          -- backward compose: \x -> g (f x)   (replaces  g . f)

-- Append / equality
xs ++ ys        -- Appendable (replaces  <>)
a != b          -- not-equal      (replaces  /=)

-- Unit
Unit            -- the type   (replaces  ())
unit            -- the value  (replaces  ())

-- Crash / stubs
panic "message" -- fail loudly (replaces  error / undefined). There is NO `todo`.

-- Do nothing (returns unit in any Applicable context)
pass            -- replaces  pure () in applicative contexts

-- Function helpers
identity        -- replaces  id
always          -- replaces  const
discard         -- replaces  void  (type-specific fmap to ())
```

---

## String interpolation — `fmt` quasi-quoter

`fmt` is re-exported by `Core` (defined in `Basics` as `Data.String.Interpolate.i`).

```haskell
-- Correct: #{expr} inside the quasi-quote
greet :: Text -> Int -> Text
greet name count =
  [fmt|Hello #{name}, you have #{count} items!|]
```

**WARNING: `REFERENCE.md` shows bare `{name}` — that is wrong.** The actual interpolation syntax is always `#{expr}`. Using `{name}` will silently produce a literal `{name}` in the output, not the value.

- DO: `[fmt|#{expr}|]`
- DON'T: `[fmt|{expr}|]` · `"${expr}"` · `printf "%s"` · `<>` concatenation for strings

---

## Int vs Float — the math split

Grounded in `NeoHaskell/core/core/Basics.hs` and `NeoHaskell/core/core/Int.hs`.

```haskell
-- Both Int and Float
(+)   :: Num n => n -> n -> n
(-)   :: Num n => n -> n -> n
(*)   :: Num n => n -> n -> n

-- Float ONLY
(/)   :: Float -> Float -> Float   -- 3.0 / 2.0 == 1.5
(^)   :: Float -> Float -> Float   -- 2.0 ^ 3.0 == 8.0

-- Int ONLY
(//)  :: Int -> Int -> Int         -- 3 // 2 == 1
Int.powerOf :: Int -> Int -> Int   -- exponent |> Int.powerOf base
                                   -- e.g.  3 |> Int.powerOf 2   == 8  (2^3)

-- Conversion (import Int qualified)
Int.toFloat :: Int -> Float
```

---

## Natural numbers

`Natural a` is a NeoHaskell wrapper for non-negative values. Grounded in `Basics.hs`.

```haskell
-- Smart constructor — returns Nothing if input <= 0
makeNatural :: (Ord n, Num n) => n -> Maybe (Natural n)

-- Smart constructor — panics if input <= 0 (useful in domain modeling)
makeNaturalOrPanic :: (Ord n, Num n, Show n) => n -> Natural n
```

Use `Natural Int` (or `Natural Float`) to represent counts and quantities that must be positive.

---

## Console — Task vs IO distinction

`Core` re-exports `Console.print`, `Console.log`, and `Console.readLine`, but they are NOT all `Task`. Grounded in `NeoHaskell/core/core/Console.hs`.

```haskell
-- print is a Task — use directly in do-notation
Console.print :: Text -> Task _ Unit   -- wraps IO internally

-- log and readLine return IO, not Task — bridge with Task.fromIO
Console.log      :: (HasCallStack) => Text -> IO Unit    -- debug logging (checks NEOHASKELL_DEBUG env var)
Console.readLine :: IO Text            -- reads a line

-- In a Task context:
doSomething :: Task _ Unit
doSomething = do
  Task.fromIO (Console.log "debug info")   -- must bridge IO -> Task
  line <- Task.fromIO Console.readLine     -- must bridge IO -> Task
  Console.print [fmt|You typed: #{line}|]  -- already a Task, no bridge needed
```

---

## Scratch module (Counter domain — copy-paste and adapt)

```haskell
module Starter.Counter.Util (
  describeCount,
  incrementIfPositive,
  summarise,
) where

import Core
import Array (Array)
import Array qualified
import Int qualified
import Text (Text)
import Text qualified


-- Pure function: pipe operator + fmt interpolation
describeCount :: Text -> Int -> Text
describeCount label count =
  [fmt|#{label}: #{count} item(s)|]


-- Pure function: case instead of multi-equation patterns; != instead of /=
incrementIfPositive :: Int -> Maybe Int
incrementIfPositive n =
  case n > 0 of
    True  -> Just (n + 1)
    False -> Nothing


-- Pure function: pipe style avoids let..in and where (both banned by style guide)
summarise :: Array Int -> Text
summarise counts =
  counts
    |> Array.sumIntegers
    |> \total -> [fmt|Total: #{total}, half: #{total // 2}|]
```

---

## DO / DON'T table

| Vanilla Haskell — DON'T write this | NeoHaskell — write this instead | Note |
|---|---|---|
| `import Prelude` | `import Core` | `NoImplicitPrelude` is always on |
| `module Foo where` (no `import Core`) | `import Core` as the first import | Required in every module |
| `f $ x` | `x \|> f` | Pipe forward |
| `g . f` | `f .> g` | Forward compose (`.>` applies f first) |
| `xs <> ys` | `xs ++ ys` | `Appendable` typeclass |
| `a /= b` | `a != b` | |
| `() :: ()` | `unit :: Unit` | Type and value both renamed |
| `error "msg"` / `undefined` | `panic "msg"` | There is no `todo` in NeoHaskell |
| `3 / 2 :: Int` | `3 // 2` | `/` is Float-only |
| `2 ^ 3 :: Int` | `3 \|> Int.powerOf 2` | `^` is Float-only; result is `8` |
| `[fmt\|{name}\|]` | `[fmt\|#{name}\|]` | `#{}` syntax — bare `{}` is wrong (REFERENCE.md is wrong here) |
| `pure x` / `return x` | `Task.yield x` | `pure`/`return` compile but violate style — treat as a **review rule**, not a compile error |
| `fmap f x` | `Array.map f x` / `Task.map f x` / `Maybe.map f x` | Qualify by type; generic `fmap` compiles but is a style violation |
| `putStrLn t` / `print x` | `Console.print t` | Returns `Task _ Unit` |
| `getLine` | `Task.fromIO Console.readLine` | `readLine` returns `IO`, not `Task` |
| `Console.log t` in Task | `Task.fromIO (Console.log t)` | `log` returns `IO Unit`, not `Task` |
| `id` / `const` / `void` | `identity` / `always` / `discard` | |
| `import Data.Text` | `import Text (Text)` + `import Text qualified` | `Text` is already in `Core` |
| `import Data.Map` | `import Map (Map)` + `import Map qualified` | `Map` is already in `Core` |
| `import Data.Set` | `import Set (Set)` + `import Set qualified` | `Set` is NOT in `Core` — must import explicitly |
| `import Data.Aeson` | `import Json qualified` | Use the `Json` module |
| `filter` / `map` unqualified | `Array.takeIf` / `Array.map` | See `neohaskell-collections` |
| multiple function equations | single `case x of` | NeoHaskell style guide |
| `let x = … in body` | `do let x = …; body` or pipe style | Style guide bans `let..in` |
| `where` clauses | `do let x = …` or a top-level helper | Style guide bans `where` |

---

## Verify

After writing or editing a module, run:

```
neo build
```

A successful build confirms `import Core` resolves, no Prelude leakage, and the lock gate passes. If you see `Module not found: Prelude` or an ambiguous-import error, check that `import Core` is present and no `import Prelude` was added.
