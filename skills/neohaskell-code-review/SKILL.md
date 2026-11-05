---
name: neohaskell-code-review
description: Apply application review criteria to changed NeoHaskell code and affected clients/UI, distinguishing demonstrated defects, compatibility risks, and style advice.
---

# Application review criteria

Use these criteria within the requested review. [nh-app-context](../nh-app-context/SKILL.md) supplies component roots and compatible APIs; [nh-interrogate](../nh-interrogate/SKILL.md) supplies general review coordination when requested. This skill is read-only unless the user also requests fixes.

1. Read the diff and related definitions, callers, authorization boundaries, serializers, tests, and client/UI behavior. Cite findings in the changed code where possible; diff-scoped reporting does not justify diff-only reasoning.
2. Prioritize demonstrated contract, security, replay, and data-loss defects. State the trigger, consequence, supporting evidence, and concrete correction. Separate a prediction from an observed failure and style advice from a functional defect.
3. Check deterministic creation against loaded state and stream preconditions. `Just derivedId` with `acceptNew` can be valid. Check browser IDs against server-owned authorization and consistency policy.
4. Review test meaning: payload, destination, history, and requested outcomes. A commit cannot prove test execution order. Integration stubs and backend wiring do not prove completed external effects or UI journeys.
5. Report only what the review establishes, with coverage limits and actual commands run. Use [the CI skill](../neohaskell-code-review-ci/SKILL.md) only when automated review installation is explicitly requested.

Use [versioning](../neo-immutability-and-versioning/SKILL.md) for compatibility policy, [the prelude](../neohaskell-core-prelude/SKILL.md) for canonical dialect differences, and [nh-api-client](../nh-api-client/SKILL.md) / [nh-frontend](../nh-frontend/SKILL.md) when those boundaries change. Qualified interoperability imports may be necessary; evaluate their context.

## Read only the relevant reference

| Condition | Resource |
|---|---|
| Review decisions, auth, projections, wiring, and evidence | [application-contracts.md](references/application-contracts.md) |
| Format severity-ranked review findings | [report.md](references/report.md) |
