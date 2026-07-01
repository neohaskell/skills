---
name: neo-run-and-inspect
description: |
  Tells an AI coding agent how to run a NeoHaskell application and work with its live HTTP surface. Use whenever the user asks to start the app, run the server, hit an endpoint, post a command, read a query, view or download the OpenAPI spec, open the Scalar docs UI, open the event-modeling IDE, run neo inspect, or sync the event model. Also use before writing hurl e2e tests to confirm endpoint paths and ports, and when the user asks about health checks, readiness probes, or port numbers. Grounds every URL, subcommand, and port in neo/src/cli.rs and Service/Transport/Web.hs so the agent never invents nonexistent CLI subcommands or wrong endpoint paths.
metadata:
  model: haiku
---

> This is NeoHaskell, not vanilla Haskell. Files share the `.hs` extension but the language uses `import Core` instead of `Prelude`, `Task` instead of `IO`, `Array` instead of lists, and `|>` instead of `$`. This skill is a tooling reference — it does not generate Haskell code.

## Inputs / Outputs / Next

- **Inputs:** a task — start the app, hit an endpoint, view API docs, open the IDE, sync the event model
- **Outputs:** exact `neo` commands, URLs, and port numbers
- **Next:** [write-hurl-e2e](../write-hurl-e2e/) (HTTP e2e tests that POST/GET these endpoints), [wire-feature](../wire-feature/) (wiring a new command or query so its endpoint exists), [neo-cli](../neo-cli/) (full CLI reference for build/test/lock), [event-modeling](../event-modeling/) (add features after `neo inspect sync`)

---

## 1. Start the app

```sh
neo run             # reconcile config, build, then start the app on :8080
neo run --watch     # same, but auto-restarts on source-file changes
```

The app binds to **`http://localhost:8080`** by default. That default comes from `Service.Transport.Web`:

```haskell
-- Service/Transport/Web.hs (neohaskell/neohaskell)
server :: WebTransport
server =
  WebTransport
    { port = 8080,
      ...
    }
```

The port is Config-derived, not hard-coded in the CLI. To override it, declare the env var in your `Config.hs`:

```haskell
|> Config.field @Int "port" |> Config.doc "HTTP port" |> Config.envVar "PORT"
```

---

## 2. HTTP API surface

All routes are implemented in `Service.Transport.Web.assembleTransport`. This is the authoritative table:

| Method | Path            | Notes |
|--------|-----------------|-------|
| `POST` | `/commands/<kebab-name>` | Execute a command; body is JSON |
| `GET`  | `/queries/<kebab-name>`  | Read a query result |
| `GET`  | `/openapi.json`          | OpenAPI 3.x spec (JSON) |
| `GET`  | `/openapi.yaml`          | OpenAPI 3.x spec (YAML) |
| `GET`  | `/docs`                  | Scalar interactive docs UI |
| `GET`  | `/health`                | Health check; 200 OK, always available |
| `GET`  | `/ready`                 | Readiness probe; **enabled by default** (200 = Ready, 503 = Rebuilding/Failed) |

**Kebab-case conversion.** The router converts the URL path segment to PascalCase before looking up the handler. The URL `/commands/increment-counter` maps to the `IncrementCounter` command type. The URL `/queries/counter-value` maps to the `CounterValue` query type.

---

## 3. Copy-paste template

Replace `increment-counter` / `counter-value` with your actual kebab-case names.

### curl

```sh
# POST a command (Counter domain — public example)
curl -s -X POST http://localhost:8080/commands/increment-counter \
  -H "Content-Type: application/json" \
  -d '{"entityId":"00000000-0000-0000-0000-000000000001","amount":1}'

# GET a query
curl -s http://localhost:8080/queries/counter-value

# OpenAPI spec — JSON (pipe to jq for readability)
curl -s http://localhost:8080/openapi.json | jq .

# OpenAPI spec — YAML
curl -s http://localhost:8080/openapi.yaml

# Scalar interactive docs — open in your browser
open http://localhost:8080/docs         # macOS
xdg-open http://localhost:8080/docs    # Linux

# Health check (always 200 when the app is up)
curl -s http://localhost:8080/health

# Readiness probe (enabled by default; 200 = Ready, 503 = Rebuilding/Failed)
curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/ready
```

### Hurl (for use with `neo test` or `write-hurl-e2e`)

```hurl
# tests/counter/increment.hurl
POST http://localhost:8080/commands/increment-counter
Content-Type: application/json
{
  "entityId": "00000000-0000-0000-0000-000000000001",
  "amount": 1
}
HTTP 200

GET http://localhost:8080/queries/counter-value
HTTP 200
```

---

## 4. `/ready` is enabled by default

`Application.new` sets `readinessConfig = Just ReadinessConfig { readinessPath = "ready", includeQueryStatus = True }`, so the endpoint is live from the first `neo run` without any extra wiring:

- **200** — app is Ready
- **503** — app is Rebuilding or Failed

`Application.useReadinessEndpoint :: Application -> Application` re-enables the endpoint after an explicit disable; you only need to call it if something in your `App.hs` has set `readinessConfig = Nothing`. Under normal circumstances (starting from `Application.new`) you can hit `/ready` immediately and load-balancer readiness checks will work out of the box.

---

## 5. OpenAPI title and version

The spec title and version come from `Application.withApiInfo`. If that call is absent, defaults from `Service.Application.Types.defaultApiInfo` are used (`"API"` / `"1.0.0"`). To customise:

```haskell
-- App.hs
Application.run
  |> Application.withApiInfo (\_ -> ApiInfo { apiTitle = "My App", apiVersion = "0.1.0", apiDescription = "" })
  ...
```

---

## 6. The event-modeling IDE (`neo ide`)

```sh
neo ide                      # binds to 127.0.0.1:2323 (loopback only)
neo ide --port 9000          # custom port
neo ide --host 0.0.0.0       # expose to LAN
```

The host argument **must be an IP literal** — `localhost` (a hostname) is rejected by the CLI parser.

Open **`http://127.0.0.1:2323`** in a browser. This is the in-browser event-modeling IDE. It is completely separate from the app API at `:8080`.

---

## 7. `neo inspect`

Print the project's domain layout as structured JSON, or filter to one section:

```sh
neo inspect                  # full project JSON — all domains as one document
neo inspect domains          # discovered domain directories under src/
neo inspect commands         # commands per domain (name, file, events produced, HTTP-reachable)
neo inspect events           # event-sum constructors per domain
neo inspect queries          # queries per domain (name, file, event constructors referenced)
neo inspect integrations     # integrations per domain (name, kind, events handled, commands emitted)
neo inspect wiring           # derived wiring: command → event → integration → command chains
```

### `neo inspect sync` — CLOBBER WARNING

```sh
neo inspect sync
```

This rewrites `event-model.json` **entirely from source code**. Any hand-authored additions (made by the [event-modeling](../event-modeling/) skill) that are not yet implemented in Haskell source will be lost.

The safe direction: drive the model **into code** (implement → wire → sync), not the reverse.

- Run `neo inspect sync` to **bootstrap** or **refresh** the model from existing code.
- Run it **before** editing `event-model.json` by hand, not after.
- After adding a feature manually to `event-model.json`, implement it first, then run sync if you want to verify round-trip fidelity.

---

## 8. DO / DON'T

| Wrong instinct | NeoHaskell-correct |
|---|---|
| `cabal run` directly | `neo run` — Nix-wrapped, reconciles config first |
| Invent `neo openapi`, `neo serve`, or `neo start` | No such subcommands; the **running app** serves its own OpenAPI at `/openapi.json` |
| Navigate to `/swagger` or `/swagger-ui` | Navigate to `/docs` (Scalar UI); `/swagger` returns 404 |
| Use port `:2323` for API calls | `:2323` is `neo ide` (event-modeling UI); the app API is `:8080` |
| Use port `:8080` to open the IDE | `:8080` is the app API; open `http://127.0.0.1:2323` for the IDE |
| Assume `/ready` must be manually wired | `/ready` is **on by default** via `Application.new`; use `Application.useReadinessEndpoint` only to re-enable after an explicit disable |
| Run `neo inspect sync` after hand-editing `event-model.json` | Sync clobbers hand-authored edits — run it only to bootstrap or refresh from existing Haskell source |
| Hard-code port 8080 everywhere | Port is Config-derived (default 8080); to override, add a `Config.envVar "PORT"` field in `Config.hs` |
| Pass `"localhost"` to `neo ide --host` | Must be an IP literal: `127.0.0.1` or `0.0.0.0`; `neo ide --host localhost` is rejected by the CLI |

---

## 9. Verify

```sh
# start the app (background so you can run checks inline)
neo run &
sleep 2

# health check — should return 200
curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/health

# openapi title — should match your Application.withApiInfo value (default: "API")
curl -s http://localhost:8080/openapi.json | jq .info.title

# if /openapi.json returns paths: {} — no commands/queries are wired yet
# → run wire-feature to register them in Service.hs and App.hs
```
