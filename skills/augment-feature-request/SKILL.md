---
name: augment-feature-request
description: >-
  Turns a vague NeoHaskell feature ask into a concrete, event-modeling-ready Feature Brief
  by running an Event Modeling DISCOVERY INTERVIEW (the 'and then what happens?' probing) —
  naming past-tense business facts (events), imperative commands, read models, automations,
  inbound timer/webhook triggers, actors, and reject rules. Use FIRST, before any coding or
  event-model.json editing, whenever a request is underspecified, hand-wavy, or phrased as a
  solution ('add a reservations feature', 'let users cancel', 'we need a dashboard') — even
  if the user never says 'event modeling' or 'brief'. Also use for one-time full-domain
  discovery on a greenfield project (no event-model.json / domain overview yet) and to write
  the domain overview. Produces a Feature Brief for event-modeling. Do NOT use to build the
  event-model.json itself (that is event-modeling) or to validate one (verify-event-model).
  Writes no Haskell and runs no neo commands.
metadata:
  model: opus
---

**This is NeoHaskell, not vanilla Haskell** — and the `.hs` extension is shared, so it is
easy to drift. This skill writes **no code at all**: your output is a Feature Brief in
plain business language. But the *downstream* skills that turn your brief into NeoHaskell
are driven by weak models that hallucinate vanilla Haskell, and they turn your names into
module names verbatim. So the discipline here is about the **words you choose** — events
are past-tense specific business facts, commands are imperative — not about syntax.

---

## Inputs / Outputs / Next

- **Input:** a vague or solution-shaped feature request, plus the project context (does an
  `event-model.json` with entities, or a `docs/domain-overview.md`, already exist?).
- **Output:** a **Feature Brief** (the template below) in business language. On a
  greenfield project, *also* a one-time `docs/domain-overview.md`.
- **Next skill:** `event-modeling` — it consumes the Feature Brief and appends a submodel
  + slices + command/event/query/integration nodes to `event-model.json`.

**Where this sits in the pipeline.** This is a **pre-cycle design** skill. The build order
is `augment-feature-request` → `event-modeling` → `verify-event-model` → then the per-slice
outside-in TDD cycle (hurl → feature tests → unit tests → domain modeling → implement →
wire). You do **not** do RED/DOMAIN/GREEN here; you produce the plan those phases execute.
The single most valuable thing you can do for the whole downstream chain is name the facts
well, because a vague event name here becomes a vague event stream forever.

**Model tier (opus).** The facilitation is genuinely reasoning-heavy — you are inferring a
timeline of facts, spotting fake automations, and choosing good names under ambiguity. In
Claude Code, delegate the interview + brief drafting to a sub-agent spawned with
`model: opus`. In hosts without sub-agents (Cursor, Codex), this is advisory — run it
inline; the method is identical.

---

## How to run it

### Step 0 — pick the discovery mode (hybrid)

Detect by **reading files**, never by running `neo`:

- Is there an `event-model.json` whose `entities` array is non-empty?
- Is there a written domain overview (e.g. `docs/domain-overview.md`)?

| What you find | Mode | Output |
| --- | --- | --- |
| Neither (greenfield) | **Full-domain discovery, once** | `docs/domain-overview.md` **and** then the Feature Brief for the asked feature |
| An overview and/or populated `event-model.json` | **Feature-scoped discovery** | Feature Brief only, extending existing entities |

Full-domain discovery is a single **broad** pass to map the entities (streams), the actors,
and each entity's headline lifecycle facts — not a deep model. Run it **once**; every later
feature is discovered onto that map. The overview template and the procedure are in
[`references/discovery-and-facilitation.md` §8](references/discovery-and-facilitation.md).

### Step 1 — run the facilitation loop

Anchor the goal, find the first fact, then walk the timeline. This is the whole technique;
the full question bank (by pattern) and naming heuristics are in the reference file.

1. **Anchor the goal** — "In one sentence, what should a person be able to accomplish?"
2. **Find the triggering fact** — "When it succeeds, what has become *true*?" → an **event**
   (past-tense, specific).
3. **Name the intent** — "What is being *asked for* that records that fact?" → a **command**
   (imperative). Is it creating something new, or acting on an existing thing?
4. **Walk forward** — "…and then what happens?" until "nothing." Each new fact is a slice.
5. **Walk the failure branch** — "What if it's rejected / cancelled / retried / the thing
   doesn't exist / already exists?" → **reject rules**, often extra events.
6. **Walk the view branch** — "Who needs to *see* this, and what do they see?" → **queries**.
7. **Walk the reaction branch** — "When this fact is recorded, does the system act on its
   own, and *only sometimes*?" → **automation** (event → condition → command).
8. **Walk the boundary** — "Does a schedule, webhook, or external system cause any of this?"
   → **translation** (inbound integration).
9. **Assign the actor** — for every command, "who may do this, and who is blocked?"

**Ask in 2–4 options, not open-ended.** A non-expert freezes on "how should this work?" and
a weak model invents. Offer concrete, mutually-exclusive choices, each tagged with the
pattern it implies, and let them pick or correct. See the reference §7 for the technique.

### Step 2 — write the Feature Brief

Fill this template. Every section maps to nodes the `event-modeling` skill will emit into
`event-model.json`, so the vocabulary (entity / command / event / query / integration
`inbound|outbound`) is deliberate. Placeholders like `Name` / `Entity` are fine.

```markdown
# Feature Brief — <FeatureName>

## Goal
<One sentence: what a person can accomplish that they couldn't before.>

## Entities
<List each stream this feature touches; mark NEW vs existing. Reuse existing names —
 do not spawn a parallel entity for something that already exists.>
- <Entity> — NEW | existing — lifecycle: <FactOpened> → <…> → <FactClosed>

## Slices
<One user-meaningful step per slice. Tag each with its pattern.>

### 1. <StepName>  (State Change)
- Actor / who may run: <role — own-thing-only or open>
- Command: <ImperativeVerb>  (creation | acts on existing)
- Event(s): <PastTenseSpecificFact>
- Reject when: <the rules that make the system say no>

### 2. <StepName>  (State View)
- Query: <ReadModelName>  — for <who>
- Fed by events: <Event>, <Event>

### 3. <StepName>  (Automation)
- Triggering event: <PastTenseFact>
- Condition: <the condition that makes it fire only sometimes>   ← required; no condition ⇒ fold into a State Change
- Command issued: <ImperativeVerb> → <ResultingFact>

### 4. <StepName>  (Translation — inbound)
- Inbound trigger: <nightly timer | webhook | external system>
- Command issued: <ImperativeVerb> → <ResultingFact>
- Condition: <what the inbound handler checks>

## Actors & authorization
- <Role>: <commands/queries they may run> (own-thing-only? open? system-only?)

## Open questions / assumptions
- <anything unresolved, with your assumed default stated>
```

A brief is **ready** when: every event has a cause (a command or an inbound integration),
every query names ≥1 feeding event, every automation states a condition, and every command
has an actor and a reject rule. Keep it to one feature — typically 1–6 slices.

---

## Naming: get the facts right at the source

The downstream verifier rejects bad names, so fix them here. **Events = past-tense specific
business facts; commands = imperative.** Full table in the reference §6.

| Reflex | Correct | Why |
| --- | --- | --- |
| `ProcessReservation`, `HandleReturn` (RPC / present-tense) | `BookReserved`, `BookReturned` | An event is a fact that *already happened*, not a function call |
| `ReservationUpdated`, `DataChanged` (vague) | `ReservationCancelled`, `ReservationExpired` | Say *what* changed, specifically |
| `Create…DTO`, `Save…`, `RowInserted` (mechanism) | name the outcome | Persistence/transport is not a business fact |
| `BookReservation` (noun) as a command | `ReserveBook` | A command is an imperative verb |
| Creation facts feared as "CRUD" | `CartCreated`, `MemberRegistered`, `LoanOpened` | Creation facts are **good** — the smell is `Update*`/`Delete*`/RPC echoes, not "Created" |

---

## DO / DON'T

| Don't (the reflex) | Do (facilitation-correct) |
| --- | --- |
| Jump straight to Haskell types, records, or `data` declarations | Stay in business language; this skill emits **no code** |
| Run `neo inspect` / `neo build` / any `neo` command to "check" | Detect discovery mode by **reading** `event-model.json` / `docs/domain-overview.md` |
| Edit `event-model.json` here | That's the `event-modeling` skill's job — you hand it a brief |
| Make architecture / tech / storage / transport decisions | Model **facts and behavior**; leave persistence, HTTP, DB out of the brief |
| Name events present-tense or RPC-shaped (`ProcessX`, `CreateXDTO`) | Past-tense specific facts (`XPlaced`, `XReserved`, `XReturned`) |
| Name events vaguely (`CartUpdated`, `StatusChanged`) | Say exactly what changed (`ItemRemovedFromCart`) |
| Call a command a noun (`ItemAdder`) | Imperative verb (`AddItem`) |
| Model an "automation" that fires **every** time | That's one State Change with two effects — only conditional reactions are automations |
| Draw a read-model → command arrow ("when the dashboard shows X, do Y") | Put the decision in the command's rules over the **event stream** |
| Run one broad full-domain pass per feature | Full-domain discovery is **once** (greenfield); features are discovered onto the existing map |
| Interrogate with open-ended questions | Offer 2–4 concrete options per question |
| Spawn a second `Cart`-shaped entity for a cart feature | Reuse the existing entity; add new events/commands/queries onto it |

---

## Verify

There is nothing to compile here — the real verification is **downstream**. Before handing
off, self-check the brief against the readiness bar, then let the chain confirm it:

1. **Self-check (this skill):** every event has a cause; every query lists feeding events;
   every automation has a condition; every command has an actor + a reject rule; all names
   pass the naming table above; entities reuse existing names.
2. **`event-modeling`** turns the brief into `event-model.json` (schema-compliant append).
3. **`verify-event-model`** gates naming, referential integrity, and best practices — this
   is where a sloppy brief gets caught, so it is cheaper to name well now.
4. Eventually the slices are built and `neo build` / `neo test` prove the whole thing — but
   that is many skills downstream, not here.

If any self-check item fails, ask one more round of 2–4-option questions rather than guessing.

For the full question bank, naming heuristics, the multiple-choice technique, the
domain-overview template, and a fully worked `Library` example, read
[`references/discovery-and-facilitation.md`](references/discovery-and-facilitation.md).
