---
name: neohaskell-collections
description: Choose revision-compatible Array, Map, Text, Set, or Uuid operations for a NeoHaskell application.
---

# Collections and identifiers

Resolve the API revision with [nh-app-context](../nh-app-context/SKILL.md). Read the one collection reference needed, confirm argument order and return type, then adapt the example to the consumer. Collection operations are immutable; observe the returned value. Array and Map folds may use different accumulator order.

For deterministic IDs, inspect the supported UUID/Decider APIs and the business-key normalization contract. A historical branch status is not a durable availability rule. Prefer [neohaskell-core-prelude](../neohaskell-core-prelude/SKILL.md) for imports and [neohaskell-effects-and-errors](../neohaskell-effects-and-errors/SKILL.md) for effectful generation.

Check the behavior at relevant empty, duplicate, and ordering boundaries using the existing component runner.

## Read only the relevant reference

| Condition | Resource |
|---|---|
| Sequence construction, transforms, and replay folds | [array.md](references/array.md) |
| Keyed lookup and map folds | [map.md](references/map.md) |
| Text operations | [text.md](references/text.md) |
| Unique values | [set.md](references/set.md) |
| Parsing, generating, or deriving identifiers | [uuid.md](references/uuid.md) |
| A complete collection module | [example.md](references/example.md) |
