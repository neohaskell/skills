---
name: neo-run-and-inspect
description: Run and inspect an application locally with explicit component root, process ownership, actual base URL, meaningful readiness, bounded observation, and scoped cleanup.
---

# Run and observe the application

Use [nh-app-context](../nh-app-context/SKILL.md) to identify the component, declared runtime command, URL, identity, dependencies, and readiness behavior. Use [nh-control-cli](../nh-control-cli/SKILL.md) for terminals and [nh-control-ui](../nh-control-ui/SKILL.md) for an available browser/UI tool.

1. Record existing processes/listeners before starting anything. Prefer the consumer's managed terminal/process tool; retain its handle and exact working directory. Reuse an existing authorized process when it is the intended app.
2. Start only the required components with their declared configuration. Declaring `PORT` does not connect it to the server: trace the setting into transport configuration and observe the actual listener.
3. Wait with a deadline for readiness that matters to the request, such as a loaded projection or a usable route. A fixed sleep, a live PID, or a health endpoint alone may not establish readiness.
4. Exercise the requested endpoint or UI with policy-correct identity and run-specific state. Capture the actual result; for asynchronous work poll the specific entity until success, failure, or timeout.
5. Keep logs and receipts in task evidence outside reusable resources. Stop only processes started and still owned by this operation, checking their handle/identity before cleanup. Leave pre-existing processes alone.

Discover routes from the actual schema/registration instead of assuming port 8080 or a default `/ready`. `neo inspect` is useful only for the revision's supported inspection surface. `neo inspect sync` rewrites a model; preserve hand-authored work and use it only for an explicitly intended regeneration.
