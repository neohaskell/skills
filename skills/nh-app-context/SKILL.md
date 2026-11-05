---
name: nh-app-context
description: Discover the application components, effective NeoHaskell revision, compatible API guidance, and available development tools before changing a consumer application.
---

# Locate the application contract

Use this skill at the start of an application change or when a specialist lacks a root, revision, contract, or runner. Inspect only the components involved in the task. The output is a short working map, not a permanent inventory.

1. Read the consumer's instructions and existing domain documentation. Identify the requested outcome and affected frontend, backend, worker, shared-contract, or package roots from manifests, imports, and actual entrypoints. In a monorepo, distinguish repository root from each command's working directory.
2. Resolve the **effective** framework revision from the actual dependency resolution: lockfiles, Cabal project/source-repository-package configuration, Nix inputs, installed CLI output, and generated project metadata as applicable. A declaration of `main`, a README version, or the collection release is not an effective revision. Record conflicting evidence and resolve which build inputs win.
3. Locate the API guide compatible with that revision through existing documentation links, installed/generated guidance, or the framework's official published material. Check the guide identity against the dependency. Use source for the same revision when an exact API needs confirmation. Do not substitute an unrelated guide or invent missing signatures. Continue independent UI or design work while naming any missing guide as a concrete dependency.
4. Discover executable capabilities from the consumer's package scripts, CLI version/help, CI commands, and declared toolchain. Identify build/test/run commands, working directories, configuration names, frontend stack, schema/client generator, authentication boundary, and available browser/CLI tools relevant to the change. Read configuration without exposing secrets. Use [toolchain selection](../nh-nix-haskell-tools/SKILL.md) and [application CLI](../neo-cli/SKILL.md) only for their respective branches.
5. Return the scoped map: component paths; effective framework revision and guide location; authoritative contract and real caller; relevant commands with cwd; configuration/identity prerequisites; unresolved dependencies. Point to existing sources instead of copying their contents. Save a task brief only in task state when needed; update durable domain knowledge in the consumer's existing glossary/ADRs.

For API or payload changes continue with [nh-api-client](../nh-api-client/SKILL.md). For interface changes use [nh-frontend](../nh-frontend/SKILL.md). For business behavior use [the application pipeline](../neohaskell-feature-pipeline/SKILL.md). A copy or color change does not require event modeling. Collection, installer, and framework versions remain separate identities.
