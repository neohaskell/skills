---
name: neohaskell-records-and-json
description: Choose serialization for ordinary records, invariant-bearing values, public wire contracts, or persisted history, including marker-generated instances and ambiguous record updates.
---

# Records and serialization

Resolve the marker and JSON APIs through [nh-app-context](../nh-app-context/SKILL.md), then choose the record's role:

| Role | Strategy |
|---|---|
| Ordinary data record | Use the supported generic instances or marker; inspect what is already generated. |
| Value with invariants | Decode through the smart constructor; a generic decoder must not bypass validation. |
| Public API payload | Preserve the documented wire representation and align schema/client through [nh-api-client](../nh-api-client/SKILL.md). |
| Persisted event or snapshot | Keep representative historical decoding/replay through [expand-entity](../expand-entity/SKILL.md). |

With supported markers, declare custom instances before the marker so it can preserve them. [Event/entity marker guidance](../implement-event-and-update-entity/references/markers.md) describes the distinction. Avoid adding duplicate JSON instances based on an older template.

Read the matching complete record example below, or the update-syntax reference when field ambiguity arises. Check real JSON behavior for invariant and compatibility changes; compilation alone is insufficient.

## Read only the relevant reference

| Condition | Resource |
|---|---|
| Adapt an ordinary entity or query record | [ordinary-records.md](references/ordinary-records.md) |
| Resolve ambiguous fields in a record update | [record-updates.md](references/record-updates.md) |
| Review historical or custom JSON needs | [custom-json.md](references/custom-json.md) |
