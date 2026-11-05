# Plan fixtures, replay, and migration evidence

Use only the branch needed by the task. Resolve the application revision and capabilities through [nh-app-context](../../nh-app-context/SKILL.md) before adapting API examples. The existing consumer layout and compatible API guide determine the actual imports, markers, and commands.

## Choosing the JSON backward-compat strategy

When you add a field, old snapshots on disk do not have that field. The empty Generic `FromJSON` derived from `deriving (Generic)` will **reject** a JSON object that is missing a required (non-`Maybe`) field. Choose one strategy:

| Strategy | Use when | How |
|---|---|---|
| **A: `Maybe` field** | the field is genuinely optional, or the "not yet set" state makes domain sense | Add `newField :: Maybe TheType`; Generic `FromJSON` tolerates its absence and decodes it as `Nothing` |
| **B: custom `parseJSON` with `.:?` / `.!=`** | the field is conceptually required but must have a sensible default on old snapshots | Write a `parseJSON` using `Json.withObject` + `obj Json..:? "key" Json..!= defaultValue` |

Never add a required non-`Maybe` field and leave the empty Generic `FromJSON` in place — that silently breaks all old snapshots the moment the code is deployed.

---


## The four-step checklist

Every field addition requires all four steps. Skipping any one breaks compilation or replay:

1. **Record** — add `newField :: FieldType` to the `data Entity` declaration.
2. **`initialState`** — add `newField = defaultValue` to the `initialState` expression.
3. **`update` fold** — add (or update) the relevant `case event of` branches to set `newField`. Branches that don't touch the field leave it via `entity { ... }` record-update; do not duplicate all fields.
4. **JSON decode** — either make the field `Maybe` (Generic `FromJSON` tolerates absence) or write a custom `parseJSON` with `.:?` / `.!=`.

The `update` fold must remain **exhaustive** — every constructor in the event ADT must have a branch.

---


## Historical fixtures and replay

Use representative persisted JSON from the consumer, with sensitive values replaced while preserving the historical shape. Include an event sequence from each supported encoding and a snapshot lacking the new field. Decode each fixture, fold events in order, and assert both the old business facts and the new field's default/transition. Test explicit null separately from an absent key where the contract distinguishes them.

Compilation proves type compatibility, not historical decoding. Record which historical shapes were exercised and any migration required. If the application discards snapshots and rebuilds them, establish that policy and test event replay instead of claiming universal snapshot compatibility. Technical file locks and retention policy are distinct; follow `neo-immutability-and-versioning` for exceptions.

---

