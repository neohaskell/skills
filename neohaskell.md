# Working in a NeoHaskell application

Start an application change with [neohaskell-feature-pipeline](skills/neohaskell-feature-pipeline/SKILL.md). Full-stack delivery is the default: backend, API/client, frontend, and verification of the requested result. It automatically invokes [nh-frontend-setup](skills/nh-frontend-setup/SKILL.md) for a missing frontend or incomplete generation/build tooling, then continues the feature. Setup bootstraps React, TypeScript, and Orval only when no frontend exists; configured applications keep their choices. Explicitly narrower UI, API/client, or internal requests retain their scope.

Use [nh-app-context](skills/nh-app-context/SKILL.md) to locate actual component roots, the effective framework revision, a compatible API guide, and the consumer's toolchain. The guide matched to that revision determines available signatures and markers. This collection's release and the installer version do not identify the framework revision.

Executable application configuration supplies the API URL, generation mechanism, and build/dev commands. [nh-frontend-setup](skills/nh-frontend-setup/SKILL.md) owns their configuration contract; [nh-api-client](skills/nh-api-client/SKILL.md) runs that mechanism and aligns wrappers and callers; [nh-frontend](skills/nh-frontend/SKILL.md) completes and observes the real interface journey. Backend revision discovery remains development guidance, not a synchronization gate for the configured service.

NeoHaskell application modules commonly use `Core`, data-last pipelines, `Text`, `Array`, `Result error value`, and `Task error value`. Consult the relevant language skill for the construct being changed, preserving justified foreign-library or test interoperability. Discover module layout, effective extensions, runner, and generated instances from the actual component rather than imposing a historical skeleton.

Preserve deployed and persisted contracts under [compatibility guidance](skills/neo-immutability-and-versioning/SKILL.md). Separate product compatibility policy from technical CLI locks. Do not discard user changes. Historical decoding and replay fixtures establish the compatibility they actually exercise.

Follow [outside-in TDD](skills/neohaskell-outside-in-tdd/SKILL.md) for its selected development route, choosing browser, API, or internal behavior as the appropriate outer boundary. A behavior can need multiple assertions. A failing test does not require an already completed feature, and commit contents alone do not establish test-writing order.

A pure event handler can describe actions whose executor performs effects. Select the supported integration mechanism by capability and resource ownership. A stub or `Integration.none` does not deliver a requested effect. Observe acceptance, pending work, and completion separately. Use the consumer's real authentication policy, and treat browser-provided identifiers as untrusted.

Keep server secrets out of logs and frontend bundles. Record redaction does not protect an extracted field. Discover actual run configuration and readiness instead of assuming a port or anonymous access.

Install all 97 skills for the user's chosen agent through the `npx skills` command in [README.md](README.md). Collection installation distributes skills; application configuration runs through the pipeline when needed. Use [nh-skills](skills/nh-skills/SKILL.md) for explicit upgrades, optional release pinning, and whole-commit recovery, preserving application-owned customizations. All persisted prose and filenames are English under [AGENTS.md](AGENTS.md).
