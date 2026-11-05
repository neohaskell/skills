# Wire boundaries

## Values and compatibility

Treat a missing key, explicit `null`, empty string, empty collection, and zero as distinct until the contract equates them. Check both request construction and response decoding. A TypeScript optional property does not prove the backend accepts omission, and a schema marked nullable does not make a field optional. Include representative serialized values for changed cases.

Keep the documented enum values and unknown-value behavior. A domain ADT may already have the correct JSON/schema instances. Do not convert every enum to `Text`; an explicit stable representation is a conscious wire-contract decision. Keep identifiers opaque, preserve precision and date/time conventions, and avoid converting large numeric identifiers through a lossy browser number.

Generated API markers may supply JSON/schema instances. Inspect the compatible guide and generated result before adding conflicting instances. Version deployed or persisted contracts through [compatibility guidance](../../neo-immutability-and-versioning/SKILL.md).

## Identity, errors, and transport

Use the consumer's real authentication policy. Session cookie, bearer token, service identity, or deliberate public access must follow the actual endpoint. Separate authentication from resource authorization, existence, and consistency. Browser-supplied IDs remain untrusted. Never expose server secrets through public build variables or client bundles.

Preserve structured domain rejection, authentication/authorization responses, validation errors, transport failures, cancellation, and retryability. Do not turn every failure into an empty success. Keep safe user-facing messages separate from operational detail, and redact tokens/credentials in logs.

Resolve base URL and path according to existing routing and deployment. Check prefix preservation, escaping, query encoding, credential mode, and CORS only where they apply. Do not hardcode localhost or infer readiness from an open port. Retry only operations whose duplicate behavior is known; preserve existing idempotency keys and correlation identifiers.

## Commands and eventual results

An HTTP acceptance or returned command ID is not the requested effect. Correlate the created resource and observe its query, persisted state, or downstream result until the specified predicate or a finite timeout. A rejection, delayed result, timeout, and actual completion need distinct caller states. Do not poll an unrelated collection and declare success because any item exists.

## Uploads

Discover whether the flow uses multipart, direct upload, signed URLs, or another existing mechanism. Preserve field names, content type, limits, expiry, authorization, completion confirmation, and cancellation behavior. Let the transport produce multipart boundaries. A successful object upload may precede the business command that attaches the object; observe both when both are promised. Treat upload tokens and signed URLs as sensitive values.

## Evidence boundaries

A decoder fixture establishes acceptance of that fixture. A mocked transport can establish the request method/path/body and client reactions. A real backend run establishes only the observed revision, identity, configuration, and outcome. Browser evidence additionally shows the exercised interface path. Keep those claims separate and use the smallest boundary needed for the requested change.
