# The consumer actually uses legacy file locks

Use only the branch needed by the task. Resolve the application revision and capabilities through [nh-app-context](../../nh-app-context/SKILL.md) before adapting API examples. The existing consumer layout and compatible API guide determine the actual imports, markers, and commands.

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

**`.locked-files` does not exist until you run `neo lock`.** `neo build` and `neo test`
**never lock** — they only *check* an already-present `.locked-files` (the pre-build gate
below). Until you deliberately run `neo lock`, there is no manifest, nothing is frozen, and
every file — including those under `Commands/`, `Events/`, `Queries/` — is freely editable.
The immutability / V2 gate only bites **after** the deliberate `neo lock` step; edit freely
during development.

**Forward rev-drift is by design, not a dirty tree.** Because `neo.json` pins
`"neo-version": "main"` only when explicitly configured. In that case `neo build`/`neo test` can advance the
neohaskell rev — rewriting `flake.nix`, `cabal.project`, and `flake.lock` together (you'll see
`Updated input 'neohaskell': …`); those modified files are expected drift, not corruption and
not a lock violation (they aren't locked paths). See `neo-cli`.

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
- **Unintentional change?** Preserve the diff and identify its owner. Confirm before discarding it; never restore files solely because a lock reports a change.
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

