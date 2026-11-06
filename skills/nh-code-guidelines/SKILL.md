---
name: nh-code-guidelines
description: NeoHaskell code style guidelines for writing and reviewing .hs code in a consumer application.
---

> Adapted for consumer applications from the public NeoHaskell project.

| Prefer in application code | Avoid unless the consumer contract requires it |
|---|---|
| `x \|> foo \|> bar` | `bar $ foo x`, `$` |
| `do let y = expr` | `let..in`, `where` |
| `case x of` | patterns in function head |
| `if cond then a else b` | `case cond of True -> …` |
| Named helpers with one abstraction level; orchestration reads top-to-bottom | nested control-flow pyramids, orchestration mixed with branch mechanics |
| Required public contracts and proven exceptions under [comment review](../nh-no-comments/SKILL.md) | comments narrating what code does; extract a named function instead |
| Early-exit sentinel guards in `Task` validation | nested if/case pyramids |
| `[fmt\|Hello #{name}!\|]` for interpolation; Core `++` for supported concatenation | foreign `<>` when the Core operation serves the contract |
| `Result err val`; convert foreign `Either` with `Result.fromEither`, then match `Ok`/`Err` | matching foreign `Left`/`Right` outside the Result conversion owner |
| `Task err val` | `IO` |
| `Task.yield v` | `pure`, `return` |
| `forall element result.` | single-letter type params |
| `import Core`; explicit type imports such as `import Foo (Foo)` and qualified operations | broad unqualified imports outside the consumer dialect |
| nhcore Core modules (`Text`, `Array`, `Char`, `File`, `Path`…) | raw `Data.*` / `System.*` / `Ghc*` imports |

For module headers and their scope, follow [module documentation](../nh-module-docs/SKILL.md). Before changing source pragmas or Cabal extension settings, follow [language extensions](../nh-language-extensions/SKILL.md).

## Readable service code

Read [Name for the reader](../nh-principle-name-for-the-reader/SKILL.md) before choosing module, type, or operation names. For service orchestration, exception boundaries, outcome types, serialization, or test resources, read [service design](../nh-best-practices/references/readable-services.md).

Discover and run the consumer's [static checks](references/static-checks.md) for affected code. The consumer owns its lint configuration and supported exceptions. Review the remaining design decisions against their owning skills.

## Application examples

Write application modules, documentation examples, and consumer fixtures in NeoHaskell's application dialect. Use the
framework markers for the instances they generate. Use `newtype` when it models
the domain. Never use explicit `stock` or `via` deriving strategies in these
application examples.

Keep each deriving clause only for a concrete framework constraint or an
operation the example actually performs. Remove unused `Eq`, `Ord` and `Show`
instances. GHC supplies `Typeable` automatically, so omit explicit `Typeable`
deriving. Keep `Generic` and serialization instances when an actual codec needs
them and a framework marker does not supply them. Apply
[Minimize Reader Load](../nh-principle-minimize-reader-load/SKILL.md) to declarations,
imports and annotations as well as control flow.

Qualified interoperability code may use foreign library machinery where the boundary requires it, including QuickCheck generators. Keep that exception explicit and preserve the supported consumer dialect.
