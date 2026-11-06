---
name: nh-api-client
description: Connect a NeoHaskell application API contract to its existing client and callers when payloads, queries, errors, authentication, transport, or uploads change.
---

# Connect the contract to its callers

Use [nh-app-context](../nh-app-context/SKILL.md) to establish the affected roots, executable configuration, and revision-compatible guidance. Run the consumer's existing generation mechanism. For frontend client work, use [nh-frontend-setup](../nh-frontend-setup/SKILL.md) when the frontend or generation/build tooling is missing, then resume client alignment here. Setup owns configuration and the URL-to-generation-to-compilation contract; an explicitly backend-only request does not require frontend scaffolding.

1. Locate the implemented endpoint/serialization for backend changes and the contract served at the configured URL for SDK generation. Inspect generator configuration/output, handwritten transport wrappers or clients, and real callers. Preserve existing application tools and choices. Diagnose an observed discrepancy at its owning layer; a local schema copy or dependency revision does not replace the configured generator input.
2. Read [wire boundaries](references/wire-boundaries.md) for the changed fields and transport. Preserve missing versus null, enums, identifiers, error shapes, identity, URL composition, and upload semantics that callers rely on. An accepted command may still have a pending observable result.
3. Change the owning contract and run the application's existing generation/build commands from their configured working directories. Executable tooling generates and compiles the SDK; recurring client generation or compatibility inference is not an AI step. Inspect output locally and adapt wrappers/callers in their own component, leaving generated files untracked under the setup contract. Do not hand-edit generated code as the durable fix. Preserve handwritten clients and update their decoding/error mapping where the contract changes.
4. Use the consumer's narrow contract checks for serialization, decoding, and request shape. For an interoperability claim, drive the actual backend using the selected identity/configuration and observe the resulting state with a bounded predicate. Simulated transport proves only the exercised client contract. Describe missing backend access or tools precisely; do not call a mock run real integration.
5. Hand the changed contract and observable states to [nh-frontend](../nh-frontend/SKILL.md) when the requested journey includes an interface. Report touched authorities/callers, generated changes, actual observations, and any unobserved boundary. Backend wiring alone does not complete a requested client flow.
