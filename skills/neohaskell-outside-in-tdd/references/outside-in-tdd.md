# Outside-In TDD for NeoHaskell — full methodology

> **Attribution & license.** Adapted from John Wilger's MIT-licensed `tdd-constraints` and
> `TDD_WORKFLOW` skills, retargeted from a generic/typed-OO setting to NeoHaskell's event-sourced
> building blocks and the `neo` toolchain. The portable discipline (double-loop outside-in, strict
> phase boundaries, one-behavior tests, test pyramid) is kept; the SDLC-plugin machinery of the
> original (red/green/domain **sub-agents**, an orchestrator, `dot`-CLI task management, ADR/story
> workflow, and the "Marvin" persona) is **not** adopted — this repo's flat skills encode the
> discipline and `neohaskell-code-review` enforces the phase boundaries. Original: MIT © John Wilger.
> This adaptation is distributed under the same terms.
>
> Every NeoHaskell code sample below is grounded in the public `neo`/`NeoHaskell` repositories: the
> `testbed` `Cart`/`Stock` bounded contexts and the framework test library
> (`core/testlib/`, `core/test/`). No private/client code appears here.

## Table of contents

1. [Why outside-in (the double loop)](#1-why-outside-in-the-double-loop)
2. [The five phases](#2-the-five-phases)
3. [Phase boundaries — what each phase may touch](#3-phase-boundaries--what-each-phase-may-touch)
4. [One behavior, one assertion, Given-When-Then](#4-one-behavior-one-assertion-given-when-then)
5. [The compiler is your first RED](#5-the-compiler-is-your-first-red)
6. [The pyramid, not the ice-cream-cone (order vs ratio)](#6-the-pyramid-not-the-ice-cream-cone-order-vs-ratio)
7. [NeoHaskell realization of each phase](#7-neohaskell-realization-of-each-phase)
8. [Locked artifacts: a fix is a fresh cycle on V2](#8-locked-artifacts-a-fix-is-a-fresh-cycle-on-v2)
9. [Anti-pattern catalogue](#9-anti-pattern-catalogue)
10. [Worked example: the Cart "AddItem" slice, end to end](#10-worked-example-the-cart-additem-slice-end-to-end)

---

## 1. Why outside-in (the double loop)

Test-driven development has two nested feedback loops:

- The **outer loop** describes *observable behavior* — what a user or another system can see. In a
  NeoHaskell app that is an HTTP round-trip (`POST /commands/<kebab>`, then a `GET /queries/<kebab>`
  on `:8080`) and, one step in, an *in-domain acceptance* flow (`decide → update → combine`) that
  exercises the same behavior without booting the server.
- The **inner loop** describes the *pure building blocks* that make the outer behavior true — the
  command **decider** (`decide`), the query **projection** (`combine`), and the outbound
  **integration** handler (`handleEvent`).

**Outside-in** means you write the *outer* failing test first and then drive **inward**: the outer red
test tells you which building blocks must exist; you TDD each block in the inner loop; when the inner
blocks go green, the outer test goes green. You are always implementing in service of a concrete,
already-written expectation, so you never build a block "because we'll probably need it."

Contrast with **inside-out** (a.k.a. classicist / bottom-up), where you build the entities and
deciders first and hope they compose into the feature. Inside-out tends to over-build the middle
(YAGNI violations) and defers the integration risk to the very end. Outside-in front-loads the
integration question ("does this actually satisfy the observable behavior?") and lets the outer test
prune the inner work to exactly what's needed.

The order is inverted; the **shape is not** (see §6).

---

## 2. The five phases

For one slice the cycle is **RED → DOMAIN → GREEN → DOMAIN → REFACTOR**. The second DOMAIN is not a
typo: GREEN sometimes reveals a missing domain concept, and the correct response is to step *back* to
DOMAIN rather than hack a primitive into a body.

### RED — write one failing test

Add exactly one failing test and *run it to watch it fail*. A test you have not seen fail is not
trustworthy — it might be asserting nothing, or passing for the wrong reason. Outer RED is a `.hurl`
that 404s because the endpoint isn't wired; acceptance RED and inner RED are specs that fail to
compile because the type/function they name does not exist yet (that *is* a valid red in a typed
language — see §5).

### DOMAIN — make it compile, still wrong

Introduce only the **types** the red test references — event payload fields, entity fields, value
objects and enums, `Result`/`Maybe` error shapes — and give every function a **stub body**. In
NeoHaskell a stub is `panic "TODO: not implemented"` for a pure or `Task` body, and `Integration.none`
(with a `-- TODO:` comment) for an outbound `handleEvent`. After DOMAIN the code **compiles** and the
red test now fails on its **assertion** (the panic fires, or the projection produces nothing) rather
than on a type error. This is where "make illegal states unrepresentable" is applied — see the
`neohaskell-domain-modeling` skill.

### GREEN — minimal body to pass the one test

Replace exactly **one** stub with the least code that makes the current red test pass. Do not
generalize, do not add the next case, do not anticipate. If the slice has more rules, you will come
back with another red inner test. Minimalism here is what keeps GREEN honest and the design driven by
tests rather than by speculation.

### DOMAIN (again) — when GREEN needs a concept

If, while writing the minimal body, you find yourself reaching for a primitive to represent something
that is really a domain concept (a quantity that must be non-negative, a status that has three legal
values), **stop GREEN and return to DOMAIN**: define the type, re-stub, and resume. Never let a naked
`Int`/`Text` stand in for a value object just to get to green faster — that debt is paid back in every
future slice.

### REFACTOR — improve structure with the bar green

With every test green, improve names, remove duplication, and extract helpers **without changing
behavior** (no new assertions in this phase). This is also where you add the **property** test — the
QuickCheck replay that folds the whole event log through the entity `update` (`Array.foldl update
initialState events`) to assert an invariant holds for *any* ordering/quantity, widening the base of
the pyramid.

---

## 3. Phase boundaries — what each phase may touch

The boundaries are the load-bearing constraint. If you let phases blur, "TDD" degrades into "write
everything then add a few tests," and the compiler-as-RED signal is lost.

| Phase | May create/edit | Must NOT touch |
|---|---|---|
| **RED** | test files only: `tests/**/*.hurl`, `test/**/*Spec.hs` | any `src/**/*.hs` implementation |
| **DOMAIN** | type definitions and instances (`data`, `newtype`, `type instance`, `instance …`), and **stubbed** bodies (`panic "TODO: not implemented"` / `Integration.none`) | real logic inside any body |
| **GREEN** | implementation **bodies** only | new types, new fields, new tests |
| **REFACTOR** | any file — **but only with all tests green** | behavior changes; new assertions |

Two practical tells that a boundary was crossed:

- You added a `data`/`newtype` while in GREEN → that belonged in DOMAIN; the design pressure the test
  was supposed to create was bypassed.
- You wrote real branching logic while in DOMAIN → you skipped the "fails on the assertion" checkpoint
  and can no longer tell whether the test actually drives the body.

`neohaskell-code-review` treats a phase-boundary violation in a diff as a finding.

---

## 4. One behavior, one assertion, Given-When-Then

Each test pins **one** behavior and makes **one** meaningful assertion. Multiple assertions in a
single `it` couple unrelated failures and blur the diagnosis when the bar goes red. Name the test as a
fact ("rejects adding an item to a cart that does not exist") and structure the body Given-When-Then.

Grounded in the framework testlib (`core/testlib/Test/Service/Command/Decide/Spec.hs`) and specs like
`core/test/IntSpec.hs`, a NeoHaskell decider test looks like:

```haskell
module Decider.AddItemSpec where

import Core
import Test                                    -- the NeoHaskell testlib
import Decider qualified
import Service.Command.Core (DecisionContext (..))
import Service.Auth qualified as Auth
import Uuid qualified
import Testbed.Cart.Core (CartEntity (..), CartEvent (..))
import Testbed.Cart.Commands.AddItem (AddItem (..), decide)


spec :: Spec Unit
spec = describe "AddItem decider" do
  it "rejects adding an item to a cart that does not exist" \_ctx -> do
    -- Given: no cart loaded, a command to add 5 units
    let cmd = AddItem {cartId = Uuid.nil, stockId = Uuid.nil, quantity = 5}
    -- When: we run the decision with Nothing
    result <-
      Decider.runDecision
        (DecisionContext {genUuid = Uuid.generate})
        (decide cmd Nothing Auth.emptyContext)
    -- Then: it is rejected with the business reason
    case result of
      RejectCommand msg -> msg |> shouldBe "Cart not found!"
      AcceptCommand _ _ -> fail "expected rejection but got acceptance"
```

NeoHaskell-specific rules a weak model gets wrong:

- `import Test`, **not** `import Test.Hspec`. The testlib is a NeoHaskell wrapper.
- `spec :: Spec Unit`, **not** `IO ()`; `it "…" \_ctx -> do …` (the lambda takes the per-test context).
- Assertion order is `actual |> shouldBe expected` — the **reverse** of vanilla Hspec's
  `shouldBe actual expected`. `shouldNotBe` exists too.
- `fail "…"` marks the impossible branch; the single *meaningful* assertion is still one `shouldBe`.

For a **projection** you assert the `combine` result (`Update`/`NoOp`/`Delete`); for an **outbound**
you assert the `Integration.Outbound` your `handleEvent` returns for a given event.

---

## 5. The compiler is your first RED

In a dynamically typed language RED is always a runtime assertion failure. In NeoHaskell — GHC, strict,
`NoImplicitPrelude` — your *first* RED for acceptance and unit tests is usually a **compile error**:
the spec references `AddItem`, `ItemAdded`, or `decide` before they exist. That is a legitimate, useful
red. "Let the compiler tell you what's missing" is the workflow:

1. Write the spec that names the not-yet-existing types/functions (RED — it doesn't compile).
2. DOMAIN: add just those types and stub the bodies → `neo build` now **compiles**.
3. Re-run `neo test`: the spec now fails on the **assertion** (the stub `panic`s, or the projection
   returns nothing) — a *different, more advanced* red.
4. GREEN: minimal body → the assertion passes.

So a slice moves through **two** reds — "won't compile" then "wrong answer" — and DOMAIN is the hinge
between them. If you ever see the assertion-level red *before* writing the type, you skipped DOMAIN's
discipline; if you never see the compile-level red, you probably wrote the implementation before the
test.

The outer hurl RED is different in kind: it fails with **HTTP 404** because the command/query endpoint
isn't registered until `wire-feature` runs `Service.command @Cmd` and the `App.hs` `withService` /
`withQuery` / `withOutbound` / `withInbound` calls. That 404 is the outer loop's red; it turns 200
(green) only at step ⑥.

---

## 6. The pyramid, not the ice-cream-cone (order vs ratio)

Outside-in dictates the **order** you *write* tests (boundary first). It says nothing about the
**ratio** you should *end up* with — and the healthy ratio is a **pyramid**:

```
        /\        few    e2e (hurl on :8080) — one observable path per slice
       /  \       some   in-domain acceptance (decide → update → combine)
      /____\      many   decider / projection / outbound / property (pure, fast)
```

The **ice-cream-cone** is the inversion — everything asserted through hurl, almost no units:

```
    \______/      many   hurl e2e  (slow, boots the app, no line-level diagnosis)
     \    /        some   acceptance
      \  /         few    units
       \/
```

Why the ice-cream-cone is a trap in NeoHaskell specifically: `neo test` boots the full app and runs
every `tests/**/*.hurl` against `:8080`; hurl assertions read JSON paths and cannot tell you *which*
branch of a `decide` was wrong. A pure decider spec fails in milliseconds and points at the exact rule.
So: pin each business rule (`reject` reasons, accept conditions, projection math) with a **pure** test,
and keep hurl for **one** end-to-end path that proves the wiring and the eventual-consistency read.
When you finish a slice, sanity-check the shape — if you added three hurl scenarios and zero deciders,
you built a cone.

---

## 7. NeoHaskell realization of each phase

### RED — outer (hurl)

Grounded in `testbed/tests/queries/cart-summary-after-create.hurl` and
`testbed/tests/scenarios/stock-reservation.hurl`. Capture the id, reuse it, retry the eventually-
consistent query:

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

Before wiring, the two `POST`s return 404 — outer red. (Query response shape varies: some queries
return a bare array `$[?…]`, others `{items:[…]}` → `$.items[?…]`; `write-hurl-e2e` detects which.)

### DOMAIN — types + stubs

The event payload lives in its own module (type literally `Event`), is unioned into the context
`Event.hs` ADT, and the entity gains any new field (add-only, so old snapshots still decode). Bodies
are stubbed:

```haskell
-- Commands/AddItem.hs (DOMAIN): the shape is real, the body is not
decide :: AddItem -> Maybe CartEntity -> RequestContext -> Decision CartEvent
decide _cmd _entity _ctx = panic "TODO: not implemented"
```

An **outbound** handler must never `panic` — a panic in this pure handler crashes the dispatcher when
the event fires. Stub it with `Integration.none`, exactly as the real fall-through in
`testbed/src/Testbed/Cart/Integrations/ReserveStockOnItemAdded.hs`:

```haskell
handleEvent :: CartEntity -> CartEvent -> Integration.Outbound
handleEvent _cart _event = Integration.none   -- TODO: emit the command in GREEN
```

### GREEN — minimal real body

The actual `Testbed.Cart.Commands.AddItem.decide` — reject paths first, then `acceptExisting` with the
event. A creation command (`Testbed.Cart.Commands.CreateCart`) instead generates ids inside the
`do` (`cartId <- Decider.generateUuid`) and ends in `Decider.acceptNew [...]`. Either way the `decide`
`do` **must** terminate in a `Decider` smart constructor (`reject`/`acceptNew`/`acceptExisting`); a
`do` ending in a bare value or `pure` throws at runtime.

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

The projection GREEN is the `combine` body (grounded in `Testbed.Stock.Queries.StockLevel`), returning
`Update`/`NoOp`/`Delete`; the entity `update` fold (grounded in `Testbed.Cart.Core.update`) gains the
new `case` arm for the event.

### REFACTOR — property replay

Fold the log oldest-event-first through `update` and assert an invariant for any generated input
(`Array.foldl` is the element-first **left** fold; quantities come from `makeNaturalOrPanic` so they
stay non-negative). `write-feature-tests` owns the full property template.

### Wiring (GREEN ⑥)

`wire-feature` appends `Service.command @AddItem` to the context `Service.hs` and adds
`withService`/`withQuery @CartSummary`/`withOutbound @H`/`withInbound @() (…)` in `App.hs`. Only now
does the outer hurl endpoint answer 200.

---

## 8. Locked artifacts: a fix is a fresh cycle on V2

NeoHaskell deployed code is immutable: `neo lock` freezes every file under a directory named exactly
`Commands`, `Events`, or `Queries`. A locked path that also shows up in `git status` is a violation,
caught by the `neo build` pre-build gate and the git pre-commit hook.

Therefore **you never TDD a change *into* a locked file.** To fix or extend deployed behavior:

1. Leave the original file byte-identical.
2. Scaffold a `V`+integer sibling — `AddItem.hs` → `AddItemV2.hs`, type `AddItem` → `AddItemV2`
   (reject `foo_v2`, `Foo.V2`, `FooVersion2`, lowercase `v`). For an event payload the in-file type
   is still literally `Event`; version at the *module* level (`Events/ItemAddedV2.hs`) and add an
   `ItemAddedV2 ItemAddedV2.Event` variant to the ADT.
3. Run this **entire** outside-in cycle (§2) on the V2 as if it were brand new — RED tests against the
   V2 endpoint, DOMAIN, GREEN, wire the V2 in.

Entities are the exception: `Entity.hs`/`Event.hs` (the singular ADT) are **not** locked and evolve
**add-only** — never remove, rename, or retype a field, so replay of the old event log still decodes.
See `neo-immutability-and-versioning` and `expand-entity` for the exact rules.

---

## 9. Anti-pattern catalogue

| Anti-pattern | Why it breaks outside-in | Correct move |
|---|---|---|
| Implementation before a red test | No proof the code is driven by a requirement; dead/gold-plated code creeps in | Write the one failing test first; run it; watch it fail |
| Test written after the code "to get coverage" | The test can only encode what the code already does; it never had a chance to fail | RED strictly precedes DOMAIN/GREEN |
| Adding a type or field during GREEN | Skips the design pressure DOMAIN creates; primitive obsession leaks in | Return to DOMAIN, define the type, re-stub, resume |
| Real logic during DOMAIN | Loses the "fails on the assertion" checkpoint | DOMAIN bodies are only `panic "TODO: not implemented"` / `Integration.none` |
| `undefined` / `error "TODO"` / `todo` stubs | Not NeoHaskell; `todo` doesn't exist; `error`/`undefined` aren't the convention | `panic "TODO: not implemented"` (pure/`Task`) |
| `panic` inside an outbound `handleEvent` | Crashes the dispatcher when that event fires in production | `Integration.none` (with `-- TODO:`) until GREEN |
| Several assertions per `it` | Couples unrelated failures; unclear diagnosis | One behavior, one assertion, GWT name |
| Vanilla Hspec idioms (`import Test.Hspec`, `IO ()`, `shouldBe actual expected`) | Won't compile / wrong arg order | `import Test`, `Spec Unit`, `actual |> shouldBe expected` |
| Proving every rule through hurl | Ice-cream-cone: slow, no line-level diagnosis | Pin rules with pure decider/projection specs; one hurl per path |
| `decide` `do` ending in a bare value or `pure` | Throws at runtime — not a valid decision | End in `Decider.reject` / `acceptNew` / `acceptExisting` |
| Editing a locked `Commands/`/`Events/`/`Queries/` file | Immutability violation; breaks the deployed contract | Fresh cycle on a `V2` sibling |
| "Outside-in means mostly e2e tests" | Confuses write-order with ratio | Invert the order; keep the pyramid ratio |

---

## 10. Worked example: the Cart "AddItem" slice, end to end

Slice (from a `verify-event-model` GO): *a shopper adds an item to an existing cart; the cart summary
reflects the new item count.* Entity `CartEntity` already exists; command `AddItem` produces event
`ItemAdded`; query `CartSummary` exposes `itemCount`.

1. **① outer RED** — `write-hurl-e2e` writes `tests/scenarios/add-item.hurl` (the §7 hurl). `neo test`
   boots the app; the `POST /commands/add-item` returns **404** (not wired). Red.

2. **② acceptance RED** — `write-feature-tests` writes `tests/Acceptance/AddItemSpec.hs` exercising
   `decide → update → combine` for the happy path. It **won't compile** (`AddItem`/`ItemAdded` don't
   exist). Red.

3. **③ inner RED** — `write-unit-tests` writes **one** decider assertion: "rejects adding an item to a
   cart that does not exist" (the §4 spec). Also won't compile yet. Red.

4. **④ DOMAIN** — `neohaskell-domain-modeling`: add the `ItemAdded` variant to `CartEvent`, ensure the
   `AddItem` command record exists, and stub `decide = panic "TODO: not implemented"`. `neo build`
   **compiles**. Re-run `neo test`: the decider spec now fails because the `panic` fires — the
   assertion-level red. (Entity already has `items`; if it didn't, `expand-entity` would add it
   add-only.)

5. **⑤ GREEN (reject rule)** — `implement-command`: give `decide` just enough to satisfy the one test —
   `Nothing -> Decider.reject "Cart not found!"`. The decider spec goes **green**. Loop back to ③ and
   add the next assertion ("accepts and emits ItemAdded when the cart exists and quantity > 0"),
   DOMAIN if needed, then GREEN the `acceptExisting` branch. Repeat until every decider rule is pinned.
   `implement-event-and-update-entity` adds the `update` `case` arm; `implement-query` fills
   `CartSummary.combine` so `itemCount` reflects the event, each driven by its own inner red test.

6. **⑥ GREEN (wire)** — `wire-feature`: `Service.command @AddItem` and the `App.hs` wiring. The command
   endpoint now answers 200, the query projects, and the **① hurl goes green** after its retry catches
   the eventually-consistent read.

7. **⑦ REFACTOR** — with the bar green, tidy names/helpers (no behavior change) and add the property
   replay spec: fold arbitrary `ItemAdded` sequences through `update` and assert `itemCount` never goes
   negative and equals the sum of quantities.

**Done** when `neo test` is all green — the pure decider/projection/outbound/property specs, the
in-domain acceptance spec, and the one hurl e2e — with every phase boundary respected. Then start the
next slice at ①.
