# State change

Use when a user or system requests a business transition. Name the imperative command, its actor, authoritative preconditions, emitted past-tense facts, and rejection behavior. Connect `commandProducesEvent` edges. Multiple facts from one accepted decision can belong to one state change. Include a `uiPlaceholder` and `commandFromUI` edge when the requested journey has an interface. Record examples for success and each meaningful rejection.

Use the [canonical schema](event-model.schema.json) and [JSON example](design-json.md) for exact structure.
