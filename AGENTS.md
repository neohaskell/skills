# Repository instructions

## English-only persistence

Write all persisted content in English. This includes documentation, skills,
examples, code comments, human-readable script output, generated artifacts,
issue-tracker text, commit messages, pull requests, and release notes.

Use English filenames and directory names. Translate existing non-English prose
when working in this repository and update references when renaming its files.
Preserve the meaning, requirements, and decisions during translation.

Keep exact API identifiers, protocol fields, external URLs, proper names, and
required original license notices intact. They are identifiers or attribution,
not an alternative language for repository prose.

## Domain documentation

Use the root `GLOSSARY.md` and `docs/adr/` as the existing single-context layout.
Read relevant decisions before changing their subject. Keep temporary task
evidence outside reusable skill resources.

## Collection maintenance

Follow the agreed NH-152 scope and ADR 0005 extension: preserve the 27 historical
skill names, adapt the 65 selected upstream skills with `nh-` names, and include
the five application additions (including `nh-frontend-setup`), for 97 skills.
Keep resources inside their owning skill and use relative links between skills.
Git records content and history; do not add a separate catalog or provenance
manifest. Evaluation campaigns and acceptance certification are excluded from
this delivery.

## Finish collection changes with a release

For implementation or maintenance tasks that change the distributed skill
collection, completion includes committing, pushing, and publishing a new GitHub
release. This is standing authorization: proceed automatically without asking
again, unless the user explicitly limits the task to local work.

1. Run the checks appropriate to the change and review the final diff. Identify
   the task's changes and preserve unrelated work in the checkout.
2. Choose the next unused version under the semantic-versioning rules in
   [ADR 0001](docs/adr/0001-collection-distribution.md). Update `CHANGELOG.md`
   with the delivered behavior and validation actually performed.
3. Commit only the task and release changes, push the intended branch to the
   repository's remote, and publish the new immutable version tag and GitHub release for
   that exact validated commit. Include its full SHA and installation command
   in the release notes. Preserve existing tags and remote history.
4. Verify the remote branch, tag, and published release resolve to the intended
   commit before marking the task complete. Report the version and release URL.
   If pushing or publishing fails, report the exact blocker and leave delivery
   incomplete; inspect remote state before retrying a partial publication.
