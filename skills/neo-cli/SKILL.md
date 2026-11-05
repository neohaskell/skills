---
name: neo-cli
description: Discover and run supported NeoHaskell application CLI operations for scaffolding, build, test, runtime, locking, and inspection.
---

# Application CLI operations

1. Locate the executable and component root through [nh-app-context](../nh-app-context/SKILL.md). Read `neo --version` and `neo --help`, then the selected subcommand's help. Use only available flags.
2. Inspect the actual dependency pin and declared tool environment. A `neo-version` value of `main` is not universal; preserve the consumer's chosen revision.
3. Prepare the component's existing Nix or other declared build environment. Run the requested operation from its root; record the command, process handle when applicable, and result.
4. Review generated-file effects after build/test/scaffolding. Reconciliation can change Cabal files and dependency pins; those are real diffs, not noise to discard.
5. Interpret the result at its actual scope: build success is compilation, tests establish covered behavior, and runtime work needs observable readiness. Use [neo-run-and-inspect](../neo-run-and-inspect/SKILL.md) for process ownership and observation.

Collection installation and updates belong exclusively to [nh-skills](../nh-skills/SKILL.md). This skill manages application operations.

## Read only the relevant reference

| Condition | Resource |
|---|---|
| Inspect an application CLI operation | [operations.md](references/operations.md) |
