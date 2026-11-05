---
name: nh-frontend
description: Deliver a requested application interface journey using the existing frontend stack, design system, navigation, forms, and data/authentication boundaries.
---

# Complete the interface journey

Start with [nh-app-context](../nh-app-context/SKILL.md) unless the relevant roots, stack, and commands are already known. Follow the consumer's components, design system, accessibility conventions, and routing. Do not introduce React, Clerk, Orval, multitenancy, or application-specific folder names by default.

1. Identify the user's starting point, action, and observable finish. Inspect the existing screen and analogous components. For text, color, layout, or empty-state work, stay within that scope; domain/event design is needed only when behavior changes.
2. Map the required states using [journey states](references/journey-states.md). Include loading, empty, success, errors, validation, and permission states that the actual flow can reach. Keep navigation, focus, and recovery coherent across those states.
3. Reuse the existing API/client path and identity boundary. For a contract change, use [nh-api-client](../nh-api-client/SKILL.md). Do not manufacture successful client state after backend failure, treat IDs from the browser as authority, or expose server secrets in frontend configuration.
4. Implement the complete requested path using existing UI and form primitives. Keep presentation changes proportional to the request. For an external effect or eventual command result, show the real pending/completed distinction and a usable recovery path.
5. Observe the changed journey through the available browser/UI tools and relevant existing checks when execution is in scope. Use [nh-control-ui](../nh-control-ui/SKILL.md) for interface operation. State what was actually observed, which viewport/identity mattered, and which tools or environments were unavailable. A screenshot establishes appearance at that state, not the whole interaction or backend delivery.

Report what users can now do, the changed paths, and any concrete limitation. When the request includes UI, an implemented backend or generated client alone is incomplete.
