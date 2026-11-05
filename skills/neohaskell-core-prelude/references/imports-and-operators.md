# Imports, exports, and canonical dialect table

Use only the branch needed by the task. Resolve the application revision and capabilities through [nh-app-context](../../nh-app-context/SKILL.md) before adapting API examples. The existing consumer layout and compatible API guide determine the actual imports, markers, and commands.

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

Use this table as an example, then inspect the effective revision's guide or source when signatures differ. Grounded in `NeoHaskell/core/core/Core.hs`.

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

