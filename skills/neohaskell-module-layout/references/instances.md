# Resolve Default and instance placement

Use only the branch needed by the task. Resolve the application revision and capabilities through [nh-app-context](../../nh-app-context/SKILL.md) before adapting API examples. The existing consumer layout and compatible API guide determine the actual imports, markers, and commands.

## instance Default rule

Every entity module must declare:

```haskell
instance Default CounterEntity where
  def = initialState
```

`Default` is re-exported by `Core` — no separate import is needed. Declaring `instance Default` for every entity is a strong project convention; the `command` and `deriveQuery` macros do not enforce it at compile time, but all public examples follow the pattern.

Grounded in: `testbed/src/Testbed/Cart/Core.hs` line 28–30.

---

