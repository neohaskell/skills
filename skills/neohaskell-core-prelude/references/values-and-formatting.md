# Numeric operations, interpolation, or console use

Use only the branch needed by the task. Resolve the application revision and capabilities through [nh-app-context](../../nh-app-context/SKILL.md) before adapting API examples. The existing consumer layout and compatible API guide determine the actual imports, markers, and commands.

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

