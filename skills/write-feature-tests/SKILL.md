---
name: write-feature-tests
description: Write RED-first application acceptance specs and separate replay/property specs using the actual component runner and historical formats.
---

# Acceptance and properties

Choose the branch before reading examples. Acceptance starts from the requested behavior and known contracts; a completed feature is not an input requirement. Add only the types/stubs required to compile, then observe a behavioral failure. Properties start from a compiling fold and stated invariants.

Use [outside-in TDD](../neohaskell-outside-in-tdd/SKILL.md) for the loop and [nh-test](../nh-test/SKILL.md) for runner discovery. Neo CLI Haskell components conventionally use `tests/`; frontend and other components retain their own test roots.

Acceptance checks the command-to-state/query contract in-domain. Property generators must encode valid domain sequences, include boundaries, and avoid overflowing numeric ranges accidentally. Add representative historical JSON fixtures when changing persisted shapes. A property that merely repeats the implementation does not establish an independent invariant.

Qualified Hspec/QuickCheck/Prelude interoperability is valid inside those libraries' APIs. Keep it explicit rather than applying application-style bans to test adapters.

## Read only the relevant reference

| Condition | Resource |
|---|---|
| Write the behavioral acceptance spec before implementation | [acceptance.md](references/acceptance.md) |
| Check replay and domain invariants | [properties.md](references/properties.md) |
