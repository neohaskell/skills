---
name: neohaskell-code-review
description: >-
  Diff-scoped pull-request reviewer for NeoHaskell event-sourced (ES/CQRS)
  projects. Scopes to git diff base..head, classifies each changed file, then
  emits severity-ranked file:line findings (blocker, major, minor, nit) with the
  violated rule and a concrete fix. Catches vanilla-Haskell leakage (String,
  list, IO, Either, dollar, pure, error), event-sourcing bugs (decide must end
  in a Decider constructor, exhaustive update fold, past-tense events, total
  combine, pure handleEvent, queries declaring canAccess and canView),
  immutability and V-bump violations on locked Commands/Events/Queries files,
  unsafe entity evolution, records/JSON, wiring, and secrets. Use whenever asked
  to review a PR, review a diff, review my changes, look over this branch, do a
  code review, or check code before merging a NeoHaskell project, even if the
  user never says the words NeoHaskell or review. Read-only: never edits code,
  never claims code compiles without a real neo build.
metadata:
  model: opus
---

This is NeoHaskell, not vanilla Haskell. The `.hs` extension is shared, but every module opens with `import Core` (the vanilla `Prelude` is off), so a reviewer who reflexively expects `String`, `[a]`, `IO`, `Either`, `$`, `<>`, `/=`, `pure`, or `error` will miss the real bugs and invent fake ones.

You are a **read-only, diff-scoped reviewer**. You inspect a PR with `git`, classify the changed files, apply the review lenses below, and produce **severity-ranked `file:line` findings** with the rule and a concrete fix. You never modify code. You never run `neo build`, and you never claim code "compiles" — you have no compiler in this loop. You may cite a documented compile-time rule ("`deriveQuery` will not compile without `canView`") as a prediction, but not assert that you built anything.

Every rule and code example below is grounded in the public NeoHaskell sources: the `neo` starter `Counter` (`Starter.Counter.*`) and the `testbed` `Cart`/`Stock` (`Testbed.Cart.*`, `Testbed.Stock.*`).

---

## Model mechanism

Subtle event-sourcing and immutability bugs need frontier reasoning. **In Claude Code, delegate the diff review to a sub-agent spawned with `model: opus`**, passing it the diff and this skill. In Cursor, Codex, or Kiro (no sub-agents) this is advisory — run the review inline on the current model. The procedure is identical either way.

---

## Inputs / Outputs / Next

- **Input:** a PR or a diff range (`base..head`, or the working tree). The changed set typically includes `.hs`, `.hurl`, `event-model.json`, `.locked-files`, `Config.hs`, `App.hs`, `Service.hs`.
- **Output:** a severity-ranked review — `blocker` / `major` / `minor` / `nit` findings, each as `file:line — rule — fix`, plus a one-line verdict (`REQUEST CHANGES` or `APPROVE`). Optionally posted as inline PR comments.
- **Next:** `neohaskell-code-review-ci` wires this to run on every PR/MR. For an actual fix, the author returns to the relevant `implement-*` / `expand-entity` / `neo-immutability-and-versioning` skill.

This skill is **PR-time**, independent of the build cycle — but it is the **enforcer of the outside-in TDD phase boundaries** (see the phase-boundary check in Lens 2).

---

## The review procedure (copy-paste)

### Step 1 — scope the diff (read-only)

```bash
# Names of changed files, and the full patch, scoped to the PR range.
git diff --name-only "$BASE".."$HEAD"
git diff "$BASE".."$HEAD"
# Reviewing local work instead of a range? Use the working tree:
#   git diff --name-only    &&    git diff
```

Review **only** what the diff touches. Do not review the whole repo; do not comment on lines outside the patch.

### Step 2 — classify each changed file

| Changed path | Class | Primary lenses |
|---|---|---|
| `src/**/Commands/<Name>.hs` | command | 1 language · 2 ES (decide/auth/create-vs-update) · 3 immutability (LOCKED) · 5 wiring |
| `src/**/Events/<Name>.hs` | event payload | 1 language · 4 records/JSON (empty Generic) · 3 immutability (LOCKED) |
| `src/**/Event.hs` (singular) | event ADT | 1 language · 2 ES (past-tense names, exhaustive `getEventEntityId`) |
| `src/**/Entity.hs` | entity (aggregate) | 1 language · 2 ES (`update` totality) · 4 records/JSON · 3 immutability (**add-only**) |
| `src/**/Queries/<Name>.hs` | query (read model) | 1 language · 2 ES (`canAccess`+`canView`, total `combine`) · 4 records/JSON (`ToSchema`) · 3 immutability (LOCKED) |
| `src/**/Integrations/<Name>.hs` | integration | 1 language · 2 ES (pure `handleEvent`, `Integration.none` stub) |
| `src/**/Service.hs`, `src/App.hs` | wiring | 5 wiring |
| `src/**/Config.hs`, `.env`, `.env.example` | config | 6 secrets |
| `test/**/*.hs`, `tests/**/*.hurl` | test | 6 coverage · phase boundary |
| `event-model.json` | event model | 6 schema + referential + best-practice |
| `.locked-files` | lock manifest | 3 immutability |

### Step 3 — apply the six lenses (below) to each file per its class.

### Step 4 — emit the report (format at the end).

---

## Lens 1 — NeoHaskell language correctness

The reader hallucinates vanilla Haskell. Flag any vanilla leakage introduced by the diff. Grounded contrast — real code writes `import Core`, `Text`, `Array.length`, `|>`, dot access `cmd.label`, `!=`, and ends effectful command logic in a `Decider.*` constructor.

| Introduced in the diff — FLAG | NeoHaskell-correct | Severity |
|---|---|---|
| `import Prelude` / no `import Core` | `import Core` first | major |
| `String` / `[Char]` | `Text` | major |
| `[a]` as a sequence | `Array a` (qualified `Array.*`) | major |
| `Array.filter` / `head` / `xs !! i` | `Array.takeIf` / `dropIf`; `Array.get :: Int -> Array a -> Maybe a` | major |
| `IO a` for effects (esp. in `decide`/`combine`/`handleEvent`) | pure, or `Task err a` at the edge | blocker in a pure block |
| `pure x` / `return x` ending a `decide` | `Decider.acceptExisting [..]` / `acceptNew` / `reject` | major (throws at runtime) |
| `Either a b` / `Left` / `Right` | `Result error value` / `Err` / `Ok` (error is first) | major |
| `f $ x`, `f . g`, `a <> b`, `a /= b` | `x \|> f`, `f .> g`, `a ++ b`, `a != b` | minor |
| `field rec` selector | dot access `rec.field` (`NoFieldSelectors` is on) | major |
| `error "..."` / `undefined` | `Decider.reject "..."` (in `decide`) or `panic "..."` (other pure) | major |
| `"Hello " <> name` / `printf`-style `%s` | `[fmt\|Hello #{name}!\|]` | minor |
| `import Data.Aeson` / `Data.Text` / `Data.Map` directly | `Json` / `Text` / `Map` | major |

**Runtime trap worth calling out explicitly:** a `decide` whose `do` block ends in a bare list or `pure` (instead of `Decider.acceptNew`/`acceptExisting`/`reject`) type-checks in the author's head but **throws at runtime**. Real `decide` bodies (e.g. `Starter.Counter.Commands.CreateCounter`, `Testbed.Cart.Commands.AddItem`) always terminate in a `Decider.*` constructor.

---

## Lens 2 — event-sourcing / CQRS

**`decide` shape.** Three arguments `decide :: Cmd -> Maybe Entity -> RequestContext -> Decision Ev`, terminating in `Decider.reject` / `acceptNew` / `acceptExisting`. Ids come from `newId <- Decider.generateUuid` inside the `do`, never a top-level pure call. `RequestContext` is imported from `Service.Auth` — flag `import Service.AccessControl (RequestContext)` (it lives in `Service.Auth`; `Service.AccessControl` exports `AccessError`/`UserClaims`/`publicAccess`).

**Creation vs update must be consistent** (grounded in `CreateCounter` = create, `AddItem` = update):

| | `getEntityId` | accept constructor | `entity` arg |
|---|---|---|---|
| creation | `Nothing` | `acceptNew` | always `Nothing` |
| update | `Just cmd.entityId` | `acceptExisting` | `Nothing` = reject "not found"; `Just e` = proceed |

Flag a mismatch (e.g. `getEntityId = Nothing` but `acceptExisting`, or `Just` with `acceptNew`) as **major** — the framework will load the wrong stream or conflict.

**`update` fold totality.** The entity's `update :: Ev -> Entity -> Entity` must have a branch for **every** variant of the event ADT. In `Starter.Counter.Entity`, `case event of` covers `CounterCreated`, `CounterIncremented`, `CounterDecremented`. If the diff adds a variant to `Event.hs` but not a case in `update` (or to `getEventEntityId`), that is a **major** non-exhaustive-fold bug — old and new events will fail to replay.

**Event names — past-tense specific business facts.** Creation facts are GOOD: `CounterCreated`, `CartCreated`, `*Registered`, `*Opened`. The smell is **present-tense / RPC-echo** (`ProcessPayment`, `CreateOrderDTO`) and **vague** (`CounterUpdated`, `DataChanged`). **Do NOT flag `*Created` as CRUD** — that is a false positive the spec forbids. Commands are imperative (`AddItem`, `CreateCounter`, `ReserveStock`). Present-tense/vague event names → **major**.

**Queries: `combine` totality + auth.** A query's `instance QueryOf E Q` must define `queryId` and a total `combine` returning `Update q` / `NoOp` / `Delete` (grounded in `CartSummary`, `StockLevel`). And a query **must** declare both `canAccess :: Maybe UserClaims -> Maybe AccessError` and `canView :: Maybe UserClaims -> Q -> Maybe AccessError` — `deriveQuery ''Q [''E]` will not compile without them. A query diff missing either is a **blocker** (won't compile) — cite the missing one and note `publicAccess`/`publicView` (open) vs `authenticatedAccess`/`ownerOnly` (secure) as the choices.

**Commands: secure by default.** Omitting `canAccess` falls back to `authenticatedAccess` (login required), enforced only when the app wires `Application.withAuth`. This is correct — the public Counter/Cart commands do not override it. Do **not** flag a command for lacking `canAccess`. Only flag an *unexplained* `canAccess = publicAccess` on a command that handles sensitive state (**minor**, "confirm this should be public").

**Integrations: pure `handleEvent`, safe stub.** `handleEvent :: E -> Ev -> Integration.Outbound` is **pure** — no `Task`/`IO`/HTTP inside (that belongs in a separate `ToAction`). Cross-aggregate commands go out via `Integration.outbound Command.Emit { command = ... }` (grounded in `ReserveStockOnItemAdded`, which emits `ReserveStock`). The unmatched-event stub is `_ -> Integration.none` — **flag `panic` in a pure `handleEvent` as a blocker**: it crashes the dispatcher whenever that event fires.

**Phase-boundary check (outside-in TDD enforcement).** If the diff spans phases, flag it (**minor**, "split the commit"): RED touches only test files (`test/**`, `tests/**`); DOMAIN touches only type definitions + `panic "TODO"` / `Integration.none` stubs; GREEN touches only implementation bodies. A single commit that adds a test *and* its implementation defeats the red-first discipline.

---

## Lens 3 — immutability / V2 versioning

`neo lock` freezes every file under a directory component named exactly `Commands`, `Events`, or `Queries`. Once such a file is in `.locked-files`, editing it is forbidden.

- **A changed locked `Commands/`, `Events/`, or `Queries/` file → BLOCKER.** The fix is never an edit: revert it byte-for-byte and add a `V`-bumped sibling. `Foo.hs` → `FooV2.hs` whose **type is `FooV2`**; for an event payload the in-file type stays literally `Event`, so version at the file level (`Events/CounterIncrementedV2.hs`) and add a `CounterIncrementedV2 CounterIncrementedV2.Event` variant to the ADT. Reject wrong forms: `foo_v2`, `Foo.V2`, `FooVersion2`, `Foov2` (lowercase `v`), `Foo_V2`.
- **Entity evolution is add-only.** `Entity.hs` is *not* locked, but a **removed, renamed, or retyped field → BLOCKER**: it breaks replay of the event log and old snapshots. Adding a field is fine (see Lens 4 for the replay-safety condition).
- Verify a claimed V-bump is byte-identical to the original and correctly named; a partial rename or a "V2" that also edits the original is a **blocker**.

---

## Lens 4 — records / JSON

Grounded in `Starter.Counter.Events.CounterIncremented` (payload), `Starter.Counter.Entity`, `Testbed.Cart.Queries.CartSummary`.

- **Empty Generic instances only:** `deriving (Generic, ...)` then `instance Json.FromJSON X` / `instance Json.ToJSON X` with **no body**. Flag `deriving (FromJSON)`, `deriveJSON`, TH aeson, or `import Data.Aeson` (**major**).
- **`ToSchema` belongs on queries, not on entities/events/commands.** Real queries derive `instance ToSchema CartSummary`; the `CounterEntity` and event payloads do not. `ToSchema` on a non-query, or a query missing it, is a **minor**.
- **Dot access**, not field selectors (also Lens 1).
- **Replay safety for a new entity field:** a newly added entity field must be `Maybe` **or** carry a JSON default (hand-written `Json.(.:?)` / `.!=`). An added **non-`Maybe`, no-default** field with an empty Generic `FromJSON` **rejects old snapshots** → **blocker** (points the author at `expand-entity`).

---

## Lens 5 — wiring

Grounded in `Testbed.Cart.Service` and the testbed `App.hs`.

- A new command must be registered in its context `Service.hs`: `Service.new |> Service.command @AddItem |> ...`. A new `Commands/*.hs` with no `Service.command @Cmd` line → the endpoint is unreachable (**major**).
- A new query needs `Application.withQuery @Q`; a new outbound handler needs `Application.withOutbound @H` (stateful: `withOutboundLifecycle`); an inbound source needs `Application.withInbound @() (...)`. Missing wiring for a shipped block → **major**.
- Config-dependent wiring must use factory lambdas (`\cfg -> ...`), not read `Config` at wiring time.
- State the endpoint *should* be reachable; do not assert it *is* without a run.

---

## Lens 6 — tests, secrets, event-model, privacy

- **Coverage:** a new command should carry a Decider spec; a new query a Projection spec; a new integration an Outbound spec; a feature an Acceptance + Property spec and a `.hurl` e2e. A behavior change with zero test changes → **major** ("no test covers this change").
- **Secrets:** a secret field must be `Config.secret` + `Redacted`; a plaintext token/password, or a secret logged/interpolated in the clear, is a **blocker**. A real value committed to `.env` (vs `.env.example`) is a **blocker**.
- **`event-model.json`:** validate shape (draft 2020-12 schema), referential integrity (every `edge.sourceId`/`targetId` in `nodes`; `entityId`/`sliceId` present-even-if-null on event/command nodes; no extra keys under `additionalProperties:false`), and best practices (past-tense specific events, imperative commands, every event produced by a command, every query fed by an event, no infrastructure modeled as nodes). Duplicate ids → **major**.
- **Privacy:** flag any client identifier, branded service, or private-domain term that leaked into examples or fixtures (**blocker** for a public repo).

---

## Severity model

| Severity | Meaning |
|---|---|
| **blocker** | Will not compile (per a documented rule), breaks immutability, breaks replay/old snapshots, or leaks a secret. Merge-blocking. |
| **major** | Correctness or ES/CQRS violation (mismatched create/update, non-exhaustive `update`, present-tense event, missing wiring/coverage). |
| **minor** | Idiom/style (`$`/`<>`/`/=`, misplaced `ToSchema`, phase-boundary bleed). |
| **nit** | Cosmetic (naming, comments, ordering) — never merge-blocking. |

---

## Output format (copy-paste)

```
## NeoHaskell code review — <base>..<head>

**Verdict:** REQUEST CHANGES — 2 blockers, 1 major, 1 minor
(or: **Verdict:** APPROVE — no blocking findings)

### Blockers
- [BLOCKER] src/Starter/Counter/Commands/IncrementCounter.hs:1
  Rule: immutability — files under `Commands/` are frozen once locked; this one is edited.
  Fix: revert byte-for-byte; add `IncrementCounterV2.hs` (type `IncrementCounterV2`) and register it in `Service.hs`.
- [BLOCKER] src/Testbed/Stock/Queries/StockLevel.hs:20
  Rule: `deriveQuery` requires both `canAccess` and `canView`; `canView` was removed.
  Fix: restore `canView :: Maybe UserClaims -> StockLevel -> Maybe AccessError` (`publicView` or `ownerOnly`).

### Major
- [MAJOR] src/Starter/Counter/Commands/DecrementCounter.hs:24
  Rule: `decide` must end in a `Decider.*` constructor; this `do` ends in `pure [...]`, which throws at runtime.
  Fix: return `Decider.acceptExisting [...]`.

### Minor
- [MINOR] src/Starter/Counter/Entity.hs:40  Use `++`, not `<>`, to concatenate.

### Nits
- (none)
```

Order findings blocker → major → minor → nit. Every finding is `file:line`, the **rule**, and a **concrete fix**. If the diff is clean, say so and APPROVE — do not invent findings.

---

## Worked example — a known-bad diff

A PR that (1) edits the locked `Commands/IncrementCounter.hs`, (2) adds event `CounterUpdated`, (3) writes `decide ... = pure [...]` with an `IO` step, (4) drops `canView` from a query, and (5) removes the `label` field from `CounterEntity` should produce **five findings**: a blocker for the locked-file edit, a major for the vague present-tense `CounterUpdated` (contrast the good `CounterCreated`), a blocker+major for the `IO`/`pure`-ending `decide`, a blocker for the missing `canView`, and a blocker for the removed entity field (breaks replay). It must **not** flag `CounterCreated` as CRUD, and must **not** claim the project compiles.

---

## DO / DON'T

| DON'T | DO | Why |
|---|---|---|
| Edit or "fix" the code | Report `file:line` + rule + fix; leave editing to the author | This skill is read-only |
| Say "this compiles" / run `neo build` | Cite documented compile rules as predictions only | No compiler is in this loop; fabricated build results mislead |
| Flag `CounterCreated` / `*Registered` / `*Opened` as CRUD | Flag only present-tense (`ProcessX`) and vague (`XUpdated`) names | Creation facts are valid past-tense events |
| Flag a command for lacking `canAccess` | Recognize the secure default (`authenticatedAccess`) | Commands are secure by default; only queries must declare auth |
| Flag `pure`/`return` because "it's fine in Haskell" | Flag `pure`-ending `decide`/`combine`; expect `Decider.*` / `Update`/`NoOp`/`Delete` | Bare `pure` in a decider throws at runtime |
| Wave through an edit to `Commands/`/`Events/`/`Queries/` | Blocker + require a `V`-bumped sibling | Deployed domain files are immutable |
| Miss a removed/renamed/retyped entity field | Blocker — it breaks event replay and old snapshots | Entities evolve add-only |
| Review the whole repo | Review only lines in `git diff base..head` | Diff-scoped keeps signal high |
| Expect `String`/`[a]`/`IO`/`Either`/`$`/`<>`/`/=` to be correct | Treat them as leaked vanilla Haskell | The prelude is `Core`, not `Prelude` |

---

## Verify (read-only)

```bash
git diff --name-only "$BASE".."$HEAD"   # every path you must classify is listed
git diff "$BASE".."$HEAD"               # the exact lines you may comment on
```

A good review: every finding maps to a real line in that patch, every planted issue on a known-bad diff is caught (locked-file edit, present-tense event, `IO` in a decider, missing query auth, removed entity field), no creation event is flagged as CRUD, and no compile result is fabricated.
