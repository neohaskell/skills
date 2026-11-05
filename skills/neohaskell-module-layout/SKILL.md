---
name: neohaskell-module-layout
description: Place application modules in the existing NeoHaskell component and resolve module, barrel, marker, and inspection conventions.
---

# Application module layout

1. Use [nh-app-context](../nh-app-context/SKILL.md) to locate source roots, module prefixes, generated modules, test roots, and the effective framework revision.
2. Preserve the component's existing split or combined entity/event layout. Use the example skeleton only for a new component that needs one; a monorepo may have several roots.
3. Inspect what its markers generate before adding instances. Match module declarations, build registration, and actual inspector requirements. A `LOCKABLE` comment provides no enforcement.
4. Compile the affected component and inspect any required discovery output. If compilation succeeds but discovery fails, check the inspector's real naming/layout contract rather than moving files speculatively.

Compatibility and active locks belong to [neo-immutability-and-versioning](../neo-immutability-and-versioning/SKILL.md).

## Read only the relevant reference

| Condition | Resource |
|---|---|
| Choose a layout and adapt complete modules | [layout-examples.md](references/layout-examples.md) |
| Resolve Default and instance placement | [instances.md](references/instances.md) |
