# Write the complete v1 JSON structure

Use only the branch needed by the task. Resolve the application revision and capabilities through [nh-app-context](../../nh-app-context/SKILL.md) before adapting API examples. The existing consumer layout and compatible API guide determine the actual imports, markers, and commands.

## Copy-paste template

The design lands as JSON. Validate it with `neo validate` (schema + referential, read-only), or offline
against the vendored schema
[`references/event-model.schema.json`](event-model.schema.json) (draft 2020-12).

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

**To add a feature**, add to the relevant arrays while preserving unrelated work. Correct outdated design nodes and their references when behavior changes; persisted event history is a separate compatibility concern. This example preserves what is already
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

**Append with a script, not by hand.** Hand-inserting objects and commas into the arrays is
error-prone (a misplaced comma, a clobbered sibling, an accidental reorder). Load the file, push onto
each array, and write it back instead:

```python
import json
m = json.load(open("event-model.json"))
m["nodes"] += [ { "id": "n-cmd-add", "type": "command", "name": "AddItem",
                  "entityId": "e-cart", "sliceId": "s-add-item" } ]
m["edges"] += [ { "id": "ed-produces", "type": "commandProducesEvent",
                  "sourceId": "n-cmd-add", "targetId": "n-evt-added" } ]
# ...same for submodels / chapters / entities / slices, and layout.nodePositions...
json.dump(m, open("event-model.json", "w"), indent=2)
```

This preserves every existing entry (the point of *append*); it only reformats whitespace — the same
benign diff described next.

**`layout.nodePositions` will drift, and that's fine.** Opening the model in the in-browser IDE
re-lays-out the node positions and pretty-prints the whole document, producing a large but benign
diff. Don't mistake it for corruption and don't hand-fight it — positions are cosmetic and never
affect `neo validate` or codegen.

### Node-shape reminders (the schema traps)

- On `event` and `command` nodes, `entityId` and `sliceId` are **required even when `null`** — write
  `"entityId": null`, never omit the key.
- A `query` node has **no `entityId` key at all** — adding one fails `additionalProperties:false`.
- `integration.kind` must be exactly `"inbound"` or `"outbound"`.
- The whole document forbids extra keys everywhere (`additionalProperties:false` on the root and every
  definition) — no `description`, `color`, `notes`, or node positions inside a node.
- **`fields` is the one allowed optional key on a node** — an array of `{ "name": ..., "type": ... }`
  entries (both required) on `command`/`event`/`query`/`integration` nodes that documents the payload;
  `type` is a free-form string that becomes a downstream type hint (e.g. `{ "name": "itemId", "type":
  "Uuid" }`). The template omits it, but populating it is valuable and stays schema-valid.

