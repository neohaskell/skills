---
name: nh-test
description: Discover and run the consumer application's relevant Haskell, HTTP, frontend, and integration tests without assuming framework testbed paths or internal CI gates.
---

> Adapted for consumer applications from the public NeoHaskell project.

# Application test runs

1. Use [nh-app-context](../nh-app-context/SKILL.md) to find the affected component, declared tests, toolchain, base URL, authentication, and required services.
2. Choose its existing runner. Haskell Neo CLI components normally use `tests/`; other components keep their existing roots. Run a focused behavior first and broader affected checks when warranted.
3. Use [nh-nix-haskell-tools](../nh-nix-haskell-tools/SKILL.md) for the declared environment. Keep commands and results in task evidence. A skipped required check remains incomplete coverage.
4. Interpret each result by its actual boundary: compilation, behavioral assertions, simulated transport, real backend interoperability, or observed UI. A zero exit code with an empty selection does not establish a behavior.
5. Clean up only owned temporary resources. Required CI checks come from the consumer's current workflows, as described in [CI verification](references/ci-verification.md).

## Optional Haskell helpers

Use the consumer's runner first. For an ordinary Cabal project with a local `cabal.project`, these bundled helpers provide bounded output and transcripts; they are not a replacement for custom project configuration. The full-suite helper requires distinct suite names across packages because Cabal's result lines identify suites by name. Use a package-qualified consumer runner when names overlap.

| Need | Invocation from the component root |
|---|---|
| All local Cabal test suites | `python3 PATH_TO_SKILL/scripts/run-full-suite --strict` |
| Source doctests | `python3 PATH_TO_SKILL/scripts/run-doctest --strict` |
| An explicitly configured HTTP suite | Set `NH_HTTP_TEST_COMMAND_JSON` to the runner's JSON argument array, then run `python3 PATH_TO_SKILL/scripts/run-testbed --strict`. |
| A focused Hspec example | Follow [nh-tdd](../nh-tdd/SKILL.md) with an explicit consumer suite. |

Resolve `PATH_TO_SKILL` from this installed skill. Use `NH_APP_ROOT` when the invocation directory is not the component root. The HTTP runner must own useful readiness, auth, assertions, and cleanup; the helper only bounds and records execution. Do not claim Hurl coverage without an actually configured runner.
