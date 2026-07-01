---
name: neo-config-and-secrets
description: >
  Use when adding a new configuration field or secret to a NeoHaskell project:
  declaring a field in Config.hs with the defineConfig TH DSL, wiring it via
  Application.withConfig, reading it in an integration or factory function, or
  setting up a .env / .env.example file. Also use when someone asks how to pass
  an API token, port, or any tuneable to the app without hand-rolling getArgs or
  lookupEnv, or when reviewing Config.hs for leaked secrets, String fields, or
  missing doc modifiers. Covers Config.field, Config.doc, Config.defaultsTo,
  Config.required, Config.envVar, Config.cliLong, Config.cliShort, Config.secret,
  Application.withConfig, the factory-lambda wiring pattern, and
  the Config.get accessor.
metadata:
  model: haiku
---

**This is NeoHaskell, not vanilla Haskell.** The `.hs` extension is shared, but
config is declared via the `defineConfig` Template Haskell DSL, never by
hand-rolling `System.Environment.lookupEnv` or `System.Environment.getArgs`.
Field types are `Text` and `Int`, never `String`.

---

## Inputs / Outputs / Next

- **Input:** a new tunable (port, flag, token) or a review of an existing `Config.hs`.
- **Output:** a `Config.hs` `defineConfig` block + `Application.withConfig` wiring
  in `App.hs` + the factory lambda pattern for config-dependent services.
- **Next skills:**
  - `implement-integration` — the most common consumer of config values
  - `wire-feature` — App.hs wiring context
  - `neo-run-and-inspect` — observing the running app after config changes

---

## Config.hs template

Grounded in `NeoHaskell/testbed/src/Testbed/Config.hs` (compiling public source).
Replace `Library` and the field names with your context.

`TemplateHaskell` is a **project default extension** — it is present in the source
file shown here for clarity, but the generated cabal file already enables it
project-wide. You do not need to add it yourself.

```haskell
{-# LANGUAGE TemplateHaskell #-}

-- | Configuration for the Library application.
module Library.Config (
  LibraryConfig (..),
  HasLibraryConfig,
) where

import Config (defineConfig)
import Config qualified
import Core


defineConfig
  "LibraryConfig"
  [ Config.field @Int "port"
      |> Config.doc "HTTP server port"
      |> Config.defaultsTo (8080 :: Int)
      |> Config.envVar "PORT"
      |> Config.cliLong "port"
      |> Config.cliShort 'p'

  , Config.field @Text "catalogBaseUrl"
      |> Config.doc "Base URL for the external catalogue service"
      |> Config.defaultsTo ("http://catalogue.internal" :: Text)
      |> Config.envVar "CATALOGUE_BASE_URL"

    -- Secret: Config.secret redacts the value in Show / --help output.
  , Config.field @Text "apiToken"
      |> Config.doc "API token for the catalogue service (sensitive)"
      |> Config.required
      |> Config.envVar "API_TOKEN"
      |> Config.secret
  ]
```

`defineConfig` generates:

| Generated artifact | What it is |
|--------------------|-----------|
| `data LibraryConfig = LibraryConfig { port :: Int, catalogBaseUrl :: Text, apiToken :: Text }` | The config record |
| `instance HasParser LibraryConfig` | Parsed from CLI args + env vars + `.env` at startup |
| `type HasLibraryConfig = (?config :: LibraryConfig)` | Implicit-parameter constraint for consumers |
| Custom `Show` instance | Replaces every `secret` field value with `REDACTED` |

---

## Wiring in App.hs

Register the config type with `Application.withConfig`. Services that need config
values receive them through a **factory lambda** — calling `Config.get` at wiring
time panics because the app has not yet loaded the config.

```haskell
module App (app) where

import Core
import Library.Config (LibraryConfig (..))
import Service.Application (Application)
import Service.Application qualified as Application
import Service.Transport.Web qualified as WebTransport
import Library.Service qualified


app :: Application
app =
  Application.new
    |> Application.withConfig @LibraryConfig
    |> Application.withTransport WebTransport.server
    |> Application.withService Library.Service.libraryService
```

When a downstream component (e.g., an event store or integration) needs the
config, pass a **factory function** — the framework calls it after the config is
loaded:

```haskell
    |> Application.withEventStore makeEventStoreConfig


makeEventStoreConfig :: LibraryConfig -> MyEventStoreConfig
makeEventStoreConfig config =
  MyEventStoreConfig
    { host = config.catalogBaseUrl
    , token = config.apiToken
    }
```

---

## Reading config at runtime

After `Application.run`, access the config anywhere with `Config.get`:

```haskell
import Library.Config (LibraryConfig)
import Config qualified

sendRequest :: Task Text ()
sendRequest = do
  let cfg = Config.get @LibraryConfig
  let token = cfg.apiToken
  -- ... use token
  Task.yield unit
```

Or carry the implicit-parameter constraint through your call chain:

```haskell
callCatalogue :: (HasLibraryConfig) => Task Text ()
callCatalogue = do
  let token = ?config.apiToken
  -- ...
  Task.yield unit
```

---

## .env and .env.example

`neo run` (and `neo test`) load `.env` automatically. Never commit `.env`; commit
`.env.example` with safe placeholder values:

```
# .env.example  — commit this
PORT=8080
CATALOGUE_BASE_URL=http://catalogue.internal
API_TOKEN=replace-me
```

```
# .env  — add to .gitignore
PORT=8080
CATALOGUE_BASE_URL=http://catalogue.internal
API_TOKEN=sk-actual-secret-value
```

---

## DO / DON'T

| You might write (vanilla reflex) | NeoHaskell-correct |
|----------------------------------|-------------------|
| `import System.Environment (lookupEnv)` and parse manually | `defineConfig` DSL — it handles CLI args, env vars, `.env`, validation, and `--help` |
| Field type `String` | Field type `Text` (string literals are already `Text` in NeoHaskell) |
| Bare `Text` for a token/password with no modifier | `field @Text ... |> Config.secret` — `Config.secret` redacts the value in `Show` / `--help` output |
| Forgetting `|> Config.secret` on a sensitive field | Always add `|> Config.secret` — without it the value appears in logs and `--help` |
| `Config.get @LibraryConfig` inside `Application.new |> ...` wiring | Factory lambda (`\config -> ...`) — `Config.get` panics if called before `Application.run` |
| `Console.print (toText cfg.apiToken)` | Safe when `Config.secret` was set — the generated `Show` instance emits `REDACTED`; the field is plain `Text` at runtime |
| Omitting `|> Config.doc "..."` | Every field needs `Config.doc` — the TH macro **rejects fields without documentation** at compile time |
| Defaultsing and requiring the same field | `defaultsTo` and `required` are mutually exclusive — using both is a compile error |
| Adding `{-# LANGUAGE TemplateHaskell #-}` assuming it's missing | It is a **project default extension** — present in the source for clarity; do not diagnose its absence as a compilation failure |

---

## Verify

```bash
neo build
```

A clean build confirms the `defineConfig` splice expanded without errors, all
`doc` modifiers are present, and `defaultsTo`/`required` exclusivity is satisfied.
If you see a TH splice error mentioning a missing doc, add `|> Config.doc "..."`.
