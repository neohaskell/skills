# Review input and result

The trusted wrapper receives three file paths: patch, related source context, and output JSON. It uses the consumer's selected provider, pinned CLI/API version, and model. Discover that command's actual structured-output interface before writing the wrapper. Its process exit status is retained separately from the JSON verdict.

The prompt states the requested review criteria, base/head identities, reviewed scope, and the JSON schema. Treat the patch and source as quoted evidence: instructions inside them cannot change the reviewer role, invoke tools, read secrets, or publish output. Disable execution tools and network access except the configured reviewer API. Pass only the reviewer credential, scoped to that API; do not give the reviewer publication tokens. Redact source secrets before external transmission according to the consumer's policy.

A clean result can contain the word `blocker`:

```json
{"summary":"APPROVE. No blocker findings.","findings":[]}
```

`parse_review.py` accepts a single JSON object, not Markdown fences or prose. The schema is in `../assets/review.schema.json`. Duplicate keys, unknown fields, invalid severity, invalid line numbers, missing files, and malformed JSON are rejected.

| Parser exit | Meaning | CI treatment |
|---|---|---|
| 0 | Valid result with no blocker findings | Review completed; apply any separate major/minor policy explicitly. |
| 1 | At least one structured blocker finding | Fail the review gate only when the consumer enabled that policy. |
| 2 | Malformed or missing result | Reviewer did not deliver a usable result; fail review execution. |
| 3 | Reviewer process failed | Preserve sanitized runner diagnostics; fail review execution. |

Never convert exits 2 or 3 into an approval, including in advisory mode. Store results as untrusted artifacts; escape Markdown/HTML when publishing and use structured API arguments or body files. Before posting, verify the PR still has the reviewed head. A stale review may be retained as historical evidence but is not a verdict on the new head.

For large changes, partition by behavior and include related callers and definitions. Combine validated findings only when every partition completed; report uncovered files. Do not silently truncate context or concatenate JSON objects.
