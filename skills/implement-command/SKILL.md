---
name: implement-command
description: Implement a NeoHaskell application command for generated-ID creation, deterministic creation, or modification, with resource authorization and explicit rejection behavior.
---

# Command decisions

Resolve the command API and entity layout through [nh-app-context](../nh-app-context/SKILL.md), then select creation, modification, or deterministic-key creation. Use the matching complete example below; keep the command's observable contract explicit.

A deterministic create may return `Just derivedId` from `getEntityId` and use `acceptNew` when the loaded entity is absent. The same business key must select the same stream; a duplicate follows the documented rejection/idempotency rule. Reactivation of an existing stream is an update, not a new creation.

Enforce the application's authentication and resource authorization at their authoritative server boundaries. Browser-provided IDs prove neither permission nor existence. Cover valid input, rejected input, unauthorized access when applicable, stream identity, and the demanded result. Use [outside-in TDD](../neohaskell-outside-in-tdd/SKILL.md) for the development loop and [wire-feature](../wire-feature/SKILL.md) for backend registration.

## Read only the relevant reference

| Condition | Resource |
|---|---|
| Select stream identity, acceptance, and access policy | [identity-and-auth.md](references/identity-and-auth.md) |
| Create with a generated ID | [create.md](references/create.md) |
| Modify an existing entity | [update.md](references/update.md) |
