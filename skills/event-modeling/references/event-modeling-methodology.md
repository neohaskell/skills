# Event Modeling methodology → `event-model.json` → NeoHaskell

> **Attribution / license.** This methodology text is *adapted* from John Wilger's MIT-licensed
> `event-modeling` skill and from Martin Dilger's *Understanding Eventsourcing* / the community
> material at [eventmodeling.org](https://eventmodeling.org). It has been **retargeted**: instead of
> emitting markdown design docs, it drives the NeoHaskell `event-model.json` artifact (JSON Schema
> draft 2020-12, `$id` `https://neohaskell.org/schemas/event-model.v1.json`) that the `neo` toolchain
> reads. The SDLC-plugin machinery of the source (TDD red/green agents, task CLIs, ADR/story
> workflow, PR orchestration, personas) is **not** adopted — only the portable modelling method.
> Reuse under the MIT terms of the upstream skill.

This is the shared reference for `event-modeling` (and its siblings `augment-feature-request` and
`verify-event-model`). It explains the *why* behind the schema so a weak model does not invent keys,
CRUD event names, or infrastructure nodes.

---

## Table of contents

1. [What Event Modeling is (and why blueprint-before-code)](#1-what-event-modeling-is)
2. [The seven steps](#2-the-seven-steps)
3. [The four patterns → schema → NeoHaskell](#3-the-four-patterns)
4. [Naming rules (the part models get wrong)](#4-naming-rules)
5. [`event-model.json` schema quick reference](#5-event-modeljson-schema-quick-reference)
6. [Worked example: appending a feature](#6-worked-example-appending-a-feature)
7. [Node → NeoHaskell code map](#7-node--neohaskell-code-map)
8. [What is NOT modeled](#8-what-is-not-modeled)

---

## 1. What Event Modeling is

Event Modeling is a way to design an information system as a **timeline of facts**. You draw the
system as a flat sequence of coloured blocks — **events** (orange, things that happened), **commands**
(blue, intents that cause events), **read models / queries** (green, views built from events), and
**integrations** (external systems, in/out) — grouped into vertical **slices** (one user-meaningful
step) that read left-to-right in time.

The point is to agree the **behavioural blueprint before writing any code**. In NeoHaskell that
blueprint is not a whiteboard — it is the machine-checkable `event-model.json` file at the workspace
root. Every block you draw becomes a real module downstream (`Events/<Name>.hs`, `Commands/<Name>.hs`,
`Queries/<Name>.hs`, `Integrations/<Handler>.hs`), so **the names you choose here are the identifiers
the code will carry.** Choose them as carefully as you would choose a type name.

Two invariants make the model trustworthy, and both are structural in the schema:

- **Commands never read from read models.** A command decides from the *event stream* only. The schema
  has no `ReadModel → Command` edge type, so this is impossible to draw — do not try to route a query
  into a command.
- **State lives only in events.** Read models are derived; they hold no authority. Every field in a
  read model must trace back to a field on some event ("information completeness").

---

## 2. The seven steps

Run these in order for each feature. Steps 1–3 discover the *facts*; 4–7 wire the *behaviour*.

1. **User goal / brainstorm the story.** State the outcome a user or actor wants ("a shopper adds an
   item to their cart"). This becomes a **Slice** (and the feature as a whole becomes a **Submodel**).
2. **Brainstorm events.** List the business facts that *happened*, past tense, ignoring order for now
   (`ItemAddedToCart`, `StockReserved`, `CartCheckedOut`). Events are the backbone — everything else
   hangs off them.
3. **Order chronologically.** Lay the events on the timeline oldest-first. This ordering is exactly
   the fold order the entity `update` will replay (`Array.foldl update`, element-first, oldest first).
4. **Identify commands.** For each event, name the imperative intent that causes it (`AddItem` →
   `ItemAddedToCart`). One command may produce one or more events; every event must be produced by some
   command **or** by an integration+command (never appear from nowhere). → **State Change** pattern.
5. **Design read models / queries.** For each place a user or system needs to *see* state, define a
   read model fed by one or more events (`CartContents` fed by `ItemAddedToCart`). → **State View**.
6. **Find automations.** Where an event should *conditionally* trigger a follow-up command without a
   human, model an **Automation**: event → integration → command. The condition ("only if stock is
   low") is **not a node** — it lives in the integration handler or the emitted command's `decide`. If
   the follow-up is *unconditional*, it is not an automation — it is just more events in the same slice.
7. **Map external integrations.** Identify where the outside world crosses the boundary — **outbound**
   (you call an external system in reaction to an event) or **inbound** (an external event/timer/webhook
   drives a command). Inbound sources use the **Translation** pattern.

---

## 3. The four patterns

Every slice is built from four repeating shapes. Each maps to a fixed set of `event-model.json` nodes
and edges, and to a fixed NeoHaskell implement-* skill.

| Pattern | Meaning | `event-model.json` nodes + edges | NeoHaskell (skill) |
| --- | --- | --- | --- |
| **State Change** | Command → Event | `command` node + `event` node, joined by `commandProducesEvent` (command→event) | `implement-command` (`decide` emits) + `implement-event-and-update-entity` |
| **State View** | Event(s) → Read Model | `query` node, each source event joined by `eventFeedsQuery` (event→query) | `implement-query` (`deriveQuery` + `QueryOf`/`combine`) |
| **Automation** | Event → [condition] → Command → Event | `integration` node (`kind:"outbound"`); `eventTriggersIntegration` (event→integration) + `integrationTriggersCommand` (integration→command); the new command then has its own State-Change edges | `implement-integration` (conditional pure `handleEvent`) + the emitted command's `decide` |
| **Translation** | External / timer / webhook → Internal Command → Event | `integration` node (`kind:"inbound"`); `integrationTriggersCommand` (integration→command); the command then produces its event | `implement-integration` (inbound `withInbound`/`Integration.Timer`) + `implement-command` + `implement-event-and-update-entity` |

Two consequences fall out and are worth stating to a weak model:

- The methodology rule **"commands never depend on read models — check the event stream"** is
  *enforced by the schema*: there is no `ReadModel → Command` edge, so you cannot draw it.
- The **Translation pattern requires an inbound integration** — that is the only way an external
  trigger legitimately enters the model. Never model a webhook/timer as a `command` node with no cause.

### The two UI edge types (frontend, usually out of scope here)

`uiPlaceholder` nodes plus `commandFromUI` (uiPlaceholder→command) and `queryToUI` (query→uiPlaceholder)
exist for wireframe slices. These backend skills rarely emit them, but they are **valid** — do not
delete a `uiPlaceholder` you find in an existing model.

---

## 4. Naming rules

Getting names right is most of the value. The `verify-event-model` skill rejects violations.

- **Events are past-tense, specific business facts.** `ItemAddedToCart`, `StockReserved`, `OrderPlaced`,
  `LoanReturned`. The name should read like a headline of something that already happened.
- **Creation facts are good, not CRUD smells.** `CounterCreated`, `CartCreated`, `MemberRegistered`,
  `LoanOpened` are all fine — the word "Created" is not the problem. The smell is **vagueness** and
  **RPC echoes**, below.
- **Reject present-tense / imperative / RPC-echo event names.** `ProcessPayment`, `CreateOrderDTO`,
  `AddItem` (as an *event*) describe an action or a transport message, not a fact. An event is never a
  verb in the imperative.
- **Reject vague "updated/changed" events.** `CartUpdated`, `DataChanged`, `RecordModified` hide *what*
  changed. Prefer the specific fact: `ItemRemovedFromCart`, `ShippingAddressChanged`.
- **Commands are imperative.** `AddItem`, `ReserveStock`, `CheckOut`, `ReturnLoan` — the intent a
  caller expresses.
- **Queries are noun phrases** describing the view: `CartContents`, `AvailableStock`, `MemberLoans`.
- **All node names are unique PascalCase.** They become NeoHaskell type/module names, so `.hs` naming
  rules apply — this is NeoHaskell, not vanilla Haskell, and a `CartUpdated` module is as bad as a
  `CartUpdated` event.

---

## 5. `event-model.json` schema quick reference

Authoritative copy is vendored alongside this file at
[`event-model.schema.json`](./event-model.schema.json) (JSON Schema draft 2020-12). Validate against
that copy offline — there is **no** `neo validate` CLI. Key facts (all enforced by the schema):

**Root object** — required keys: `id`, `name`, `chapters`, `entities`, `nodes`, `edges`, `slices`,
`layout`. Optional: `submodels`. `additionalProperties:false` **everywhere** (root and every `$def`) —
you may not add `description`, `color`, `notes`, or any convenience key.

**Grouping chain:** `node.sliceId → Slice.chapterId → Chapter.submodelId → Submodel`. A **feature is a
Submodel**.

- `Submodel` / `Entity`: `{ id, name, order }`.
- `Chapter`: `{ id, name, order, submodelId? }`.
- `Slice`: `{ id, name, chapterId, order }` (`chapterId` may be `null` but the key is required).

**Nodes** (`oneOf`, discriminated by `type`):

| `type` | Required keys | Notes |
| --- | --- | --- |
| `event` | `id, type, name, entityId, sliceId` | `entityId`/`sliceId` **required even when `null`** |
| `command` | `id, type, name, entityId, sliceId` | same null-but-present rule |
| `query` | `id, type, name, sliceId` | **no `entityId` key** — adding one fails `additionalProperties:false` |
| `integration` | `id, type, name, kind, sliceId` | `kind ∈ {"inbound","outbound"}` |
| `uiPlaceholder` | `id, type, name, sliceId` | frontend |

Every node type also allows an optional `fields: [{ name, type }, …]` array (each `Field` requires
both `name` and `type`).

**Edges** (`oneOf`, discriminated by `type`) — each requires `{ id, type, sourceId, targetId }`
(optional `sourceHandle`/`targetHandle`, string-or-null):

| `type` | source → target |
| --- | --- |
| `commandProducesEvent` | command → event |
| `eventFeedsQuery` | event → query |
| `eventTriggersIntegration` | event → integration |
| `integrationTriggersCommand` | integration → command |
| `commandFromUI` | uiPlaceholder → command |
| `queryToUI` | query → uiPlaceholder |

**Layout** — required `{ nodePositions: { <nodeId>: {x,y} }, viewport: {x,y,zoom} }`; optional
`bySubmodel: { <submodelId>: { <nodeId>: {x,y} } }` for per-feature drag. `NodePosition` = `{x,y}`;
`Viewport` = `{x,y,zoom}`.

**Referential integrity** (a second pass in `neo`, after shape validation — mirror it by inspection):

- every `edge.sourceId`/`targetId` exists in `nodes`;
- every string `node.entityId` exists in `entities`;
- every string `slice.chapterId` exists in `chapters`;
- every string `chapter.submodelId` exists in `submodels`;
- `null` is always allowed; **duplicate ids are NOT flagged in v1** — do not rely on that, keep ids
  unique yourself.

---

## 6. Worked example: appending a feature

Grounded in the public `Cart`/`Stock` testbed contexts, plus the neutral illustrative `Library`
(`Loan`) domain for the inbound Translation. Suppose the model already has an entity `e-cart` (`Cart`)
and we append the **"Shopping"** feature.

### 6a. Create-if-absent skeleton

If `event-model.json` does not exist yet, start from this minimal-but-valid document (matches the
schema's required-keys set) and then append into it:

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

### 6b. Append the feature (additive — never rewrite existing arrays, only push to them)

```json
{
  "submodels": [
    { "id": "sm-shopping", "name": "Shopping", "order": 0 }
  ],
  "chapters": [
    { "id": "c-cart", "name": "Cart management", "order": 0, "submodelId": "sm-shopping" }
  ],
  "entities": [
    { "id": "e-cart",  "name": "Cart",  "order": 0 },
    { "id": "e-stock", "name": "Stock", "order": 1 }
  ],
  "slices": [
    { "id": "s-add-item", "name": "AddItemToCart", "chapterId": "c-cart", "order": 0 }
  ],
  "nodes": [
    { "id": "n-cmd-add",   "type": "command", "name": "AddItem",         "entityId": "e-cart",  "sliceId": "s-add-item" },
    { "id": "n-evt-added", "type": "event",   "name": "ItemAddedToCart", "entityId": "e-cart",  "sliceId": "s-add-item" },
    { "id": "n-qry-cart",  "type": "query",   "name": "CartContents",                            "sliceId": "s-add-item" },

    { "id": "n-int-reserve", "type": "integration", "name": "ReserveStockOnItemAdded", "kind": "outbound", "sliceId": "s-add-item" },
    { "id": "n-cmd-reserve", "type": "command", "name": "ReserveStock",  "entityId": "e-stock", "sliceId": "s-add-item" },
    { "id": "n-evt-reserved","type": "event",   "name": "StockReserved", "entityId": "e-stock", "sliceId": "s-add-item" }
  ],
  "edges": [
    { "id": "ed-produces",  "type": "commandProducesEvent",     "sourceId": "n-cmd-add",     "targetId": "n-evt-added" },
    { "id": "ed-feeds",     "type": "eventFeedsQuery",          "sourceId": "n-evt-added",   "targetId": "n-qry-cart" },

    { "id": "ed-triggers",  "type": "eventTriggersIntegration", "sourceId": "n-evt-added",   "targetId": "n-int-reserve" },
    { "id": "ed-int-cmd",   "type": "integrationTriggersCommand","sourceId": "n-int-reserve","targetId": "n-cmd-reserve" },
    { "id": "ed-reserved",  "type": "commandProducesEvent",     "sourceId": "n-cmd-reserve", "targetId": "n-evt-reserved" }
  ],
  "layout": {
    "nodePositions": {
      "n-cmd-add":    { "x": 0,   "y": 0 },
      "n-evt-added":  { "x": 200, "y": 0 },
      "n-qry-cart":   { "x": 400, "y": 0 },
      "n-int-reserve":{ "x": 200, "y": 160 },
      "n-cmd-reserve":{ "x": 400, "y": 160 },
      "n-evt-reserved":{ "x": 600, "y": 160 }
    }
  }
}
```

This slice shows three patterns at once: **State Change** (`AddItem` → `ItemAddedToCart`), **State
View** (`ItemAddedToCart` → `CartContents`), and **Automation** (`ItemAddedToCart` →
`ReserveStockOnItemAdded` → `ReserveStock` → `StockReserved`). The automation is a *true* automation
because reserving stock is conditional (only reserve if the item is stock-tracked and available); that
condition lives in `ReserveStockOnItemAdded.handleEvent` / `ReserveStock.decide`, **not** as a node.

### 6c. A Translation (inbound) snippet — illustrative `Library` domain

An overdue-loan sweep driven by a daily timer (the illustrative `Library` domain — `Loan` entity
`e-loan`). The timer is an **inbound** integration; it enters the model through
`integrationTriggersCommand`:

```json
{
  "nodes": [
    { "id": "n-int-overdue", "type": "integration", "name": "DailyOverdueSweep", "kind": "inbound", "sliceId": "s-overdue" },
    { "id": "n-cmd-mark",    "type": "command", "name": "MarkLoanOverdue", "entityId": "e-loan", "sliceId": "s-overdue" },
    { "id": "n-evt-overdue", "type": "event",   "name": "LoanMarkedOverdue", "entityId": "e-loan", "sliceId": "s-overdue" }
  ],
  "edges": [
    { "id": "ed-in-cmd",   "type": "integrationTriggersCommand", "sourceId": "n-int-overdue", "targetId": "n-cmd-mark" },
    { "id": "ed-marked",   "type": "commandProducesEvent",       "sourceId": "n-cmd-mark",    "targetId": "n-evt-overdue" }
  ]
}
```

---

## 7. Node → NeoHaskell code map

Each node the model emits is the contract for a downstream module. The **name must equal the
identifier** the implement-* skill will emit.

| Node | Becomes | Built by |
| --- | --- | --- |
| `command` | `Commands/<Name>.hs` (record + `getEntityId` + `decide` + `command ''Name`) | `implement-command` |
| `event` | `Events/<Name>.hs` payload (type literally `Event`) + a variant in `Event.hs` ADT + an `update` case | `implement-event-and-update-entity` |
| `query` | `Queries/<Name>.hs` (record + `deriveQuery` + `QueryOf`/`combine` + `canAccess`/`canView`) | `implement-query` |
| `integration` (outbound) | `Integrations/<Name>.hs` (marker + pure `handleEvent`) | `implement-integration` |
| `integration` (inbound) | inbound source wired with `withInbound`/`Integration.Timer` | `implement-integration` |
| entity referenced by `entityId` | evolves `Entity.hs` (add-only) | `expand-entity` |

Each **Slice** is one **outside-in TDD vertical slice**: the design here precedes the RED phase, then
that slice is driven hurl → feature → unit → domain-modeling → implement-* → wire (see
`neohaskell-outside-in-tdd`).

---

## 8. What is NOT modeled

Event Modeling captures **behaviour**, not **plumbing**. Do not create nodes for:

- **Persistence / storage.** Event stores, databases, tables, snapshots — the framework owns these.
  "Save the cart" is not an event; `ItemAddedToCart` is.
- **Transport.** HTTP endpoints, JSON DTOs, request/response shapes, queues, brokers. `POST /commands/add-item`
  is how `AddItem` is invoked, not a node.
- **Infrastructure disguised as a Translation.** An inbound integration is for a *business* external
  trigger (a payment webhook, a scheduled sweep). A database poll or a cache refresh is not a
  Translation.
- **UI internals** beyond the optional `uiPlaceholder` wireframe blocks.

If a proposed node describes a mechanism rather than a business fact/intent/view/boundary-crossing,
drop it. `verify-event-model` flags infrastructure nodes.
