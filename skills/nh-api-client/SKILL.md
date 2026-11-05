---
name: nh-api-client
description: Connect a NeoHaskell application API contract to its existing client and callers when payloads, queries, errors, authentication, transport, or uploads change.
---

# Connect the contract to its callers

Use [nh-app-context](../nh-app-context/SKILL.md) to establish the affected roots and revision-compatible guidance. Work through the consumer's existing schema/client mechanism; a new generator or provider is a product decision, not a prerequisite of this skill.

1. Find the authority: implemented endpoint and serialization, public schema/OpenAPI if maintained, generator configuration, generated output, handwritten transport wrapper, and real callers. Identify whether source types or an external schema owns the contract. Name drift instead of choosing whichever representation is easiest to edit.
2. Read [wire boundaries](references/wire-boundaries.md) for the changed fields and transport. Preserve missing versus null, enums, identifiers, error shapes, identity, URL composition, and upload semantics that callers rely on. An accepted command may still have a pending observable result.
3. Change the owning contract and regenerate through the existing command when generated files are involved. Review the output and adapt wrappers/callers in their own component. Do not hand-edit generated code as the durable fix. For a handwritten client, update its decoding and error mapping with the same contract discipline.
4. Use the consumer's narrow contract checks for serialization, decoding, and request shape. For an interoperability claim, drive the actual backend using the selected identity/configuration and observe the resulting state with a bounded predicate. Simulated transport proves only the exercised client contract. Describe missing backend access or tools precisely; do not call a mock run real integration.
5. Hand the changed contract and observable states to [nh-frontend](../nh-frontend/SKILL.md) when the requested journey includes an interface. Report touched authorities/callers, generated changes, actual observations, and any unobserved boundary. Backend wiring alone does not complete a requested client flow.
