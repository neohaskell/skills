---
name: nh-skills
description: Install, explicitly upgrade, or recover the complete NeoHaskell skill collection in a consumer project using pinned npx skills and Git, preserving customized and unrelated files.
---

# Maintain the complete collection

This is the collection's single maintenance entry. Operate only in the authorized consumer Git root. Keep application changes separate. The collection version, installer version, and effective framework revision are different identities. Upstream synchronization of this publishing repository is a separate operation from upgrading a consumer.

Use Node >=22.20.0 and **skills@1.7.6**. Install every skill for **Codex and Claude Code**, with canonical files in `.agents/skills/`, relative links in `.claude/skills/`, and `skills-lock.json` committed together. No global/selective installation, silent update, Neo CLI manager, or additional public maintenance command belongs to this contract.

1. Select the actual immutable release and read its changes/migration notes. Resolve its full 40-character commit SHA. Identify the installed release from collection entries in the lock and Git history; verify it against the old published content. A clean worktree or matching lock hash does not establish that installed files are uncustomized.
2. Follow [prepare and compare](references/prepare-and-compare.md). The internal [comparison helper](scripts/compare.py) compares every installed file against the complete old release, including committed customizations, and blocks path/lock collisions or unknown ownership. It never overwrites or removes files. If identity is insufficient or custom files exist, stop replacement and preserve them; explain the exact conflict. Keep extensions in separate skill directories.
3. Once the comparison is clear and the concrete change is authorized, follow [apply and reconcile](references/apply-and-reconcile.md). Use `add` with the explicit new SHA and both agents. `update -p` follows the recorded ref; it does not jump to the chosen release. Reconcile owned removals/renames explicitly after confirmation for destructive actions.
4. Inspect canonical resources, links, lock entries, and unrelated-file preservation together. Commit the update separately using only the established owned paths. Do not claim host behavior was exercised merely because files exist. If an installer run fails, preserve the failed state for diagnosis and follow [recovery](references/recovery.md) before retrying.
5. Report old/new release SHAs, the separate update commit, additions/removals/migrations, preserved extensions, and any limitation. Rollback reverts the **whole update commit**, restoring files, resources, lock, and links together. Never restore arbitrary paths based only on a lock entry.
