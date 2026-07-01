---
name: neohaskell-outside-in-tdd
description: >-
  The per-slice development discipline for building a feature in a NeoHaskell
  event-sourced project: outside-in, test-first TDD run as RED then DOMAIN then
  GREEN then DOMAIN then REFACTOR, one assertion per test, Given-When-Then
  naming, strict phase boundaries, and "let the compiler tell you what is
  missing." Use whenever you are about to build or change a NeoHaskell feature
  slice, right after verify-event-model and before writing any command, event,
  query, or integration — even if the user just says "implement this" or reaches
  straight for code with no failing test. Also use when asked which test to write
  first, what red-green-refactor or outside-in TDD looks like in NeoHaskell, how
  to keep the test pyramid from becoming an ice-cream-cone, or how to fix
  deployed (locked) code as a fresh V2 cycle. This is the portable "start here"
  process index ordering write-hurl-e2e, write-feature-tests, write-unit-tests,
  neohaskell-domain-modeling, the implement-* skills, and wire-feature.
metadata:
  model: opus
---

**This is NeoHaskell, not vanilla Haskell** — `.hs` is a shared extension, but the language, prelude
(`import Core`, not `Prelude`), test library (`import Test`, not `import Test.Hspec`), and stub
convention (`panic "TODO: not implemented"`, never `undefined`/`error`/`todo`) are different. A weak
model will reflexively hallucinate vanilla Haskell here; this skill's job is to keep the *process*
honest so the individual code skills stay grounded.

---

## Inputs / Outputs / Next

- **In:** a **verified slice** — one user-meaningful step from a `verify-event-model` GO verdict
  (a command→event, event→query, or automation, with its node names already frozen as the future
  `Commands/`, `Events/`, `Queries/` type names).
- **Out:** the **ordered, test-first cycle** the other skills execute for that slice, plus the phase
  boundaries and definition-of-done that keep them honest. This skill produces *discipline*, not
  `.hs` files — the code skills it orders produce those.
- **Next:** run the cycle below, skill by skill: `write-hurl-e2e` → `write-feature-tests` →
  `write-unit-tests` → `neohaskell-domain-modeling` → `implement-command` / `implement-event-and-update-entity`
  / `implement-query` / `implement-integration` (+ `expand-entity`) → `wire-feature` → refactor →
  next slice. For a change to **deployed (locked)** code, this same cycle runs on a `V2` sibling —
  see `neo-immutability-and-versioning`.

**Run the heavy reasoning on Opus.** In Claude Code, when a slice is non-trivial, delegate the
planning of the cycle (deciding the outer behavior, the minimal inner assertions, and where the phase
boundaries fall) to a sub-agent spawned with `model: opus` — sequencing tests outside-in and holding
the phase discipline rewards frontier reasoning. In hosts without sub-agents (Cursor, Codex) this is
advisory: run the cycle inline. Either way, the discipline below is the deliverable.

---

## The cycle: RED → DOMAIN → GREEN → DOMAIN → REFACTOR

Outside-in TDD is a **double loop**. The *outer* loop is observable behavior (HTTP, then in-domain
acceptance); the *inner* loop is the pure building blocks (decider, projection, outbound). You start
at the outside with a failing test and drive **inward** until the pure units are green, which turns
the outer test green.

| # | Phase | Skill | What you write | "Red" means |
|---|---|---|---|---|
| ① | **RED** (outer) | `write-hurl-e2e` | one `.hurl` on `:8080` — `POST /commands/<kebab>`, then a retrying `GET /queries/<kebab>` assert | endpoint not wired yet → **HTTP 404** |
| ② | **RED** (acceptance) | `write-feature-tests` | one in-domain flow spec (`decide → update → combine`, no HTTP) | the command/event/query type doesn't exist → **compile error** |
| ③ | **RED** (inner) | `write-unit-tests` | **one** decider / projection / outbound spec, **one** assertion, Given-When-Then | function missing, or stub `panic`s → **compile error, then assertion failure** |
| ④ | **DOMAIN** | `neohaskell-domain-modeling` | the *types* the red tests reference — event payload fields, entity fields, value objects/enums, `Result`/`Maybe` — with **stubbed bodies** (`panic "TODO: not implemented"`; outbound `handleEvent` → `Integration.none`) | now it **compiles**; the red spec fails on the **assertion**, not the type |
| ⑤ | **GREEN** | `implement-command` / `-event-and-update-entity` / `-query` / `-integration` (+ `expand-entity`) | the **minimal body** that makes the one red inner test pass | — |
| ↩ | **DOMAIN** (again) | `neohaskell-domain-modeling` | if GREEN reveals a missing domain concept, drop *back* to DOMAIN and add the type — do **not** smuggle a primitive into GREEN | — |
| ⑥ | **GREEN** (wire) | `wire-feature` | `Service.command @Cmd`; `withService`/`withQuery`/`withOutbound`/`withInbound` in `App.hs` | endpoint now exists → outer ① hurl goes green |
| ⑦ | **REFACTOR** | (inline) + `write-feature-tests` | improve structure with all tests green; add the **property** replay spec (`Array.foldl update`) | — |

**The inner loop repeats.** For a slice with several decider/projection rules, do ③→④→⑤ once **per
assertion** — add one red unit test, make it compile (DOMAIN), make it pass (GREEN), repeat — before
returning to the outer loop. That is what keeps the base of the pyramid wide.

---

## Phase boundaries (the rule that makes this work)

Each phase may touch **only** its own kind of file. Crossing a boundary is the single most common way
outside-in TDD collapses into "write everything, then hope," and `neohaskell-code-review` flags it.

| Phase | May touch | May **not** touch |
|---|---|---|
| **RED** | test files only (`tests/**.hurl`, `test/**Spec.hs`) | any `src/**.hs` implementation |
| **DOMAIN** | type definitions + stubbed bodies (`data`/`newtype`/`type instance`/instances; body = `panic "TODO: not implemented"` or `Integration.none`) | real logic in any body |
| **GREEN** | implementation **bodies** only | new types, new fields, new tests |
| **REFACTOR** | any file, **all tests green** | changing behavior (no new assertions here) |

**Why the DOMAIN stub matters.** In a typed language your *first* red is a compile error: the test
names a type or function that doesn't exist. DOMAIN's job is to make the code **compile with the
behavior still absent** — every pure/`Task` body is `panic "TODO: not implemented"`, and an outbound
`handleEvent` returns `Integration.none` with a `-- TODO:` (a `panic` in a pure handler crashes the
dispatcher when that event fires). Now `neo test` compiles and the red spec fails on its **assertion**
(the panic fires, or the `Integration.none` produces no command). GREEN then replaces exactly one stub
with the minimal real body. This is "let the compiler tell you what's missing," phase by phase.

---

## One assertion, Given-When-Then

Each inner test asserts **one** behavior, structured Given-When-Then so the name reads as a fact.
Grounded in the framework testlib (`core/testlib/Test/Service/Command/Decide/Spec.hs`) and real specs
like `core/test/IntSpec.hs`:

```haskell
-- test/Decider/AddItemSpec.hs — ③ inner RED (write-unit-tests owns the full template)
module Decider.AddItemSpec where

import Core
import Test                                    -- NeoHaskell testlib, NOT Test.Hspec
import Decider qualified
import Service.Command.Core (DecisionContext (..))
import Service.Auth qualified as Auth
import Uuid qualified
import Testbed.Cart.Core (CartEntity (..), CartEvent (..))
import Testbed.Cart.Commands.AddItem (AddItem (..), decide)


spec :: Spec Unit                              -- Spec Unit, NOT IO ()
spec = describe "AddItem decider" do
  it "rejects adding an item to a cart that does not exist" \_ctx -> do
    -- Given no existing cart, and a command to add 5 units
    let cmd = AddItem {cartId = Uuid.nil, stockId = Uuid.nil, quantity = 5}
    -- When we decide with no entity loaded
    result <-
      Decider.runDecision
        (DecisionContext {genUuid = Uuid.generate})
        (decide cmd Nothing Auth.emptyContext)
    -- Then the command is rejected with a business reason (ONE assertion)
    case result of
      RejectCommand msg -> msg |> shouldBe "Cart not found!"   -- actual |> shouldBe expected
      AcceptCommand _ _ -> fail "expected rejection but got acceptance"
```

The one assertion is `msg |> shouldBe "Cart not found!"` — actual on the left, `|> shouldBe` expected
on the right (the reverse of vanilla Hspec's `shouldBe actual expected`). The reject string is the
real one from `Testbed.Cart.Commands.AddItem`.

---

## Outside-in inverts the ORDER, not the RATIO

Outside-in means you **write** tests from the boundary inward (hurl first, units last). It does **not**
mean you *end up* with mostly slow tests. The finished slice keeps a **pyramid shape**: many fast
decider/projection/outbound/property specs, a few in-domain acceptance specs, one slow hurl e2e. The
failure mode to avoid is the **ice-cream-cone** — all behavior asserted through hurl, no units —
because hurl boots the whole app on `:8080`, is slow, and gives no line-level diagnosis. If a rule can
be pinned by a pure decider test, pin it there; reserve hurl for one observable end-to-end path.

---

## Copy-paste: the per-slice worksheet

Copy this, fill in the slice, and work top to bottom. Placeholders (`<Cmd>`, `<Event>`, `<Query>`,
`<Entity>`) are the frozen node names from `verify-event-model`. The example column is grounded in the
public `Cart`/`Stock` testbed slice "add an item to a cart."

```
SLICE: <one user-meaningful step>            e.g. "AddItem to a cart"
  entity  : <Entity>                          CartEntity   (exists — build on it)
  command : <Cmd>  -> event <Event>           AddItem -> ItemAdded
  query   : <Query> (field touched)           CartSummary (itemCount)

[ ] ① RED  outer   write-hurl-e2e        tests/scenarios/add-item.hurl   -> expect 404 (not wired)
[ ] ② RED  accept. write-feature-tests   test/Acceptance/AddItemSpec.hs  -> compile error
[ ] ③ RED  inner   write-unit-tests      test/Decider/AddItemSpec.hs     -> 1 assert, GWT, compile error
[ ] ④ DOMAIN       neohaskell-domain-modeling
                   - event payload Events/<Event>.hs (type `Event`) + variant in Event.hs
                   - entity field(s) in Entity.hs / expand-entity (add-only, replay-safe)
                   - `decide`/`combine`/`handleEvent` bodies STUBBED
                     pure/Task  -> panic "TODO: not implemented"
                     outbound   -> Integration.none  -- TODO:
                   -> `neo build` compiles; ③ now fails on the ASSERTION
[ ] ⑤ GREEN        implement-command / -event-and-update-entity / -query / -integration
                   -> minimal body; ③ goes green; repeat ③→④→⑤ for each remaining assertion
[ ] ⑥ GREEN  wire  wire-feature          Service.command @<Cmd>; App.hs withService/withQuery/...
                   -> ① hurl goes green (endpoint now answers 200)
[ ] ⑦ REFACTOR     tidy (all green) + write-feature-tests property replay (Array.foldl update)
[ ] DONE           `neo test` all green (hspec + hurl); phase boundaries respected

If <Cmd>/<Event>/<Query> is LOCKED (deployed): do NOT edit it. Run this WHOLE worksheet on a V2
sibling (`<Cmd>V2`) per neo-immutability-and-versioning, then wire the V2 in.
```

### The phases, grounded (Cart `AddItem`)

**① outer RED** — grounded in `testbed/tests/queries/cart-summary-after-create.hurl`. Fails 404 until ⑥:

```hurl
POST http://localhost:8080/commands/create-cart
[]
HTTP/1.1 200
[Captures]
cart_id: jsonpath "$.entityId"

POST http://localhost:8080/commands/add-item
{ "cartId": "{{cart_id}}", "stockId": "11111111-1111-1111-1111-111111111111", "quantity": 5 }
HTTP/1.1 200

GET http://localhost:8080/queries/cart-summary
[Options]
retry: 5
retry-interval: 100
HTTP/1.1 200
[Asserts]
jsonpath "$.items[?(@.cartSummaryId == '{{cart_id}}')].itemCount" nth 0 == 5
```

**④ DOMAIN stub** — the types exist; the body does not. It compiles, so ③ can fail on the assertion:

```haskell
-- Commands/AddItem.hs, DOMAIN phase: stub only
decide :: AddItem -> Maybe CartEntity -> RequestContext -> Decision CartEvent
decide _cmd _entity _ctx = panic "TODO: not implemented"
```

For an **outbound** handler the stub is `Integration.none`, never `panic` (grounded in
`testbed/.../Integrations/ReserveStockOnItemAdded.hs`, whose fall-through is `_ -> Integration.none`):

```haskell
handleEvent :: CartEntity -> CartEvent -> Integration.Outbound
handleEvent _cart _event = Integration.none   -- TODO: emit the cross-aggregate command in GREEN
```

**⑤ GREEN** — replace the one stub with the minimal real body (the actual `Testbed.Cart.Commands.AddItem`):

```haskell
decide :: AddItem -> Maybe CartEntity -> RequestContext -> Decision CartEvent
decide cmd entity _ctx = case entity of
  Nothing -> Decider.reject "Cart not found!"
  Just cart ->
    if cmd.quantity <= 0
      then Decider.reject "Quantity must be positive"
      else
        Decider.acceptExisting
          [ ItemAdded {entityId = cart.cartId, stockId = cmd.stockId, quantity = cmd.quantity} ]
```

(Creation slices end in `Decider.acceptNew [...]` with ids from `newId <- Decider.generateUuid`, as in
`Testbed.Cart.Commands.CreateCart`. The full per-block templates live in the `implement-*` skills.)

**⑦ REFACTOR** — with everything green, add the property replay spec that folds the event log oldest
event first with the entity's `update` (`Array.foldl update initialState events`), per
`write-feature-tests`.

---

## DO / DON'T

| DON'T (vanilla-Haskell or process reflex) | DO (NeoHaskell outside-in) |
|---|---|
| Write implementation before a failing test ("I'll add the test after") | Write the **one** failing test first, run `neo test`, watch it fail — RED before any `src/**.hs` |
| Edit a body during DOMAIN, or add a type/field during GREEN | Respect phase boundaries: DOMAIN = types + stubs; GREEN = bodies only |
| Stub with `undefined` / `error "TODO"` / `todo` | `panic "TODO: not implemented"` (pure/`Task`); `Integration.none` for an outbound `handleEvent` |
| `panic` inside a pure outbound `handleEvent` | Return `Integration.none` — a panic there crashes the dispatcher when the event fires |
| Assert several behaviors in one `it` | **One** assertion per test, Given-When-Then name |
| `import Test.Hspec`; `spec :: IO ()`; `shouldBe actual expected` | `import Test`; `spec :: Spec Unit`; `it "..." \_ctx -> do`; `actual |> shouldBe expected` |
| Prove every rule through hurl (ice-cream-cone) | Pyramid: pin rules in pure decider/projection tests; one hurl for the observable path |
| "Fix" a deployed `Commands/`/`Events/`/`Queries/` file in place | Leave it byte-identical; run this whole cycle on a `V2` sibling (`neo-immutability-and-versioning`) |
| Treat outside-in as "mostly e2e tests" | Outside-in is the **write order**; the **ratio** stays pyramid-shaped |

---

## Verify

Run the real toolchain — never `cabal`/`ghc` directly:

```sh
neo build     # DOMAIN done: it COMPILES (stubs and all)
neo test      # runs the hspec pyramid, then every tests/**/*.hurl against a booted app
```

**Definition of done for a slice:** `neo test` is **all green** (hspec units + property + acceptance,
then hurl e2e), and the phase boundaries above hold (checkable by `neohaskell-code-review`). Then loop
back to ① for the next slice.

> Note: the full Haskell test pyramid assumes [neohaskell/neo#2](https://github.com/neohaskell/neo/issues/2)
> (the generated `test-suite` stanza, nearly landed) so `neo test` compiles and runs the specs. Build
> as if it is in place.

---

## The portable process index ("start here")

Whether a human or an agent is driving, this is the order for **every** slice. Each step is its own
skill; this skill only sequences them.

1. Design first (once per feature, before any slice): `augment-feature-request` → `event-modeling` →
   `verify-event-model`.
2. Per slice, outside-in and test-first:
   `write-hurl-e2e` (① outer RED) → `write-feature-tests` (② acceptance RED) →
   `write-unit-tests` (③ inner RED) → `neohaskell-domain-modeling` (④ DOMAIN) →
   `implement-command` / `implement-event-and-update-entity` / `implement-query` /
   `implement-integration` — with `expand-entity` when a field is needed — (⑤ GREEN) →
   `wire-feature` (⑥ GREEN) → refactor + property (⑦).
3. Fixing deployed code = a **fresh run of steps 2** on a `V2` sibling (`neo-immutability-and-versioning`),
   never an edit.

The full methodology — the double-loop rationale, the per-phase constraints, the anti-pattern
catalogue, and a worked end-to-end example — is in **`references/outside-in-tdd.md`**. Read it when a
slice is subtle or when a teammate/agent breaks discipline and you need the "why."
