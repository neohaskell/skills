---
name: verify-event-model
description: >-
  Gates a freshly-appended NeoHaskell event-model.json BEFORE any code, in three passes:
  PASS 1 JSON-Schema shape offline against the vendored v1 schema; PASS 2 referential
  integrity (edge endpoints resolve, entityId/duplicate-id/edge-endpoint-type checks,
  mirroring neo's validate.rs); PASS 3 Event Modeling best practices neo never machine-
  checks. Flags present-tense or RPC-echo event names (IncrementCounter, CreateFooDTO),
  vague names (CartUpdated, DataUpdated), read-model fields tracing to no event, missing
  command-produces-event or event-feeds-query links, fake unconditional automations, infra-
  as-nodes, orphans, and ReadModel-to-Command flows. Use to CHECK, validate, audit, or gate
  a model — 'check the model', 'is my event model right', 'validate event-model.json', after
  event-modeling and before the TDD cycle. Do NOT use to DESIGN or add nodes to the model —
  that is event-modeling. Does NOT flag creation facts like CounterCreated or
  MemberRegistered.
metadata:
  model: opus
---

**This is NeoHaskell, not vanilla Haskell** — `.hs` is a shared extension, but this skill does not
touch `.hs`. It verifies `event-model.json` (JSON Schema draft 2020-12), the design artifact the
`.hs` implementers will realize. Get it right here and every node name becomes a correct NeoHaskell
type; get it wrong and the error propagates into locked, immutable code.

---

## Inputs / Outputs / Next

**Input:** the project-root `event-model.json` after `event-modeling` appended a feature (a new
`submodel` + its chapters/slices/nodes/edges). You verify the whole file, focusing on the new feature.

**Output:** a **GO / NO-GO verdict** plus concrete, id-scoped fixes (see the report template below). No
edits to the model — verification is a gate, not a rewrite.

**Next skills:**
- **GO** → `neohaskell-outside-in-tdd` (start the per-slice cycle) → `write-hurl-e2e` (first RED).
- **NO-GO** → back to `event-modeling` to apply the fixes, then re-verify.

**Where this sits in the cycle.** This is the **design gate that runs before** the outside-in TDD
cycle (RED → DOMAIN → GREEN → REFACTOR) — it is *not* itself a RED/DOMAIN/GREEN step. Its job is to
guarantee the model is schema-valid, referentially sound, and methodologically honest **before** a
single failing test is written, because the model's node names are about to be frozen into
`Commands/`, `Events/`, and `Queries/` files that are immutable once deployed.

**Run heavy reasoning on Opus.** In Claude Code, delegate PASS 3 (the judgment-heavy methodology
review) to a sub-agent spawned with `model: opus` — subtle naming and automation smells reward frontier
reasoning. In hosts without sub-agents (Cursor, Codex), this is advisory: run all three passes inline.

---

## The three passes

Full checklist, every rule, and every `jq` recipe: **`references/event-model-checklist.md`** (read it —
this section is only the map). The vendored schema is **`references/event-model.schema.json`**.

| Pass | What | How | Failure |
|---|---|---|---|
| **1 · schema shape** | required keys, node/edge types, `additionalProperties:false`, `null`-but-required `entityId`/`sliceId` | offline JSON-Schema validation against the vendored schema (or by eye) | **NO-GO**; stop, report |
| **2 · referential** | edge endpoints exist; `entityId`→entities, `chapterId`→chapters, `submodelId`→submodels; **+ duplicate ids + edge-endpoint types** | `jq` recipes (offline) | **NO-GO** |
| **3 · best practices** | past-tense specific events, imperative commands, every event has a command, every query fed by an event, field traceability, true-vs-fake automation, no infra nodes, no ReadModel→Command, unique PascalCase, no orphans | judgment, by inspection | NO-GO **for coding**; fix model first |

PASS 1 and 2 are mechanical and offline. PASS 3 is the reason this skill is Opus.

---

## Copy-paste: run PASS 1 + PASS 2 offline

There is **no `neo validate` subcommand**, and `neo inspect sync` would **clobber** the hand-authored
model (it regenerates `event-model.json` *from source*). So verify the file directly, offline:

```sh
# PASS 1 — schema shape (pip install check-jsonschema; supports draft 2020-12).
# Adjust the schema path to wherever `neo skills setup` installed this skill.
check-jsonschema \
  --schemafile .claude/skills/verify-event-model/references/event-model.schema.json \
  event-model.json

# PASS 2 — referential integrity (offline, jq). Each prints [] when CLEAN.
jq -c '[.nodes[].id] | group_by(.) | map(select(length>1)) | map(.[0])' event-model.json          # duplicate node ids
jq -c '[.nodes[].id] as $ids | [ .edges[]
        | select((.sourceId|IN($ids[])|not) or (.targetId|IN($ids[])|not)) | .id ]' event-model.json  # dangling endpoints
jq -c '[.entities[].id] as $e | [ .nodes[]
        | select(.entityId!=null and (.entityId|IN($e[])|not)) | {node:.id, entityId:.entityId} ]' event-model.json
jq -c '(reduce .nodes[] as $n ({}; .[$n.id]=$n.type)) as $t
       | { commandProducesEvent:["command","event"], eventFeedsQuery:["event","query"],
           eventTriggersIntegration:["event","integration"], integrationTriggersCommand:["integration","command"],
           commandFromUI:["uiPlaceholder","command"], queryToUI:["query","uiPlaceholder"] } as $rule
       | [ .edges[] | select( $t[.sourceId] != $rule[.type][0] or $t[.targetId] != $rule[.type][1] )
           | {edge:.id, type:.type} ]' event-model.json                                            # edge-endpoint type mismatch
```

The full recipe set (slice/chapter/submodel dangling refs, orphan nodes, unknown edge types,
event-without-command, query-without-event) is in the checklist, section 3.

---

## Copy-paste: the verdict report

Grounded in the public `Cart`/`Stock` (testbed) example. Emit exactly this shape:

```
Event-model verification — AddItemToCart

PASS 1 · schema shape ....... PASS
PASS 2 · referential ........ PASS
PASS 3 · best practices ..... FAIL

Verdict: NO-GO

Findings:
- [PASS 3][major] node n-added (event "AddItemToCart") — RPC echo; an event is a past-tense fact
    → rename to ItemAddedToCart (keep the producing AddItem command imperative)
- [PASS 3][major] node n-view (query "CartContents") — field `reservedAt` traces to no event
    → add reservedAt to a feeding event (e.g. StockReserved), or drop the field
- [PASS 3][major] node n-reserve-h (integration "ReserveStockAlways", outbound) — unconditional
    → not an automation; fold ReserveStock into the ItemAddedToCart State-Change slice, delete the node
```

A **creation fact** such as `CartCreated` in that same model is **correct** — never list it as a
finding. Severity: **blocker** (PASS 1/2), **major** (ES methodology), **minor**/**nit** (style). Any
blocker ⇒ NO-GO; a best-practice-only failure is NO-GO **for coding** until the model is fixed.

---

## DO / DON'T

| DO | DON'T |
|---|---|
| Run PASS 1 offline against the **vendored** `references/event-model.schema.json` | Run `neo validate` (no such subcommand) or `neo inspect sync` (it **clobbers** the model from source) |
| Treat `*Created`/`*Opened`/`*Registered`/`*Added` creation events as **good** | Flag creation facts as "CRUD" — the smell is present-tense/RPC-echo and *vague* names, not the word "Created" |
| Reject present-tense/RPC-echo events (`IncrementCounter`, `AddItemToCart`, `CreateFooDTO`) and vague ones (`CartUpdated`, `DataUpdated`) | Reject a specific past-tense fact (`ItemRemovedFromCart`, `StockReserved`) |
| Require every `event` to be a `commandProducesEvent` target, every `query` an `eventFeedsQuery` target | Demand a command for an inbound-triggered event chain differently — inbound Translation still ends in a command that produces the event |
| Accept `kind:"inbound"` integrations (timer/webhook) as legitimate **Translation** | Flag inbound integrations as "infrastructure" |
| Accept `uiPlaceholder` nodes and `commandFromUI`/`queryToUI` edges as valid | Report a `uiPlaceholder` (or its edges) as a schema error or an orphan |
| Assert **no `ReadModel→Command`** flow (there is no `query→command` edge type) | Allow a design where a command "reads a query" — that conditional lives in `decide`/`handleEvent` |
| Flag an **unconditional** `integration` node as a fake automation | Flag a single command that produces two events in one slice — that is a valid State Change |
| Insist `entityId`/`sliceId` are **present even when `null`** on event/command nodes | Accept an *omitted* `entityId` on an event/command node, or an `entityId` key on a `query`/`integration`/`uiPlaceholder` |
| Check every read-model **field** traces back through `eventFeedsQuery` to an event field | Let a query invent a field no event supplies |
| Verify node **names** are unique PascalCase (they become NeoHaskell types) | Ignore a duplicate or non-PascalCase name (`add_item`, `Add Item`) |

---

## Verify

This skill's own "did it work" is the two offline checks above:

```sh
check-jsonschema --schemafile <this-skill>/references/event-model.schema.json event-model.json  # PASS 1
# then the jq recipes for PASS 2; each must print []
```

PASS 1 clean **and** every PASS 2 recipe returns `[]` **and** PASS 3 raises no major finding ⇒ emit
**GO** and hand off to `neohaskell-outside-in-tdd`. Any failure ⇒ **NO-GO** with the fix list back to
`event-modeling`. Do not claim a downstream `neo build`; this skill runs entirely on the JSON, offline.
