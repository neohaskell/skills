# Receive a timer or webhook trigger

Use only the branch needed by the task. Resolve the application revision and capabilities through [nh-app-context](../../nh-app-context/SKILL.md) before adapting API examples. The existing consumer layout and compatible API guide determine the actual imports, markers, and commands.

## Template 3 — Inbound (Timer)

An inbound integration fires a command on a schedule or from a webhook. It
produces an `Integration.Inbound` value. There is no marker type and no macro;
the value is passed directly to `withInbound` in `App.hs`.

Illustrative example using the Library domain (structural pattern grounded in
`Testbed.Cart.Integrations.periodicCartCreator`, public testbed):

```haskell
-- src/Library/Integrations.hs
-- Illustrative: Library domain — check for overdue loans every 30 minutes.
module Library.Integrations (
  overdueChecker,
) where

import Integration qualified
import Integration.Timer qualified as Timer
import Library.Commands.CheckOverdueLoans (CheckOverdueLoans (..))


-- | Fires a CheckOverdueLoans command every 30 minutes.
-- The command must use InternalTransport (not WebTransport) since it is
-- emitted by the framework, not an HTTP client.
overdueChecker :: Integration.Inbound
overdueChecker =
  Timer.every Timer.Every
    { interval = Timer.seconds (30 * 60)
    , toCommand = \_ -> CheckOverdueLoans
    }
```

The testbed version uses `Timer.seconds 3` and `CreateCartInternal`. The
`toCommand` lambda receives a timer tick value and returns any command whose
`type instance TransportsOf Cmd = '[InternalTransport]`.

---

