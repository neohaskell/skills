# Review decisions, auth, projections, wiring, and evidence

Use only the branch needed by the task. Resolve the application revision and capabilities through [nh-app-context](../../nh-app-context/SKILL.md) before adapting API examples. The existing consumer layout and compatible API guide determine the actual imports, markers, and commands.

## Lens 2 — event-sourcing / CQRS

**`decide` shape.** Three arguments `decide :: Cmd -> Maybe Entity -> RequestContext -> Decision Ev`, terminating in `Decider.reject` / `acceptNew` / `acceptExisting`. Ids come from `newId <- Decider.generateUuid` inside the `do`, never a top-level pure call. `RequestContext` is imported from `Service.Auth` — flag `import Service.AccessControl (RequestContext)` (it lives in `Service.Auth`; `Service.AccessControl` exports `AccessError`/`UserClaims`/`publicAccess`).

**Creation vs update must be consistent** (grounded in `CreateCounter` = create, `AddItem` = update):

| | `getEntityId` | accept constructor | `entity` arg |
|---|---|---|---|
| creation | `Nothing` | `acceptNew` | always `Nothing` |
| update | `Just cmd.entityId` | `acceptExisting` | `Nothing` = reject "not found"; `Just e` = proceed |

A deterministic create may use `getEntityId = Just derivedId` with `acceptNew`: the first request loads no entity and creates that stream; a duplicate loads an existing entity and must follow the documented rejection/idempotency policy. Inspect identity derivation, loaded state, and stream preconditions before reporting a mismatch. `Nothing` with `acceptExisting` still requires an explanation backed by the executor contract.

**`update` fold totality.** The entity's `update :: Ev -> Entity -> Entity` must have a branch for **every** variant of the event ADT. In `Starter.Counter.Entity`, `case event of` covers `CounterCreated`, `CounterIncremented`, `CounterDecremented`. If the diff adds a variant to `Event.hs` but not a case in `update` (or to `getEventEntityId`), that is a **major** non-exhaustive-fold bug — old and new events will fail to replay.

**Event names — past-tense specific business facts.** Creation facts are GOOD: `CounterCreated`, `CartCreated`, `*Registered`, `*Opened`. The smell is **present-tense / RPC-echo** (`ProcessPayment`, `CreateOrderDTO`) and **vague** (`CounterUpdated`, `DataChanged`). **Do NOT flag `*Created` as CRUD** — that is a false positive the spec forbids. Commands are imperative (`AddItem`, `CreateCounter`, `ReserveStock`). Present-tense/vague event names → **major**.

**Queries: `combine` totality + auth.** A query's `instance QueryOf E Q` must define `queryId` and a total `combine` returning `Update q` / `NoOp` / `Delete` (grounded in `CartSummary`, `StockLevel`). And a query **must** declare both `canAccess :: Maybe UserClaims -> Maybe AccessError` and `canView :: Maybe UserClaims -> Q -> Maybe AccessError` — `deriveQuery ''Q [''E]` will not compile without them. A query diff missing either is a **blocker** (won't compile) — cite the missing one and note `publicAccess`/`publicView` (open) vs `authenticatedAccess`/`ownerOnly` (secure) as the choices.

**Commands: secure by default.** Omitting `canAccess` falls back to `authenticatedAccess` (login required), enforced only when the app wires `Application.withAuth`. This is correct — the public Counter/Cart commands do not override it. Do **not** flag a command for lacking `canAccess`. Only flag an *unexplained* `canAccess = publicAccess` on a command that handles sensitive state (**minor**, "confirm this should be public").

**Integrations: pure `handleEvent`, safe stub.** `handleEvent :: E -> Ev -> Integration.Outbound` is **pure** — no `Task`/`IO`/HTTP inside (that belongs in a separate `ToAction`). Cross-aggregate commands go out via `Integration.outbound Command.Emit { command = ... }` (grounded in `ReserveStockOnItemAdded`, which emits `ReserveStock`). The unmatched-event stub is `_ -> Integration.none` — **flag `panic` in a pure `handleEvent` as a blocker**: it crashes the dispatcher whenever that event fires.

**Regression evidence.** A commit containing tests and implementation does not reveal their execution order. Ask for or inspect recorded RED/GREEN results when that evidence matters; distinguish an observed behavioral failure, a compilation failure, and an unexecuted test. Report defects from the code and contract, not an inferred TDD history.

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

