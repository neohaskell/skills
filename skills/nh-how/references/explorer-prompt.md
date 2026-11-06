> Adapted for consumer applications from the public NeoHaskell project.

# Explorer Prompt Template

Build each explorer subagent's prompt from this template. Fill in the placeholders.

---

When other explorers are assigned, they own different slices of the same question. Focus on your assigned angle. Investigate the affected consumer components, actual callers, and revision-compatible API guidance without editing files. Framework source is optional supporting evidence for the matching revision, not a required checkout or the exclusive search scope.

For local Haskell navigation, resolve the installed `nh-how/scripts/codemap.py` path and run it from the chosen component, or set `CODEMAP_ROOT` to that component. These paths illustrate installation at the consumer Git root:

    python3 .agents/skills/nh-how/scripts/codemap.py map TOPIC
    python3 .agents/skills/nh-how/scripts/codemap.py symbol NAME
    python3 .agents/skills/nh-how/scripts/codemap.py callers MODULE.SYMBOL
    python3 .agents/skills/nh-how/scripts/codemap.py api "TYPE TEXT"

Check each result against current source. Caller results are lexical candidates, not a complete call graph. API results are literal signature matches, not type unification.

## Question

> {QUESTION}

## Your Exploration Angle

{EXPLORATION_ANGLE}

## Output

### Components Found
The key types, services, functions, modules, typeclasses, instances, and abstractions relevant to your angle. For each: name, file path with relevant line references, and a one-sentence description of its role. For a service represented as a record of functions, identify its operations, the constructor that supplies them, and the dependencies captured by those implementations.

### Flow
Trace the relevant data dependencies or execution flow. Explain the types and values involved and distinguish pure transformations, deferred evaluation, and effects where that distinction matters. Follow typeclass instances or generated declarations only when they affect the answer. Do not infer an imperative execution order from the textual order of pure expressions. Cite source locations for the important steps.

### Files Read
Every file you read during exploration, with the relevant locations supporting your findings. Distinguish source-backed facts from inferences or unverified behavior.

### Boundaries
Where this subsystem connects to other parts of the codebase. The inputs and outputs. For relationships between services, name the records involved, the operations used, and where the dependencies are wired. Distinguish the service contract from its concrete implementation and explain which service owns the responsibility relevant to the question.

### Non-Obvious Things
Anything surprising, historically motivated, or easy to get wrong. Things that look like they should work one way but work another.

### Open Questions
Anything you couldn't fully trace or understand. Be honest about gaps.
