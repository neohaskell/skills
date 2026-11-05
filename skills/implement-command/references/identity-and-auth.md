# Select stream identity, acceptance, and access policy

Use only the branch needed by the task. Resolve the application revision and capabilities through [nh-app-context](../../nh-app-context/SKILL.md) before adapting API examples. The existing consumer layout and compatible API guide determine the actual imports, markers, and commands.

## Create vs update — the only decision you make first

| Pattern | `getEntityId` returns | `decide` accept constructor | When `entity` arg is |
|---|---|---|---|
| **Creation** — the entity does not exist yet | `Nothing` | `Decider.acceptNew [..]` | always `Nothing` (framework never loads) |
| **Update** — the entity must already exist | `Just cmd.entityId` | `Decider.acceptExisting [..]` | `Nothing` = reject "not found"; `Just existing` = proceed |

Generate a new id inside the `decide` `do` block with `Decider.generateUuid` — never pass a UUID in from outside for creation.

---


## Accept constructors carry a stream-state requirement

Each `Decider.accept*` constructor asserts a precondition on the event stream (from `core/service/Decider.hs`):

| Constructor | Stream-state requirement |
|---|---|
| `Decider.acceptNew [..]` | `StreamCreation` — the stream must **not** already exist |
| `Decider.acceptExisting [..]` | `ExistingStream` — the stream must already exist |
| `Decider.acceptAny [..]` | `AnyStreamState` — no precondition |
| `Decider.acceptAfter pos [..]` | optimistic concurrency — stream must be at expected position `pos` |

Consequence: a creation command whose `getEntityId` resolves to an **already-existing** stream cannot `acceptNew` — it would violate `StreamCreation`. So an entity whose id is a natural key can never be re-created once its stream exists (see *Natural-key identity* below).

---


## Natural-key identity — uniqueness by business key

`decide` cannot read other aggregates, so to enforce "no duplicate by business key `x`" (e.g. unique project name) do **not** generate a random id — derive the entity's stream id deterministically from `x`, so a second create resolves to the *same* stream:

`deriveId` here is **your own** helper — NeoHaskell has no built-in deterministic UUID in a pinned rev yet (pending neohaskell#596), so vendor `Data.UUID.V5` in one helper module and swap later; see `neohaskell-collections` (Uuid section).

```haskell
getEntityId :: RegisterProject -> Maybe Uuid
getEntityId cmd = Just (deriveId cmd.name)   -- deterministic from the natural key, NOT random

decide :: RegisterProject -> Maybe ProjectEntity -> RequestContext -> Decision ProjectEvent
decide cmd entity _ctx = case entity of
  Just _existing -> Decider.reject "A project with that name already exists"
  Nothing        ->                          -- stream absent → this is the first create
    Decider.acceptNew
      [ ProjectRegistered ProjectRegistered.Event { entityId = deriveId cmd.name, name = cmd.name } ]
```

`getEntityId` returns `Just` (so the framework loads that deterministic stream), but `entity` is still `Nothing` until the stream has events — so the first create legitimately `acceptNew`s (no stream yet), and every subsequent create sees `Just` and rejects. Request/response shape is identical to a generated-id create. See `neohaskell-domain-modeling` for the design write-up (choosing the key, deriving the id).

**Sharp edge:** because the id *is* the natural key, once the stream exists it can never be re-created (the `acceptNew`/`StreamCreation` requirement above) — even after "archiving" it. There is no "re-register as new"; reactivation must be a separate `acceptExisting` command (e.g. `Unarchive`) on the existing stream.

---


## Auth policy

For commands that create protected values or request erasure, also use [neo-protected-erasure](../../neo-protected-erasure/SKILL.md). It owns the authorization, reference, and pending-request decisions.

Commands are **secure by default**: if you omit `canAccess`, the `command` macro falls back to `authenticatedAccess` (login required). This is enforced only when the application wires `Application.withAuth`. Without `withAuth`, every command is reachable unauthenticated and returns 200 — so `write-hurl-e2e` happy-path tests work without a token.

To open a command to unauthenticated callers explicitly:

```haskell
import Service.AccessControl (publicAccess)

canAccess :: Maybe UserClaims -> Maybe AccessError
canAccess = publicAccess
```

The public Counter source does not override `canAccess` — the default `authenticatedAccess` is the correct starting point for all new commands.

---

