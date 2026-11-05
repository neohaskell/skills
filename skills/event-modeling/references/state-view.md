# State view

Use when a consumer needs a read model. Identify the reader and decision the view supports, then trace each field to source facts or a deterministic derivation. Connect `eventFeedsQuery` edges and, when applicable, `queryToUI` edges. State visibility policy, empty states, and eventual-consistency behavior. A view does not become authoritative state for a command simply because the UI displays it.

Use the [canonical schema](event-model.schema.json) and [JSON example](design-json.md) for exact structure.
