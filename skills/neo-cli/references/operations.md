# Inspect an application CLI operation

Use only the branch needed by the task. Resolve the application revision and capabilities through [nh-app-context](../../nh-app-context/SKILL.md) before adapting API examples. The existing consumer layout and compatible API guide determine the actual imports, markers, and commands.

## Command surface (grounded in `neo/src/cli.rs` + `neo/src/subprocess/nix.rs`)

### Global flags (always placed BEFORE the subcommand)

```
neo [--verbose | -v] [--ci] <subcommand> …
```

| Flag | Effect |
|------|--------|
| `--verbose` / `-v` | Enable debug-level output |
| `--ci` | Disable interactive prompts, animations, and colors. **Incompatible with `--watch`**; `neo --ci build --watch` is rejected. |

**Always use `neo --ci <cmd>` in any agent, CI, or non-interactive (non-TTY) shell.** With no
controlling terminal, bare `neo build` / `neo test` **panics before doing anything** — it tries to
drive an interactive TTY progress animation for its `nix` subprocess and dies with:

```
thread 'main' panicked at src/subprocess/nix.rs:108: called `Result::unwrap()` on an `Err` value:
Os { code: 6, kind: Uncategorized, message: "Device not configured" }
```

(errno 6 / ENXIO). `neo --ci build` / `neo --ci test` fixes it; the flag goes **before** the
subcommand. This is the single highest-value fact for agent/CI use — it blocks the very first build.

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

**Reconcile manages the cabal module lists.** The "Reconciling project artifacts" step
**regenerates** `exposed-modules` (and each test suite's `other-modules`) from the filesystem and
alphabetizes them. You do **not** need to hand-edit the `.cabal`: adding a `.hs` file under `src/`
(or a `*Spec.hs` under `tests/`) is enough to register it — any manual edits are normalized on the
next `neo build` / `neo test`.

**Inspect reconciliation effects.** Read the actual `neo.json` and effective dependency pin. If a project explicitly tracks `main`, build/test may advance it and print, for example,
`Updated input 'neohaskell': b5aa84d → e55fdf6`, rewriting `flake.nix` (`rev` + `neohaskellCommit`),
`cabal.project` (`tag:`), and `flake.lock` **together**. These are real working-tree changes. Review the diff and preserve the consumer's intended revision; do not normalize an unexpected upgrade away. Also covered by `neo-immutability-and-versioning`.

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

**Boot wait:** `neo test` boots the app and polls `http://127.0.0.1:8080/` (root path)
every ~250 ms for up to 60 s. It fires the hurl files as soon as **any** HTTP response
arrives — even a 404 — so it does not require a readiness endpoint to exist. It does
**not** use a fixed sleep. (For `/ready` endpoint details see `neo-run-and-inspect`.)
Build-chain for hurl tests: see `write-hurl-e2e`.

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
neo inspect sync          # regenerates event-model.json from source (overwrites manual edits)
```

**Warning — `neo inspect sync` clobbers `event-model.json`**. It regenerates the file
entirely from source code. Any hand-authored additions (e.g. from the `event-modeling`
skill) that have not yet been committed to code will be lost. Only run it when you want
source code to be the authoritative source of truth for the model.

HTTP endpoint inspection → `neo-run-and-inspect`.

---

### `neo validate [<path>] [--json]`

Lint `event-model.json` against the embedded JSON Schema **and** referential-integrity rules —
**read-only** (never modifies the file). This is the CLI form of the check the `neo ide` runs.

```sh
neo validate                         # validates <cwd>/event-model.json
neo validate path/to/event-model.json
neo validate --json                  # emit the ValidationOutcome as JSON on stdout
neo validate --json | jq -e '.status == "valid"'
```

Exit codes: **0** valid · **1** IO error · **2** invalid (schema/referential) · **3** malformed JSON ·
**4** file missing. Used by `verify-event-model` for PASS 1 + PASS 2. (For best-practice/naming review
— PASS 3 — see `verify-event-model`; `neo validate` does the mechanical passes only.)

---

