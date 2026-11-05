# Apply and reconcile

The comparison must be clear immediately before installation. Avoid concurrent writers to the managed directories. Resolve every placeholder below to the selected immutable release; never run a placeholder or a truncated SHA.

```sh
npx --yes skills@1.7.6 add "neohaskell/skills#$NH_SKILLS_SHA" --skill '*' --agent codex claude-code --yes
```

Run from the consumer Git root. The installer can replace whole folders and does not merge customizations. It can leave old catalog names after removals or renames. It may fall back to copies when symlink creation fails; the collection's relative-link contract still needs resolution before claiming a successful update.

## Owned removals and renames

Use only the old-minus-new names in the clear comparison. Each name must have been present in the old release, matched its complete old bytes, and had the verified collection lock entry and Claude link. Recompare that obsolete directory/link immediately before deletion; stop if it changed after the snapshot. Confirm the concrete destructive removal if not already authorized.

Remove only that canonical skill directory and its relative Claude link. Delete only its matching key from `skills-lock.json`, preserving every third-party key and all unrelated fields. Do not clear either host's whole skills directory, remove consumer instructions, use a wildcard removal, or assume a renamed skill is safe because the new name resembles the old one. Update caller references according to the release migration notes and review them as part of the separate collection change.

The internal helper deliberately does not perform deletions. Its before-phase establishes ownership; the agent performs the reviewed, explicitly scoped reconciliation using ordinary filesystem/Git tools. If an old name contains a customization, leave it intact until the user chooses its migration.

## Inspect the result

Run the same helper with `after` and the same consumer, source repository, old/new SHAs, and snapshot path. It checks target-release bytes, executable flags, relative Claude links, new lock source/ref/path shape, absence of old-only names, and unchanged third-party paths/lock entries. This checks the operation's file result; it is not a host execution or application compatibility certification.

Inspect `git diff` and stage only the resulting owned content, lock, links, and explicitly migrated references. Ensure all additions and deletions are included, no application edits are staged, and no temporary snapshot/log is staged. Commit the collection change separately. Record the actual commit in the result so recovery has a concrete unit.

An initial installation has the same collision and preservation requirements. No lock-only restore is promised: the lock is not a complete description of both host destinations or removal history. For recovery of an existing committed installation, prefer its recorded whole-tree Git state.
