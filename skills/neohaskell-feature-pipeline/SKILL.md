---
name: neohaskell-feature-pipeline
description: Deliver a requested NeoHaskell application change across the components it touches. Use for a complete feature, a deployed bug, a new application, or choosing the appropriate skills; route UI-only, API/client, internal behavior, and business workflows separately.
---

# Deliver the application change

1. Resolve the task's components and effective framework revision with [nh-app-context](../nh-app-context/SKILL.md). Preserve the existing monorepo roots and product instructions. Do not scaffold over an existing application.
2. State the requested observable result. Inspect code and existing domain documentation before using [augment-feature-request](../augment-feature-request/SKILL.md) for unresolved product decisions. Keep a working brief in task state, not installed skill resources.
3. Choose the smallest route that covers the **whole requested outcome** using the table below. Direct invocation of a specialist is valid when its prerequisites are already known.
4. Implement each behavior using [outside-in TDD](../neohaskell-outside-in-tdd/SKILL.md). That skill owns the testing discipline; [nh-orchestrate](../nh-orchestrate/SKILL.md) owns general coordination when multiple work streams require it. Use [nh-roles](../nh-roles/SKILL.md) for available host roles without overriding configured models or delegation permissions.
5. Finish at the requested boundary. State what actually ran and what it proved. A stub, `Integration.none` on the requested trigger, backend wiring, or accepted command does not prove a requested UI or external effect is complete.

| Requested change | Conditional route |
|---|---|
| Text, color, layout, or an empty state | [UI route](references/ui.md): context and frontend; event modeling is unnecessary unless behavior changes. |
| Request payload, query shape, upload, or client interoperability | [API/client route](references/api-client.md): backend contract, schema, client, affected UI. |
| A pure function or internal behavior | [Internal route](references/internal.md): local regression and implementation; browser evidence only when the request reaches the browser. |
| New business behavior or an integration | [Business route](references/business.md): domain discovery, event model, commands/events/projections, wiring, effects, then requested client/UI. |
| Deployed contract or persisted-data change | First apply [neo-immutability-and-versioning](../neo-immutability-and-versioning/SKILL.md), then the appropriate route above. |

Completion means the requested behavior exists across every affected component, with evidence appropriate to that boundary. Record pending effects and external dependencies as incomplete work; continue independent work within the authorized scope.
