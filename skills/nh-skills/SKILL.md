---
name: nh-skills
description: Install, explicitly upgrade, or recover the complete NeoHaskell skill collection in a consumer project, preserving customized and unrelated files.
---

# Maintain the complete collection

This is the collection's single maintenance entry. Operate only in the authorized consumer Git root. Keep application changes separate. The collection version, installer version, and effective framework revision are different identities. Upstream synchronization of this publishing repository is a separate operation from upgrading a consumer.

Use Node >=22.20.0. Install the complete collection in the project for the user's chosen agent. Commit installed content, the lockfile, and any agent links together. Keep application extensions in separate skill directories.

## First installation

For a project without an existing collection installation or conflicting skill names, run:

```sh
npx skills add neohaskell/skills --skill '*'
```

Let the user choose their agent and project scope through the installer, or pass the already-requested agent with `--agent`. Use the current installer and default branch; release lookup, SHA validation, and the comparison helper are not prerequisites for this path. If existing content would be replaced, use the update guidance below. Review and commit the resulting installation separately from application changes.

## Update a quick-start installation

1. Identify the collection's installed paths, lock entries, selected agents, and original installation commit. Compare current files with that original content, including committed customizations. If the original commit includes customizations or cannot be established, identify the exact upstream baseline before replacement; preserve files while resolving uncertainty.
2. Select the target upstream revision and inspect its changes. Compare complete old and target skill folders, including resources, to identify additions, removals, and collisions. Preserve unrelated skills and lock entries. Resolve customizations before running an installer that replaces folders.
3. Apply the chosen revision with `npx skills add`, selecting every skill and retaining the user's agent selection and installation layout. Verify the installed content against that revision. Remove obsolete paths only after establishing ownership and confirming destructive changes. Review all content, links, and lock changes in a separate update commit; record the target revision and actual validation performed.

The [comparison helper](scripts/compare.py) requires the pinned dual-agent layout described below. For other layouts, compare content and ownership with Git and filesystem tools; do not change the user's installation merely to satisfy the helper. For interrupted installations or rollback, follow [recovery](references/recovery.md).

## Explicit release-pinned installation or update

Use this procedure when the user requests a pinned installation for both **Codex and Claude Code**, or maintains an existing installation in that form. It uses **skills@1.7.6**, canonical files in `.agents/skills/`, relative links in `.claude/skills/`, and `skills-lock.json` committed together.

1. Select the actual immutable release and read its changes/migration notes. Resolve its full 40-character commit SHA. Identify the installed release from collection entries in the lock and Git history; verify it against the old published content. A clean worktree or matching lock hash does not establish that installed files are uncustomized.
2. Follow [prepare and compare](references/prepare-and-compare.md). The internal [comparison helper](scripts/compare.py) compares every installed file against the complete old release, including committed customizations, and blocks path/lock collisions or unknown ownership. It never overwrites or removes files. If identity is insufficient or custom files exist, stop replacement and preserve them; explain the exact conflict. Keep extensions in separate skill directories.
3. Once the comparison is clear and the concrete change is authorized, follow [apply and reconcile](references/apply-and-reconcile.md). Use `add` with the explicit new SHA and both agents. `update -p` follows the recorded ref; it does not jump to the chosen release. Reconcile owned removals/renames explicitly after confirmation for destructive actions.
4. Inspect canonical resources, links, lock entries, and unrelated-file preservation together. Commit the update separately using only the established owned paths. Do not claim host behavior was exercised merely because files exist. If an installer run fails, preserve the failed state for diagnosis and follow [recovery](references/recovery.md) before retrying.
5. Report old/new release SHAs, the separate update commit, additions/removals/migrations, preserved extensions, and any limitation. Rollback reverts the **whole update commit**, restoring files, resources, lock, and links together. Never restore arbitrary paths based only on a lock entry.
