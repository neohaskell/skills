# Format severity-ranked review findings

Use only the branch needed by the task. Resolve the application revision and capabilities through [nh-app-context](../../nh-app-context/SKILL.md) before adapting API examples. The existing consumer layout and compatible API guide determine the actual imports, markers, and commands.

## Severity model

| Severity | Meaning |
|---|---|
| **blocker** | Will not compile (per a documented rule), breaks immutability, breaks replay/old snapshots, or leaks a secret. Merge-blocking. |
| **major** | Correctness or ES/CQRS violation (mismatched create/update, non-exhaustive `update`, present-tense event, missing wiring/coverage). |
| **minor** | Idiom/style (`$`/`<>`/`/=`, misplaced `ToSchema`, phase-boundary bleed). |
| **nit** | Cosmetic (naming, comments, ordering) — never merge-blocking. |

---


## Output format (copy-paste)

```
## NeoHaskell code review — <base>..<head>

**Verdict:** REQUEST CHANGES — 2 blockers, 1 major, 1 minor
(or: **Verdict:** APPROVE — no blocking findings)

### Blockers
- [BLOCKER] src/Starter/Counter/Commands/IncrementCounter.hs:1
  Rule: immutability — files under `Commands/` are frozen once locked; this one is edited.
  Fix: revert byte-for-byte; add `IncrementCounterV2.hs` (type `IncrementCounterV2`) and register it in `Service.hs`.
- [BLOCKER] src/Testbed/Stock/Queries/StockLevel.hs:20
  Rule: `deriveQuery` requires both `canAccess` and `canView`; `canView` was removed.
  Fix: restore `canView :: Maybe UserClaims -> StockLevel -> Maybe AccessError` (`publicView` or `ownerOnly`).

### Major
- [MAJOR] src/Starter/Counter/Commands/DecrementCounter.hs:24
  Rule: `decide` must end in a `Decider.*` constructor; this `do` ends in `pure [...]`, which throws at runtime.
  Fix: return `Decider.acceptExisting [...]`.

### Minor
- [MINOR] src/Starter/Counter/Entity.hs:40  Use `++`, not `<>`, to concatenate.

### Nits
- (none)
```

Order findings blocker → major → minor → nit. Every finding is `file:line`, the **rule**, and a **concrete fix**. If the diff is clean, say so and APPROVE — do not invent findings.

---

