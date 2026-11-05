---
name: neohaskell-core-prelude
description: Resolve NeoHaskell prelude, import, operator, numeric, and interpolation questions while writing or reviewing an application module.
---

# Core dialect

Read the effective revision's guide through [nh-app-context](../nh-app-context/SKILL.md). Use `Core` for application code and the canonical table below for dialect differences. A Haskell extension or familiar operator is not evidence that a NeoHaskell API exists.

1. Identify the operation and inspect the corresponding reference only.
2. Match exports and signatures to the actual dependency. Consult source when the guide is incomplete; record a concrete missing API instead of guessing.
3. Use qualified interoperability imports when an external test/parser/compiler API requires them. Keep that boundary explicit; do not treat all `Prelude` or library imports as application defects.

For collections use [neohaskell-collections](../neohaskell-collections/SKILL.md); for effects and errors use [neohaskell-effects-and-errors](../neohaskell-effects-and-errors/SKILL.md). Completion is code that uses the supported dialect and compiles in the discovered component; compilation alone does not prove behavior.

## Read only the relevant reference

| Condition | Resource |
|---|---|
| Imports, exports, and canonical dialect table | [imports-and-operators.md](references/imports-and-operators.md) |
| Numeric operations, interpolation, or console use | [values-and-formatting.md](references/values-and-formatting.md) |
| A complete small module example | [module-example.md](references/module-example.md) |
