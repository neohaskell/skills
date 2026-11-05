# Declare, wire, or read server configuration

Use only the branch needed by the task. Resolve the application revision and capabilities through [nh-app-context](../../nh-app-context/SKILL.md) before adapting API examples. The existing consumer layout and compatible API guide determine the actual imports, markers, and commands.

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

