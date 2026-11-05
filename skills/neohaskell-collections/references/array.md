# Sequence construction, transforms, and replay folds

Use only the branch needed by the task. Resolve the application revision and capabilities through [nh-app-context](../../nh-app-context/SKILL.md) before adapting API examples. The existing consumer layout and compatible API guide determine the actual imports, markers, and commands.

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

