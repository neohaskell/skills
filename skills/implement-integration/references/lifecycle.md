# Own resources or run a lifecycle subprocess

Use only the branch needed by the task. Resolve the application revision and capabilities through [nh-app-context](../../nh-app-context/SKILL.md) before adapting API examples. The existing consumer layout and compatible API guide determine the actual imports, markers, and commands.

## Template 4 — Lifecycle outbound (stateful worker)

A lifecycle integration holds per-entity state across events — for example, a
connection pool, a gRPC channel, or a counter. It is wired with
`withOutboundLifecycle`, not `withOutbound`.

Illustrative example using the Library domain (structurally grounded in
`Testbed.Cart.Integrations.EventCounter`, public testbed):

```haskell
-- src/Library/Integrations/LoanNotifier.hs
-- Illustrative: Library domain — stateful per-member notification worker.
module Library.Integrations.LoanNotifier (
  loanNotifierIntegration,
  LoanNotifierState (..),
) where

import Console qualified
import Core
import Integration.Lifecycle qualified as Lifecycle
import Service.Event.StreamId qualified as StreamId
import Task qualified


-- | State held by each entity's worker for the lifetime of the worker process.
data LoanNotifierState = LoanNotifierState
  { memberId :: Text
  }
  deriving (Generic)


-- | Lifecycle config: initialize on first event, processEvent on each event,
-- cleanup when the worker is reaped after idle timeout.
loanNotifierIntegration :: Lifecycle.OutboundConfig LoanNotifierState
loanNotifierIntegration = Lifecycle.OutboundConfig
  { initialize = \streamId -> do
      let memberIdText = StreamId.toText streamId
      Console.print [fmt|[LoanNotifier] Starting worker for member: #{memberIdText}|]
      Task.yield LoanNotifierState { memberId = memberIdText }

  , processEvent = \state _event -> do
      -- TODO: send notification or other side-effecting work.
      Task.yield []

  , cleanup = \state -> do
      Console.print [fmt|[LoanNotifier] Worker done for: #{state.memberId}|]
  }
```

`initialize` returns the initial state wrapped in `Task`. `processEvent` has type
`state -> Event Json.Value -> Task Text (Array Integration.CommandPayload)` — the
element type is the framework wrapper `Integration.CommandPayload`, not a raw
command. Lifecycle `processEvent` is for side-effecting work (incrementing
counters, sending notifications, writing to external stores); the testbed
`EventCounter` just returns `Task.yield []` without touching the payload. For a
**real** side effect that decodes the event and shells out, see **Template 5**.
Cross-aggregate command dispatch belongs in a per-trigger outbound handler
(Template 1), not in a lifecycle `processEvent`. `cleanup` runs when the worker is
reaped; it returns `Task Text Unit`.

---


## Template 5 — Real outbound side effect (Subprocess: decode the event + shell out)

Templates 1 and 4 never touch the event *payload* — Template 1's `handleEvent` is
pure, and the Template 4 counter returns `Task.yield []` without decoding. This lifecycle example decodes the triggering `Event Json.Value`, selects a variant, and runs a subprocess. Use it only when lifecycle ownership fits; supported declarative actions use their existing executor. Confirm signatures against the installed revision before adapting it.

```haskell
-- src/App/Context/Integrations/GitWorktreeProvisioner.hs
module App.Context.Integrations.GitWorktreeProvisioner (
  gitWorktreeProvisioner,
) where

import Array qualified
import Core
import Integration qualified                        -- Integration.CommandPayload
import Integration.Lifecycle qualified as Lifecycle  -- Lifecycle.OutboundConfig
import Json qualified                               -- Json.decode :: Json.Value -> Result Text a
import Path qualified                               -- Path.fromText :: Text -> Maybe Path
import Service.Event (Event)                        -- the Event record; theEvent.event :: Json.Value
import Subprocess qualified                         -- Subprocess.run / .Error / .Completion
import Task qualified                               -- Task.yield / .throw / .mapError
import App.Context.Core (WorktreeEvent (..))        -- your event ADT (derives FromJSON)


-- | processEvent :: state -> Event Json.Value -> Task Text (Array Integration.CommandPayload)
--   (Integration.Lifecycle.OutboundConfig, core/service/Integration/Lifecycle.hs:74)
processEvent :: Unit -> Event Json.Value -> Task Text (Array Integration.CommandPayload)
processEvent _state theEvent =
  -- theEvent.event :: Json.Value                        (core/service/Service/Event.hs:33)
  -- Json.decode :: Json.Value -> Result Text WorktreeEvent  (core/json/Json.hs:71)
  --   — a RESULT (Ok/Err), NOT the bare event; your ADT derives FromJSON.
  case Json.decode theEvent.event of
    Err reason -> Task.throw [fmt|Cannot decode owned event: #{reason}|]
    Ok decoded -> case decoded of
      WorktreeCreated {repoPath, worktreePath, branch} -> do
        -- Path.fromText :: Text -> Maybe Path            (core/system/Path.hs:47)
        dir <- case Path.fromText repoPath of
          Nothing   -> Task.throw [fmt|Invalid repo path: #{repoPath}|]
          Just aDir -> Task.yield aDir
        -- Subprocess.run :: Text -> Array Text -> Path -> Task Subprocess.Error Subprocess.Completion
        --   (core/system/Subprocess.hs:83). Task.mapError bridges Subprocess.Error → the
        --   Text error channel processEvent requires (core/core/Task.hs:89).
        _completion <-
          Subprocess.run "git" ["worktree", "add", "-b", branch, worktreePath] dir
            |> Task.mapError (\err -> [fmt|git worktree add failed: #{err}|])
        if _completion.exitCode != 0
          then Task.throw [fmt|git worktree add failed with exit code #{_completion.exitCode}|]
          else Task.yield Array.empty
      _ -> Task.yield Array.empty                         -- other variants: nothing to do


-- Stateless config (state = Unit). Field types: Lifecycle.hs:68/74/83.
gitWorktreeProvisioner :: Lifecycle.OutboundConfig Unit
gitWorktreeProvisioner =
  Lifecycle.OutboundConfig
    { initialize   = \_streamId -> Task.yield unit
    , processEvent = processEvent
    , cleanup      = \_state -> Task.yield unit
    }
```

Wire it (see **Wiring in App.hs** below):
`Application.withOutboundLifecycle @() @WorktreeEntity (\_ -> gitWorktreeProvisioner)`.

**Example primitives (confirm against the effective framework revision):**

| Need | API (grounded) |
|---|---|
| The event payload | `Event { entityName :: EntityName, streamId :: StreamId, event :: eventType, metadata :: EventMetadata }` (`Service.Event`). In `processEvent`, `theEvent.event :: Json.Value`; `theEvent.entityName` identifies the source entity. |
| Decode payload → typed event | `Json.decode :: (FromJSON a) => Json.Value -> Result Text a` (`Json.hs:71`). Returns a **`Result`** — match `Ok`/`Err`; do **not** expect the bare event. |
| Run a command | `Subprocess.run :: Text -> Array Text -> Path -> Task Subprocess.Error Subprocess.Completion`; `Completion { exitCode :: Int, stdout :: Text, stderr :: Text }`. Also `which`, `runWithTimeout` (timeout `Int` is its **first** arg), `open`. |
| Working-dir `Path` | `Path.fromText :: Text -> Maybe Path` (`Path.hs:47`). |
| Error channel | `Subprocess.Error = ProcessError Text \| TimeoutError Text \| ToolNotFound Text` (Show, Eq). `processEvent` is `Task Text …`, so bridge with `Task.mapError` (`Task.hs:89`). |
| No follow-up command | return `Array.empty :: Array Integration.CommandPayload`. To emit one, build it with `Integration.makeCommandPayload yourCommand`. |
| Wire it | `Application.withOutboundLifecycle @() @WorktreeEntity (\_ -> provisioner)`. |

> **⚠️ `Subprocess.run` does not fail on a non-zero exit code.** It returns a
> `Completion` even when `git` exits non-zero, and only fails the `Task` on
> spawn/IO errors (e.g. the tool is missing). If a non-zero exit should be an
> error, inspect `_completion.exitCode` yourself and `Task.throw`. Also: the wired
> entity type (`WorktreeEntity`) needs a `TypeName.Inspectable` instance, and the
> `@()` config form is required for `Application.runWith`.

### Testing a real side effect — NOT with `Test.AppSpec`

**`Test.AppSpec` is currently a structural spec-*builder* skeleton, not a runner —
do not reach for it to test integrations.** On the pinned toolchain, `verifyAppSpec`
is wired to `panic "verifyScenario: not implemented"` and crashes on any non-empty
spec, and the scenario combinators (`given`, `expect`, `and`, `receivedCommand`,
`registeredEvent`, `executedTask`) are all `panic "… not implemented"`
(`core/testlib/Test/AppSpec/*`). The only thing that works today is building an
`AppSpec` record with `specificationFor`/`scenario` and comparing it via `shouldBe`;
nothing executes an app, dispatches a command, or mocks/captures a task. It does
**not** "run the app with integrations mocked." Treat the
`given → expect … executedTask` surface as aspirational/WIP in that historical example. Check the installed revision before using this assertion surface; use its actual runner and observable task/result when it is unavailable.

So test a real side effect at the layers that *do* run:

- **Keep the side effect thin; unit-test the pure part directly.** Factor decoding +
  variant selection into a pure helper (e.g. `Event Json.Value -> Maybe GitPlan`) and
  unit-test that with sample payloads (`write-unit-tests`). Assert the *intent* — the
  decoded plan / the exact args you would pass to `git` — not the OS effect.
- **Hurl smoke for the real spawn** (`write-hurl-e2e`): drive the command that emits
  the triggering event against the running app and assert the observable outcome (the
  worktree exists, the endpoint reports it). This is the only end-to-end coverage of
  the actual process spawn.

---

