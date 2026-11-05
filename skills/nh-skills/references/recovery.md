# Recover a complete installation

For a committed update, inspect the identified update commit and the current worktree. Preserve later application changes. Revert the whole update commit with Git, resolving genuine conflicts without replacing unrelated files. Review canonical content/resources, relative Claude links, lock entries, and added/removed names together before committing the revert. A whole-commit revert restores the previous recorded collection state; it does not undo external effects caused by later use of a skill.

For an interrupted, uncommitted installation, stop further installer runs. Compare the failed state with the known pre-update Git baseline and temporary snapshot. The snapshot proves expected fingerprints; it is not a content backup. Recover only the established owned paths from that baseline, with confirmation before discarding changes. Preserve unexpected concurrent edits separately. Remove only newly created collection paths whose ownership and unchanged content are established. Restore the old lock without losing third-party changes, and restore the old relative links. Review the complete diff before retrying.

If the pre-update content was never committed or otherwise preserved, do not promise automatic rollback. Obtain the exact old release, retain custom files, and reconcile with the user. Reinstalling an old release blindly can overwrite customizations and leave new names behind. Neither `git restore` of all skill paths nor a lock-derived bulk delete is a safe substitute for known ownership.

This collection has no silent synchronization. Upgrading its publishing source from public upstream and upgrading an application's installed release are separate, explicit changes with their own reviewable diffs.
