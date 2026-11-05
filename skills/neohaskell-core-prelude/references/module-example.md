# A complete small module example

Use only the branch needed by the task. Resolve the application revision and capabilities through [nh-app-context](../../nh-app-context/SKILL.md) before adapting API examples. The existing consumer layout and compatible API guide determine the actual imports, markers, and commands.

## Scratch module (Counter domain — copy-paste and adapt)

```haskell
module Starter.Counter.Util (
  describeCount,
  incrementIfPositive,
  summarise,
) where

import Core
import Array (Array)
import Array qualified
import Int qualified
import Text (Text)
import Text qualified


-- Pure function: pipe operator + fmt interpolation
describeCount :: Text -> Int -> Text
describeCount label count =
  [fmt|#{label}: #{count} item(s)|]


-- Pure function: case instead of multi-equation patterns; != instead of /=
incrementIfPositive :: Int -> Maybe Int
incrementIfPositive n =
  case n > 0 of
    True  -> Just (n + 1)
    False -> Nothing


-- Pure function: pipe style avoids let..in and where (both banned by style guide)
summarise :: Array Int -> Text
summarise counts =
  counts
    |> Array.sumIntegers
    |> \total -> [fmt|Total: #{total}, half: #{total // 2}|]
```

---

