---
name: neohaskell-outside-in-tdd
description: Drive the application double loop from the appropriate observable boundary through RED, domain types, GREEN, and refactoring, with honest regression evidence.
---

# Outside-in TDD

This skill owns the testing discipline; [the feature pipeline](../neohaskell-feature-pipeline/SKILL.md) chooses and orders the application route. Use [nh-test](../nh-test/SKILL.md) to discover actual runners.

1. Choose the outer boundary that expresses the request: browser interaction, HTTP contract, or internal behavior. Use [frontend](../nh-frontend/SKILL.md), [Hurl](../write-hurl-e2e/SKILL.md), or [feature tests](../write-feature-tests/SKILL.md) accordingly.
2. Write the outer failing behavior and focused inner [unit tests](../write-unit-tests/SKILL.md). Introduce only missing domain types and safe stubs through [domain modeling](../neohaskell-domain-modeling/SKILL.md).
3. Establish behavioral RED after compilation is possible, then implement the smallest change that makes that behavior GREEN. A missing import, compiler error, or disconnected test is preparation evidence rather than proof of a reproduced regression.
4. Refactor while preserving behavior. Add independent properties or historical fixtures when the domain or persisted formats require them. One behavior may need several assertions; split unrelated behaviors, not assertions mechanically.
5. Re-run the relevant inner and outer checks. Record command, inputs, revision, and result in task evidence. Tests and implementation in one commit do not prove that TDD was violated.

The test pyramid still favors fast focused checks. A UI-only change does not require HTTP or event modeling; internal behavior does not universally require a browser. See [the detailed method](references/outside-in-tdd.md) for worked examples and [the worksheet](references/worksheet.md) when coordinating a business slice.

## Read only the relevant reference

| Condition | Resource |
|---|---|
| Track a business slice across the double loop | [worksheet.md](references/worksheet.md) |
