---
name: implement-integration
description: Select and implement declarative outbound actions, inbound triggers, custom execution, or resource-owning lifecycle integrations for an application.
---

# Integration capabilities and outcomes

Read the effective API through [nh-app-context](../nh-app-context/SKILL.md), then choose by capability and resource ownership:

| Need | Branch |
|---|---|
| Describe a supported command or external action | [Declarative outbound](references/declarative.md): a pure handler builds actions; the executor performs effects. |
| Receive a timer tick or webhook | [Inbound](references/inbound.md): validate input, identity, and delivery policy. |
| Execute an unsupported action | [Custom execution](references/custom-execution.md): use the available extension API. |
| Own state, a pool, or another long-lived resource | [Lifecycle](references/lifecycle.md): initialize, process, and clean up explicitly. |

A pure `handleEvent` can describe real external effects. Lifecycle is not mandatory for every outbound effect. `Integration.none` is valid for unrelated events or temporary scaffolding; leaving it on the requested trigger leaves the effect unfinished.

Specify destination, payload, failures, retries/idempotency, and the observable completion result. Promise only guarantees supported by the executor and application protocol. Test the action contract separately from its real execution; simulated transport does not establish external delivery. Register through [wire-feature](../wire-feature/SKILL.md), then observe the requested outcome with a bounded wait.

## Read only the relevant reference

| Condition | Resource |
|---|---|
| Build actions in a pure per-trigger handler | [declarative.md](references/declarative.md) |
| Receive a timer or webhook trigger | [inbound.md](references/inbound.md) |
| Own resources or run a lifecycle subprocess | [lifecycle.md](references/lifecycle.md) |
