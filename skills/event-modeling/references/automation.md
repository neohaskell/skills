# Automation

Use when recorded facts trigger a conditional reaction. Name the triggering event, condition, intended command/action, destination, and observable result. Connect `eventTriggersIntegration` and `integrationTriggersCommand` where those node types apply. Model retries, idempotency, failure, and pending states when the requested effect needs them. Do not invent a conditional automation merely to split one unconditional state change into more nodes.

Use the [canonical schema](event-model.schema.json) and [JSON example](design-json.md) for exact structure.
