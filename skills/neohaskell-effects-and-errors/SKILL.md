---
name: neohaskell-effects-and-errors
description: Choose pure transformation, Result, Task, or Decider operations and bridge error channels in NeoHaskell application code.
---

# Effects and error channels

1. Discover supported signatures through [nh-app-context](../nh-app-context/SKILL.md).
2. Choose a pure function for a total transformation, `Maybe` for absence, `Result error value` for a pure failure with detail, `Task error value` for execution, and the supported `Decision` API for command decisions.
3. Preserve error meaning when mapping channels. End command decisions with the appropriate Decider constructor; distinguish constructing a decision from executing it.
4. Test success and the relevant failure path. Compilation, a returned action plan, and an executed external effect establish different facts.

`Result error value` puts the error first, just like the usual `Either error value` convention. Formatting and the general operator table belong to [neohaskell-core-prelude](../neohaskell-core-prelude/SKILL.md).

## Read only the relevant reference

| Condition | Resource |
|---|---|
| Choose and use an error/effect type | [effects.md](references/effects.md) |
| Adapt a complete effect module | [example.md](references/example.md) |
