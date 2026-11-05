---
name: wire-feature
description: Register application commands, projections, and integrations using the effective NeoHaskell revision; verify the backend endpoint and hand off to affected clients or UI.
---

# Backend registration

Use [nh-app-context](../nh-app-context/SKILL.md) to identify component roots, registration APIs, transports, auth, and the actual runtime command. Match the current revision; do not impose a legacy `Service.hs` layout on a marker-based application.

1. Register the relevant commands and queries in the existing composition root.
2. Register outbound, inbound, or lifecycle integrations with their required configuration and resource ownership. See [implement-integration](../implement-integration/SKILL.md).
3. Compile and inspect the endpoint at the real base URL with the identity required by its policy. Record the route, payload, response, and any pending asynchronous result.
4. Continue through [nh-api-client](../nh-api-client/SKILL.md) and [nh-frontend](../nh-frontend/SKILL.md) when the request includes those components.

This skill completes backend wiring. A registered endpoint, accepted command, or integration stub does not complete a requested full stack feature.

## Read only the relevant reference

| Condition | Resource |
|---|---|
| Register commands, queries, and integrations | [registration.md](references/registration.md) |
