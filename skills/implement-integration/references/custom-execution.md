# Custom action execution

First inspect the effective revision's integration extension API. When an existing declarative action already performs the effect, configure it instead of building a second executor. Use lifecycle only when the application must own resources across events.

At the researched public revision `f09b360025d842e5ad9bc471f46af91e43cbdab7`, `Integration` exports `ToAction`, `action`, `emitCommand`, `noCommand`, `runAction`, and `getActions`. A custom `ToAction` converts a typed configuration value into an action whose execution receives the runtime context. Keep the pure handler responsible for selecting destination and payload; keep transport calls, failures, and result commands in the executor. The runtime owns the action context; do not copy its construction from an unrelated framework test fixture.

Resolve the actual method signatures from the compatible guide before implementation. Specify timeouts, cancellation, owned resources, idempotency keys, retryable versus permanent failures, and result callbacks only as supported by the API. A failed decode of an owned event must remain visible; an unrelated event can legitimately produce no action.

Use `runAction` with the consumer's supported test context to assert emitted `CommandPayload.commandType` and `commandData`, or test the typed plan consumed by the executor. For real transport delivery, exercise the configured application against the intended safe destination and observe the requested result. A mock or action count does not prove delivery.
