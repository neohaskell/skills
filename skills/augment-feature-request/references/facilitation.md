# A product decision requires further discovery

Use only the branch needed by the task. Resolve the application revision and capabilities through [nh-app-context](../../nh-app-context/SKILL.md) before adapting API examples. The existing consumer layout and compatible API guide determine the actual imports, markers, and commands.

## How to run it

### Step 0 — pick the discovery mode (hybrid)

Detect by **reading files**, never by running `neo`:

- Is there an `event-model.json` whose `entities` array is non-empty?
- Is there a written domain overview (e.g. `docs/domain-overview.md`)?

| What you find | Mode | Output |
| --- | --- | --- |
| Neither (greenfield) | **Scoped domain discovery** | A temporary Feature Brief; durable knowledge goes in the existing domain documents |
| An overview and/or populated `event-model.json` | **Feature-scoped discovery** | Feature Brief only, extending existing entities |

When the task requires a new domain map, discovery is a scoped pass to map the entities (streams), the actors,
and each entity's headline lifecycle facts — not a deep model. Reuse the application's existing glossary/ADRs or domain map instead of creating a parallel source. The overview template and the procedure are in
[`references/discovery-and-facilitation.md` §8](discovery-and-facilitation.md).

### Step 1 — run the facilitation loop

Read the available code, tests, existing domain documentation, and request first. Answer the prompts from evidence; ask the user only for unresolved product decisions. Anchor the goal, find the first fact, then walk the timeline. This is the whole technique;
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

When a decision requires the user, ask one short question with concrete options where helpful. A non-expert freezes on "how should this work?" and
a weak model invents. Offer concrete, mutually-exclusive choices, each tagged with the
pattern it implies, and let them pick or correct. See the reference §7 for the technique.

### Step 2 — write the Feature Brief

Fill this template. Every section maps to nodes the `event-modeling` skill will emit into
`event-model.json`, so the vocabulary (entity / command / event / query / integration
`inbound|outbound`) is deliberate. Use discovered names in the actual brief; placeholders below only illustrate its shape. Store the brief in temporary task state, outside reusable skill resources. If UI is requested, include entry, navigation, form, loading, empty, error, permission, and completion states where applicable.

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

Improve names here, separating clarity advice from functional ambiguity. A naming preference alone does not block a valid model. **Events = past-tense specific
business facts; commands = imperative.** Full table in the reference §6.

| Reflex | Correct | Why |
| --- | --- | --- |
| `ProcessReservation`, `HandleReturn` (RPC / present-tense) | `BookReserved`, `BookReturned` | An event is a fact that *already happened*, not a function call |
| `ReservationUpdated`, `DataChanged` (vague) | `ReservationCancelled`, `ReservationExpired` | Say *what* changed, specifically |
| `Create…DTO`, `Save…`, `RowInserted` (mechanism) | name the outcome | Persistence/transport is not a business fact |
| `BookReservation` (noun) as a command | `ReserveBook` | A command is an imperative verb |
| Creation facts feared as "CRUD" | `CartCreated`, `MemberRegistered`, `LoanOpened` | Creation facts are **good** — the smell is `Update*`/`Delete*`/RPC echoes, not "Created" |

---

