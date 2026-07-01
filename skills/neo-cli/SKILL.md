---
name: neo-cli
description: >
  Use when the user needs to know the correct `neo` subcommand for any tooling intent:
  building, running, testing, scaffolding, locking domain files, inspecting the domain
  layout, opening the IDE, or installing skills. Maps every intent to the exact
  `neo` subcommand invocation and flags, explains the Nix wrapping (build/run/test
  are NOT plain cabal), and states the real ports (IDE port 2323 vs app port 8080).
  Also use when a `neo` invocation fails, to confirm the correct flag name/order, or
  to clarify what is and is not a real subcommand (e.g. there is no `neo serve`,
  `neo deploy`, or `neo openapi`).
metadata:
  model: haiku
---

This is NeoHaskell, not vanilla Haskell. The `.hs` extension is shared, but NeoHaskell
uses a custom `Core` prelude and the `neo` CLI wraps every Haskell build step inside
`nix develop --command bash -c "cabal …"`. Never call `cabal`, `stack`, or `ghc`
directly; always go through `neo`.

---

## Inputs / Outputs / Next

**Input:** a tooling intent ("build the project", "run tests", "open the IDE", "scaffold
a new project", "lock a file") plus the project root (must contain `flake.nix` and
`neo.json`).

**Output:** the exact `neo <subcommand> [flags]` command(s) + what they wrap/require.

**Next skills:**
- `neo-run-and-inspect` — HTTP endpoints, OpenAPI, `/health`, `neo inspect`
- `neo-immutability-and-versioning` — `.locked-files`, lock gate, V-bump rule
- `wire-feature` — after building, to register new commands/queries
- `write-hurl-e2e` — after `neo test` is confirmed working

---

## Command surface (grounded in `neo/src/cli.rs` + `neo/src/subprocess/nix.rs`)

### Global flags (always placed BEFORE the subcommand)

```
neo [--verbose | -v] [--ci] <subcommand> …
```

| Flag | Effect |
|------|--------|
| `--verbose` / `-v` | Enable debug-level output |
| `--ci` | Disable interactive prompts, animations, and colors. **Incompatible with `--watch`**; `neo --ci build --watch` is rejected. |

---

### `neo new [<project-name>] [--library]`

Scaffold a new NeoHaskell project (interactive interview, or CI-defaults if `--ci`).

```sh
neo new my-app          # interactive; prompts for name/version/license
neo new my-lib --library  # library project (no executable stanza)
neo --ci new my-app     # non-interactive, uses defaults
```

**Requires:** nothing (downloads the starter template).

---

### `neo build [--watch] [--skip-lock-check]`

Lock-gate check, then reconcile `neo.json` → `flake.nix` + `.cabal`, then:

```
nix develop --command bash -c "cabal build all"
```

```sh
neo build                       # standard build with lock check
neo build --watch               # GHCi hot-reload session (incompatible with --ci)
neo build --skip-lock-check     # bypass the pre-build lock gate (use sparingly)
```

**Requires:** `nix` on `PATH` + a flake-enabled directory (`flake.nix` present).

The lock gate aborts `neo build` if any path listed in `.locked-files` appears in
`git status --porcelain`. Fix = create a `V2` sibling (see `neo-immutability-and-versioning`),
never edit the locked file.

**Verify the build compiled:** `neo build` exits 0 on success.

---

### `neo run [--watch]`

Reconcile, then:

```
nix develop --command bash -c "cabal run all"
```

```sh
neo run           # build and start the app; serves on http://localhost:8080
neo run --watch   # auto-restart on file changes (incompatible with --ci)
```

**App port:** `8080` — this comes from the project's `Config.hs` / env var (typically
`PORT`), **not from a CLI flag**. There is no `--port` option on `neo run`.

**Requires:** `nix` on `PATH` + a flake-enabled directory.

---

### `neo test [--watch]`

```
nix develop --command bash -c "cabal test all"
```
then discovers and runs every `tests/**/*.hurl` file against a freshly booted app.

```sh
neo test          # unit tests (cabal) + hurl e2e files
neo test --watch  # re-run on file changes (incompatible with --ci)
```

**Boot wait:** `neo test` boots the app and waits approximately 2 seconds before firing
hurl files. It does **not** poll `/ready` — `GET /ready` is 404 unless
`Application.withReadinessProbe` is explicitly wired. Build-chain for hurl tests: see
`write-hurl-e2e`.

**Requires:** `nix` on `PATH` + `git` (required by the test runner) + a flake-enabled directory.

---

### `neo lock`

Manage the `.locked-files` immutability manifest. Three forms:

```sh
neo lock <search-string>   # fuzzy-match and lock discovered domain files
neo lock --all             # lock ALL discovered domain files under src/
neo lock install           # install the git pre-commit hook (run once, after neo new)
neo lock check             # check if any locked files are modified (used by the hook)
```

There is **no** `neo lock --remove` or `neo lock uninstall` subcommand.
Full `.locked-files` mechanics → `neo-immutability-and-versioning`.

---

### `neo ide [--host <IP>] [--port <N>]`

Start the bundled in-browser event-modeling IDE.

```sh
neo ide                          # binds 127.0.0.1:2323 (loopback only)
neo ide --host 0.0.0.0           # reachable from other machines on the network
neo ide --host 0.0.0.0 --port 9000
```

Defaults from `cli.rs`:
- `--host` default: `127.0.0.1` (loopback; literal IPv4/IPv6 address required — **not** a hostname like `localhost`)
- `--port` default: `2323`

**IDE port 2323 is not the app API port (8080).** Do not confuse them.

Open the printed URL in a browser. Press Ctrl-C to stop.

---

### `neo inspect [<subcommand>]`

Print the project's domain layout. With no subcommand, dumps everything as JSON.

```sh
neo inspect               # full JSON dump of all domains
neo inspect domains       # discovered domain directories under src/
neo inspect commands      # commands per domain (name, file, events produced, HTTP flag)
neo inspect events        # event-sum constructors per domain
neo inspect queries       # queries per domain
neo inspect integrations  # integrations per domain (name, kind, events, commands emitted)
neo inspect wiring        # derived wiring: command → event → integration → command
neo inspect sync          # DESTRUCTIVE: rewrites event-model.json from source
```

**Warning — `neo inspect sync` clobbers `event-model.json`**. It regenerates the file
entirely from source code. Any hand-authored additions (e.g. from the `event-modeling`
skill) that have not yet been committed to code will be lost. Only run it when you want
source code to be the authoritative source of truth for the model.

HTTP endpoint inspection → `neo-run-and-inspect`.

---

### `neo skills setup [flags]`

Fetch `github.com/neohaskell/skills` and install skills into the project's AI tool folders.

```sh
neo skills setup                          # interactive tool picker
neo skills setup --tool claude            # install for Claude Code only
neo skills setup --tool claude --tool cursor  # multiple tools (flag is repeatable)
neo skills setup --all-tools              # install for every supported tool
neo skills setup --skill neo-cli          # install only this skill (repeatable)
neo skills setup --force                  # overwrite existing destinations
neo skills setup --dry-run                # print the plan without writing anything
neo skills setup --refresh                # re-clone the library (ignore cached copy)
neo --ci skills setup --all-tools         # non-interactive, all tools
```

Supported tool IDs: `claude`, `codex`, `kiro`, `cursor`, `agents`.

---

## DO / DON'T

| You might reach for | NeoHaskell-correct |
|---|---|
| `cabal build` directly | `neo build` (Nix-wrapped; runs the lock gate first) |
| `cabal test` directly | `neo test` (also runs hurl e2e files) |
| `cabal run` directly | `neo run` |
| `stack build` / `ghc` | never; `neo build` only |
| `neo serve` / `neo deploy` / `neo openapi` | these subcommands do not exist |
| `neo run --port 9090` | no `--port` flag on `neo run`; port is Config/env-var (`PORT`) |
| `neo --ci build --watch` | `--watch` and `--ci` are mutually exclusive; pick one |
| `neo ide --host localhost` | must be a literal IP address (e.g. `127.0.0.1`); hostnames are rejected by clap |
| `neo lock --remove` | does not exist; only `install`/`check`/`<search>`/`--all` |
| assume `/ready` polls before hurl | `neo test` waits ~2s; `/ready` is 404 unless `withReadinessProbe` wired |
| `neo inspect sync` to see the model | sync **clobbers** `event-model.json`; use `neo inspect` (no subcommand) to read |
| global flags after the subcommand | global flags (`--verbose`, `--ci`) must come **before** the subcommand |

---

## Verify

After any build-related change, confirm with:

```sh
neo build
```

Exit 0 = compiled. Non-zero = the lock gate tripped or cabal compilation failed (read
the error output; lock violations say which file; compilation errors show the GHC
message from inside the Nix shell).
