# Domain Modeling Principles (NeoHaskell)

Reference for the `neohaskell-domain-modeling` skill — the reasoning behind the fast-path
DO/DON'T in `SKILL.md`. Read this when a model is non-obvious: how to choose types so that wrong
values cannot be built, where to put validation, and how the DOMAIN phase hands off to GREEN.

> **Attribution & licence.** Adapted from John Wilger's `domain-modeling` skill (MIT-licensed) and
> the type-driven-design tradition it draws on — Yaron Minsky's "make illegal states
> unrepresentable" and Alexis King's "Parse, don't validate". This adaptation is **retargeted to
> NeoHaskell idioms** (the `Core` prelude, `Result`/`Maybe`, `Natural`/`Decimal`/`Redacted`/`Uuid`,
> algebraic data types, and `panic "TODO"` stubs) and is distributed under the same MIT terms. The
> original SDLC-plugin machinery (red/green sub-agents, task CLI, personas) is **not** adopted; only
> the portable modelling principles are.

## Table of contents

1. [The one job of the DOMAIN phase](#1-the-one-job-of-the-domain-phase)
2. [Principle 1 — Make illegal states unrepresentable](#2-principle-1--make-illegal-states-unrepresentable)
3. [Principle 2 — Parse, don't validate](#3-principle-2--parse-dont-validate)
4. [Principle 3 — Types first (let the compiler drive)](#4-principle-3--types-first-let-the-compiler-drive)
5. [Principle 4 — Kill primitive obsession](#5-principle-4--kill-primitive-obsession)
6. [Principle 5 — Smart constructors and encapsulation](#6-principle-5--smart-constructors-and-encapsulation)
7. [Principle 6 — Total functions and exhaustiveness](#7-principle-6--total-functions-and-exhaustiveness)
8. [Worked refactor — from primitive soup to a domain model](#8-worked-refactor--from-primitive-soup-to-a-domain-model)
9. [Choosing the right NeoHaskell wrapper](#9-choosing-the-right-neohaskell-wrapper)
10. [How DOMAIN hands off to GREEN](#10-how-domain-hands-off-to-green)

---

## 1. The one job of the DOMAIN phase

In the outside-in loop (**RED → DOMAIN → GREEN → REFACTOR**), a failing test names types, fields, and
functions that do not exist yet. DOMAIN's only job is to **introduce exactly those types so the code
compiles**, with bodies stubbed. No behaviour is implemented here.

Why the split matters: designing the *types* separately from the *logic* forces you to answer "what
shape is this data, and what values are legal?" before "how do I compute the answer?". A good type
answers the first question so thoroughly that the second becomes almost mechanical — and often makes
whole classes of test unnecessary, because the compiler already rejects the bad case.

The discipline is: **add the type, keep the body a stub.** Stubs are `panic "TODO: not implemented"`
for pure/`Task` bodies (`panic :: Text -> a`, so it fits any return type) and `Integration.none` for
an outbound `handleEvent` (a `panic` in a pure handler crashes the dispatcher when that event
fires). NeoHaskell has no `todo`.

---

## 2. Principle 1 — Make illegal states unrepresentable

If a value is illegal in the domain, arrange the types so it **cannot be constructed**. The compiler
then enforces the rule everywhere, for free, forever — no runtime check, no test, no code review.

**Enum over stringly-typed status.** A `status :: Text` can hold `"bananas"`; every reader must
defensively handle the impossible. A sum type cannot:

```haskell
-- Illegal states possible:
--   data Loan = Loan { status :: Text }      -- "bananas" type-checks

-- Illegal states impossible (grounded pattern: core/core/Log.hs Level):
data LoanStatus = OnLoan | Returned | Overdue
  deriving (Eq, Show, Ord, Generic)
```

**Sum-of-records over a bag of `Maybe`s.** When fields only make sense together, a record full of
`Maybe` allows contradictory combinations (returned *and* still on loan; neither). Model each legal
shape as its own constructor carrying exactly its data:

```haskell
-- Contradictions representable:
--   data Loan = Loan { returnedAt :: Maybe Timestamp, dueDate :: Maybe Timestamp }
--   -- both Nothing? both Just? what does that mean?

-- Each case carries exactly what it needs, nothing it doesn't:
data LoanState
  = Active   { dueDate :: Uuid }        -- illustrative fields
  | Closed   { returnedAt :: Uuid }
  deriving (Eq, Show, Generic)
```

**Non-negative counts.** A quantity of `-3` books is nonsense. `Natural Int` (constructor hidden;
built only via `makeNatural`/`makeNaturalOrPanic`) makes the nonsense unconstructible — this is why
the real `testbed` `CartItem` field is `amount :: Natural Int`, not `amount :: Int`.

---

## 3. Principle 2 — Parse, don't validate

*Validation* checks a value and throws it back unchanged, so every later step must check again — and
one forgotten check is a bug. *Parsing* checks a value **once** and returns a **new type** that
carries the proof. After parsing, the type *is* the guarantee; nothing downstream re-validates.

In NeoHaskell the parse boundary is a **smart constructor** that returns `Result`/`Maybe`:

```haskell
-- Parse: Text -> a validated type. The Isbn type is proof of a valid ISBN.
makeIsbn :: Text -> Result Text Isbn
```

Contrast with validation, which leaves you holding the same untrusted `Text`:

```haskell
-- Validation smell: returns Bool, value stays a raw Text forever after.
isValidIsbn :: Text -> Bool
```

The wire boundary counts too. A JSON `FromJSON` for a value object should run the smart constructor,
not trust the bytes. NeoHaskell's `Decimal` does exactly this — its `parseJSON` calls `parseDecimal`
and *fails* on bad input (`core/decimal/Decimal.hs`). Follow that model with `Json.withText` +
`Json.yield`/`Json.fail` (see `SKILL.md`'s `Isbn` template). An **empty** Generic `FromJSON` on a
value object silently trusts the wire and defeats the point.

Where to parse: **at the edges** — command JSON decoding, config loading, inbound integration
payloads. The core of the domain then deals only in already-valid types.

---

## 4. Principle 3 — Types first (let the compiler drive)

Write the type signatures before the bodies. In a compiled language the RED signal is frequently a
**type error** ("not in scope", "no instance", "no such field"), which is a precise, free to-do
list: it tells you exactly which type is missing. DOMAIN answers that list — and *only* that list —
so the compiler goes quiet and the test can finally run and fail on its assertion.

Two habits make this work:

- **Signature, then stub.** `decide :: BorrowBook -> Maybe LoanEntity -> RequestContext -> Decision
  LoanEvent` with body `panic "TODO: not implemented"` compiles and documents intent.
- **Introduce the minimum.** Add the field the test names; do not speculatively add three more.
  Speculative types are untested weight and often wrong.

This is also why you resist writing logic in DOMAIN: the moment you compute a real answer you are in
GREEN, and you have skipped the "does it even compile?" checkpoint that keeps the loop tight.

---

## 5. Principle 4 — Kill primitive obsession

"Primitive obsession" is modelling domain concepts with `Int`, `Float`, `Text`, and `Bool` because
they are at hand. The costs: illegal values slip through, units get mixed (cents vs dollars, id of
the wrong entity), and meaning lives in variable names instead of types.

The fix is a thin wrapper per concept. NeoHaskell ships the common ones:

| Primitive smell | Domain type | Guarantee bought |
|---|---|---|
| `Int` for a count | `Natural Int` | never `<= 0` |
| `Float` for money | `Decimal` | exact fixed-point; no rounding drift |
| `Text` for an id | `Uuid` | well-formed identity, generated not typed |
| `Text` for a secret | `Redacted Text` | absent from `Show`/logs; no `ToJSON` |
| `Text`/`Bool` for a state | an enum sum type | only legal states exist |

For anything domain-specific (ISBN, email, slug), a `newtype` with a hidden constructor and a smart
constructor gives the same benefit — see Principle 5.

---

## 6. Principle 5 — Smart constructors and encapsulation

A **smart constructor** is a function that is the *only* way to build a value, so it can enforce an
invariant that the type then carries. NeoHaskell's own wrappers are built this way:

- `Natural` — constructor unexported; built via `makeNatural :: n -> Maybe (Natural n)` (or
  `makeNaturalOrPanic`). (`core/core/Basics.hs`)
- `Uuid` — `newtype Uuid = Uuid UUID` with the constructor unexported; built via `Uuid.generate` or
  `Uuid.fromText :: Text -> Maybe Uuid`. (`core/core/Uuid.hs`)
- `Decimal` — built via `Decimal.decimal`, `Decimal.fromCents`, `Decimal.parseDecimal`.
  (`core/decimal/Decimal.hs`)

To build your own, **hide the data constructor** by exporting the type without `(..)`:

```haskell
module Library.Loan.Isbn (Isbn, makeIsbn, toText) where   -- `Isbn`, not `Isbn (..)`
```

Now `makeIsbn` is the sole entrance and can guarantee the invariant. Expose a reader (`toText`) for
when the raw value is genuinely needed. Prefer `Result Err a` over `Maybe a` when the *reason* for
rejection matters to the caller (it usually does at a boundary); `Maybe` is fine for a
one-bit "valid or not". Either way the error is the **first** type parameter and the constructors are
`Result.Ok` / `Result.Err` — never `Either`/`Left`/`Right`.

---

## 7. Principle 6 — Total functions and exhaustiveness

A **total** function returns a valid result for every input of its type — no partial patterns, no
hidden `error`. Good types make totality natural: once the input type excludes the bad cases, the
function has nothing to crash on.

- **Exhaustive `case`.** The entity `update` fold and the query `combine` must handle every
  constructor. NeoHaskell's style favours a single `case event of …` with a branch per event; adding
  a new event variant then produces a compiler warning at every non-exhaustive fold — a free
  reminder. (See `implement-event-and-update-entity`.)
- **No partiality via primitives.** A function taking `Natural Int` need not guard against zero; the
  type already did. This is the payoff of Principles 1 and 4 compounding.
- **Stubs are honest partiality, temporarily.** A DOMAIN stub *is* partial (`panic "TODO"`), and
  that is fine — the failing test proves it is not yet real. GREEN removes the partiality.

---

## 8. Worked refactor — from primitive soup to a domain model

Start (primitive-obsessed; several illegal states representable):

```haskell
data BorrowBook = BorrowBook
  { memberId :: Text     -- an id as free text
  , copies   :: Int      -- could be 0 or -5
  , status   :: Text     -- could be "wat"
  }
```

Refactored (each concept has a type that admits only legal values):

```haskell
data BorrowBook = BorrowBook
  { memberId :: Uuid          -- identity, not free text
  , copies   :: Natural Int   -- guaranteed > 0
  }
  deriving (Generic, Typeable, Show)
-- `status` is gone from the *command*: a borrow request has no status; status
-- is a property of the resulting Loan entity, modelled by the LoanStatus enum.
```

What the refactor bought, before a single line of logic:

- `memberId` can no longer be `""` or `"todo"`; it is a `Uuid`.
- `copies` can no longer be `0` or negative; the smart constructor behind `Natural` refused it at the
  boundary.
- The impossible "borrow request with status `Overdue`" simply cannot be expressed — the field does
  not exist on the command. Status belongs to the `Loan` entity and is an enum.

Three test cases (empty id, non-positive copies, bogus status) just evaporated: the compiler now
enforces what they asserted. That is the leverage of modelling first.

---

## 9. Choosing the right NeoHaskell wrapper

A quick decision guide for the DOMAIN phase:

- **Is it a whole-number count/quantity that must be positive?** → `Natural Int`.
- **Is it money or a value needing exact decimals?** → `Decimal` (never `Float`; divide with
  `Decimal.divide`, not `/`).
- **Is it an identity?** → `Uuid` (generate in `decide` via `Decider.generateUuid`; parse external
  ids with `Uuid.fromText`).
- **Is it a secret / PII?** → `Redacted Text` (no `ToJSON`, no `Eq`, hidden in `Show`).
- **Is it one of a fixed, known set of states?** → an enum sum type with empty `Json` instances.
- **Is it a domain string/number with an invariant (ISBN, email, slug, percentage)?** → a `newtype`
  with a hidden constructor + a smart constructor returning `Result`.
- **Is it a plain record with no invariant beyond its field types?** → a record `deriving (Generic)`
  with empty `Json` instances (see `neohaskell-records-and-json`).

When in doubt, prefer the more specific type. It costs one `newtype` and buys compiler-enforced
correctness across the whole codebase.

---

## 10. How DOMAIN hands off to GREEN

DOMAIN is complete when:

1. Every type, field, value object, and enum the red test names **exists**.
2. Every new function has a **real signature** and a **stub body** (`panic "TODO: not implemented"`,
   or `Integration.none` for an outbound `handleEvent`).
3. `neo build` **compiles**.
4. The red test now fails on its **assertion** (e.g. `shouldBe`), not on a type/scope error.

At that point the baton passes to the GREEN skills — `implement-command`,
`implement-event-and-update-entity`, `implement-query`, `implement-integration` — which touch only
the **bodies**, replacing each stub with real logic until the assertion passes. Do not let GREEN
work leak back into DOMAIN or vice versa: the phase boundary is what keeps the loop fast and is
checked by `neohaskell-code-review`.
