# Keyed lookup and map folds

Use only the branch needed by the task. Resolve the application revision and capabilities through [nh-app-context](../../nh-app-context/SKILL.md) before adapting API examples. The existing consumer layout and compatible API guide determine the actual imports, markers, and commands.

## Map — key-value lookup (`Map key value`)

NeoHaskell's `Map` is an Elm-style wrapper over `Data.Map.Strict`. Every operation name differs
from the `containers` package. Import `Data.Map.Strict` directly only for low-level compatibility.

### Creation

```haskell
Map.empty                           -- empty map (re-exported from Data.Map.Strict)
Map.fromArray [(k1,v1),(k2,v2)]     -- :: (Eq key, Ord key) => Array (key, value) -> Map key value

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

