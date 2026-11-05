---
name: implement-event-and-update-entity
description: Implement application events together with entity replay, preserving historical decoding and matching the supported marker or explicit-instance layout.
---

# Events and entity replay

1. Locate the actual entity/event modules and API revision through [nh-app-context](../nh-app-context/SKILL.md).
2. Select the existing explicit-instance layout or supported marker layout. Read [marker behavior](references/markers.md) when markers are present; avoid generating a second instance.
3. Add the business fact and update its event sum/routing and pure fold together. Follow [expand-entity](../expand-entity/SKILL.md) if entity shape changes and [versioning](../neo-immutability-and-versioning/SKILL.md) for persisted/published compatibility.
4. Decode representative historical payloads and replay them in order. Assert old facts remain and new events produce the requested state. Compilation only proves the code type-checks.

Use [outside-in TDD](../neohaskell-outside-in-tdd/SKILL.md) for the loop. Completion includes event decoding and fold evidence, not only a new constructor.

## Read only the relevant reference

| Condition | Resource |
|---|---|
| Extend an existing split or combined layout | [explicit-layout.md](references/explicit-layout.md) |
