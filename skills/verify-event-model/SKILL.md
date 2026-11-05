---
name: verify-event-model
description: Review an application event model without editing it; report structural defects and separate methodology advice using machine-readable findings.
---

# Read-only event-model review

1. Identify the model path and schema version through [nh-app-context](../nh-app-context/SKILL.md). Inspect the whole model while focusing explanations on changed behavior.
2. Use the installed `neo validate --json MODEL` if its help confirms that interface and its validation coverage. For v1 mechanical checks that are unavailable or incomplete, run the [bundled validator](scripts/validate_model.py) with Python and `jsonschema` installed: `python3 PATH_TO_THIS_SKILL/scripts/validate_model.py MODEL`. Resolve the skill path from the installed file location. It reads the canonical schema owned by `event-modeling` and does not edit the model.
3. Review field traceability, meaningful causes, automations, UI edges, and domain vocabulary using [the checklist](references/event-model-checklist.md). Inspect the relevant finding category rather than loading every reference by default.
4. Emit JSON with `status`, `checks`, and `findings`; each finding has `category`, `severity`, `id`, `message`, and `fix`. Mark unexecuted checks as `not_run`. Structural failures block implementation; naming advice alone is advisory unless it causes a concrete ambiguity or contract defect.
5. Send concrete fixes to [event-modeling](../event-modeling/SKILL.md). A GO requires the applicable structural checks to have actually passed and functional design gaps to be resolved. Review remains separate from editing.

`neo inspect sync` regenerates the model from code and is not a read-only validator. Compilation and implementation are outside this review. The [schema](../event-modeling/references/event-model.schema.json) has one owner and one distributed copy.
