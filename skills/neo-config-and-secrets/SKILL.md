---
name: neo-config-and-secrets
description: Add backend configuration, wire real options, and preserve secret boundaries across server and browser code.
---

# Configuration and secrets

Resolve the actual config and transport API through [nh-app-context](../nh-app-context/SKILL.md). Add documented settings with appropriate defaults or required values; trace each option to its real consumer.

`Config.secret` redacts the generated config record's display. An extracted field such as `cfg.apiToken` remains ordinary `Text` and must never be logged. Server credentials stay on the server. Browser-bundled values are public regardless of their variable names.

Use synthetic sentinels to check logging examples; preserve the secret in logs, responses, and browser assets. Declaring a port variable is not enough: wire it into transport configuration and observe the requested listener. Store real secrets outside Git and document safe placeholders.

## Read only the relevant reference

| Condition | Resource |
|---|---|
| Declare, wire, or read server configuration | [backend-config.md](references/backend-config.md) |
| Environment files, logging, or browser configuration | [secret-boundaries.md](references/secret-boundaries.md) |
