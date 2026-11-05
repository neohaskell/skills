# Journey states

| Boundary | Questions that change the implementation |
|---|---|
| Entry and navigation | Can the intended user reach the screen directly and through existing navigation? Do back, refresh, deep links, and selected resource identity behave according to the application? |
| Loading and empty | Is a pending request distinct from a completed empty result? Does loading preserve useful context and avoid duplicate submissions? Does an empty result offer the appropriate next action? |
| Forms | Are labels, instructions, validation, keyboard order, focus, and submitted values connected? Are server-side field errors shown without erasing valid work? |
| Failure and permissions | Can the user distinguish retryable failure, expired identity, denied action, and unavailable resource where the policy permits disclosure? Is recovery available without inventing privileges? |
| Completion | Does the UI wait for the promised outcome, keep the relevant identifier, and update the right view? Are pending, partial, cancelled, failed, and completed operations represented where reachable? |

Use native semantics and the existing design system for interactive elements. Keep visible focus, accessible names, adequate contrast, and keyboard operation. Announce dynamic status through the established accessible pattern. Do not replace buttons with clickable containers or encode state by color alone.

For asynchronous operations, handle stale responses, navigation away, cancellation, and repeated action according to the existing data layer. Preserve user-entered data when a retry is safe. An optimistic update needs a defined reconciliation or rollback path; it does not prove persistence.

Use the consumer's responsive breakpoints and content constraints. Check the viewports that could be affected by the change, including long text or empty data when relevant. Keep reduced-motion and localization behavior already supported. Persist repository text and filenames in English; retain externally defined identifiers and required localization keys as identifiers.

Mock data is useful for displaying states that are otherwise hard to reach. Label it as simulated evidence. To claim the real end-to-end journey, observe the actual action, request identity, and resulting application state through the real backend configuration.
