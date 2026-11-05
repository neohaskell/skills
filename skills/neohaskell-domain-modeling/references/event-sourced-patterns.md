# Model identity, references, or composed projections

Use only the branch needed by the task. Resolve the application revision and capabilities through [nh-app-context](../../nh-app-context/SKILL.md) before adapting API examples. The existing consumer layout and compatible API guide determine the actual imports, markers, and commands.

## Event-sourced design patterns

Four recurring decisions that shape the DOMAIN types. The *mechanics* live in the `implement-*` skills; the *design rationale* is here.

### Natural-key identity — uniqueness without reading other aggregates

A `decide` sees only its own aggregate (its entity `Maybe`, never another stream), so it cannot enforce "no duplicate by business key `x`" (e.g. unique project name) by looking around. Instead, derive the entity's **stream id deterministically** from `x` — `getEntityId cmd = Just (deriveId cmd.x)`, **not** a random `Uuid`. A second create then resolves to the *same* stream, so `decide` sees `Just entity` and rejects the duplicate. Request/response shape is identical to a generated-id create.

**Sharp edge — this was the code-review finding.** Because the id *is* the natural key, once the stream exists it can **never** be re-created — even after "archiving" it. A creation command uses `acceptNew`, which requires the stream to *not* exist (`StreamCreation`), so there is no "re-register as new". Reactivation must be a **separate `Unarchive`-style command** acting on the *existing* stream (`acceptExisting`), not a re-create. → `implement-command` holds the `acceptNew`/`StreamCreation` mechanics.

### Cross-aggregate references and authority

A browser-supplied ID is untrusted input. Parsing a UUID proves its shape, not the caller's permission or the resource's existence. Discover the application's policy and enforce authentication, resource authorization, existence, and consistency at the server boundary that owns each decision. A pure `decide` sees its own aggregate; that constraint does not give the UI authority over another stream. Use the supported server-side access checks, an authoritative command, or an explicit process manager/compensation protocol for cross-stream invariants. Define races and stale-reference behavior. Store a denormalized reference only after the applicable policy has been enforced; test unauthorized and missing-resource cases separately.

### Status-as-ADT, expose-as-text

Hold an entity's status as an **ADT** so illegal states are unrepresentable (the enum move above) — never a `Text` that could be `"bananas"`. Choose the wire representation from the public contract: a documented enum, a tagged object, or an explicit text tag. Converting an ADT to `Text` does not make new values backward-compatible. Keep JSON, OpenAPI, and client handling aligned, including unknown-value behavior. See `implement-query` and `nh-api-client`.

### Composed read models + count-via-id-set

One read model can be fed by **several** entity streams keyed by a common id — e.g. `deriveQuery ''ProjectOverview [''ProjectEntity, ''TaskEntity, ''WorktreeEntity]`, one `QueryOf` instance per entity, each contributing its slice to the same `queryId` row (the dashboard / aggregate-view pattern). Caveat for **distinct counts**: `combine` fires on every event of a contributor and only ever sees *that* entity's current folded state, never the set of contributors — so `count = existing.count + 1` **over-counts**. Hold an **id-set** (a deduped `Array Uuid`, or a `Set`) in the read model and derive the count from its size. → `implement-query` holds the multi-entity `deriveQuery` mechanics.

---

