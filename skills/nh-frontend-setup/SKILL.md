---
name: nh-frontend-setup
description: Establish a missing application frontend or reconcile missing API generation and build tooling. Use from the feature pipeline or a frontend/client specialist when setup is incomplete.
---

# Establish the frontend and API tooling

Own initial setup and missing-tool reconciliation. [The feature pipeline](../neohaskell-feature-pipeline/SKILL.md) invokes this skill automatically and resumes the feature afterward; the user need not request setup separately. Recurring client alignment belongs to [nh-api-client](../nh-api-client/SKILL.md), and interface delivery to [nh-frontend](../nh-frontend/SKILL.md).

## 1. Locate the existing application

Use the working map from [nh-app-context](../nh-app-context/SKILL.md), refreshing only missing facts. Establish frontend/backend/package roots, each command's working directory, package manager, scripts, generator configuration and output, handwritten clients, transport, and authentication boundaries before writing configuration. Distinguish the schema retrieval URL and credentials from the runtime client's base URL and identity.

Orval configuration and project scripts hold discoverable setup facts. Keep credentials in the application's existing secret mechanism, outside frontend bundles and logs. An API profile document, `api.md`, or agent-instruction pointer is not required. If guidance that cannot be discovered later becomes necessary, keep it near application skills under `.agents`, outside managed collection directories.

## 2. Reconcile only missing setup

| Discovered state | Action |
|---|---|
| No frontend | Establish a minimal React and TypeScript frontend with Orval, using the application's package manager, workspace layout, and compatible build tooling. Connect its entrypoint and scripts so the requested UI can be implemented. |
| Existing frontend with incomplete generation/build tooling | Complete the missing configuration in that frontend. Preserve its framework, generator, handwritten transport, and application customizations; do not scaffold it again. |
| Application already satisfies the setup contract below | Reuse its tooling and return to the caller. Initial scaffolding is complete; recurring generation runs through its commands. |

Inspect existing files before scaffolding; reconcile owned configuration and stale references on reruns without replacing handwritten content. Keep generated output in dedicated paths apart from handwritten wrappers. An established generator or toolchain remains in place: resolve an actual conflict with the required build behavior instead of silently replacing it. Ask only for a genuinely missing choice or conflict. Component libraries, styling systems, and state management are outside this setup decision.

## 3. Configure direct service input

Use the configured service URL as the OpenAPI input. If none is selected, discover the local NeoHaskell service address and configure that; `http://localhost:8080/openapi.json` is only an example. Honor any user-selected URL, including test or production services, without choosing or classifying environments. Assume that URL identifies the intended running backend; dependency discovery for development does not impose backend revision or freshness validation here.

For Orval, set `input.target` to the URL directly in its configuration, using existing configuration/secret loading as needed. Preserve required schema-retrieval authentication and reference resolution without exposing those credentials to the runtime SDK. Configure generated output paths and add them to the application's Git ignore rules. Verify output is ignored and untracked; if generated files were previously tracked, establish their ownership and confirm removal from the index while retaining local and handwritten content. Do not maintain or commit an OpenAPI copy or add a separate schema-fetch stage.

## 4. Make generation a prerequisite of compilation

Wire every frontend build entrypoint to run Orval against the configured URL before SDK/frontend compilation. Apply the same order to the development command's initial compilation. For an established alternative generator, preserve it and implement the same sequence through its supported executable tooling, resolving any conflict before claiming setup complete.

Use the actual package-manager commands and working directories. Sequence generation and compilation with failure propagation, such as `generate && compile`, or an equivalent required task dependency. Inspect the resolved command chain: a lifecycle hook name alone does not prove it runs for the installed package manager. Keep generation unconditional for each build; an output cache or alternate build entrypoint must not bypass it. Include the application's TypeScript/SDK checks and frontend compilation, not just a transpiler that skips type errors.

For development, run generation and a foreground, one-shot compilation gate before starting the long-running development server. A server that stays alive while reporting initial compiler errors does not satisfy a failing command exit status. Reuse the application's compiler/build commands rather than introducing a second compiler configuration.

Retrieval, OpenAPI processing, generation, or SDK/frontend compilation failure must produce a visible error and a nonzero exit status from the invoking build/dev command. Compilation must never run after failed generation, even if old SDK files remain. Do not swallow errors or fall back to a previous SDK when the service is unavailable. Scope generator cleanup to generated paths so reconciliation cannot erase handwritten files.

This ordering lives in executable application tooling. The agent configures or repairs it; recurring builds do not ask an agent to generate clients or infer compatibility. Backend watchers, restart triggers, periodic generation, revision/freshness checks, independent schema-validation tests, SDK drift comparisons, and required receipts/hashes are outside this contract.

## 5. Verify setup and resume delivery

Inspect and run the affected application commands from their actual working directories. Confirm generation precedes compilation for build and initial development, output stays outside Git, and failures propagate without compilation or stale-SDK fallback. Use bounded checks appropriate to changed executable tooling, preserving handwritten work and existing processes. If access or tooling prevents a check, name that exact boundary as incomplete rather than adding substitute synchronization machinery.

Return the configured paths, commands/cwd, actual results, and unresolved prerequisites to the caller. Continue through [nh-api-client](../nh-api-client/SKILL.md) and [nh-frontend](../nh-frontend/SKILL.md) to finish the requested feature. Successful setup or compilation alone does not establish a working UI-to-API journey.
