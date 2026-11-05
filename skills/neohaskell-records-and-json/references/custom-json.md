# Review historical or custom JSON needs

Use only the branch needed by the task. Resolve the application revision and capabilities through [nh-app-context](../../nh-app-context/SKILL.md) before adapting API examples. The existing consumer layout and compatible API guide determine the actual imports, markers, and commands.

## Backward-compat trap — adding a field to an existing entity

When you hand-write a `FromJSON` instance (instead of using the empty Generic
form), use `(.:?)` and `(.!=)` from `Json` to give new fields a default so old
snapshots without that field still decode:

```haskell
instance Json.FromJSON <Entity> where
  parseJSON = Json.withObject "<Entity>" \obj -> do
    <entityId> <- obj Json..:  "<entityId>"
    <fieldA>   <- obj Json..:  "<fieldA>"
    -- New field added later — optional with a default so old snapshots decode:
    <newField> <- obj Json..:? "<newField>" Json..!= 0
    Json.yield <Entity> {<entityId>, <fieldA>, <newField>}
```

**The empty Generic `FromJSON` rejects an old snapshot that is missing a new
non-`Maybe` field** — it has no concept of a default. If you are expanding an
entity rather than creating one from scratch, use `expand-entity` instead of
this skill; that skill owns the backward-compat field-addition rules.

---


## Deriving clause by block type

| Block | Typical deriving | Notes |
|---|---|---|
| Entity record | `(Generic)` | Add `Eq, Show` if tests need it |
| Nested value object | `(Generic)` | Same |
| Command record | `(Generic, Typeable, Show)` | `Typeable` is required by the `command` TH macro |
| Event payload | `(Eq, Show, Ord, Generic)` | `Ord` useful; events go in `Events/<Name>.hs` |
| Query read model | `(Generic, Eq, Show)` | `ToSchema` added separately; `deriveQuery` may also emit Generic/Show/JSON for fresh types |

---

