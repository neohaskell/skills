---
name: neohaskell-domain-modeling
description: Model application values, identity, states, and trust boundaries with domain types compatible with the effective NeoHaskell revision.
---

# Application domain types

Read the consumer's glossary, decisions, and effective API through [nh-app-context](../nh-app-context/SKILL.md). This skill owns application modeling choices; [outside-in TDD](../neohaskell-outside-in-tdd/SKILL.md) owns the phase protocol. Use the shared [type discipline](../nh-principle-type-system-discipline/SKILL.md) and [boundary discipline](../nh-principle-boundary-discipline/SKILL.md) where applicable.

1. State the actual invariant before choosing a wrapper. Positive quantities, non-negative counts, and signed balances are different domains; zero is valid for many counters.
2. Parse untrusted input into domain values at the authoritative boundary. A valid UUID from a browser establishes shape only. Authentication, resource authorization, existence, and cross-stream consistency each need their own policy and owner.
3. Choose IDs and stream identity intentionally. Deterministic creation and duplicate handling follow [implement-command](../implement-command/SKILL.md); use supported helpers from the actual revision.
4. Keep domain state precise while choosing the public representation through [nh-api-client](../nh-api-client/SKILL.md). Converting an ADT to text does not guarantee wire compatibility.
5. Introduce the types and necessary stubs, then resume the behavioral loop. Validate domain bounds and decoding failures, not merely compilation.

A redacted wrapper protects its supported display path; unwrapping a secret still requires careful handling. JSON and persisted-data evolution belong to [records and JSON](../neohaskell-records-and-json/SKILL.md) and [expand-entity](../expand-entity/SKILL.md).

## Read only the relevant reference

| Condition | Resource |
|---|---|
| Choose a standard value type or build a smart constructor | [values.md](references/values.md) |
| Model identity, references, or composed projections | [event-sourced-patterns.md](references/event-sourced-patterns.md) |
