# API integration without a maintained OpenAPI copy

**Finding:** remote SDK generation and drift comparison are feasible without committing OpenAPI. They establish different facts from deployment identity and real-response compatibility. Keep those claims separate; the application still needs to choose its authority, generator, and freshness policy.

Research completed 2026-11-06 for [Verify live OpenAPI and remote SDK generation capabilities](https://plane.p.egregore.io/egregore/projects/5535680e-e3f6-4023-b400-2b27544130e2/issues/c622783c-0417-4573-8e75-30ef48bbf438/). **Fact** means inspected primary source or the local observation described below; **inference** means a proposed consequence; **unknown** means evidence was unavailable. No consumer deployment was supplied or probed. No skills were implemented.

## 1. Setup and consumer pattern

**Fact:** at `mattpocock/skills` commit `4ae2317ddb22b046e26455e4f9c9b3aaaf62212d`, setup discovers existing repository conventions, presents configuration, confirms a draft, then writes `docs/agents/*.md` and a short `Agent skills` pointer in the existing agent-instruction file. It updates an existing block while preserving surrounding edits. The tracker document is later consumed by Wayfinder. This is prompt-driven configuration, not a machine-validated API profile. [Setup source](https://github.com/mattpocock/skills/blob/4ae2317ddb22b046e26455e4f9c9b3aaaf62212d/skills/engineering/setup-matt-pocock-skills/SKILL.md), [Wayfinder consumer](https://github.com/mattpocock/skills/blob/4ae2317ddb22b046e26455e4f9c9b3aaaf62212d/skills/engineering/wayfinder/SKILL.md#configuration).

**Inference:** reusable discovery plus one application-owned configuration source is transferable. Its path, format, setup ownership, approval flow, and API fields are product decisions, not requirements inherited from this example.

## 2. NeoHaskell source and revision evidence

**Fact:** inspected framework commit `f09b360025d842e5ad9bc471f46af91e43cbdab7`, also the `v0.17.0` tag and target of the published [`neo-v0.17.0` release](https://github.com/neohaskell/NeoHaskell/releases/tag/neo-v0.17.0). Its WebTransport builds `/openapi.json` and `/openapi.yaml` from registered command/query schemas plus enabled OAuth/file features; `/docs` loads the JSON route. JSON responses specify `Cache-Control: public, max-age=3600`. The inspected route sets neither an ETag nor a build-revision header. [Route implementation](https://github.com/neohaskell/NeoHaskell/blob/f09b360025d842e5ad9bc471f46af91e43cbdab7/core/service/Service/Transport/Web.hs#L1220).

**Fact:** OpenAPI `info.version` comes from application metadata, defaulting to `1.0.0`; it is not an automatic Git SHA. The standard health body is `status: ok`, optionally with integration mode, without build identity. Generated-project tooling can pin framework revisions: `neo new` uses the embedded starter's locked revision by default, and templates record resolved source information. These are build-input evidence, not proof of what a deployed URL runs. [Metadata defaults](https://github.com/neohaskell/NeoHaskell/blob/f09b360025d842e5ad9bc471f46af91e43cbdab7/core/service/Service/Application/Types.hs), [OpenAPI metadata mapping](https://github.com/neohaskell/NeoHaskell/blob/f09b360025d842e5ad9bc471f46af91e43cbdab7/core/schema/Schema/OpenApi.hs#L174), [health response](https://github.com/neohaskell/NeoHaskell/blob/f09b360025d842e5ad9bc471f46af91e43cbdab7/core/service/Service/Transport/Web.hs#L1521), [starter revision](https://github.com/neohaskell/NeoHaskell/blob/f09b360025d842e5ad9bc471f46af91e43cbdab7/neo/src/network.rs#L303), [new-project behavior](https://github.com/neohaskell/NeoHaskell/blob/f09b360025d842e5ad9bc471f46af91e43cbdab7/neo/src/commands/new.rs#L309).

**Fact:** [ADR 0053](https://github.com/neohaskell/NeoHaskell/blob/f09b360025d842e5ad9bc471f46af91e43cbdab7/docs/decisions/0053-openapi-query-pagination-schema.md) records a historical mismatch: OpenAPI declared arrays while runtime returned paginated objects. Current [query registration](https://github.com/neohaskell/NeoHaskell/blob/f09b360025d842e5ad9bc471f46af91e43cbdab7/core/service/Service/Query/Definition.hs#L189) describes the envelope, matching the fields constructed by the [response implementation](https://github.com/neohaskell/NeoHaskell/blob/f09b360025d842e5ad9bc471f46af91e43cbdab7/core/service/Service/Query/Endpoint.hs#L107). This source correspondence is narrower than observing a consumer deployment. Existing [OpenAPI integration assertions](https://github.com/neohaskell/NeoHaskell/blob/f09b360025d842e5ad9bc471f46af91e43cbdab7/testbed/tests/integrations/openapi.hurl) were inspected, not executed.

**Unknown:** consumer URL, effective framework/application build, proxy cache behavior, schema authorization, and deployment identity mechanism. Source inspection does not establish a reachable or current consumer schema. A proxy may add headers absent from framework source.

## 3. Two generator capabilities

Source snapshots: Orval `68087ee84a5614b0472fda97957bb29511b49b2a` (package declares 8.46.0); Hey API `d6ba11fd9ae4f2b707454940121056fdb505235c` (declares 0.99.0). Experiments used the published npm versions below, separately from those source snapshots.

| Capability | Orval 8.46.0 | `@hey-api/openapi-ts` 0.99.0 |
| --- | --- | --- |
| Input | `input.target`: URL, file, or object | `input`: URL, file, or object; `input.path` for configured input |
| Schema-fetch authentication | `input.parserOptions.headers`: domain-specific headers | `input.fetch.headers` for the root request |
| External references | Explicit `parserOptions.externalRefs.allow`; default denies external refs. Relative references retain their source origin. | Bundles external file/URL references, including relative references. Root request options are not forwarded by the inspected external-ref resolver. |
| Generation / comparison | `orval --config orval.config.ts`; `orval --config orval.config.ts --outdated` compares expected output with disk. | `openapi-ts --file openapi-ts.config.ts`; `--dry-run` is not an equality check. Generate into an isolated destination for comparison. |

**Facts and limits:** Orval's comparison reports changed/missing files, plus obsolete files only when cleaning is configured; incompatible post-write hooks, Biome/oxfmt, and documentation output reject the check. Root header matching uses hostname, while external-reference matching uses host including a non-default port; the fixture needed both entries. [Input documentation](https://github.com/orval-labs/orval/blob/68087ee84a5614b0472fda97957bb29511b49b2a/docs/content/docs/reference/configuration/input.mdx), [comparison contract](https://github.com/orval-labs/orval/blob/68087ee84a5614b0472fda97957bb29511b49b2a/docs/content/docs/reference/cli.mdx#--outdated), [root matching](https://github.com/orval-labs/orval/blob/68087ee84a5614b0472fda97957bb29511b49b2a/packages/orval/src/utils/options.ts#L1489), [reference matching](https://github.com/orval-labs/orval/blob/68087ee84a5614b0472fda97957bb29511b49b2a/packages/orval/src/import-specs.ts#L1855).

**Facts and limits:** Hey API documents root fetch options, but its external resolver calls `resolver.handler({ file })` without those options. Its dry-run skips generated-file writes while output cleanup is unconditional when `output.clean` is true, the default. Do not interpret this release's dry-run as a safe drift check. [Input configuration](https://github.com/hey-api/hey-api/blob/d6ba11fd9ae4f2b707454940121056fdb505235c/web/src/content/docs/docs/openapi/typescript/configuration/input.mdx), [external resolution](https://github.com/hey-api/hey-api/blob/d6ba11fd9ae4f2b707454940121056fdb505235c/packages/json-schema-ref-parser/src/resolve-external.ts#L150), [output implementation](https://github.com/hey-api/hey-api/blob/d6ba11fd9ae4f2b707454940121056fdb505235c/packages/openapi-ts/src/generate/output.ts#L12), [clean default](https://github.com/hey-api/hey-api/blob/d6ba11fd9ae4f2b707454940121056fdb505235c/packages/openapi-ts/src/config/output/config.ts#L115).

These headers authenticate schema retrieval; runtime SDK authentication is a separate configuration concern. Temporary files work with both generators. Copying only an entry document changes relative-reference resolution; preserve the reference graph/base or create a temporary self-contained bundle using the application's authorized retrieval mechanism. Do not enable source-document output when the agreed policy excludes persisting OpenAPI.

## 4. Bounded local observations

**Observed:** Node 24.21.0, npm Orval 8.46.0, Hey API 0.99.0, TypeScript 6.0.3. One loopback HTTP fixture served a minimal OpenAPI 3.0.3 GET endpoint with an object response, either inline or through `./schema.json#/Item`; root and reference authorization were independently controlled. The token was an inert fixture value. Commands used each installed CLI with the configurations above. Drift was a deliberately appended comment in generated output.

| Probe | Result |
| --- | --- |
| Orval: protected root + protected relative ref | Exit 0; server observed authorization on both requests. |
| Orval: `--outdated`, then altered generated file | Exit 0 unchanged; exit 1 after alteration; file bytes remained untouched. |
| Hey API: protected root; public relative ref; protected relative ref | Root-only and public-ref cases exited 0. Protected-ref case exited 1: reference request lacked authorization and received 401. |
| Hey API: `--dry-run` after altering output, default clean | Exit 0; generated output was removed. This agrees with the cleanup source above. |
| Temporary self-contained JSON input | Both generators exited 0, without HTTP requests. |

An initial unconstrained install selected TypeScript 7.0.2 and Hey API failed before fetching (`SyntaxKind.AnyKeyword` unavailable). Pinning TypeScript 6.0.3 allowed these probes; this is an observed dependency combination, not a support matrix. Schemas, generated clients, and experiment files stayed in a temporary directory and are not published. These observations do not cover every plugin, reference topology, redirect, or generator version.

## 5. What freshness evidence proves

| Evidence | Supported claim | Limit |
| --- | --- | --- |
| Successful authenticated fetch and parse | That identity retrieved an accepted document from that URL at that time. | Does not establish deployment revision or response fidelity; caches may serve older content. |
| Recorded content digest | Same captured bytes, or an explicitly defined canonical representation. | Hash the resolved reference closure when references exist. Root-only hashes miss ref changes; formatting can change raw hashes; hashes do not identify the running build. |
| ETag / conditional request | Server validator for the selected representation. | ETags are opaque; weak tags need not imply byte equality. A 304 is not a backend Git identity or schema correctness certificate. |
| Release/build identity tied to the served instance | Evidence connects that response to identified application, framework, and configuration inputs. | A local lockfile or human-set `info.version` alone cannot make that connection; mixed deployments need scoped evidence. |
| Deterministic regeneration plus complete output comparison; representative real calls | Regeneration establishes SDK agreement with captured input/config/toolchain. Real calls establish behavior for the exercised revision, identity, and cases. | Equal SDK output can hide ignored schema changes; generated types are not runtime validation. Neither result proves all API behavior. |

HTTP validator semantics come from [RFC 9110 §8.8](https://www.rfc-editor.org/rfc/rfc9110.html#section-8.8); cache revalidation and freshness come from [RFC 9111 §4–5](https://www.rfc-editor.org/rfc/rfc9111.html#section-4). OpenAPI distinguishes document metadata from specification version; it does not define `info.version` as a deployed-build attestation. [OpenAPI Info Object](https://spec.openapis.org/oas/v3.0.3.html#info-object).

**Inference:** a feasible workflow captures authorized live input once into temporary storage, resolves its references, records observation/revision evidence separately, runs the locked generator and formatting hooks, and compares the complete generated tree. Include added and removed files: plain `git diff --exit-code` misses untracked output. A fresh isolated checkout plus scoped `git status --porcelain --untracked-files=all`, or a complete tree comparison, can cover them. No maintained schema copy is necessary. Cache revalidation can improve retrieval freshness; it cannot substitute for deployment identity.

**Still a product decision:** which environment is authoritative; acceptable freshness and unavailable-service behavior; required build identity; where generation receipts live; and whether generated SDK output is committed. Orval is one supported example, not a mandated choice.
