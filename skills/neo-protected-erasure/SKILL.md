---
name: neo-protected-erasure
description: Use when a NeoHaskell application must erase a protected value while retaining its event history and selected business facts. Guides command, event, entity, query, outbound integration, configuration, and recovery choices.
---

# Build application-owned protected erasure

Use this skill alongside `implement-command`, `implement-event-and-update-entity`, `implement-query`, `implement-integration`, and `neo-config-and-secrets` for their respective files. The application chooses its retention and authorization policy. The example below retains a case status for illustration. Do not copy that policy into an unrelated product.

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

## Configure and verify

Use PostgreSQL for protected event storage. Supply `PostgresEventStore.erasableApplicationScope` as a stable, nonempty application identifier. Configure the PostgreSQL host, port, database, user, password, pool size, and TLS options through application configuration; mark the password secret. Install this skill in a generated project with `neo skills setup --tool codex --skill neo-protected-erasure`, or replace `codex` with the selected supported tool. Setup fetches the published `neohaskell/skills` repository.

Run the application through a command that creates a protected event. Read the authorized query while the value is `Available`, request erasure, then read `Erased` with the chosen retained facts intact. `Available` containing an optional null is distinct from `Erased`. Test an unknown reference, an unauthorized caller, an operational failure, a rejected result callback, an explicit retry, and a process restart. Rebuild the query from persisted events after erasure and assert the retained outcome without consulting erased inputs. Exercise concurrent tasks and independent pools in one application instance, followed by restart and reconnect. The maintained NeoHaskell testbed example and its exact run commands live in the framework repository's `testbed/README.md` under "Application-owned erasure".

The active-store key deletion does not erase backups, WAL, replicas, or plaintext already delivered to a client. The deployer must set retention and restore procedures and preserve erasure intent across a restore. An old backup with an old key can recover old data. This workflow does not certify GDPR compliance.
