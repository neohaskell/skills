# Changelog

## v1.0.1 — 2026-11-06

Correct consumer/frontend guidance, verification examples, skill references, domain-documentation layout, and contradictory TDD and comment-review instructions. Preserve the 96 public skill names and the immutable v1.0.0 release.

Fix published-layout resource checking, unfiltered codemap inventory, pending Hspec verdicts, ambiguous Cabal suite accounting, and output-pipe cleanup when a process is cancelled during launch. Replace framework-checkout-dependent helper tests with portable checks of the supported consumer behavior.

Validation: 113 local helper tests pass. All 96 skills pass native metadata validation, and all 235 skill documents pass the resource checker. Public skill paths are unchanged. No consumer evaluation campaign or host certification was run.

## v1.0.0 — 2026-11-05

First stable release of the complete 96-skill application collection: 27 historical entries retain their names, 65 shared procedures/principles are adapted with `nh-` names, and four application capabilities are added.

### Application delivery

`nh-app-context` discovers actual component roots, effective framework revision, compatible API guidance, and tools. `nh-api-client` connects wire contracts to existing clients. `nh-frontend` completes the requested interface journey in the consumer's stack. The application pipeline chooses only the relevant route.

Historical guidance now separates secret redaction from extracted values, supports declarative effect descriptions and deterministic creation, respects actual authentication/authorization, and distinguishes command acceptance, stubs, wiring, and completed outcomes. JSON/history, replay, integration, review, and test examples are disclosed through owned references. Automated-review resources use structured output with distinct malformed-output and runner-failure results.

### Distribution and maintenance

Install the entire collection locally for Codex and Claude Code using `skills@1.7.6`, Node >=22.20.0, and the release's full commit SHA. Commit canonical resources, relative Claude links, and the installer lock together. `nh-skills` supplies a read-only comparison against old/new release content, blocks customizations and collisions, preserves unrelated paths, describes explicit removal/rename reconciliation, and recovers through a whole update-commit revert.

The 27 historical names remain stable. New shared names use `nh-`; resources and playbooks move into their owning skills. Consumers upgrading an earlier installation must use `nh-skills` to preserve custom edits and migrate any direct references to moved resources. All persisted prose and filenames are English, including the glossary and ADRs.

### Scope and external requirements

No evaluation campaign, synthetic-consumer scenarios, agent comparisons, or acceptance certification were run for this batch, as requested. Included test/parser/checker recipes are product resources, not executed delivery evidence. Actual use depends on the consumer's compatible API guide, declared tools, credentials, and available host capabilities. Optional helpers declare their additional dependencies beside their instructions.

Tags are immutable. Compatible fixes use patch releases, compatible additions use minor releases, and removals, renames, or breaking changes use major releases. The GitHub release records this tag's full commit SHA and installation command.
