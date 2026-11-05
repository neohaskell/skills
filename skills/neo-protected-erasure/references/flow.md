# Implement the application-owned erasure protocol

Use only the branch needed by the task. Resolve the application revision and capabilities through [nh-app-context](../../nh-app-context/SKILL.md) before adapting API examples. The existing consumer layout and compatible API guide determine the actual imports, markers, and commands.

## Decide what the application retains

1. List each personal input, its copies and derivatives, event metadata, query field, log, export, and external effect. Put a value in `Erasable` only if erasing its key can remove every required active read of that value. A derived name, hash, or search label may need its own protected reference or a separate retention decision.
2. Separate decision inputs from recorded outcomes. For example, a name used to decide eligibility is an input; the recorded eligibility outcome may be a retained business fact if the application's policy permits it. Record the chosen outcome explicitly in the event. Do not reconstruct it from an erased input.
3. Record which facts remain after erasure and why. Review owner identifiers and event metadata as possible personal derivatives. The example may retain an owner identifier to authorize retries; another application may need a different model.


## Implement the event flow

1. Create each independently erasable value with a separate `Erasable.new` call inside `decide`. Store `Erasable value` in the event, entity, and managed query fields. A copy or `Erasable.map` keeps the reference. Do not expose ordinary plaintext JSON or an extractor as a convenience API.
2. Keep the command's authorization check on the loaded entity. For an erasure request, check the authenticated user and confirm that the supplied reference belongs to the owned entity. `Erasable.reference` is metadata for an authorized lookup, not authority to erase.
3. Append a pending request event before the outbound effect. Use `Integration.outbound` with `Integration.Erasable.Erase`, one `ErasureTarget` per invocation, and `onResult` and `onFailure` callbacks that emit application commands. Set the target's reference, owning entity name, and stream ID. Register the outbound handler with `Application.withOutbound`.
4. Record completion only when the result command commits an event. Handle `ErasedNow` and `AlreadyErased` as successful key outcomes, `UnknownReference` as a separate failure, and operational or scope errors through `onFailure`. A runner's `Processed` log does not prove application completion.
5. Expose an owner-authorized retry for pending or failed requests. On restart, reconstruct the entity and query, find unresolved requests, and retry them explicitly. A retry after a committed deletion can return `AlreadyErased`. The framework does not replay an application result automatically.

