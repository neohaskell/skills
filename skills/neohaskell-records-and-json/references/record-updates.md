# Resolve ambiguous fields in a record update

Use only the branch needed by the task. Resolve the application revision and capabilities through [nh-app-context](../../nh-app-context/SKILL.md) before adapting API examples. The existing consumer layout and compatible API guide determine the actual imports, markers, and commands.

## Record update under DuplicateRecordFields + NoFieldSelectors

`DuplicateRecordFields` is project-wide. It is **expected and fine** for an entity and its event
constructors to share field names — `CartEntity.ownerId` and `CartCreated.ownerId`, or several
constructors of one event ADT each carrying `entityId :: Uuid`. That shared naming is the root
cause of the two update pitfalls below.

### Ambiguous record update — `-Werror=ambiguous-fields` (GHC-02256)

A record **update** `entity {f = .., g = ..}` where **every** field set is *also* a field of the
event constructor being matched has no entity-only field to anchor the type, so GHC rejects it:

```
error: [GHC-02256] [-Wambiguous-fields, -Werror=ambiguous-fields]
  Ambiguous record update with parent type constructor 'SessionEntity'
```

e.g. `SessionEntity` and `SessionActivityObserved` both have `messageCount`/`lastActivity`, so
`entity {messageCount = .., lastActivity = ..}` is ambiguous. Most fold cases are fine because
they set at least one entity-only field (`status`, an id the events don't carry). Two fixes:

```haskell
-- (a) include an entity-only field so the update is unambiguous
entity {messageCount = .., lastActivity = .., status = entity.status}

-- (b) reconstruct via the constructor (all fields) — construction is NOT subject to
--     the warning; only record *update* is
SessionEntity
  { entityId     = entity.entityId
  , messageCount = ..
  , lastActivity = ..
  , status       = entity.status
  }
```

`implement-event-and-update-entity` references this for its inline-event fold layout.

### Qualified field label in an update (module imported `qualified`)

When the record's module is imported `qualified as X`, the bare field label is **not in scope**
for an update under `NoFieldSelectors`:

```haskell
import <App>.<Context>.Commands.RegisterProject qualified as RegisterProject

-- Wrong: bare label -> "Not in scope: record field 'name'"
validCmd {name = ""}

-- Correct: qualify the field label
validCmd {RegisterProject.name = ""}
```

Construction via the qualified constructor `RegisterProject.RegisterProject {name = ..}` works —
which is why the value's own definition compiled. `write-unit-tests` references this.

---

