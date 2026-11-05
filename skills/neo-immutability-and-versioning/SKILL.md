---
name: neo-immutability-and-versioning
description: Change published application contracts or persisted data while honoring the product policy and actual technical locks.
---

# Compatibility and versioning

1. Identify persisted events/snapshots, published API consumers, deployment policy, and the actual lock mechanism. A folder name or deployment alone does not prove a lock exists.
2. For an active immutable-code contract, introduce the supported V2 sibling and route new callers explicitly. Preserve old event decoding and replay. For a mutable component, follow its documented migration policy instead of imposing a universal V2 rule.
3. Review compatibility separately for data, API consumers, and generated files. [expand-entity](../expand-entity/SKILL.md) owns historical snapshot/event fixtures; [nh-api-client](../nh-api-client/SKILL.md) owns schema/client alignment.
4. Preserve local edits and user work. Do not discard changes because a lock reports them. Confirm before destructive cleanup or migrations; retain a recovery path.
5. Demonstrate the chosen compatibility path with representative historical inputs and affected consumers. A clean build alone cannot prove replay or published-contract compatibility.

Exceptions require an explicit application policy, migration plan, and evidence at the affected boundary. Keep collection upgrades in [nh-skills](../nh-skills/SKILL.md), separate from framework revision upgrades.

## Read only the relevant reference

| Condition | Resource |
|---|---|
| The consumer actually uses legacy file locks | [locked-artifacts.md](references/locked-artifacts.md) |
| Add a V2 command or event | [versioned-examples.md](references/versioned-examples.md) |
