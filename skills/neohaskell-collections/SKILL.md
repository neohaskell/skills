---
name: neohaskell-collections
description: >-
  Use when writing any NeoHaskell code that needs sequences, key-value lookups,
  text manipulation, or sets. Covers Array (the default sequence — no filter,
  use takeIf/dropIf; get returns Maybe; foldl is element-first left fold for
  replays), Map (set/get/contains/remove; reduce takes acc first), Text
  (split/joinWith/replace; interpolate with #{} not ${}), and Set (not in Core
  — must import explicitly). Also use when you reach for a vanilla reflex such
  as arr !! i, head, Map.insert, Map.lookup, Map.member, or Array.filter —
  every one of those is wrong in NeoHaskell.
metadata:
  model: haiku
---

**This is NeoHaskell, not vanilla Haskell.** The `.hs` extension is shared, but the collection
types, qualified names, and fold argument orders are all different. Read this skill before writing
any sequence, lookup, string, or set logic.

---

## Inputs / Outputs / Next

**Input:** a sequence, lookup, string, or set need; or a vanilla-Haskell reflex (list, `!!`, `head`,
`Map.insert`, `Map.lookup`, `filter`, `<>`).

**Output:** correct `Array.*` / `Map.*` / `Text.*` / `Set.*` calls with the right import lines and
Maybe-safe access patterns.

**Next:** `neohaskell-effects-and-errors` (Task/Result wrapping), `neohaskell-records-and-json`
(record fields using these types), `implement-event-and-update-entity` (`Array.foldl update` replay
fold), `implement-query` (Map-backed read models).

---

## Import cheatsheet

```haskell
import Core                    -- Array, Map, Text, Maybe already in scope (type names only)

import Array (Array)           -- the type, for annotations
import Array qualified          -- Array.map, Array.takeIf, Array.get, etc.

import Map (Map)               -- the type
import Map qualified            -- Map.set, Map.get, Map.contains, Map.remove, etc.

import Text (Text)             -- usually redundant (Text is in Core), but explicit is clearer
import Text qualified           -- Text.split, Text.joinWith, Text.replace, Text.length, etc.

-- Set is NOT re-exported by Core — import both lines every time you use Set:
import Set (Set)
import Set qualified            -- Set.insert, Set.contains, Set.toArray, etc.
```

---

## Array — the default sequence (`Array a`)

Array is backed by `Data.Vector`. It replaces `[a]` everywhere. There is **no** `Array.filter`.

### Creation

```haskell
Array.empty              :: Array a
Array.wrap x             :: Array a           -- single-element array
Array.range lo hi        :: Array Int         -- inclusive, e.g. Array.range 1 3 == [1,2,3]
[1, 2, 3] :: Array Int                        -- OverloadedLists literal
Array.fromLinkedList xs  :: Array a           -- convert from a GHC list / LinkedList
Array.repeat n x         :: Array a           -- n copies of x
```

### Query

```haskell
Array.length arr         :: Int
Array.isEmpty arr        :: Bool
Array.get i arr          :: Maybe a           -- safe; never panics on bad index
Array.first arr          :: Maybe a           -- head, safe
Array.last arr           :: Maybe a           -- last, safe
Array.contains x arr     :: Bool              -- requires Eq
Array.find pred arr      :: Maybe a           -- first match or Nothing
Array.any pred arr       :: Bool
```

### Mutation-by-copy

```haskell
Array.push x arr         :: Array a           -- appends x to the END   ← use this to grow
Array.set i x arr        :: Array a           -- replaces element at index (noop if out of range)
Array.append other arr   :: Array a           -- concatenates other onto the end of arr (data-last)
```

> **Warning — `pushBack` prepends, not appends.** The name is misleading: `Array.pushBack x arr`
> inserts `x` at the **front** of the array (like `cons`), not the back. Prefer `Array.push` to
> add to the end and `Array.prepend` to prefix a whole array. Do not rely on `pushBack` without
> checking the source.

### Transform

```haskell
Array.map f arr          :: Array b           -- apply f to every element

-- Filtering (there is NO Array.filter):
Array.takeIf pred arr    :: Array a           -- keep elements that match
Array.dropIf pred arr    :: Array a           -- drop elements that match

Array.flatMap f arr      :: Array b           -- map then flatten
Array.flatten arr        :: Array a           -- when arr :: Array (Array a)
Array.slice from to arr  :: Array a           -- sub-array; negative indices count from end
Array.take n arr         :: Array a
Array.drop n arr         :: Array a
Array.reverse arr        :: Array a
Array.indexed arr        :: Array (Int, a)    -- pairs each element with its index
Array.zip other arr      :: Array (a, b)      -- data-last; pipe arr |> Array.zip other
```

### Fold / reduce — argument orders

NeoHaskell inverts the standard Haskell fold argument order. The **element** comes before the
accumulator in the folding function. This matters most for the entity-replay pattern.

```haskell
-- Array.foldl: LEFT fold (oldest-first), element-first function
-- Signature: (element -> acc -> acc) -> acc -> Array element -> acc
Array.foldl :: (a -> b -> b) -> b -> Array a -> b

-- Array.reduce: RIGHT fold, same element-first function order
-- Signature: (element -> acc -> acc) -> acc -> Array element -> acc
Array.reduce :: (a -> b -> b) -> b -> Array a -> b
```

The standard Haskell `foldl` is `(acc -> elem -> acc)` — NeoHaskell flips this to
`(elem -> acc -> acc)`. When in doubt: the **second argument to the fold function is always the
accumulator**.

**The canonical replay fold** (used by `write-feature-tests` property tests):

```haskell
-- Replay a list of events through the update function, left to right (oldest first).
-- update :: Event -> Entity -> Entity   (element first — matches Array.foldl)
let finalState = Array.foldl update initialState events
```

---

## Map — key-value lookup (`Map key value`)

NeoHaskell's `Map` is an Elm-style wrapper over `Data.Map.Strict`. Every operation name differs
from the `containers` package. Import `Data.Map.Strict` directly only for low-level compatibility.

### Creation

```haskell
Map.empty                           -- empty map (re-exported from Data.Map.Strict)
Map.fromArray [(k1,v1),(k2,v2)]     -- :: (Ord key) => Array (key, value) -> Map key value

-- Builder pattern (do-notation style):
Map.build do
  "shelf-a" --> 10
  "shelf-b" --> 25
```

### Operations

```haskell
Map.set    key value map  :: Map key value    -- insert or update (NOT Map.insert)
Map.get    key map        :: Maybe value      -- safe lookup     (NOT Map.lookup)
Map.getOrElse key def map :: value            -- lookup with default
Map.contains key map      :: Bool             -- membership test (NOT Map.member)
Map.remove  key map       :: Map key value    -- delete          (NOT Map.delete)
Map.merge   left right    :: Map key value    -- union, left-biased
```

### Inspection

```haskell
Map.length map   :: Int
Map.keys map     :: Array key
Map.values map   :: Array value
Map.entries map  :: Array (key, value)
Map.mapValues f map :: Map key valueB
```

### Map.reduce — accumulator comes FIRST

`Map.reduce` flips the argument order relative to `Array.reduce`. The accumulator is the **first**
argument (not the function):

```haskell
-- Map.reduce: acc FIRST, then the folding function
-- Signature: acc -> (key -> value -> acc -> acc) -> Map key value -> acc
Map.reduce :: acc -> (key -> value -> acc -> acc) -> Map key value -> acc

-- Example: sum all map values
total = Map.reduce 0 (\k v acc -> acc + v) myMap

-- Contrast with Array.reduce where the function comes first:
total = Array.reduce (\v acc -> acc + v) 0 myArray
```

---

## Text — string handling (`Text`)

`Text` is `Data.Text.Text`. String literals are already `Text` (OverloadedStrings). Never use
`String` / `[Char]`. Do not `import Data.Text` directly.

### Common operations

```haskell
Text.length txt           :: Int
Text.isEmpty txt          :: Bool
Text.split sep txt        :: Array Text         -- returns Array, not a list
Text.joinWith sep arr     :: Text               -- intercalate
Text.replace old new txt  :: Text
Text.contains sub txt     :: Bool               -- isInfixOf
Text.startsWith pre txt   :: Bool
Text.endsWith suf txt     :: Bool
Text.toUpper / Text.toLower txt :: Text
Text.trim / Text.trimLeft / Text.trimRight txt  :: Text
Text.toInt txt            :: Maybe Int
Text.fromInt n            :: Text
Text.toFloat txt          :: Maybe Float
Text.fromFloat f          :: Text
Text.words txt            :: Array Text         -- split on whitespace
Text.lines txt            :: Array Text         -- split on newlines
```

### String interpolation

Use the `fmt` quasi-quoter (re-exported by `Core`) with `#{expr}` syntax. Never use `<>` / `++`
for strings when interpolation reads more clearly, and never use `${}` or `%s`.

```haskell
-- Correct: #{expr} inside [fmt|...|]
greet :: Text -> Int -> Text
greet name count =
  [fmt|Hello #{name}! You have #{count} item(s).|]

-- Wrong forms (all silently incorrect or don't compile):
--   [fmt|{name}|]       -- bare {} silently prints literal "{name}"
--   "${name}"           -- not valid in NeoHaskell
--   name ++ " world"    -- works but prefer fmt for readability
```

---

## Set — unique element collection (`Set a`)

`Set` is **not** re-exported by `Core`. Always add both import lines.

```haskell
import Set (Set)
import Set qualified
```

### Operations

```haskell
Set.empty              :: (Ord a) => Set a
Set.wrap x             :: (Ord a) => Set a        -- singleton set
Set.singleton x        :: (Ord a) => Set a        -- same as wrap
Set.fromArray arr      :: (Ord a) => Set a
Set.insert x set       :: (Ord a) => Set a        -- add element
Set.remove x set       :: (Ord a) => Set a        -- delete element (noop if absent)
Set.contains x set     :: (Ord a) => Bool
Set.size set           :: Int
Set.isEmpty set        :: Bool
Set.union other self   :: (Ord a) => Set a
Set.intersection other self :: (Ord a) => Set a
Set.difference other self   :: (Ord a) => Set a   -- elements in self not in other
Set.map f set          :: (Ord b) => Set b
Set.takeIf pred set    :: Set a
Set.dropIf pred set    :: Set a
Set.toArray set        :: Array a                 -- elements in ascending order
```

---

## Copy-paste template (Library illustrative domain)

This module illustrates all four collection types together. Replace `Library` / `Loan` / `BookTitle`
/ `MemberId` with your actual context. Every identifier resolves to a real exported name from the
public source files.

```haskell
module Library.Catalog.Util (
  availableTitles,
  summariseLoan,
  memberTags,
) where

import Core
import Array (Array)
import Array qualified
import Map (Map)
import Map qualified
import Text (Text)
import Text qualified
import Set (Set)
import Set qualified
import Maybe qualified


-- | Filter a catalog to titles that still have copies.
-- Uses Array.takeIf — there is no Array.filter.
availableTitles :: Array (Text, Int) -> Array Text
availableTitles catalog =
  catalog
    |> Array.takeIf (\(_title, copies) -> copies > 0)
    |> Array.map (\(title, _copies) -> title)


-- | Build a per-member loan index.
-- Map.set (not insert), Map.get returns Maybe (not lookup).
addLoan :: Text -> Text -> Map Text (Array Text) -> Map Text (Array Text)
addLoan memberId title index = do
  let existing = Map.getOrElse memberId Array.empty index
  Map.set memberId (Array.push title existing) index


-- | Count loans per member across the index.
-- Map.reduce: accumulator comes FIRST (unlike Array.reduce).
totalLoans :: Map Text (Array Text) -> Int
totalLoans index =
  Map.reduce 0 (\_ loans acc -> acc + Array.length loans) index


-- | Interpolate a summary sentence for a loan.
-- Use #{expr} inside [fmt|...|] — not ${} or bare {}.
summariseLoan :: Text -> Int -> Text
summariseLoan title daysLeft =
  [fmt|"#{title}" is due in #{daysLeft} day(s).|]


-- | Collect unique genre tags for a member's loans.
-- Set requires its own import — it is not re-exported by Core.
memberTags :: Array Text -> Set Text
memberTags tags =
  Set.fromArray tags


-- | Replay events left-to-right to rebuild state.
-- Array.foldl is element-first: f :: element -> acc -> acc.
-- This is the pattern used in property-based replay tests.
replayCount :: Array Int -> Int
replayCount deltas =
  Array.foldl (\delta acc -> acc + delta) 0 deltas
```

---

## DO / DON'T

| Vanilla-Haskell reflex — DON'T | NeoHaskell-correct — DO | Why |
|---|---|---|
| `filter pred xs` (unqualified) | `Array.takeIf pred xs` | `Array.filter` does not exist |
| `xs !! i` | `Array.get i xs` returning `Maybe a` | No safe indexing via `!!` |
| `head xs` / `tail xs` | `Array.first xs` / `Array.drop 1 xs` | `head` panics on empty; `first` returns `Maybe` |
| `Map.insert k v m` | `Map.set k v m` | NeoHaskell uses Elm-style names |
| `Map.lookup k m` | `Map.get k m` (returns `Maybe`) | Renamed |
| `Map.member k m` | `Map.contains k m` | Renamed |
| `Map.delete k m` | `Map.remove k m` | Renamed |
| `Data.Map.foldr f z m` | `Map.reduce z f m` | Acc is the **first** arg in `Map.reduce` |
| `Prelude.foldl f z xs` | `Array.foldl f z xs` | Element first: `f :: elem -> acc -> acc` |
| `Set.member x s` | `Set.contains x s` | Renamed (also `Set.member` exists as alias but `contains` is canonical) |
| `import Set (Set)` forgotten | Add `import Set (Set)` + `import Set qualified` | `Set` is not re-exported by `Core` |
| `Data.Text.splitOn sep txt` | `Text.split sep txt :: Array Text` | Returns `Array`, not a GHC list |
| `intercalate sep xs` | `Text.joinWith sep arr` | Takes `Array Text`, not `[Text]` |
| `"Hello " <> name` | `[fmt|Hello #{name}|]` | `<>` works but fmt is idiomatic for strings |
| `[fmt|{name}|]` | `[fmt|#{name}|]` | Bare `{}` prints the literal text `{name}` |
| `Array.pushBack x arr` to append | `Array.push x arr` | `pushBack` **prepends** (front); `push` appends (end) |

---

## Verify

```
neo build
```

If `Array.filter` appears anywhere in GHC output as "not in scope", replace with `Array.takeIf`
or `Array.dropIf`. If `Set` appears as "not in scope", add `import Set (Set)` and
`import Set qualified`.
