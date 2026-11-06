---
name: nh-module-docs
description: Write and review top-level Haddock for public application modules and other Haskell modules covered by the consumer's documentation policy, including generated templates and fixtures when applicable.
---

> Adapted for consumer applications from the public NeoHaskell project.

# Document each new module

Follow the consumer's module documentation policy. Each new public application module should have a concise top-level Haddock comment
before its `module` declaration. State the module's responsibility and normal
usage. The header explains the module as a whole. Operation names still need to
communicate what calls do under [Name for the reader](../nh-principle-name-for-the-reader/SKILL.md).

1. Inventory added Haskell files against the owning base with
   `git diff --name-status --diff-filter=A <owning-base> -- '*.hs'`.
   Include staged and untracked additions, application-owned generated module templates, and
   complete fixture modules that the diff command cannot enumerate.
2. Apply the consumer's policy to each entry. Write a required header when creating the module. Describe what it owns and how a
   caller normally uses it. Omit change history, implementation narration, and
   instructions to future agents.
3. Check every inventory entry before review. Read the exported contract and
   representative use to confirm that the header is accurate. Run the relevant
   compiler or Haddock check when markup, references, or generated output change.
4. Preserve qualifying module headers during
   [comment review](../nh-no-comments/references/comment-reviewer.md). Report missing
   or inaccurate headers as authoring defects instead of deleting the obligation.

This complete illustrative module owns a mail-delivery decision. Its header
states that responsibility and the caller's normal use.

```haskell
{-| Decide whether to attempt a mail delivery.
Call 'shouldDeliver' with the recipient's opt-in state before queuing mail.
-}
module Mail.DeliveryPolicy (shouldDeliver) where

import Core

shouldDeliver :: Bool -> Bool
shouldDeliver optedIn = optedIn
```

The illustrative predicate only models opt-in. Real policy belongs in its owning
module and must state any stronger guarantee it promises.
