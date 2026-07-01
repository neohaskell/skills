# Discovery & Facilitation — Event Modeling for a Feature Brief

Reference material for `augment-feature-request`. Load this when you actually run an
interview — the `SKILL.md` body is the short spine; this file is the full question bank,
the naming heuristics, and a worked example.

> **Attribution / license.** Adapted (MIT) from the Event Modeling methodology —
> Adam Dymitruk's *eventmodeling.org* and Martin Dilger's *Understanding Eventsourcing* —
> and from jwilger's MIT-licensed `event-modeling` skill. Retargeted from generic
> whiteboard/PRD output to a **Feature Brief** that feeds the NeoHaskell `event-modeling`
> skill (which emits `event-model.json`). The SDLC-plugin machinery (red/green agents,
> task CLIs, PR orchestration, personas) is **not** adopted — only the portable
> discovery/facilitation method.

## Table of contents

1. [Why discovery is events-first](#1-why-discovery-is-events-first)
2. [Two discovery modes (the hybrid rule)](#2-two-discovery-modes-the-hybrid-rule)
3. [The four patterns you are hunting for](#3-the-four-patterns-you-are-hunting-for)
4. [The core facilitation loop: "and then what happens?"](#4-the-core-facilitation-loop-and-then-what-happens)
5. [The question bank](#5-the-question-bank)
6. [Naming heuristics (good fact vs smell)](#6-naming-heuristics-good-fact-vs-smell)
7. [Ask in 2–4 options, not open-ended](#7-ask-in-24-options-not-open-ended)
8. [Full-domain discovery + the domain-overview template](#8-full-domain-discovery--the-domain-overview-template)
9. [Feature-scoped discovery](#9-feature-scoped-discovery)
10. [Worked example — Library "reserve a book"](#10-worked-example--library-reserve-a-book)
11. [When to stop; anti-patterns](#11-when-to-stop-anti-patterns)

---

## 1. Why discovery is events-first

Event Modeling describes a system as a **timeline of facts**. Everything else hangs off
those facts:

- A **command** is the intent that, when accepted, records one or more **events**.
- A **read model / query** is a view rebuilt by folding events.
- An **automation** reacts to an event and (conditionally) issues another command.
- A **translation** turns something arriving from *outside* into an internal command.

So the most productive move in an interview is to get the person to name the **business
facts** — the things that become irreversibly true — and then walk the timeline forward
and backward from there. Data models, screens, and tech choices are downstream of the
facts; if you start there you model the *nouns* and miss the *behavior*.

You produce **no code and run no `neo` commands.** Your artifact is a Feature Brief in
business language. The reason to still respect NeoHaskell's naming discipline (past-tense
specific facts, imperative commands) is that a *weak* downstream model turns your names
into module names verbatim — a vague or RPC-shaped name there becomes a vague or
RPC-shaped event stream forever.

## 2. Two discovery modes (the hybrid rule)

Detect the situation by **reading files** (never by running `neo`):

- Is there an `event-model.json` with a non-empty `entities` array?
- Is there a written domain overview (e.g. `docs/domain-overview.md`)?

| Situation | Mode | Extra output |
| --- | --- | --- |
| Neither exists (new / greenfield project) | **Full-domain discovery**, once | Also write a `domain-overview.md` |
| An overview and/or populated `event-model.json` already exists | **Feature-scoped discovery** | Feature Brief only |

Full-domain discovery is *not* "model the whole app in detail." It is a single, broad
pass to establish the **entities (streams)**, the **actors**, and the **major lifecycle
events per entity** — a map. Every later feature is discovered *onto* that map. Running
the broad pass more than once produces contradictory maps; run it once, then extend.

## 3. The four patterns you are hunting for

Each answer you gather should slot into one of these four shapes (they are exactly the
shapes the downstream `event-model.json` can express, so naming them keeps you honest):

| Pattern | Shape | What to ask for |
| --- | --- | --- |
| **State Change** | Command → Event(s) | An intent + the fact(s) it records |
| **State View** | Event(s) → Read model | What someone must *see* + which events feed it |
| **Automation** | Event → *(condition)* → Command → Event | A reaction that fires **only under a condition** |
| **Translation** | External (timer/webhook) → inbound integration → Command | Something *outside* pushing in |

Two rules fall out of the schema and are worth enforcing while you interview:

- **Commands never read a read model to decide.** If someone says "when the dashboard
  shows X, do Y," the decision belongs in the command's own rules over the event stream,
  not in a read-model→command arrow. Rephrase it as a State Change or a conditional
  Automation.
- **A true Automation is conditional.** "Every time the loan is opened we also send a
  receipt, always" is not an automation — it is one State Change slice with two effects.
  An automation earns its own nodes only when it fires **sometimes** (e.g. *only* overdue
  loans get a notice). Probe the condition explicitly; if there is none, collapse it.

## 4. The core facilitation loop: "and then what happens?"

This is the whole technique. Pick the user goal, find the first fact, then walk:

1. **Anchor the goal.** "In one sentence, what should a person be able to accomplish?"
2. **Find the triggering fact.** "When they do that and it succeeds, what has become
   *true* that wasn't true before?" → an **event** (past-tense).
3. **Name the intent.** "What is the person (or system) *asking for* that produces that
   fact?" → a **command** (imperative).
4. **Walk forward:** "…and then what happens?" Repeat until the person says "nothing —
   that's the end." Each new fact is another event/slice.
5. **Walk the failure branch:** "What if that request is *rejected*? What if it's
   *cancelled*, *retried*, *times out*, or the thing doesn't exist / already exists?"
   → **reject rules** and often extra events.
6. **Walk the view branch:** at each fact, "who needs to *see* that this happened, and
   what do they see?" → **read models / queries**.
7. **Walk the reaction branch:** "when this fact is recorded, does the system do anything
   *by itself* — and only sometimes?" → **automations** (event → condition → command).
8. **Walk the boundary:** "does anything *outside* the app cause any of this — a
   schedule, a webhook, another system?" → **translations** (inbound integrations).
9. **Assign the actor:** for every command, "who is allowed to do this, and who is *not*?"

Keep looping steps 4–9 until the timeline is closed on both the happy path and the obvious
failure paths. You are done for a feature when every fact has a cause (command or
integration), every view names its feeding events, and every command has an actor and a
reject rule.

## 5. The question bank

Grouped by what you are trying to surface. Ask a few at a time, in the person's own
business language.

### Goal & scope
- "What should a person be able to accomplish that they can't today?"
- "Which existing thing does this touch — a `Cart`, a `Loan`, a new kind of thing?"
- "What's explicitly **out** of scope for this feature?"

### Events (facts)
- "When it works, what has become permanently true?"
- "…and then what happens? Keep going until nothing does."
- "Is that one fact, or several? (‘Checked out 3 books’ is usually 3 facts.)"
- "Would you ever want to look back and *know that this exact thing happened*?" (yes ⇒ event)

### Commands (intents)
- "What is the person asking the system to do to produce that fact?"
- "Is this creating something brand new, or acting on something that already exists?"
  (creation vs. update — shapes the event name and the accept path downstream)

### Read models (views)
- "To decide to do this, what does someone need to *see* first?"
- "After it happens, who checks that it worked, and on what screen/list?"
- "Which facts does that view summarize?"

### Automations (conditional reactions)
- "When [fact] is recorded, does the system react on its own?"
- "Does it react **every** time, or only when some condition holds?" (only-sometimes ⇒
  automation; always ⇒ fold it into the State Change)
- "What command does that reaction issue, and on which thing?"

### Translations (inbound / external)
- "Does anything happen on a **schedule** (nightly, every hour)?" ⇒ inbound timer
- "Does an **external system or webhook** ever push data or an instruction in?" ⇒ inbound
- "Is that external thing the *cause*, with no earlier click behind it?" (confirms inbound)

### Actors & authorization
- "Who initiates this — a specific role, any logged-in user, an anonymous visitor, or the
  system itself?"
- "Who must be **blocked** from doing it?"
- "Can someone act only on their *own* thing, or across everyone's?" (owner-only vs open)

### Reject & edge cases
- "What makes the system say *no* to this request?"
- "What if the thing doesn't exist yet? What if it already exists?"
- "What if it's cancelled or reversed later — is *that* also a fact worth recording?"
- "What are the limits — quantities, states it can't be in, duplicates?"

## 6. Naming heuristics (good fact vs smell)

The downstream verifier rejects bad names, so get them right at the source. **Events are
past-tense, specific business facts; commands are imperative.**

| Kind | Good | Smell — rephrase |
| --- | --- | --- |
| Event (creation fact) | `CartCreated`, `MemberRegistered`, `LoanOpened`, `AccountOpened` | — creation facts are **good**; the word "Created" is not the smell |
| Event (specific fact) | `ItemAddedToCart`, `ItemRemovedFromCart`, `OrderPlaced`, `BookReturned`, `StockReserved` | — |
| Event — present-tense / RPC echo | — | `ProcessPayment`, `CreateOrderDTO`, `HandleReturn` → name the *fact*: `PaymentCaptured`, `OrderPlaced`, `BookReturned` |
| Event — vague | — | `CartUpdated`, `DataChanged`, `StatusUpdated` → say *what* changed: `ItemRemovedFromCart`, `LoanMarkedOverdue` |
| Command | `AddItem`, `ReserveBook`, `ReturnBook`, `CancelReservation` | `ItemAdder`, `BookReservation` (noun) → make it an imperative verb |

Heuristic: an event is a fact you could **write in a history book** — it already happened,
it names a specific business outcome, and you'd never need to "un-happen" it (a reversal
is its own new fact, e.g. `ReservationCancelled`). If a proposed event name reads like a
function call or a table write (`Update…`, `Save…`, `…DTO`, `Process…`), it's describing
mechanism, not a fact — rename it after the outcome.

## 7. Ask in 2–4 options, not open-ended

Open questions ("how should reservations work?") make a non-expert freeze and make a weak
model invent. Offer concrete, mutually-exclusive options and let them pick or correct:

> **Example.** When a reserved book is returned, what should happen to the reservation?
> 1. The next member in line is automatically notified (an **automation** — only fires if
>    a queue exists).
> 2. Nothing automatic — a librarian looks at the queue and hands it over (a **read model**
>    only).
> 3. The reservation is auto-converted into a loan for the next member (a stronger
>    automation).
>
> *(Pick one, or tell me it's different.)*

Each option is tagged with the pattern it implies, so the person's choice directly
determines the slice shape. Prefer options that surface a **decision the person actually
has to make**, not trivia the request already answers.

## 8. Full-domain discovery + the domain-overview template

Run this **once**, on a greenfield project, before the first Feature Brief. Goal: a map of
the streams and their lifecycles — broad, not deep. Use the loop in §4 but stay at the
level of "what are the main things, and what are the headline facts in each thing's life?"

Write the result to `docs/domain-overview.md` (a planning artifact — **not** read by
`neo`, not `event-model.json`). Template:

```markdown
# Domain Overview — <ProjectName>

_Discovery map. Planning artifact only; the machine-readable model is event-model.json._

## Actors
- <Role> — <what they do>
- System — <timers / external systems that act on their own>

## Entities (streams)
Each entity owns a sequence of events (its stream).

### <EntityName>
- **Purpose:** <one line — what this thing is>
- **Lifecycle facts (events):** <Opened> → <…> → <Closed>   (past-tense, specific)
- **Key rules:** <the invariants that make a command reject>

### <EntityName>
- ...

## Bounded contexts / chapters (optional)
- <ContextName> — <which entities/slices cohere here>

## Known integrations
- Inbound: <timer/webhook> — <what it triggers>
- Outbound: <notification/export> — <which fact triggers it>

## Open questions
- <anything the discovery pass could not resolve>
```

## 9. Feature-scoped discovery

Once an overview (or a populated `event-model.json`) exists, discover **onto** it:

1. Read the overview / entities so you reuse existing names instead of inventing parallel
   ones. If the feature extends `Cart`, the brief must say so and must not spawn a second
   cart-shaped entity.
2. Run the §4 loop scoped to just this feature's slices.
3. Only introduce a **new** entity if the feature genuinely tracks a new lifecycle; prefer
   adding events/commands/queries onto an existing entity.
4. Produce the Feature Brief (template in `SKILL.md`). Do not touch the overview unless the
   feature adds a brand-new entity, in which case append its stub to the overview.

## 10. Worked example — Library "reserve a book"

*(Illustrative `Library` domain — `BookTitle` / `Member` / `Loan` — not copied from a
compiling source. Chosen because it's neutral.)*

**Vague request:** "Members should be able to reserve books that are checked out."

Walking the loop:

- **Goal:** a member puts a hold on a title that has no available copy, and gets it when
  one frees up.
- **First fact:** "When a member reserves, what's true?" → `BookReserved` (specific fact).
  Existing entity? A reservation has its own lifecycle (placed → fulfilled/cancelled/
  expired) → **new entity `Reservation`**, referencing `BookTitle` + `Member`.
- **Command:** `ReserveBook` (imperative, creation — a new reservation stream).
- **Reject rules:** member has unpaid fines? a copy is *currently* available (then just
  borrow, don't reserve)? member already holds a reservation for this title? over the
  per-member reservation cap?
- **…and then what happens?** A copy is returned → is the reserver notified? Options
  offered (see §7) → they pick "auto-notify the next in line, only if a queue exists" →
  **Automation:** `BookReturned` → *(condition: an active reservation exists for that
  title)* → `NotifyNextReserver`/produces `ReserverNotified`.
- **View branch:** a librarian needs the **queue** per title → read model
  `ReservationQueue`; a member needs **their** holds → `MemberReservations`.
- **Boundary branch:** reservations expire if not picked up in 48h → a **nightly timer**
  (inbound translation) → `ExpireStaleReservations` → `ReservationExpired`.
- **Actors:** `ReserveBook` — the member, owner-only (own card); `NotifyNextReserver` —
  system; queue view — librarian.

The resulting Feature Brief (abridged) fills the `SKILL.md` template like this:

```markdown
# Feature Brief — ReserveBook

## Goal
Let a member place a hold on a title with no available copy, and be first in line when one returns.

## Entities
- Reservation — NEW — lifecycle: BookReserved → (ReserverNotified) → ReservationFulfilled | ReservationCancelled | ReservationExpired
- BookTitle — existing (referenced)
- Member — existing (referenced)

## Slices
### 1. Reserve a book  (State Change)
- Actor / who may run: the member, own card only (owner-only)
- Command: ReserveBook (creation)
- Event(s): BookReserved
- Reject when: a copy is currently available; member already holds this title; member over reservation cap; member has blocking fines

### 2. See the queue for a title  (State View)
- Query: ReservationQueue  — for librarians
- Fed by events: BookReserved, ReservationCancelled, ReservationExpired, ReservationFulfilled

### 3. See my reservations  (State View)
- Query: MemberReservations — owner-only
- Fed by events: BookReserved, ReserverNotified, ReservationFulfilled, ReservationExpired

### 4. Notify next reserver on return  (Automation)
- Triggering event: BookReturned
- Condition: an active reservation exists for that title  ← makes it a real automation
- Command issued: NotifyNextReserver → ReserverNotified

### 5. Expire stale reservations  (Translation — inbound timer)
- Inbound trigger: nightly scheduler
- Command issued: ExpireStaleReservations → ReservationExpired
- Condition: reservation older than 48h and not fulfilled

## Actors & authorization
- Member: ReserveBook (own card), MemberReservations (own)
- Librarian: ReservationQueue
- System: NotifyNextReserver, ExpireStaleReservations

## Open questions / assumptions
- Reservation cap per member? (assumed 5)
- Does a fulfilled reservation auto-create a Loan, or just notify? (assumed: notify only)
```

That brief is *event-modeling-ready*: every event has a cause, every query names its
feeding events, both automations state a condition, and each command has an actor.

## 11. When to stop; anti-patterns

Stop when the happy path **and** the obvious failure paths are closed — not when the
domain is "complete." A Feature Brief is one feature, typically 1–6 slices.

Anti-patterns to catch in yourself:

- **Modeling nouns/CRUD.** `Reservation` with `Create/Read/Update/Delete` is a data model,
  not a behavior model. Model the *facts* (`BookReserved`, `ReservationCancelled`).
- **Inventing infrastructure as facts.** "SavedToDatabase," "RowUpdated," "MessagePublished"
  are mechanism, not business facts — leave persistence/transport out of the brief.
- **Fake automations.** Unconditional "and also do X every time" is one State Change with
  two effects, not an automation.
- **Read-model→command reasoning.** Move the decision into the command's rules over the
  event stream.
- **Writing Haskell or running `neo`.** That's the downstream skills' job; stay in business
  language.
- **Open-ended interrogation.** If you've asked more than a couple of open questions
  without options, switch to 2–4-option questions (§7).
