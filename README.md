# NeoHaskell Application Skills

A complete collection of **96 skills** for developing consumer applications with NeoHaskell: the 27 established application skills, 65 adapted shared skills, and four new capabilities for application context, API clients, frontend delivery, and collection maintenance.

The collection follows the application's technology and requested outcome. A UI copy change uses context and frontend guidance; a business change reaches commands, events, projections, integrations, and any requested client/UI. Complete examples and resources live inside the skill that owns them. No framework checkout is required.

## Install the complete collection

Use Node **22.20.0 or newer** and the fixed installer **skills@1.7.6**. Run from the consumer application's Git root only when installation there is authorized. Existing managed content or path collisions must first go through [nh-skills](skills/nh-skills/SKILL.md).

1. Open the [v1.0.0 release](https://github.com/neohaskell/skills/releases/tag/v1.0.0) and read its changes and full commit SHA. An absent release means publication is still pending; do not substitute `main`.
2. Resolve the immutable annotated tag to its full commit SHA:

   ```sh
   NH_SKILLS_SHA=$(git ls-remote https://github.com/neohaskell/skills.git 'refs/tags/v1.0.0^{}' | cut -f1)
   ```

3. Check that the value is exactly 40 hexadecimal characters, then install all skills for both hosts:

   ```sh
   case "$NH_SKILLS_SHA" in
     ''|*[!0-9a-f]*) echo 'Release SHA is unavailable or invalid';;
     *)
       if [ "${#NH_SKILLS_SHA}" -eq 40 ]; then
         npx --yes skills@1.7.6 add "neohaskell/skills#$NH_SKILLS_SHA" --skill '*' --agent codex claude-code --yes
       else
         echo 'Expected a full 40-character release SHA'
       fi
       ;;
   esac
   ```

4. Review and commit canonical content under `.agents/skills/`, `skills-lock.json`, and the relative Claude links under `.claude/skills/`. Keep application extensions separate from managed skill folders.

The installer does not resolve inter-skill dependencies. Install the whole collection, not selected entries. Resources are ordinary files inside their owner's folder; sibling skills use relative links. The lockfile alone does not promise reconstruction of both host destinations or recovery of removed/renamed skills.

## Use the collection

Start with [neohaskell-feature-pipeline](skills/neohaskell-feature-pipeline/SKILL.md) for an application change, or invoke a specialist directly when its prerequisites are known.

| Need | Entry |
|---|---|
| Locate components, effective revision, compatible API guidance, and tools | [nh-app-context](skills/nh-app-context/SKILL.md) |
| Align backend JSON/schema and client consumers | [nh-api-client](skills/nh-api-client/SKILL.md) |
| Complete the requested interface journey in the existing stack | [nh-frontend](skills/nh-frontend/SKILL.md) |
| Design business behavior and implement NeoHaskell slices | [neohaskell-feature-pipeline](skills/neohaskell-feature-pipeline/SKILL.md) |
| Install, explicitly upgrade, or recover the collection | [nh-skills](skills/nh-skills/SKILL.md) |

Shared principles and procedures use `nh-` names. The 27 historical identifiers remain unchanged. [nh-roles](skills/nh-roles/SKILL.md) owns role guidance; the host's real tools, user instructions, configured models, and delegation permissions take precedence. Skills load their detailed branches conditionally instead of loading the whole installed collection.

## Versions and maintenance

Collection versions, installer versions, and framework revisions are separate identities. The compatible API guide for the application's effective framework revision remains authoritative.

Releases use immutable semantic-version tags: compatible fixes are patches, compatible capabilities are minor releases, and renames, removals, or breaking changes are major releases. [nh-skills](skills/nh-skills/SKILL.md) compares installed files against the identified old release before replacement, detects committed and uncommitted customizations, preserves unrelated skills/extensions, reconciles owned additions/removals/renames, and keeps an update in its own reviewable commit. Rollback reverts that whole commit, including content, resources, lockfile, and links.

Use `add` with the explicit target release SHA for a release change. `update -p` retains its reference and is not a release-jump mechanism. Clean Git status does not prove that managed files have no committed customizations. No silent updates or extra public maintenance CLI are part of this contract.

## Documentation and scope

All persisted prose and filenames are English; see [AGENTS.md](AGENTS.md). Domain vocabulary lives in [GLOSSARY.md](GLOSSARY.md), and agreed decisions live in [docs/adr](docs/adr). Git records content and history without an additional provenance or catalog manifest.

This batch excludes an evaluation campaign, synthetic-consumer certification, and Jev. Test and review skills remain reusable product content. Their inclusion does not claim those recipes have been executed or authorize installing CI or automation in a consumer.

The design methodology adapts Event Modeling and outside-in TDD material from [jwilger/claude-code-plugins](https://github.com/jwilger/claude-code-plugins), retaining applicable attribution. Shared procedures are adapted from the public [NeoHaskell repository](https://github.com/neohaskell/NeoHaskell). Original applicable notices accompany their resources.
