---
name: nh-frontend
description: Deliver a requested application interface journey using the existing frontend stack, design system, navigation, forms, and data/authentication boundaries.
---

# Complete the interface journey

Start with [nh-app-context](../nh-app-context/SKILL.md) unless the relevant roots, stack, and commands are already known. If the frontend or generation/build tooling is missing, invoke [nh-frontend-setup](../nh-frontend-setup/SKILL.md) and return here to complete the interface. Setup owns initial stack defaults and configuration; this skill follows the resulting application components, design system, accessibility conventions, routing, and identity boundary. Preserve established application choices.

1. Identify the user's starting point, action, and observable finish. Inspect the existing screen and analogous components. For text, color, layout, or empty-state work, stay within that scope; domain/event design is needed only when behavior changes.
2. Map the required states using [journey states](references/journey-states.md). Include loading, empty, success, errors, validation, and permission states that the actual flow can reach. Keep navigation, focus, and recovery coherent across those states.
3. Reuse the existing API/client path and identity boundary. For a contract change, use [nh-api-client](../nh-api-client/SKILL.md). Do not manufacture successful client state after backend failure, treat IDs from the browser as authority, or expose server secrets in frontend configuration.
4. Implement the complete requested path using existing UI and form primitives. Keep presentation changes proportional to the request. For an external effect or eventual command result, show the real pending/completed distinction and a usable recovery path.
5. Run relevant application checks with [nh-test](../nh-test/SKILL.md) and observe the changed journey through browser/UI tools, using [nh-control-ui](../nh-control-ui/SKILL.md) for interface operation. For features touching UI, follow the real UI-to-API path through the requested result, including completion of any promised effect. State what was actually observed and which viewport/identity mattered. If credentials, backend access, or UI tools prevent observation, name the exact boundary and leave runtime verification incomplete. A generated client, passing compiler, mock, screenshot, wiring, accepted command, or pending effect alone does not establish completed delivery.

Report what users can now do, the changed paths, and any concrete limitation. When the request includes UI, an implemented backend or generated client alone is incomplete.
