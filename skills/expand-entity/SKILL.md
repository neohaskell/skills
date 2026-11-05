---
name: expand-entity
description: Evolve an application entity while preserving required snapshot and event compatibility, with historical fixtures and an explicit migration strategy.
---

# Evolve an entity

Discover the persisted formats and active locks with [nh-app-context](../nh-app-context/SKILL.md) and [versioning](../neo-immutability-and-versioning/SKILL.md). State which history must still decode, which snapshots can be rebuilt, and whether a migration is authorized.

1. Add the state and its initial value, then update all affected transitions. Preserve unrelated fields and existing behavior.
2. Choose missing-field semantics deliberately: optional value, a justified historical default, or an explicit migration. Missing and null are not automatically equivalent.
3. Use the actual serializer/marker API. Put custom decoders before markers that would otherwise derive them.
4. Decode representative historical snapshot and event fixtures, then fold old and new events. Assert retained facts and new-field behavior. A mental walkthrough or successful build is insufficient compatibility evidence.

Read only the matching decoder example below. Source examples use a Library domain; adapt their module roots and fixture fields to the actual application.

## Read only the relevant reference

| Condition | Resource |
|---|---|
| Old snapshots should decode the field as absent | [optional-field.md](references/optional-field.md) |
| Old snapshots need a documented default | [defaulted-field.md](references/defaulted-field.md) |
| Plan fixtures, replay, and migration evidence | [history.md](references/history.md) |
