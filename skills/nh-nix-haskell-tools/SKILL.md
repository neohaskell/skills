---
name: nh-nix-haskell-tools
description: Select the consumer component's declared Haskell toolchain, using its Nix development shell when present and preserving explicit compiler/build configuration.
---

> Adapted for consumer applications from the public NeoHaskell project.

# Use the declared toolchain

Resolve the component root and toolchain with [nh-app-context](../nh-app-context/SKILL.md). If it declares a Nix development shell, run Haskell tools through `nix develop --command TOOL ARGS` from that component. If it uses another declared environment, use that environment; do not impose the framework's Nix setup.

1. Inspect Cabal/project files, the dependency pin, flake or other environment declarations, and existing runner commands. Do not assume `cabal.project.dev`, `nix/hix.nix`, or a framework suite name exists.
2. Use the selected environment consistently for compiler, test, formatter, and REPL commands. A failed Nix preparation is an environment failure; do not silently retry with different host tools.
3. For repeated Hspec work, open the actual test component's REPL and use `:main --match "example"`, `:reload`, and the same selection. Restart after module, dependency, extension, generated source, or build configuration changes.
4. Use [nh-test](../nh-test/SKILL.md) for relevant suites. Scope database/container ownership to the consumer's configuration and stop only resources this run started.
5. Report what the selected environment exercised and what remains unavailable. Consumer CI and release policy determine required gates; framework-internal checks are not inherited.

Internal shared helpers under [nh-best-practices/scripts](../nh-best-practices/scripts/) accept `NH_APP_ROOT` for a component root and `NH_TOOLCHAIN=host` only for a consumer that explicitly uses host tools. Default behavior selects the component's flake when present and otherwise uses its declared host environment.
