---
name: augment-feature-request
description: Clarify unresolved application behavior from existing code and domain knowledge, producing a task-local feature brief with actors, failures, and any requested UI journey.
---

# Discover the requested behavior

1. Read [nh-app-context](../nh-app-context/SKILL.md), relevant code, existing domain documents, and the user's request. Reuse facts already available; missing design documents do not prove an application is greenfield.
2. Resolve inspectable questions yourself. Ask only for product decisions that available evidence cannot settle, with a concise choice when useful.
3. Describe actors, triggers, business facts, rejection rules, and the requested observable result. If UI is requested, include navigation, loading, empty, permission, error, and retry states that matter.
4. Keep the feature brief in task state. Update the application's existing glossary/ADRs or domain documents when durable knowledge changes; do not create a parallel inventory or put execution receipts in skills.
5. Hand off to [event-modeling](../event-modeling/SKILL.md) for business behavior, or directly to the scoped [pipeline route](../neohaskell-feature-pipeline/SKILL.md) when no event design changes.

The brief is ready when the requested result and unresolved decisions are explicit. Discovery should not demand answers the repository already provides.

## Read only the relevant reference

| Condition | Resource |
|---|---|
| A product decision requires further discovery | [facilitation.md](references/facilitation.md) |
