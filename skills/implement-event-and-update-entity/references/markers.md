# Supported markers and historical layouts

Use this branch only after the effective API guide confirms these markers. The explicit-instance examples in `explicit-layout.md` cover an existing split/combined layout; do not combine both approaches blindly.

At the researched public framework revision `f09b360025d842e5ad9bc471f46af91e43cbdab7`, `Service.Event.TH.deriveEvent` generates missing `Show`, `Generic`, `Json.FromJSON`, and `Json.ToJSON` instances. Custom instances come **before** the marker. For example:

```haskell
module Library.Loan.Events.LoanOpened where

import Core
import Service.Event.TH (deriveEvent)

data LoanOpened = LoanOpened
  { loanId :: Uuid
  , memberId :: Uuid
  }

deriveEvent ''LoanOpened
```

`Service.Entity.TH.deriveEntity ''LoanEntity ''LoanEvent` generates missing naming, associations, JSON, `Default`, entity, and routing plumbing. Define `initialState`, `update`, and `getEventEntityId` before the marker when the corresponding business instances are absent. Preserve custom instances before the marker. It does not decide business transitions for the application.

`deriveEntityEvents` builds an event sum from a nonempty explicit payload list whose payloads already map to the entity. Its generated constructor names and JSON tags are part of the wire/history contract. Inspect the actual generated shape before replacing an existing event ADT; round-trip and replay representative persisted payloads. Adopting a marker is not permission to rewrite stored history.

A different effective framework revision may expose a different API. Follow that revision's guide or source; do not invent marker signatures from these examples.
