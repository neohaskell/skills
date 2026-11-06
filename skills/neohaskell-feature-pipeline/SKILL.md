---
name: neohaskell-feature-pipeline
description: Deliver NeoHaskell application features full stack by default, including automatic missing-frontend setup. Use for a complete feature, a deployed bug, a new application, or skill routing; preserve explicitly narrower UI, API/client, and internal requests.
---

# Deliver the application change

1. Resolve the task's components, executable configuration, and compatible framework guidance with [nh-app-context](../nh-app-context/SKILL.md). Preserve the existing monorepo roots and product instructions.
2. State the requested observable result. Inspect code and existing domain documentation before using [augment-feature-request](../augment-feature-request/SKILL.md) for unresolved product decisions. Keep a working brief in task state, not installed skill resources.
3. Default to full-stack delivery: backend behavior, API/client, frontend, and verification through the requested result. Preserve explicitly narrower requests using the table below. For routes that need a frontend, invoke [nh-frontend-setup](../nh-frontend-setup/SKILL.md) automatically when the frontend is absent or its generation/build tooling is incomplete, then resume this route. Reuse configured applications; users need not invoke setup separately. Direct specialist invocation remains valid when its prerequisites are known.
4. Implement each behavior using [outside-in TDD](../neohaskell-outside-in-tdd/SKILL.md). That skill owns the testing discipline; [nh-orchestrate](../nh-orchestrate/SKILL.md) owns general coordination when multiple work streams require it. Use [nh-roles](../nh-roles/SKILL.md) for available host roles without overriding configured models or delegation permissions.
5. Run relevant application checks through [nh-test](../nh-test/SKILL.md) and observe the requested result. For features touching UI, [nh-frontend](../nh-frontend/SKILL.md) owns observation of the real UI-to-API journey. State what actually ran and what it proved. A stub, `Integration.none` on the requested trigger, backend wiring, or accepted command does not prove a requested UI or external effect is complete.

| Requested change | Conditional route |
|---|---|
| Text, color, layout, or an empty state | [UI route](references/ui.md): context and frontend; event modeling is unnecessary unless behavior changes. |
| Explicit API/client scope: request payload, query shape, upload, or interoperability | [API/client route](references/api-client.md): backend contract, configured service, client, and any affected UI within the requested scope. |
| A pure function or internal behavior | [Internal route](references/internal.md): local regression and implementation; browser evidence only when the request reaches the browser. |
| Complete feature, new application, business behavior, or integration (default) | [Business route](references/business.md): domain discovery, event model, commands/events/projections, wiring, effects, client, frontend, and runtime verification; reconcile missing setup automatically. |
| Deployed contract or persisted-data change | First apply [neo-immutability-and-versioning](../neo-immutability-and-versioning/SKILL.md), then the appropriate route above. |

Completion means the requested behavior exists across every affected component, with evidence appropriate to that boundary. Record pending effects and external dependencies as incomplete work; continue independent work within the authorized scope.
