# Unique values

Use only the branch needed by the task. Resolve the application revision and capabilities through [nh-app-context](../../nh-app-context/SKILL.md) before adapting API examples. The existing consumer layout and compatible API guide determine the actual imports, markers, and commands.

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

