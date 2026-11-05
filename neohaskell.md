# Working in a NeoHaskell application

Start an application change with [neohaskell-feature-pipeline](skills/neohaskell-feature-pipeline/SKILL.md). It selects the relevant route for the requested outcome. A UI copy change needs context and frontend work; a business behavior change may require domain design, commands, events, projections, and integrations. Backend wiring does not finish a requested client/UI or external effect.

Use [nh-app-context](skills/nh-app-context/SKILL.md) to locate actual component roots, the effective framework revision, a compatible API guide, and the consumer's toolchain. The guide matched to that revision determines available signatures and markers. This collection's release and the installer version do not identify the framework revision.

NeoHaskell application modules commonly use `Core`, data-last pipelines, `Text`, `Array`, `Result error value`, and `Task error value`. Consult the relevant language skill for the construct being changed, preserving justified foreign-library or test interoperability. Discover module layout, effective extensions, runner, and generated instances from the actual component rather than imposing a historical skeleton.

Preserve deployed and persisted contracts under [compatibility guidance](skills/neo-immutability-and-versioning/SKILL.md). Separate product compatibility policy from technical CLI locks. Do not discard user changes. Historical decoding and replay fixtures establish the compatibility they actually exercise.

Follow [outside-in TDD](skills/neohaskell-outside-in-tdd/SKILL.md) for its selected development route, choosing browser, API, or internal behavior as the appropriate outer boundary. A behavior can need multiple assertions. A failing test does not require an already completed feature, and commit contents alone do not establish test-writing order.

A pure event handler can describe actions whose executor performs effects. Select the supported integration mechanism by capability and resource ownership. A stub or `Integration.none` does not deliver a requested effect. Observe acceptance, pending work, and completion separately. Use the consumer's real authentication policy, and treat browser-provided identifiers as untrusted.

Keep server secrets out of logs and frontend bundles. Record redaction does not protect an extracted field. Discover actual run configuration and readiness instead of assuming a port or anonymous access.

Install the complete collection for Codex and Claude Code through the pinned `npx skills` contract in [README.md](README.md). Use [nh-skills](skills/nh-skills/SKILL.md) for explicit upgrades and whole-commit recovery. All persisted prose and filenames are English under [AGENTS.md](AGENTS.md).
