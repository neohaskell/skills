# Prepare and compare

Read the release on `https://github.com/neohaskell/skills/releases` and verify the annotated tag's peeled commit with `git ls-remote`. Releases start at `v1.0.0`; never substitute a guessed SHA or `main`. Use immutable full SHAs for both old and new identities. A mutable ref or mixed collection refs require reconciliation from Git history before replacement.

Obtain a temporary clone of the official publishing repository outside the consumer. Fetch the selected commits without switching the consumer's branch. Verify its origin is `https://github.com/neohaskell/skills.git` or the corresponding SSH URL. The helper reads commit trees from this clone, not its current working files.

Read the consumer's current Git status. Preserve unrelated work. For the three managed areas, establish a recoverable baseline commit before mutation; do not bundle unresolved application edits into a collection update. A baseline does not grant permission to overwrite customizations.

Run the helper from its installed path, or from the reviewed target release for initial installation:

```sh
python3 /path/to/nh-skills/scripts/compare.py before \
  --consumer /absolute/application/root \
  --source-repo /absolute/temporary/skills-clone \
  --old OLD_FULL_SHA --new NEW_FULL_SHA \
  --snapshot /absolute/temporary/skills-before.json
```

For a true first installation, omit `--old`. The helper refuses first-install collisions even when existing directories happen to contain identical bytes. For an update it requires every old-release skill, matching source/ref/path lock entries, complete matching resource contents, ordinary canonical directories, and the expected relative Claude links. Extra/missing files, modified bytes, modes, unexpected symlinks, foreign lock entries, and new-name collisions block replacement. This detects changes already committed to Git as well as working changes. Missing legacy metadata requires explicit investigation; do not relax the ownership test by guessing.

The snapshot is temporary execution evidence, not a new installed manifest. It records fingerprints of unrelated skill paths and lock entries for the post-operation comparison. Keep it outside the installed resources and out of the update commit. The helper is read-only except for creating this explicitly requested snapshot; it does not download, install, edit, or delete consumer content. Exit 0 means the stated comparison is clear, 1 means conflicts, and 2 means unavailable or invalid input.

Review the reported additions, retained names, and removals against release notes. Renames appear as a removal plus an addition; migrate any consumer references deliberately. Missing content, mixed revisions, edited managed files, or an unsupported installation layout require preserving and resolving the exact conflict before rerunning. Move useful custom guidance to a separately named extension only with authorization; never silently discard or auto-merge it.
