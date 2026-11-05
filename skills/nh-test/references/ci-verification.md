> Adapted for consumer applications from the public NeoHaskell project.

# Consumer CI verification

Read the application's actual workflows, branch rules, changed-path selection, credentials policy, and required checks. Confirm which checks ran against the exact candidate head. A skipped required check is incomplete evidence; an unrelated passing job does not cover the changed contract.

Use supported opt-in labels or workflow dispatch only if the consumer defines them. Do not assume `run-full-ci`, generated-project checks, a framework starter/testbed, or a particular forge exists. Compilation, runtime behavior, API/client interoperability, UI interactions, and performance each need evidence at the boundary claimed.

Keep reviewer and publication permissions separate. [neohaskell-code-review-ci](../../neohaskell-code-review-ci/SKILL.md) installs automated review only when explicitly requested.
