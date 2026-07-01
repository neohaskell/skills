---
name: neo-immutability-and-versioning
description: >-
  Explains NeoHaskell's DEPLOYED-CODE IMMUTABILITY model and how to change a frozen domain
  file: the .locked-files manifest, how neo lock and the neo build pre-build gate freeze
  every file under Commands/ Events/ Queries/, and the exact V-BUMP rule (change Foo.hs by
  creating a byte-new sibling FooV2.hs whose type is FooV2, leaving the original untouched),
  plus add-only entity evolution (entities are never locked/versioned). Use whenever you
  need to change, fix, rename, or delete a command, event payload, or query; when neo build
  or a git commit fails with a lock violation ('Build refused: N locked file(s) violate the
  lock'); or when tempted to edit a file under Commands/Events/Queries — even without the
  words 'lock' or 'versioning'. Do NOT use to write the V2 file's decide/wire it (implement-
  command / wire-feature), to add a field to an entity record (expand-entity), or for the
  neo lock SUBCOMMAND flag reference (neo-cli).
metadata:
  model: haiku
---

This is NeoHaskell, not vanilla Haskell. The `.hs` extension is shared, but every module
opens with `import Core` (the vanilla `Prelude` is off), and immutability is enforced by
the `neo` tool, not by GHC.

**One rule to remember:** a deployed command, event payload, or query file is **immutable**.
You never edit it. To change its behavior you create a **new sibling file with a `V`-bumped
suffix** and leave the original byte-for-byte identical.

---

## Inputs / Outputs / Next

**Input:** a request to change / fix / rename / delete a domain artifact (a `Commands/*.hs`,
`Events/*.hs`, or `Queries/*.hs` file), **or** a lock-violation error from `neo build` or a
blocked `git commit`.

**Output:** a decision (safe edit vs. new `V`-bumped sibling) and, when a bump is needed, a
new `FooV2.hs` file (type `FooV2`) plus its wiring, with the original left untouched.

**Next skills:**
- `implement-command` / `implement-event-and-update-entity` / `implement-query` — write the V2 body.
- `expand-entity` — add a field to the (unlocked) entity that the V2 needs.
- `wire-feature` — register the V2 command/query/event so its endpoint goes live.
- `neo-cli` — the `neo lock` / `neo build` command surface.

**Outside-in TDD role.** A change to a *deployed (locked)* artifact is not an edit — it is a
**fresh outside-in TDD cycle on the `V2` sibling** (RED → DOMAIN → GREEN → REFACTOR), exactly
as if the V2 were a brand-new feature. Start from a failing test against the new behavior.

---

## What is locked (grounded in `neo/src/lock.rs`)

`neo lock` discovers "domain files" by walking `src/` and matching any path that has a
**directory component named exactly** `Commands`, `Events`, or `Queries`:

| Path pattern | Status |
|---|---|
| `src/**/Commands/*.hs` | **LOCKED** once deployed — never edit |
| `src/**/Events/*.hs` (per-event payloads, type `Event`) | **LOCKED** once deployed — never edit |
| `src/**/Queries/*.hs` | **LOCKED** once deployed — never edit |
| `Entity.hs`, the singular `Event.hs` ADT, `Core.hs`, `Service.hs`, `App.hs`, `Config.hs`, `Integrations/*.hs` | **NOT locked** — may evolve (add-only for entities) |

The locked paths live in a plain-text manifest, one repo-relative path per line, at the
project root:

```
.locked-files
────────────
src/Starter/Counter/Commands/IncrementCounter.hs
src/Starter/Counter/Events/CounterIncremented.hs
src/Starter/Counter/Queries/CounterView.hs
```

**Why locking exists:** NeoHaskell projects are event-sourced. Every deployed node replays
its persisted event log on start, decoding it against the shapes these files define. Editing,
renaming, or deleting a locked file silently breaks replay on every deployed node — a bug
invisible in tests and catastrophic in production. The lock prevents that.

---

## How enforcement works (grounded in `lock.rs`, `commands/lock.rs`, `commands/build.rs`)

A path is **violated** when it appears in **both** `.locked-files` **and**
`git status --porcelain` (staged, unstaged, untracked, deleted, or renamed — a rename reports
both the old and the new path). It is **not** hash-based and **not** a GHC/compile-time check.

Two gates catch violations:

1. **`neo build` pre-build gate** — runs `neo lock check` before compiling; aborts on violation
   (unless a human passes an escape flag, which you must not rely on — see DON'T table).
2. **git pre-commit hook** — `neo lock install` writes `.git/hooks/pre-commit` that runs
   `neo lock check`, so a commit touching a locked file is rejected.

The real `neo lock` subcommands are exactly: `neo lock` (lock discovered files), `neo lock <query>`
(fuzzy pick), `neo lock --all`, `neo lock install`, and `neo lock check`. **There is no
`neo lock --remove`** — locking is one-way.

The violation error you will see:

```
Build refused: N locked file(s) violate the lock
  Pre-build lock check on `.locked-files` aborted...
```

When you hit it, do exactly one of:
- **Unintentional change?** Discard it: `git restore -- src/Starter/Counter/Commands/IncrementCounter.hs`
  so the file is byte-identical again.
- **Need new behavior?** Do the `V`-bump below.

---

## The exact `V`-bump rule (grounded in `derive_next_version`, `neo/src/errors.rs`)

Create a new sibling in the **same directory**; bump the suffix; the **filename stem and the
type name must match**; leave the original file byte-identical.

| Locked file | New sibling | Type: old → new |
|---|---|---|
| `Commands/IncrementCounter.hs` | `Commands/IncrementCounterV2.hs` | `IncrementCounter` → `IncrementCounterV2` |
| `Commands/IncrementCounterV2.hs` (already versioned) | `Commands/IncrementCounterV3.hs` | `IncrementCounterV2` → `IncrementCounterV3` |
| `Events/ItemAddedV99.hs` | `Events/ItemAddedV100.hs` | `ItemAddedV99` → `ItemAddedV100` |

The suffix is **`V` immediately followed by an integer**, PascalCase. These forms are all
**wrong** and will not be recognized as the next version: `increment_counter_v2`,
`IncrementCounter.V2`, `IncrementCounterVersion2`, `IncrementCounterv2` (lowercase `v`),
`IncrementCounter_V2`. (A lowercase `Barv2.hs` is treated as *unversioned*, so its bump is the
nonsensical `Barv2V2` — another reason to always use the canonical capital `V`.)

---

## Copy-paste template: a `V2` command sibling

Adapted from the public Counter command (`Starter.Counter.Commands.IncrementCounter`,
`neo` test-project). The original stays locked and untouched; the V2 carries the new rule.

```haskell
-- FILE: src/Starter/Counter/Commands/IncrementCounterV2.hs   (NEW sibling; original left byte-identical)
module Starter.Counter.Commands.IncrementCounterV2 (
  IncrementCounterV2 (..),
  getEntityId,
  decide,
) where

import Core
import Decider qualified
import Json qualified
import Service.Auth (RequestContext)
import Service.Command.Core (TransportsOf)
import Service.CommandExecutor.TH (command)
import Service.Transport.Web (WebTransport)
import Starter.Counter.Core
import Starter.Counter.Events.CounterIncremented qualified as CounterIncremented


data IncrementCounterV2 = IncrementCounterV2
  { entityId :: Uuid
  , amount :: Int
  }
  deriving (Generic, Typeable, Show)


instance Json.FromJSON IncrementCounterV2


getEntityId :: IncrementCounterV2 -> Maybe Uuid
getEntityId cmd = Just cmd.entityId


decide :: IncrementCounterV2 -> Maybe CounterEntity -> RequestContext -> Decision CounterEvent
decide cmd entity _ctx = case entity of
  Nothing -> Decider.reject "Counter not found"
  Just existing ->
    if cmd.amount <= 0
      then Decider.reject "Amount must be positive"
      else
        if cmd.amount > 100
          then Decider.reject "Amount may not exceed 100" -- NEW rule that motivated the V2
          else
            Decider.acceptExisting
              [ CounterIncremented
                  CounterIncremented.Event
                    { entityId = existing.counterId
                    , amount = cmd.amount
                    }
              ]


type instance EntityOf IncrementCounterV2 = CounterEntity


type instance TransportsOf IncrementCounterV2 = '[WebTransport]


command ''IncrementCounterV2
```

This V2 reuses the existing `CounterIncremented` event because only the *rule* changed. If the
**event's shape** must change, version the payload file too (next section).

---

## Special case: versioning a locked event payload

Per-event payload modules are locked, and their in-file type is **literally `Event`**. Version
at the **file/module** level; the type stays `Event`. Then add a new variant to the (unlocked)
singular `Event.hs` ADT and handle it in the (unlocked) entity.

```haskell
-- FILE: src/Starter/Counter/Events/CounterIncrementedV2.hs   (NEW; type is still `Event`)
module Starter.Counter.Events.CounterIncrementedV2 (Event (..)) where

import Core
import Json qualified

data Event = Event
  { entityId :: Uuid
  , amount :: Int
  , reason :: Text -- the new field this V2 exists to carry
  }
  deriving (Generic, Show)


instance Json.FromJSON Event


instance Json.ToJSON Event
```

```haskell
-- FILE: src/Starter/Counter/Event.hs   (NOT locked — add the variant here)
data CounterEvent
  = CounterCreated CounterCreated.Event
  | CounterIncremented CounterIncremented.Event
  | CounterIncrementedV2 CounterIncrementedV2.Event -- NEW variant wrapping the V2 payload
  deriving (Generic, Show)
```

Then extend `getEventEntityId` (in `Event.hs`) and the entity's `update` fold (in `Entity.hs`)
with a case for `CounterIncrementedV2`. Both are unlocked, so you edit them in place — but the
`update` fold must stay **exhaustive**, and the old `CounterIncremented` case must remain (old
logged events still replay through it).

**Wire the V2 in** exactly like a fresh artifact (see `wire-feature`): a new command goes into
`Service.hs` (`Service.command @IncrementCounterV2`); a new query into `App.hs`; a new event
variant into the ADT + `update` as above.

---

## Entities evolve, they are never versioned (add-only)

`Entity.hs` is **not** locked and gets **no `V2`** — contrast with the locked artifacts above.
There is no automated guard, so the rule is convention: **add fields only**. Never remove,
rename, or retype a field (that breaks replay of old snapshots and the logged event stream).
A new field must be (1) added to the record, (2) given a value in `initialState`, (3) produced
in the relevant `update` case, and (4) replay-safe for old snapshots (make it `Maybe`, or give
its JSON decode a default). Use the `expand-entity` skill for this.

---

## DO / DON'T

| DO | DON'T |
|---|---|
| Create a new sibling `FooV2.hs` with type `FooV2`, leave `Foo.hs` byte-identical | Edit, rename, or delete a locked file under `Commands/`, `Events/`, or `Queries/` |
| Bump the suffix as `V` + integer, PascalCase (`FooV2`, `FooV3`) | Use `foo_v2`, `Foo.V2`, `FooVersion2`, `Foov2` (lowercase `v`), or `Foo_V2` |
| Match filename stem to type name (`BarV2.hs` ↔ `BarV2`) | Rename the type without renaming the file (or vice-versa) |
| Keep the payload type literally `Event`; version the file (`CounterIncrementedV2.hs`) | Rename the in-file type to `EventV2` |
| `git restore -- <path>` to discard an accidental edit to a locked file | Reach for `neo build --skip-lock-check` or hand-edit `.locked-files` (railguarded escape hatches — don't rely on them) |
| Look for `neo lock install` / `neo lock check` | Invent `neo lock --remove` / `neo unlock` — they do not exist |
| Add fields to `Entity.hs` in place (add-only) | Create `EntityV2` for entities, or remove/rename/retype an entity field |
| In the V2 body: `import Core`; `Text` not `String`; `!=` not `/=`; `panic "TODO"` not `error`; `Result`/`Ok`/`Err` not `Either` | Reflex to vanilla Haskell just because the file is `.hs` |
| Keep the `update` fold exhaustive, keeping every old event case | Drop the old event case when adding the V2 variant (old logs still replay) |

---

## Verify it

The lock is a `neo` gate, so check it with the tool, not the compiler:

```sh
neo lock check   # exits clean if no locked file is modified; prints "Build refused: ..." on violation
neo build        # runs the same pre-build gate, then compiles the V2 + its wiring
```

Green `neo lock check` + a compiling `neo build` means the original stayed frozen and the V2 is
wired correctly. If `neo lock check` still complains, you edited a locked file — revert it with
`git restore --` and move the change into the `V2` sibling instead.
