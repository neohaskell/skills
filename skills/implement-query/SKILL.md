---
name: implement-query
description: Build a single or composed application projection and preserve its authorization, JSON schema, and client contract.
---

# Application projections

Resolve the query API and public response shape with [nh-app-context](../nh-app-context/SKILL.md). Start with a single-entity projection; read composed projection guidance only when several streams contribute.

Implement access and row visibility according to the actual application policy. Preserve total `combine` behavior and idempotence under replay. For counts, identify what is being counted and how removals/status changes affect membership; repeated updates must not inflate the total.

Choose the wire enum/shape deliberately. Mapping an ADT to `Text` does not make new values compatible. Use [nh-api-client](../nh-api-client/SKILL.md) to align JSON, schema/OpenAPI, generated or handwritten clients, and the affected UI.

Observe the requested projection for the specific entity after a bounded wait. Distinguish command acceptance from projection readiness. Use [wire-feature](../wire-feature/SKILL.md) for registration and [outside-in TDD](../neohaskell-outside-in-tdd/SKILL.md) for the loop.

## Read only the relevant reference

| Condition | Resource |
|---|---|
| Implement a simple query and its access policy | [single-entity.md](references/single-entity.md) |
| Choose response shape or enum evolution | [wire-contract.md](references/wire-contract.md) |
| Aggregate multiple streams | [composed.md](references/composed.md) |
