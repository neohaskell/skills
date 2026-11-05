---
name: neo-protected-erasure
description: Implement application-owned protected-value erasure while retaining explicitly chosen event history and business facts, including retry and restore limits.
---

# Application-owned protected erasure

Resolve the effective protected-value API with [nh-app-context](../nh-app-context/SKILL.md). The application owns retention and resource authorization. This skill does not prescribe a universal retention policy or certify legal compliance.

1. Identify personal inputs, copies, derivatives, metadata, projections, logs, exports, and external effects. Decide which facts remain and why; retain recorded decisions explicitly rather than recomputing them from erased input.
2. Implement the [request/effect/result flow](references/flow.md). A request commits a pending fact; the outbound effect's callback commits completion or failure. A runner log does not prove the result command committed.
3. Expose owner-authorized retry for unresolved requests. Reconstruct state on restart and use the supported idempotent key outcome; never treat a supplied reference as authority to erase.
4. Use the [consumer fixture recipe](references/consumer-fixture.md) to exercise available, erased, denied, missing, failed, retried, and restarted behavior with synthetic values. Read the [state catalog](references/states.md) when interpreting results.
5. Document backup, WAL, replica, export, and restore limitations. A historical backup with the old key can recover data; retain erasure intent through restore procedures.

Use [configuration](../neo-config-and-secrets/SKILL.md), [integration](../implement-integration/SKILL.md), and [query](../implement-query/SKILL.md) guidance only for the respective implementation branches.

## Read only the relevant reference

| Condition | Resource |
|---|---|
| Implement the application-owned erasure protocol | [flow.md](references/flow.md) |
