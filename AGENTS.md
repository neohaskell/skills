# Working in a NeoHaskell project

This project is built with **NeoHaskell** — an event-sourced / CQRS framework with a
custom `Core` prelude, driven by the `neo` CLI. The `.hs` extension is shared with
Haskell, but **this is NOT vanilla Haskell.** The `neohaskell-*` / `neo-*` skills
installed in this repo carry the details; this primer is the baseline that always applies.

## Start here

To **add, build, change, or design a feature**, **start a new project**, or **fix a bug in
deployed code**, use the **`neohaskell-feature-pipeline`** skill — it drives the whole flow
(augment → event-model → verify → outside-in TDD per slice) and routes to the right
specialized skill at each step. When unsure which skill applies, start there.

## Non-negotiable invariants

These hold across every task, even before a specific skill is consulted:

- **`import Core`, not `Prelude`.** `NoImplicitPrelude` is on project-wide. Use `Text` (not
  `String`), `Array a` (not `[a]`; there is no `Array.filter` — use `takeIf`/`dropIf`),
  `Task err a` (not `IO`), `Result`/`Ok`/`Err` (not `Either`), `|>` (not `$`), `++` or
  `[fmt|…#{x}…|]` (not `<>`), `!=` (not `/=`), `panic` (not `error`; there is no `todo`),
  and dot access (`rec.field`, not field-selector functions).
- **Deployed code is immutable.** Never edit, rename, or delete a file under `Commands/`,
  `Events/`, or `Queries/` once it is locked/deployed — `neo build` refuses it. A fix is a
  new `V2`/`V3` sibling (see `neo-immutability-and-versioning`). Entities evolve **add-only**
  (never remove, rename, or retype a field).
- **Outside-in, test-first.** Build each vertical slice tests-first (hurl → acceptance →
  unit → domain types → minimal implementation → wire → refactor). Write the failing test
  before the code.
- **All tests live under `tests/`** — both Hspec/QuickCheck specs *and* `.hurl` files. Never
  use a `test/` directory; `neo` won't discover it.
- **Stub outbound integrations with `Integration.none` + a `-- TODO:` comment** — never
  `panic` a pure `handleEvent` (it crashes the dispatcher when that event fires). `panic
  "TODO: not implemented"` is only for pure functions and `Task` bodies.
- **Drive the toolchain through `neo`** (`neo build` / `run` / `test`), which wraps the
  Haskell toolchain in Nix — never call `cabal`, `stack`, or `ghc` directly.

## The skills

Installed by `neo skills setup`: an entry point (`neohaskell-feature-pipeline`), the design
skills (`augment-feature-request`, `event-modeling`, `verify-event-model`), the outside-in
TDD discipline + domain modeling, the implementers (`implement-*`, `expand-entity`,
`wire-feature`), the test writers (`write-*`), the language cheatsheets (`neohaskell-*`) and
tooling (`neo-*`), and PR review (`neohaskell-code-review`, `neohaskell-code-review-ci`).
Consult the relevant skill for any non-trivial step — its templates are grounded in real
NeoHaskell source, which the models tend to hallucinate otherwise.
