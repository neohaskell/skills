---
name: event-modeling
description: >-
  Designs an Event Modeling blueprint for a NeoHaskell feature and appends it ADDITIVELY to
  the project's event-model.json — a submodel, chapters, slices, and
  command/event/query/integration nodes plus edges — creating the file if absent and staying
  compliant with the vendored JSON Schema 2020-12. Runs the seven-step workflow (goal,
  brainstorm events, order chronologically, identify commands, design read models, find
  automations, map integrations) and the four patterns (State Change, State View,
  Automation, Translation). Use to CREATE or EXTEND the model: 'model this feature', 'add a
  slice', 'design the events and commands', 'do the event modeling', or 'update event-
  model.json' — even without naming the file. Runs after augment-feature-request. Do NOT use
  to CHECK an existing model (schema/referential/naming audit) — that is verify-event-model
  — and do NOT use to run the discovery interview or write a Feature Brief — that is
  augment-feature-request.
metadata:
  model: opus
---

# event-modeling

**This is NeoHaskell, not vanilla Haskell — `.hs` is a shared extension.** You are writing JSON here,
but every node name you choose becomes a real NeoHaskell identifier/module downstream
(`Events/<Name>.hs`, `Commands/<Name>.hs`, `Queries/<Name>.hs`), so name blocks like NeoHaskell types,
never vanilla-Haskell ones.

Turn a **Feature Brief** into an Event Modeling blueprint and **append** it — additively — to the
project's `event-model.json`. This is the *design* artifact the whole build pipeline consumes; get the
names and edges right here and the implement-* skills just transcribe them into code.

## Inputs / Outputs / Next

- **Inputs:** a Feature Brief (from `augment-feature-request`) plus the existing `event-model.json` at
  the workspace root (or none yet).
- **Outputs:** an updated `event-model.json` — a new `Submodel` (the feature) + `Chapter`(s) +
  `Slice`(s) + `nodes` + `edges` + `layout` entries, with **all pre-existing content byte-preserved**.
- **Next skill:** `verify-event-model` (schema + referential + best-practice gate). Do **not** run
  `neo inspect sync` after — it regenerates `event-model.json` *from source* and would clobber your
  hand-authored design.

## Where this sits in the cycle

Design comes first: `augment-feature-request` → **`event-modeling`** → `verify-event-model` → then the
per-slice outside-in TDD loop (`neohaskell-outside-in-tdd`). This skill runs **before RED** — each
`Slice` you emit becomes one outside-in vertical slice that is later driven hurl → feature → unit →
domain-modeling → implement-* → wire. Nothing here is code; the RED/DOMAIN/GREEN phases come after.

## Model tier

This is reasoning-heavy design work (tier: **opus**). In Claude Code, delegate the actual modelling to
a sub-agent spawned with `model: opus` so the frontier model does the naming/edge reasoning; pass it
the Feature Brief, this skill, and `references/event-modeling-methodology.md`. In hosts without
sub-agents (Cursor/Codex), this is advisory — run it inline.

## The seven steps

Grounded in [`references/event-modeling-methodology.md`](./references/event-modeling-methodology.md)
(read it for the full method + naming rules). For each feature, in order:

1. **User goal** — the outcome an actor wants → becomes a **Slice**; the feature becomes a **Submodel**.
2. **Brainstorm events** — the past-tense business facts (`ItemAddedToCart`, `StockReserved`).
3. **Order chronologically** — oldest-first (this is the entity `update` replay order).
4. **Identify commands** — the imperative intent that causes each event (`AddItem`). → State Change.
5. **Design read models** — the views users/systems need, fed by events (`CartContents`). → State View.
6. **Find automations** — an event that *conditionally* triggers a follow-up command. → Automation.
7. **Map external integrations** — outbound (react to an event) or inbound (timer/webhook drives a
   command). → Translation for inbound.

## The four patterns → schema

Every slice is built from these four shapes (full mapping + NeoHaskell targets in the methodology ref):

| Pattern | `event-model.json` nodes + edges |
| --- | --- |
| **State Change** — Command → Event | `command` + `event`, joined by `commandProducesEvent` (command→event) |
| **State View** — Event(s) → Read Model | `query`, each source event joined by `eventFeedsQuery` (event→query) |
| **Automation** — Event → [condition] → Command | `integration` (`kind:"outbound"`); `eventTriggersIntegration` (event→integration) + `integrationTriggersCommand` (integration→command); the new command then has its own State-Change edges |
| **Translation** — External/timer/webhook → Command | `integration` (`kind:"inbound"`); `integrationTriggersCommand` (integration→command); the command then produces its event |

The condition in an Automation is **not a node** — it lives in the integration's `handleEvent` or the
emitted command's `decide`. Commands never read from a query: there is no `ReadModel → Command` edge in
the schema, so it is structurally impossible — do not try.

## Copy-paste template

The design lands as JSON. Validate it with `neo validate` (schema + referential, read-only), or offline
against the vendored schema
[`references/event-model.schema.json`](./references/event-model.schema.json) (draft 2020-12).

**If `event-model.json` does not exist yet**, create this minimal-but-valid document first (all
root-required keys present), then append into its arrays:

```json
{
  "id": "m1",
  "name": "MyApp",
  "submodels": [],
  "chapters": [],
  "entities": [],
  "slices": [],
  "nodes": [],
  "edges": [],
  "layout": { "nodePositions": {}, "viewport": { "x": 0, "y": 0, "zoom": 1 } }
}
```

**To append a feature**, *push onto* each existing array — never rewrite or reorder what is already
there. This worked slice (public `Cart`/`Stock` testbed contexts) shows State Change + State View +
Automation together:

```json
{
  "submodels": [ { "id": "sm-shopping", "name": "Shopping", "order": 0 } ],
  "chapters":  [ { "id": "c-cart", "name": "Cart management", "order": 0, "submodelId": "sm-shopping" } ],
  "entities":  [
    { "id": "e-cart",  "name": "Cart",  "order": 0 },
    { "id": "e-stock", "name": "Stock", "order": 1 }
  ],
  "slices":    [ { "id": "s-add-item", "name": "AddItemToCart", "chapterId": "c-cart", "order": 0 } ],
  "nodes": [
    { "id": "n-cmd-add",    "type": "command",     "name": "AddItem",                 "entityId": "e-cart",  "sliceId": "s-add-item" },
    { "id": "n-evt-added",  "type": "event",       "name": "ItemAddedToCart",         "entityId": "e-cart",  "sliceId": "s-add-item" },
    { "id": "n-qry-cart",   "type": "query",       "name": "CartContents",                                   "sliceId": "s-add-item" },
    { "id": "n-int-reserve","type": "integration", "name": "ReserveStockOnItemAdded", "kind": "outbound",    "sliceId": "s-add-item" },
    { "id": "n-cmd-reserve","type": "command",     "name": "ReserveStock",            "entityId": "e-stock", "sliceId": "s-add-item" },
    { "id": "n-evt-reserved","type": "event",      "name": "StockReserved",           "entityId": "e-stock", "sliceId": "s-add-item" }
  ],
  "edges": [
    { "id": "ed-produces", "type": "commandProducesEvent",      "sourceId": "n-cmd-add",     "targetId": "n-evt-added" },
    { "id": "ed-feeds",    "type": "eventFeedsQuery",           "sourceId": "n-evt-added",   "targetId": "n-qry-cart" },
    { "id": "ed-triggers", "type": "eventTriggersIntegration",  "sourceId": "n-evt-added",   "targetId": "n-int-reserve" },
    { "id": "ed-int-cmd",  "type": "integrationTriggersCommand","sourceId": "n-int-reserve", "targetId": "n-cmd-reserve" },
    { "id": "ed-reserved", "type": "commandProducesEvent",      "sourceId": "n-cmd-reserve", "targetId": "n-evt-reserved" }
  ],
  "layout": {
    "nodePositions": {
      "n-cmd-add":     { "x": 0,   "y": 0 },
      "n-evt-added":   { "x": 200, "y": 0 },
      "n-qry-cart":    { "x": 400, "y": 0 },
      "n-int-reserve": { "x": 200, "y": 160 },
      "n-cmd-reserve": { "x": 400, "y": 160 },
      "n-evt-reserved":{ "x": 600, "y": 160 }
    }
  }
}
```

For an **inbound Translation** (e.g. a daily timer) add an `integration` with `"kind": "inbound"` and
join it to its command with `integrationTriggersCommand`. See §6c of the methodology reference for a
full inbound snippet (illustrative `Library`/`Loan` domain).

### Node-shape reminders (the schema traps)

- On `event` and `command` nodes, `entityId` and `sliceId` are **required even when `null`** — write
  `"entityId": null`, never omit the key.
- A `query` node has **no `entityId` key at all** — adding one fails `additionalProperties:false`.
- `integration.kind` must be exactly `"inbound"` or `"outbound"`.
- The whole document forbids extra keys everywhere (`additionalProperties:false` on the root and every
  definition) — no `description`, `color`, `notes`, or node positions inside a node.

## DO / DON'T

The reflexes to fight here are treating this like free-form JSON and slipping into CRUD/RPC naming.

| DO | DON'T |
| --- | --- |
| **Append** — push onto the existing `submodels`/`chapters`/`slices`/`nodes`/`edges` arrays | Rewrite, reorder, or renumber existing nodes/edges (breaks other features + git history) |
| Model one **vertical slice per user-meaningful step** | Cram unrelated behaviour into one slice, or split one step across slices |
| Write `"entityId": null` / `"sliceId": null` explicitly on event/command nodes | Omit `entityId`/`sliceId` because the value is null (schema requires the key) |
| Keep queries with **no `entityId` key**; keep only the schema's keys | Add `entityId` to a query, or any convenience key (`description`, `color`) — `additionalProperties:false` rejects it |
| Name events past-tense specific facts (`ItemRemovedFromCart`); creation facts (`CartCreated`) are fine | Present-tense/RPC echoes (`ProcessPayment`, `CreateOrderDTO`) or vague `CartUpdated`/`DataChanged` |
| Name commands imperative (`AddItem`); queries as noun views (`CartContents`) | Reuse a command name for its event, or lowercase/duplicate node ids |
| Model an Automation only when the follow-up is **conditional** (event→integration→command) | Model unconditional co-production as an automation — that is one State-Change slice |
| Use an **inbound** integration for a business external trigger (webhook/timer) | Model persistence, HTTP transport, DTOs, queues, or DB polls as nodes (that is plumbing) |
| Set `integration.kind` to `"inbound"` or `"outbound"` | Route a `query` into a `command` — there is no such edge; commands read the event stream |
| Keep node names identical to the identifiers the implement-* skills will emit | Rename a node after code exists for it |

## Verify

There is no `neo` build step for the model itself — it is data. Check it two ways:

1. **`neo validate`.** Run `neo validate` (or `neo validate path/to/event-model.json`, `--json` for a
   machine result) — it lints the file against the embedded schema **and** referential-integrity rules,
   read-only, and exits non-zero on any problem. Offline fallback, schema only:

   ```bash
   check-jsonschema --schemafile skills/event-modeling/references/event-model.schema.json event-model.json
   ```
2. **Hand off to `verify-event-model`** for referential integrity (every `edge.sourceId`/`targetId`
   resolves to a node; every string `entityId`/`chapterId`/`submodelId` resolves) plus the
   best-practice checks (past-tense specific events, imperative commands, no infrastructure nodes, true
   vs fake automation). Keep ids unique yourself — v1 does not flag duplicate ids.

Once it validates and passes verification, each `Slice` is ready to enter the outside-in TDD cycle.
