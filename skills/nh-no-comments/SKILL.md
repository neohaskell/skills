---
name: nh-no-comments
description: "Delegate to a comment reviewer, fix accepted findings, and offer encodings for claimed constraints."
---

> Adapted for consumer applications from the public NeoHaskell project.

# No comments

Use [nh-roles](../nh-roles/SKILL.md) to resolve authorized delegation. When a separate reviewer is available, delegate and act on accepted findings. Otherwise apply the same review instructions inline and report that the review was not independent.

## Scope

Use the caller's files or diff. Otherwise discover the PR base or configured upstream base and include the working tree in the scoped diff. If the base is unresolved, report it and review only the explicitly identified files; do not assume `main`.

Compiler pragmas, preprocessor directives and tool-consumed annotations are not ordinary prose comments. Trace their owning compiler/tool contract. The reviewer flags any required changes for the coordinator; those changes belong in the scoped implementation/configuration work. Public API Haddock, including examples that specify the contract, qualifies for the existing public-contract exception. For new Haskell modules, also apply [module documentation](../nh-module-docs/SKILL.md). A missing required header is a finding, not a reason to skip its review.

## Steps

1. Delegate to a comment reviewer using the complete [reviewer instructions](references/comment-reviewer.md). Pass the scope. Follow the delegation instructions in `AGENTS.md`. Do not restate the reviewer rules.
2. Inspect its report and diff. Reject implementation-code edits, semantic-directive changes, scope escapes, exception-protected deletions, misstated `MUST KILL` reasons, and flags that treat kept intentional code as guilty. Reshape flags on our-code surprises stay actionable. Do not restore those comments. A keep survives only with scoped proof of an exception in the reviewer instructions; apply the full exception list. Audit missed scoped HLint and compiler-warning suppressions. Correctness or safety suppressions stay actionable `MUST KILL`s; handle semantic-directive changes through the scoped implementation steps, not comment-only deletion. Restore deletions only with exact exceptions and scoped proof. Before accepting thin `IMPORTANT` or `do not remove` kills or keeps, run `/nh-how` or `/nh-why` on their symbol. If a kill is ambiguous, do not restore. If a keep is refuted or still ambiguous, delete it. Revert and rerun one rejected report with the failure named. Reject a second, report it open, and fail `/nh-no-comments`.
3. Fix trivial accepted flags directly by deleting a dead path, dropping a parameter, or using the real API. If any fix needs a shape, run `/nh-architect` once for the accepted set and surrounding code. Stop at the sketch. Architect shapes. Step 4 implements.
4. Implement the smallest root-cause fix in scope. Remove every named workaround. If the root cause is out of scope, land the smallest in-scope fix and report the rest open. The **nh-principle-fix-root-causes** and **nh-principle-redesign-from-first-principles** skills guide intent only. Neither authorizes widening the fence nor fixing instances outside it. Never bolt on symptom guards.
5. Constraint comments say `do not remove`, `do not change wording`, or `talk to X before changing`. Leave comments that satisfy a proven exception in the reviewer instructions. Offer the cheapest in-scope type, runtime, test, or CI lint. Apply it when the caller has authorized that implementation work; otherwise leave the encoding proposal open. Delete an exception-protected comment only after its constraint has an equivalent maintained encoding. Preserve protected comments while an encoding is pending, and report out-of-scope work.
6. Report the deletion count, restored comments, reruns, architect sketch, fixes, encoding offers, encodings, unenforced constraints, and other open work.
