# Environment files, logging, or browser configuration

Use only the branch needed by the task. Resolve the application revision and capabilities through [nh-app-context](../../nh-app-context/SKILL.md) before adapting API examples. The existing consumer layout and compatible API guide determine the actual imports, markers, and commands.

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
| `Console.print (toText cfg.apiToken)` | Exposes the token: extracting `cfg.apiToken` produces ordinary `Text`. `Config.secret` redacts the generated config record's display, not the extracted value. Pass it only to the intended client; log a fixed message such as `"Catalogue credentials configured"` instead. |
| Omitting `|> Config.doc "..."` | Every field needs `Config.doc` — the TH macro **rejects fields without documentation** at compile time |
| Defaultsing and requiring the same field | `defaultsTo` and `required` are mutually exclusive — using both is a compile error |
| Adding `{-# LANGUAGE TemplateHaskell #-}` assuming it's missing | It is a **project default extension** — present in the source for clarity; do not diagnose its absence as a compilation failure |

---


## Server and browser boundaries

Server credentials stay in backend configuration. Values embedded in a browser bundle are public, even if their variable name contains `SECRET`; expose only the explicitly public configuration the UI needs. Use a synthetic sentinel when checking redaction and confirm it is absent from logs, serialized responses, and browser assets. Never use a real credential as a fixture.

Declaring `PORT` does not wire the transport. Trace the parsed option to the actual server configuration using the installed revision's API, start the owned local process, and observe the listener at the requested port. Report a declaration-only change as configuration preparation until that connection exists.

