---
name: event-modeling
description: Design or correct the application event model for changed business behavior, including commands, facts, projections, integrations, and applicable UI interactions.
---

# Event model design

Read the task brief and current application model. [nh-app-context](../nh-app-context/SKILL.md) identifies the effective model format and compatible framework guide. This skill owns the [canonical v1 JSON schema](references/event-model.schema.json); consumers of that schema link here.

1. Preserve unrelated design work and existing domain vocabulary. Correct obsolete nodes and edges when behavior changes. Append-only event storage is not a universal ban on editing a design document.
2. Walk the timeline from intent to recorded fact and observable view. Read only the applicable pattern: [state change](references/state-change.md), [state view](references/state-view.md), [automation](references/automation.md), or [translation](references/translation.md).
3. Include UI placeholders and their command/query edges when the requested journey reaches a UI. Keep system infrastructure out of the domain model.
4. Update the document using its actual schema and consistent IDs. The [complete JSON example](references/design-json.md) shows v1 structure; confirm compatibility before adapting it.
5. Hand off to [verify-event-model](../verify-event-model/SKILL.md) for read-only review. Persisted event changes separately follow [versioning](../neo-immutability-and-versioning/SKILL.md).

For a complex timeline, consult [the detailed methodology](references/event-modeling-methodology.md). This skill edits the design; it does not claim that modeled behavior is implemented.

## Read only the relevant reference

| Condition | Resource |
|---|---|
| Write the complete v1 JSON structure | [design-json.md](references/design-json.md) |
