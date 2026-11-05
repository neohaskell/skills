---
name: write-unit-tests
description: Write focused application decider, projection, and integration contract tests that assert behavior, payload, destination, and relevant invariants.
---

# Unit behavior

Resolve the component runner with [nh-test](../nh-test/SKILL.md) and follow [outside-in TDD](../neohaskell-outside-in-tdd/SKILL.md). Use the Haskell component's existing `tests/` convention; do not move frontend tests into it.

Each test establishes one behavior and may need several assertions. For an integration, action count alone cannot detect wrong destinations or payloads. Use distinct entity IDs, vary meaningful input, and assert the command type and serialized payload using the installed revision's `runAction` context, or the typed plan actually consumed by the handler. Keep an unrelated-event case that emits no action.

A pure plan test proves intent. A simulated executor proves its contract. Only exercising the real application/effect boundary proves that external effect. Report those evidence levels separately.

## Read only the relevant reference

| Condition | Resource |
|---|---|
| Test decisions, rejections, and identity | [decider.md](references/decider.md) |
| Test projection updates | [projection.md](references/projection.md) |
| Test integration action intent | [integration.md](references/integration.md) |
