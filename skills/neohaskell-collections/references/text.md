# Text operations

Use only the branch needed by the task. Resolve the application revision and capabilities through [nh-app-context](../../nh-app-context/SKILL.md) before adapting API examples. The existing consumer layout and compatible API guide determine the actual imports, markers, and commands.

## Text — string handling (`Text`)

`Text` is `Data.Text.Text`. String literals are already `Text` (OverloadedStrings). Never use
`String` / `[Char]`. Do not `import Data.Text` directly.

### Common operations

```haskell
Text.length txt           :: Int
Text.isEmpty txt          :: Bool
Text.split sep txt        :: Array Text         -- returns Array, not a list
Text.joinWith sep arr     :: Text               -- intercalate
Text.replace old new txt  :: Text
Text.contains sub txt     :: Bool               -- isInfixOf
Text.startsWith pre txt   :: Bool
Text.endsWith suf txt     :: Bool
Text.left n txt           :: Text               -- first n chars
Text.right n txt          :: Text               -- last n chars
Text.dropLeft n txt       :: Text               -- drop first n chars
Text.dropRight n txt      :: Text               -- drop last n chars  (Data.Text.dropEnd)
Text.slice from to txt    :: Text               -- substring by index
Text.reverse txt          :: Text
Text.toUpper / Text.toLower txt :: Text
Text.trim / Text.trimLeft / Text.trimRight txt  :: Text
Text.toInt txt            :: Maybe Int
Text.fromInt n            :: Text
Text.toFloat txt          :: Maybe Float
Text.fromFloat f          :: Text
Text.words txt            :: Array Text         -- split on whitespace
Text.lines txt            :: Array Text         -- split on newlines
Text.toBytes txt          :: Bytes             -- encode to Bytes
Text.fromBytes bytes      :: Text              -- decode Bytes back to Text
```

> **No `stripSuffix` / `stripPrefix` / `dropWhileEnd`** — those vanilla `Data.Text` names are not
> exposed. You rarely need them: strip a known trailing affix with `endsWith` + `dropRight`. E.g. drop
> a trailing slash with `if Text.endsWith "/" p then Text.dropRight 1 p else p`; strip a fixed suffix
> with `Text.dropRight (Text.length suffix) p` (guarded by `endsWith`). `Text.trim` only removes
> whitespace.

### String interpolation

Use the `fmt` quasi-quoter (re-exported by `Core`) with `#{expr}` syntax. Never use `<>` / `++`
for strings when interpolation reads more clearly, and never use `${}` or `%s`.

```haskell
-- Correct: #{expr} inside [fmt|...|]
greet :: Text -> Int -> Text
greet name count =
  [fmt|Hello #{name}! You have #{count} item(s).|]

-- Wrong forms (all silently incorrect or don't compile):
--   [fmt|{name}|]       -- bare {} silently prints literal "{name}"
--   "${name}"           -- not valid in NeoHaskell
--   name ++ " world"    -- works but prefer fmt for readability
```

---

