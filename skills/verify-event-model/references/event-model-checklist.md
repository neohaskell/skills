# Event-model verification checklist

The full three-pass checklist for `verify-event-model`. `SKILL.md` is the short driver; this file is
the exhaustive reference. Walk it top-to-bottom against the `event-model.json` at the project root and
emit a GO / NO-GO verdict with `file:node-id`-scoped findings.

> Adapted (MIT) from the Event Modeling methodology (Martin Dilger's *Understanding Eventsourcing* /
> eventmodeling.org), retargeted from markdown docs to `event-model.json`. Schema and referential
> rules mirror the public `neo` repo (`assets/ide/src/model/event-model.schema.json`, `types.ts`,
> `src/ide/validate.rs`) as captured in `BLUEPRINT.md` section 4.

## Table of contents

1. [How to run the three passes](#1-how-to-run-the-three-passes)
2. [PASS 1 — schema shape (offline, mechanical)](#2-pass-1--schema-shape-offline-mechanical)
3. [PASS 2 — referential integrity (mirror validate.rs + additions)](#3-pass-2--referential-integrity-mirror-validaters--additions)
4. [PASS 3 — methodology best practices (judgment)](#4-pass-3--methodology-best-practices-judgment)
5. [Event / command name smell dictionary](#5-event--command-name-smell-dictionary)
6. [Common false alarms — do NOT flag these](#6-common-false-alarms--do-not-flag-these)
7. [Verdict report format](#7-verdict-report-format)

---

## 1. How to run the three passes

Verification is a gate, not a rewrite. You never reorder or edit the model here — you produce a verdict
and a fix list; the fixes go back through `event-modeling`.

- **PASS 1 — schema shape.** Mechanical. Run offline against the vendored `event-model.schema.json`
  (this folder) with a JSON-Schema validator, or walk section 2 by eye. Any failure ⇒ **NO-GO**;
  stop and report — passes 2 and 3 assume a well-formed shape.
- **PASS 2 — referential integrity.** Mechanical. Mirrors what neo's `validate.rs` checks after the
  shape check, **plus** a duplicate-id check and edge-endpoint-type check that v1 neo does not do. Run
  the `jq` recipes in section 3. Any dangling reference ⇒ **NO-GO**.
- **PASS 3 — methodology best practices.** Judgment. neo never machine-checks these. Read every node
  name and every read-model field and apply section 4. Naming smells and traceability gaps are
  usually **major** (fix before coding), not blockers.

Run `neo validate` (or `neo validate path/to/event-model.json`, `--json` for a machine result) to run
PASS 1 (schema) + PASS 2 (referential) read-only — exit **0** valid, **2** invalid, **3** malformed
JSON, **4** missing, **1** IO error. Never run `neo inspect sync` to "check" a hand-authored model —
`sync` regenerates `event-model.json` *from source code* and will **clobber** the feature you just
designed. If `neo` is not on PATH, run PASS 1 offline against the file (below).

---

## 2. PASS 1 — schema shape (offline, mechanical)

The schema is **JSON Schema draft 2020-12**, `$id`
`https://neohaskell.org/schemas/event-model.v1.json`. `additionalProperties: false` holds at the root
and in **every** definition — you may **not** add convenience keys (`description`, `color`, `notes`,
node positions inline, …). Adding any unlisted key is a **schema failure**, not a nit.

### 2.1 Root object

Required keys: `id`, `name`, `chapters`, `entities`, `nodes`, `edges`, `slices`, `layout`.
Optional: `submodels`. Nothing else may appear at the root.

### 2.2 Grouping records

| Record | Required keys | Notes |
|---|---|---|
| `submodel` (a **feature**) | `id`, `name`, `order` | |
| `chapter` | `id`, `name`, `order`, `submodelId?` | `submodelId` is optional; when present, a string or `null` |
| `entity` | `id`, `name`, `order` | |
| `slice` | `id`, `name`, `chapterId`, `order` | `chapterId` is a string or `null` |

### 2.3 Nodes (`oneOf`, discriminated by `type`)

| `type` | Required keys | Forbidden keys |
|---|---|---|
| `event` | `id`, `type`, `name`, `entityId`, `sliceId` (optional `fields`) | — |
| `command` | `id`, `type`, `name`, `entityId`, `sliceId` (optional `fields`) | — |
| `query` | `id`, `type`, `name`, `sliceId` (optional `fields`) | **no `entityId`** |
| `integration` | `id`, `type`, `name`, `kind`, `sliceId` | **no `entityId`**; `kind` ∈ {`inbound`,`outbound`} |
| `uiPlaceholder` | `id`, `type`, `name`, `sliceId` | **no `entityId`** |

**The `null`-but-required trap.** On `event` and `command` nodes, `entityId` and `sliceId` are required
*even when null* — `"entityId": null` must be **present**, not omitted. Conversely, because
`additionalProperties:false` holds, you may **not** add `entityId` to a `query`, `integration`, or
`uiPlaceholder` node (put the relationship in an edge instead).

`Field` shape is exactly `{ "name": string, "type": string }` — no other keys, no nested objects.

### 2.4 Edges (`oneOf`, discriminated by `type`)

Every edge has exactly `id`, `type`, `sourceId`, `targetId` (source/target non-empty strings). `type`
must be one of these **six and only these six**:

| `type` | source → target (checked in PASS 2) |
|---|---|
| `commandProducesEvent` | command → event |
| `eventFeedsQuery` | event → query |
| `eventTriggersIntegration` | event → integration |
| `integrationTriggersCommand` | integration → command |
| `commandFromUI` | uiPlaceholder → command |
| `queryToUI` | query → uiPlaceholder |

There is **no** `query → command` edge type. That is the schema-level guarantee behind the methodology
rule "commands never depend on read models" (PASS 3, section 4.7). Any 7th edge type is a schema
failure.

### 2.5 `layout`

`layout` requires `nodePositions` (an object mapping node-id → `{x, y}`) and `viewport`
(`{x, y, zoom}`). Optional `bySubmodel`. Positions carry only numeric `x`/`y`.

### 2.6 Running PASS 1

Primary: `neo validate` (runs PASS 1 + PASS 2). The commands below are the **offline fallback** when
`neo` is unavailable — from the project root (adjust the schema path to wherever `neo skills setup`
installed this skill):

```sh
# Offline fallback for PASS 1: check-jsonschema (pip install check-jsonschema) — supports draft 2020-12
check-jsonschema \
  --schemafile .claude/skills/verify-event-model/references/event-model.schema.json \
  event-model.json
```

```sh
# Fallback: the jsonschema library (pip install jsonschema)
python3 - <<'PY'
import json
from jsonschema import Draft202012Validator
schema = json.load(open(".claude/skills/verify-event-model/references/event-model.schema.json"))
doc    = json.load(open("event-model.json"))
errs   = sorted(Draft202012Validator(schema).iter_errors(doc), key=lambda e: list(e.path))
for e in errs:
    print("FAIL", list(e.path), "-", e.message)
print("PASS 1 clean" if not errs else f"PASS 1: {len(errs)} schema error(s)")
PY
```

If no validator is installed, walk sections 2.1–2.5 by eye — the schema is small.

---

## 3. PASS 2 — referential integrity (mirror validate.rs + additions)

neo's `validate.rs` checks, after the shape check: every `edge.sourceId`/`targetId` exists in `nodes`;
`node.entityId` (when a string) exists in `entities`; `slice.chapterId` (when a string) exists in
`chapters`; `chapter.submodelId` (when a string) exists in `submodels`. `null` is always allowed.
**v1 neo does NOT flag duplicate ids and does NOT check edge-endpoint types** — so this pass adds both.

Every recipe below prints an **empty array `[]` when clean**. A non-empty result is a **NO-GO** finding.

```sh
# (a) duplicate node ids  (neo v1 does not catch these — we do)
jq -c '[.nodes[].id] | group_by(.) | map(select(length>1)) | map(.[0])' event-model.json

# (b) dangling edge endpoints — sourceId/targetId not present in nodes
jq -c '[.nodes[].id] as $ids
       | [ .edges[]
           | select((.sourceId|IN($ids[])|not) or (.targetId|IN($ids[])|not))
           | .id ]' event-model.json

# (c) node.entityId pointing at a non-existent entity
jq -c '[.entities[].id] as $e
       | [ .nodes[] | select(.entityId!=null and (.entityId|IN($e[])|not))
           | {node:.id, entityId:.entityId} ]' event-model.json

# (d) slice.chapterId and chapter.submodelId dangling
jq -c '[.chapters[].id]  as $c | [ .slices[]   | select(.chapterId!=null  and (.chapterId|IN($c[])|not))  | .id ]' event-model.json
jq -c '[.submodels[].id] as $s | [ .chapters[] | select(.submodelId!=null and (.submodelId|IN($s[])|not)) | .id ]' event-model.json

# (e) edge-endpoint TYPE mismatch — the edge's ends are the wrong node kinds (neo v1 does not catch this)
jq -c '(reduce .nodes[] as $n ({}; .[$n.id]=$n.type)) as $t
       | { commandProducesEvent:["command","event"],
           eventFeedsQuery:["event","query"],
           eventTriggersIntegration:["event","integration"],
           integrationTriggersCommand:["integration","command"],
           commandFromUI:["uiPlaceholder","command"],
           queryToUI:["query","uiPlaceholder"] } as $rule
       | [ .edges[]
           | select( $t[.sourceId] != $rule[.type][0] or $t[.targetId] != $rule[.type][1] )
           | {edge:.id, type:.type, gotSource:$t[.sourceId], gotTarget:$t[.targetId]} ]' event-model.json

# (f) assert no ReadModel->Command edge slipped in as an unknown type
jq -c '[ .edges[]
         | select(.type|IN("commandProducesEvent","eventFeedsQuery","eventTriggersIntegration","integrationTriggersCommand","commandFromUI","queryToUI")|not)
         | {edge:.id, type:.type} ]' event-model.json
```

The `id`-uniqueness check (a) covers `nodes`; also eyeball `entities`, `slices`, `chapters`,
`submodels`, and `edges` for repeated ids — a duplicate id silently makes the last one win.

---

## 4. PASS 3 — methodology best practices (judgment)

neo never checks any of these. Apply them by reading the model.

### 4.1 Events are past-tense, specific business facts

Good: `OrderPlaced`, `ItemAddedToCart`, `ItemRemovedFromCart`, `StockReserved`, `CounterIncremented`.
Each names a fact that already happened, in the ubiquitous business language, specific enough that a
domain expert recognizes it.

**Creation facts are good, not smells.** `CounterCreated`, `CartCreated`, `BookTitleAdded`,
`MemberRegistered`, `LoanOpened` are all correct events — the word "Created" is fine. The rule is
*past-tense specific fact*, not "avoid the word Created". (See section 6.)

### 4.2 Event name smells (reject → send back to `event-modeling`)

- **Present-tense / RPC echo** — an event named like the command or a remote call:
  `IncrementCounter`, `AddItemToCart`, `ReserveStock` used as an *event* name; `CreateCounterDTO`,
  `AddItemRequest`. An event is the *result* (`CounterIncremented`), never the imperative or the DTO.
- **Vague / CRUD-ish** — `CounterUpdated`, `CartUpdated`, `CartChanged`, `StateChanged`, `DataUpdated`,
  `CartDeleted` (as a generic catch-all). These hide *which* business fact occurred. Ask "updated
  *how*? which fact?" and split into specific past-tense events (`ShippingAddressCorrected`,
  `ItemRemovedFromCart`).

### 4.3 Commands are imperative

`AddItem`, `RemoveItem`, `ReserveStock`, `IncrementCounter`, `RegisterMember`. A command is a request
that may be rejected; its name is a verb phrase in the imperative. A *noun* or *past-tense* command
name (`ItemAddition`, `ItemAdded` as a command) is a smell.

### 4.4 Every event is produced by a command

Each `event` node must be the target of at least one `commandProducesEvent` edge (State Change
pattern). An event with no producing command is either orphaned or an infrastructure leak.

```sh
jq -c '[.edges[]|select(.type=="commandProducesEvent")|.targetId] as $p
       | ([.nodes[]|select(.type=="event")|.id] - $p) | unique' event-model.json   # want []
```

### 4.5 Every query is fed by at least one event

Each `query` node must be the target of ≥1 `eventFeedsQuery` edge (State View pattern). A read model
with no feeding event has no source of truth.

```sh
jq -c '[.edges[]|select(.type=="eventFeedsQuery")|.targetId] as $f
       | ([.nodes[]|select(.type=="query")|.id] - $f) | unique' event-model.json   # want []
```

### 4.6 Information completeness — every read-model field traces to an event

For each `query` node's `fields`, confirm every field can be populated from the `fields` of the events
that feed it (follow the `eventFeedsQuery` edges backward). A read-model field with no upstream event
field means the model can never fill it — the event is missing a field, or the field is invented.
Example: `CartContents.quantity` is fillable only if `ItemAddedToCart` (or a sibling event feeding the
query) carries `quantity`. This is a judgment check; the `fields` arrays make it inspectable.

### 4.7 No `ReadModel → Command` flow

The methodology rule "commands never depend on read models — check the event stream instead" is
*structurally enforced*: there is no `query → command` edge type. **Assert it holds** — PASS 2 recipe
(f) already fails any unknown edge type. If a design *narrative* says a command reads a query to
decide, that conditional belongs in the command's `decide` (which sees the event stream) or the
integration's `handleEvent` (which sees entity state), never as an edge.

### 4.8 No infrastructure modeled as nodes

Persistence, transport, HTTP, queues, databases, caches are **not** domain nodes and **not**
Translations. If you see a node named `SaveToDatabase`, `PublishToKafka`, `HttpController`, or an
`integration` whose job is "write to the event store", it is infrastructure leaking into the model —
remove it. Real domain integrations talk to *other bounded contexts or the outside world*, not to the
plumbing.

### 4.9 True vs fake automation

An **Automation** (State Change triggered by a prior event: `event → integration → command`) is only
warranted when the trigger is **conditional**. Example (real): `ItemAddedToCart → ReserveStockWhenLow
(outbound integration) → ReserveStock` — stock is reserved *only when* the level crosses a threshold;
the condition lives in the integration's `handleEvent` or the emitted command's `decide`.

If instead *every* `ItemAddedToCart` **always** and unconditionally produces `StockReserved` with no
decision, that is **not** an automation — it is one **State Change slice** and should be modeled as a
single command producing both events (or two events in the same slice), *without* an integration node.
Flag an unconditional integration node as a fake automation.

### 4.10 Inbound integrations (Translation) are in scope and legitimate

An `integration` with `kind:"inbound"` feeding a command (`integrationTriggersCommand`) is the
**Translation** pattern — an external event (a timer firing, a webhook arriving) translated into an
internal command. This is correct and must **not** be flagged as "infrastructure". Validate only that
it is a genuine external source (timer/webhook/other context), not the app's own plumbing (4.8).

### 4.11 Names unique and PascalCase; no orphans

Node **names** (not just ids) should be unique PascalCase identifiers — they become NeoHaskell type
and module names downstream, so `Add Item`, `add_item`, or a duplicate `AddItem` will collide. And
every node should participate in at least one edge (no orphans), except `uiPlaceholder` nodes, which
may legitimately sit at a slice boundary.

```sh
# orphan nodes (no incoming and no outgoing edge)
jq -c '([.edges[].sourceId] + [.edges[].targetId] | unique) as $touched
       | [ .nodes[] | select((.id|IN($touched[]))|not) | {node:.id, type:.type, name:.name} ]' event-model.json
```

---

## 5. Event / command name smell dictionary

Grounded in the public example domains (Counter — neo test-project; Cart/Stock — testbed; Library —
neutral illustrative: `BookTitle`/`Member`/`Loan`).

| Bad (smell) | Why | Better |
|---|---|---|
| `IncrementCounter` (as an **event**) | present-tense / command echo | `CounterIncremented` |
| `AddItemToCart` (as an **event**) | RPC echo | `ItemAddedToCart` |
| `ReserveStock` (as an **event**) | imperative echo | `StockReserved` |
| `CreateCounterDTO`, `AddItemRequest` | DTO / transport echo, not a fact | `CounterCreated`, `ItemAddedToCart` |
| `CartUpdated`, `CounterUpdated` | vague — which fact? | `ItemAddedToCart` / `ItemRemovedFromCart` |
| `CartChanged`, `StateChanged`, `DataUpdated` | vague catch-all | the specific fact that changed |
| `LoanUpdated` | vague | `LoanExtended` / `LoanReturned` |
| `ItemAdded` (as a **command**) | past-tense command | `AddItem` |
| `SaveToDatabase`, `PublishToKafka` | infrastructure, not domain | remove (not a node) |
| `CounterCreated`, `CartCreated`, `MemberRegistered`, `LoanOpened` | **NOT a smell — creation fact** | keep as-is |

---

## 6. Common false alarms — do NOT flag these

- **Creation facts.** `*Created`, `*Opened`, `*Registered`, `*Added` (as an event of a genuine
  creation) are correct. Do not reject them as "CRUD". The smell is present-tense/RPC-echo and *vague*
  names, not the word "Created".
- **`uiPlaceholder` nodes and `commandFromUI` / `queryToUI` edges.** These are the frontend touchpoints
  and are valid schema members. They are out of scope for the backend skills but must **not** be
  reported as errors. A `uiPlaceholder` with no other edge is not an orphan.
- **Inbound integrations.** `kind:"inbound"` is a first-class Translation source, not infrastructure
  (section 4.10).
- **`entityId: null` / `sliceId: null` on event/command nodes.** Required-when-null is correct; a
  present `null` is valid, an *omitted* key is the failure.
- **A single command producing two events in one slice.** That is a legitimate State Change, not a
  missing automation — only flag *unconditional* `integration` nodes (section 4.9).
- **`neo validate` output.** It is real and is the **primary** PASS 1+2 tool (sections 1 and 2.6). A
  clean run prints `[ok] event-model.json is valid` and exits **0** — that is a pass, not a finding.
  The offline `check-jsonschema` route is only the fallback when `neo` is off PATH.

---

## 7. Verdict report format

Emit a compact, copyable verdict. `PASS`/`FAIL` per pass, an overall `GO`/`NO-GO`, then findings keyed
by pass, severity, and the offending node/edge id with a concrete fix.

```
Event-model verification — <submodel/feature name>

PASS 1 · schema shape ....... PASS | FAIL
PASS 2 · referential ........ PASS | FAIL
PASS 3 · best practices ..... PASS | FAIL

Verdict: GO | NO-GO

Findings:
- [PASS 1][blocker] node n7 (query "CartView") — has key "entityId"; queries forbid it
    → move the relationship into an eventFeedsQuery edge; delete entityId
- [PASS 2][blocker] edge x2 (commandProducesEvent) — targetId "n-nope" not in nodes
    → point it at the real event node id, or drop the edge
- [PASS 3][major] node n3 (event "CartUpdated") — vague name, hides the business fact
    → rename to the specific past-tense fact, e.g. ItemRemovedFromCart
- [PASS 3][major] node n9 (integration "ReserveAlways", outbound) — unconditional automation
    → fold into the ItemAddedToCart State-Change slice; delete the integration node
```

Severity guide: **blocker** = won't pass schema/referential (PASS 1/2 failures); **major** = ES
methodology violation (naming smell, missing command→event / event→query, fake automation, infra node,
untraceable field); **minor** = style; **nit**. Any blocker ⇒ **NO-GO**. A best-practice-only failure
is a **NO-GO for coding** — fix the model first, because every node name becomes a NeoHaskell type.
