---
name: write-hurl-e2e
description: Write HTTP boundary tests with configurable base URL, policy-correct identity, isolated state, and bounded polling for the created entity or requested effect.
---

# HTTP behavior

Resolve URL, routes, auth, and actual response schema through [nh-app-context](../nh-app-context/SKILL.md). Hurl is an HTTP boundary tool; [nh-frontend](../nh-frontend/SKILL.md) handles browser behavior.

1. Select the authorized or denied identity required by the application policy. Public endpoints can be intentionally anonymous. Supply test credentials privately, never in committed fixtures or logs.
2. Parameterize `base_url`, identity, and test state. Create or isolate records for this run and capture their IDs.
3. Assert the requested response and poll the **captured entity's** terminal state with fixed retries and intervals. Avoid asserting global collection counts as evidence of this run.
4. Separate command acceptance, projection readiness, and completed effects. Timeout reports the last observed state and an unmet result, not success. Do not retry a mutating request unless its idempotency contract makes that safe.

Use the discovered runner or `hurl --test --variable base_url=URL FILE` after replacing URL and FILE with actual values. The consumer's runner may supply variables through another supported interface. Use [outside-in TDD](../neohaskell-outside-in-tdd/SKILL.md) for RED/GREEN evidence.

## Read only the relevant reference

| Condition | Resource |
|---|---|
| Create records or check rejection responses | [requests.md](references/requests.md) |
| Capture IDs and wait for query/effect completion | [eventual-results.md](references/eventual-results.md) |
| Resolve capture, assertion, or option syntax | [hurl-syntax.md](references/hurl-syntax.md) |
