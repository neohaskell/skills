# Choose and use an error/effect type

Use only the branch needed by the task. Resolve the application revision and capabilities through [nh-app-context](../../nh-app-context/SKILL.md) before adapting API examples. The existing consumer layout and compatible API guide determine the actual imports, markers, and commands.

## Quick reference

### Task

`Task err value` is the NeoHaskell effect type. **Error is the first type parameter.** `IO` never appears in domain logic — only inside `main` or `Application.run`.

| Operation | Signature — grounded in Task.hs | Note |
|---|---|---|
| wrap a value | `Task.yield :: value -> Task _ value` | replaces `pure`/`return` |
| fail with typed error | `Task.throw :: err -> Task err _` | replaces `throwIO`/`error` |
| chain | `Task.andThen :: (a -> Task err b) -> Task err a -> Task err b` | or use do-notation |
| transform value | `Task.map :: (a -> b) -> Task err a -> Task err b` | replaces `fmap` for Task |
| transform error | `Task.mapError :: (e1 -> e2) -> Task e1 a -> Task e2 a` | |
| recover from error | `Task.recover :: (err -> Task err2 a) -> Task err a -> Task err2 a` | replaces `catch` |
| capture as Result | `Task.asResult :: Task err a -> Task err2 (Result err a)` | |
| at the boundary only | `Task.runOrPanic :: (HasCallStack, Show err) => Task err a -> IO a` | `main`/`Application.run` |
| wrap any IO action | `Task.fromIO :: IO a -> Task _ a` | IO bridge — see below |
| conditional run | `Task.when :: Bool -> Task err Unit -> Task err Unit` | |
| loop over Array | `Task.forEach :: (a -> Task err Unit) -> Array a -> Task err Unit` | |

**IO bridge rule:** `Console.print :: Text -> Task _ Unit` is already a `Task` — call it directly in do-notation. `Console.log` and `Console.readLine` return `IO` — wrap them with `Task.fromIO`.

### Result

`Result error value` — **error is the first type parameter**, as in the usual `Either error value` convention.

| Operation | Signature — grounded in Result.hs | Note |
|---|---|---|
| success | `Result.Ok :: value -> Result error value` | construct or pattern match |
| failure | `Result.Err :: error -> Result error value` | construct or pattern match |
| fallback value | `Result.withDefault :: a -> Result b a -> a` | |
| transform value | `Result.map :: (a -> b) -> Result x a -> Result x b` | |
| chain | `Result.andThen :: (a -> Result e b) -> Result e a -> Result e b` | |
| transform error | `Result.mapError :: (a -> b) -> Result a c -> Result b c` | |
| to Maybe | `Result.toMaybe :: Result a b -> Maybe b` | |
| from Maybe | `Result.fromMaybe :: a -> Maybe b -> Result a b` | |
| inspect | `Result.isOk :: Result a b -> Bool` / `Result.isErr` | |

### Maybe

`Maybe a` — constructors `Just`/`Nothing` are in scope from `import Core`.

| Operation | Signature — grounded in Maybe.hs | Note |
|---|---|---|
| fallback | `Maybe.withDefault :: a -> Maybe a -> a` | replaces `fromMaybe` |
| transform | `Maybe.map :: (a -> b) -> Maybe a -> Maybe b` | replaces `fmap` for Maybe |
| chain | `Maybe.andThen :: (a -> Maybe b) -> Maybe a -> Maybe b` | short-circuits on Nothing |
| flatten | `Maybe.flatten :: Maybe (Maybe a) -> Maybe a` | |
| unsafe unwrap | `Maybe.getOrDie :: Maybe a -> a` | panics on `Nothing` |

