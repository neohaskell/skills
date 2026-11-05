# Parsing, generating, or deriving identifiers

Use only the branch needed by the task. Resolve the application revision and capabilities through [nh-app-context](../../nh-app-context/SKILL.md) before adapting API examples. The existing consumer layout and compatible API guide determine the actual imports, markers, and commands.

## Uuid — identifier values (`Uuid`)

`Uuid` is a `newtype` over `Data.UUID`. `Core` re-exports the **type only** — every function is
qualified, so always add `import Uuid qualified` (the full Core re-export table lives in
`neohaskell-core-prelude`).

```haskell
import Uuid qualified          -- the FUNCTIONS; the Uuid type itself comes from Core
```

### Operations (pinned rev — `core/core/Uuid.hs`)

```haskell
Uuid.generate      :: Task _ Uuid    -- v4 RANDOM; effectful, must run inside a Task
Uuid.nil           :: Uuid           -- all-zero UUID (also `def`, via Default)
Uuid.fromText txt  :: Maybe Uuid     -- parse; Nothing on malformed input
Uuid.toText u      :: Text
Uuid.fromLegacy uu :: Uuid           -- from a Data.UUID.UUID
Uuid.toLegacy u    :: UUID.UUID      -- to a Data.UUID.UUID
```

For deterministic identity, inspect the effective revision's `Uuid` and `Decider` APIs. Use its supported helper when available; otherwise isolate a justified interoperability boundary. Never infer availability from a pending branch or use a random generator for a stable business key.

---

