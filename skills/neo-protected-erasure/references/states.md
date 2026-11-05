# Erasure state interpretation

| Observation | Meaning |
|---|---|
| `Available value` | The active key permits reading; an optional null value is still available, not erased. |
| Pending request | The application recorded intent; the effect or its result is still unresolved. |
| `ErasedNow` | This effect deleted the active key; application completion still needs a committed result fact. |
| `AlreadyErased` | The key was deleted previously; an authorized retry may complete the same application request. |
| `UnknownReference` | The target reference was not found; treat it as a separate failure, not success. |
| Operational/scope error | The effect failed; retain a visible failure and an authorized recovery path. |
| `Erased` on replay | The protected input is unreadable; retained recorded facts must still reconstruct correctly. |

Only claim the application's completion state after its result command has committed. A rejected callback can leave the key erased and the application request pending; an explicit retry must reconcile that state.
